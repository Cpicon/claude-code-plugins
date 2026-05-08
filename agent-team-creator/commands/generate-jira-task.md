---
name: generate-jira-task
description: Generate a Jira task from a debugging report with implementation guidance
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Edit
  - Bash
  - Task
  - AskUserQuestion
  - mcp__plugin_atlassian_atlassian__getVisibleJiraProjects
  - mcp__plugin_atlassian_atlassian__createJiraIssue
  - mcp__plugin_atlassian_atlassian__getAccessibleAtlassianResources
  - mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql
  - mcp__plugin_atlassian_atlassian__getJiraProjectIssueTypesMetadata
  - mcp__plugin_atlassian_atlassian__atlassianUserInfo
  - mcp__plugin_atlassian_atlassian__getJiraIssue
  - mcp__plugin_atlassian_atlassian__addCommentToJiraIssue
argument-hint: "[debugging-report-path]"
---

# Jira Task Generator

Transform debugging reports into well-structured Jira tasks with implementation guidance.

## Architecture Note

This command follows a **HYBRID architecture**:
- **Command handles**: All MCP operations (Jira API), file I/O, caching, user interaction
- **Agents handle**: Pure reasoning (`implementation-planner`) and formatting (`jira-writer`)

This separation avoids the known MCP access bug in plugin-defined agents (GitHub #13605, #15810).

## Prerequisites

- A debugging report from `/generate-debugger` workflow saved to `.claude/reports/debugging/`
- Atlassian MCP plugin configured (optional - falls back to markdown if unavailable)

---

## Execution Flow

Execute phases 0-6 in order. Track `JIRA_MODE` state throughout.

### Phase 0: Prerequisite Check

**Purpose**: Determine the Jira transport mode: MCP, REST, or OFFLINE.

**State variable**: `JIRA_MODE` — one of `"MCP"`, `"REST"`, `"OFFLINE"`

1. **Locate REST script** (for Step 3)

   Use Glob to find `**/agent-team-creator/scripts/jira_client.py`.
   If not found, try `~/.claude/plugins/agent-team-creator/scripts/jira_client.py`.
   Store the absolute path as `SCRIPT_PATH`, or `null` if not found.

2. **Step 1: Try Atlassian MCP**

   Call `mcp__plugin_atlassian_atlassian__getAccessibleAtlassianResources()`.

   - If the tool call **succeeds**: Continue to authentication check
   - If **fails** (tool not found or error): Fall through to Step 3

   Call `mcp__plugin_atlassian_atlassian__atlassianUserInfo()`.

   - If **succeeds**: Set `JIRA_MODE = "MCP"`. User is logged in. Skip to step 5.
   - If **fails** (401/403): Fall through to Step 3

3. **Step 2: Try REST API** (only if MCP failed)

   If `SCRIPT_PATH` is null: Set `JIRA_MODE = "OFFLINE"`. Skip to step 5.

   Check Python availability:
   Bash: `python3 --version`
   If fails: Set `JIRA_MODE = "OFFLINE"`. Skip to step 5.

   Check for cached REST credentials:
   Use Read tool to check if `.claude/jira-rest-config.json` exists.

   - If **file exists and has `baseUrl`, `email`, `apiToken`**:
     - Validate credentials:
       Bash: `python3 {SCRIPT_PATH} --action verify-auth --config .claude/jira-rest-config.json`
     - If exit 0: Set `JIRA_MODE = "REST"`. Skip to step 5.
     - If exit 1: Delete stale config file. Fall through to Step 4.
   - If **file missing or invalid**: Fall through to Step 4.

4. **Step 3: Prompt for REST credentials** (only if no valid config)

   Ask user via AskUserQuestion: "Atlassian MCP is unavailable. Would you like to configure the REST API fallback?"

   Options:
   - "Yes, I have Jira API credentials"
   - "No, work offline (markdown drafts)"

   If **"No"**: Set `JIRA_MODE = "OFFLINE"`. Skip to step 5.

   If **"Yes"**:
   - Ask: "Enter your Atlassian site URL (e.g., https://yoursite.atlassian.net):"
   - Ask: "Enter the email for your Atlassian account:"
   - Ask: "Enter your Jira API token (create at https://id.atlassian.com/manage-profile/security/api-tokens):"
   - Write credentials to `.claude/jira-rest-config.json`
   - Validate: Bash: `python3 {SCRIPT_PATH} --action verify-auth --config .claude/jira-rest-config.json`
   - If exit 0: Set `JIRA_MODE = "REST"`.
   - If exit 1: "Credentials invalid. Running in offline mode." Set `JIRA_MODE = "OFFLINE"`.

5. **Communicate mode to user**

   - If `JIRA_MODE = "MCP"`: "Connected to Jira via MCP plugin."
   - If `JIRA_MODE = "REST"`: "Connected to Jira via REST API."
   - If `JIRA_MODE = "OFFLINE"`: "Running in offline mode. Will generate markdown drafts."

**JIRA_MODE Effects**:
- `JIRA_MODE = "MCP"`: All phases run with MCP tools
- `JIRA_MODE = "REST"`: Skip Phase 1 (use cache/prompt), Skip Phase 3 (no duplicate check), Phase 6 uses REST script
- `JIRA_MODE = "OFFLINE"`: Skip Phase 1, Skip Phase 3, Phase 6 writes markdown drafts

---

### Phase 1: Project Resolution

> **SKIP if JIRA_MODE != "MCP"**. For REST and OFFLINE modes: read `.claude/jira-project.json` for cached project key. If no cache, ask user via AskUserQuestion: "Enter your Jira project key (e.g., PROJ):". Then proceed to Phase 2.

**Purpose**: Determine which Jira project to create the issue in.

1. **Check for cached project configuration**

   Use Read tool to check if `.claude/jira-project.json` exists.

   - If file exists:
     - Parse JSON for `projectKey`, `projectName`, `cloudId`
     - Validate cache is not corrupted (all required fields present)
     - If valid: Use cached values, notify user: "Using cached Jira project: [projectName] ([projectKey])"
     - Continue to Phase 2

2. **First-time setup** (if no cache or cache invalid)

   a. **Get Atlassian cloud ID**
      - Use the response from `getAccessibleAtlassianResources()` (already called in Phase 0)
      - Extract the first available `cloudId` from the response

   b. **Extract project name hint**
      - Try to get project name from the current directory name
      - Clean up: remove special characters, convert to search-friendly query

   c. **Search for matching Jira projects**

      Call `mcp__plugin_atlassian_atlassian__getVisibleJiraProjects`:
      ```
      cloudId: [extracted cloudId]
      searchString: [project name hint]
      maxResults: 10
      ```

   d. **Match and confirm with user**

      - If **exact match found** (case-insensitive):
        - Ask user via AskUserQuestion: "Found Jira project '[Name]' ([KEY]). Use this project for task creation?"
        - Options: "Yes, use this project" / "No, search for another"

      - If **multiple fuzzy matches**:
        - Display list of matching projects with names and keys
        - Ask user via AskUserQuestion: "Which project should Jira tasks be created in?"
        - Options: List each project as an option

      - If **no matches found**:
        - Ask user via AskUserQuestion: "No matching Jira project found. Please enter the exact Jira project key:"
        - Accept text input

   e. **Cache the selected project**

      Write to `.claude/jira-project.json`:
      ```json
      {
        "projectKey": "[selected key]",
        "projectName": "[project name]",
        "cloudId": "[cloud id]",
        "configuredAt": "[current ISO timestamp]",
        "configuredFrom": "[current working directory]"
      }
      ```

---

### Phase 2: Load Debugging Report

**Purpose**: Load and validate the debugging report that will be transformed into a Jira task.

1. **Determine report location**

   - If **argument provided** (debugging-report-path):
     - Use the provided file path directly

   - If **no argument**:
     - Use Glob tool to find files matching `.claude/reports/debugging/report-*.md`
     - Sort results by modification time (most recent first)
     - Select the most recent report

   - If **no reports found**:
     - Ask user via AskUserQuestion: "No debugging reports found. Please provide the path to a debugging report:"
     - Accept text input for file path

2. **Read the debugging report**

   Use Read tool to load the report content.

   - If read fails: Error and abort

3. **Validate report format**

   Check for required sections (using flexible header matching for `##` or `###`):
   - `Issue Summary` or `Reported Issue`
   - `Root Cause` or `Root Cause Analysis`
   - `Solutions` or `Recommended Fix`

   - If **any required section missing**:
     - Warn user: "Debugging report is missing sections: [list missing]. This may affect task quality."
     - Ask via AskUserQuestion: "Proceed with incomplete report?"
     - Options: "Yes, proceed anyway" / "No, abort"

   - If user chooses to abort: End execution

4. **Check report age** (optional warning)

   Extract timestamp from filename (format: `report-YYYY-MM-DD-HHmm.md`).

   - If report is older than 24 hours:
     - Warn user: "This debugging report is [X] days old. The codebase may have changed since then."

5. **Store report content**

   Keep the full report text for use in Phase 4.

6. **Detect update mode**

   Check if the report content starts with YAML frontmatter (`---` delimiter):
   - If the report begins with `---`, parse the YAML block between the first and second `---` delimiters
   - Look for a `jira_key` field in the parsed frontmatter

   **If `jira_key` is present and non-empty:**
   - Set `UPDATE_MODE = true`
   - Store the value as `EXISTING_JIRA_KEY`
   - Extract `jira_url` if present, store as `EXISTING_JIRA_URL`
   - Notify user: "This report is linked to Jira issue {EXISTING_JIRA_KEY}. Will update existing issue instead of creating a new one."
   - **Skip Phase 3 entirely** — proceed directly to Phase 4

   **If no frontmatter or no `jira_key`:**
   - Set `UPDATE_MODE = false`
   - Continue to Phase 3 as normal

---

### Phase 3: Duplicate Check

> **SKIP if JIRA_MODE != "MCP"**. Proceed directly to Phase 4.

**Purpose**: Check if a similar Jira issue already exists to prevent duplicates.

1. **Extract search keywords**

   From the debugging report, extract key terms:
   - From Issue Summary: main nouns and error types
   - From Root Cause: component names and technical terms
   - Limit to 5-7 most relevant keywords
   - Escape any JQL special characters

2. **Search for similar issues**

   Call `mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql`:
   ```
   cloudId: [cached from Phase 1]
   jql: "project = [projectKey] AND text ~ '[keyword1] [keyword2] [keyword3]' AND status != Done ORDER BY created DESC"
   maxResults: 5
   fields: ["summary", "status", "created", "key"]
   ```

3. **Evaluate search results**

   - If **no results**: Continue to Phase 4

   - If **results found**:
     - Display: "Found [N] potentially similar issues:"
     - For each result: "[KEY]: [Summary] (Status: [Status])"
     - Ask user via AskUserQuestion: "How would you like to proceed?"
     - Options:
       - For each found issue: "Update {KEY}: {Summary}" (shows as separate option per issue)
       - "Create new task anyway"
       - "Abort"

4. **Handle user choice**

   - If user selects "Update {KEY}":
     - Set `UPDATE_MODE = true`
     - Set `EXISTING_JIRA_KEY = {KEY}` (the key from the selected option)
     - Continue to Phase 4
   - If "Create new task": Set `UPDATE_MODE = false`, continue to Phase 4
   - If "Abort": End execution with message

---

### Phase 4: Implementation Planning

**Purpose**: Transform the debugging report into a structured implementation plan using an agent.

1. **Invoke implementation-planner agent**

   Use the Task tool with:
   - `subagent_type`: `"agent-team-creator:implementation-planner"`
   - `prompt`: The full debugging report content from Phase 2
   - `description`: "Create implementation plan from debugging report"

   Wait for agent to complete and receive the implementation plan output.

2. **Validate implementation-planner output**

   Check that the output contains required sections:
   - `## Problem Summary` - must exist
   - `## Recommended Approach` - must contain tier selection (Quick Fix, Proper Fix, or Comprehensive Fix)
   - `## Implementation Steps` - must have at least one step with `**File**:` or `**File(s)**:` reference
   - `## Testing Requirements` - must exist
   - `## Risk Assessment` - must exist

   - If **validation fails**:
     - List the missing sections
     - Ask user via AskUserQuestion: "Implementation plan is missing: [sections]. Proceed anyway?"
     - Options: "Yes, proceed" / "No, abort"

   - If user aborts: End execution

3. **Store implementation plan**

   Keep the full agent output for use in Phase 5.

---

### Phase 5: Jira Content Generation

**Purpose**: Format the debugging report and implementation plan into Jira-compatible content.

1. **Prepare combined input for jira-writer**

   **CRITICAL**: Format the input exactly as follows (jira-writer expects these headers):

   ```
   ## Debugging Report

   [Full debugging report content from Phase 2]

   ## Implementation Plan

   [Full implementation plan from Phase 4]
   ```

2. **Invoke jira-writer agent**

   Use the Task tool with:
   - `subagent_type`: `"agent-team-creator:jira-writer"`
   - `prompt`: The combined input formatted above
   - `description`: "Format debugging report for Jira"

   Wait for agent to complete and receive the Jira-formatted output.

3. **Determine issue type** (COMMAND responsibility, not agent)

   Scan the debugging report and implementation plan for keywords:

   **Bug indicators** (high confidence):
   - "error", "exception", "crash", "failure", "broken"
   - "bug", "defect", "incorrect", "wrong", "invalid"
   - "null pointer", "undefined", "NaN", "timeout"
   - "regression", "memory leak", "deadlock"

   **Task indicators**:
   - "enhancement", "improvement", "refactor"
   - "feature", "add", "implement", "optimize"
   - "cleanup", "tech debt"

   Decision logic:
   - If any bug indicator found: `issue_type = "Bug"`
   - Otherwise: `issue_type = "Task"`

4. **Generate and sanitize labels** (COMMAND responsibility)

   Extract label suggestions from:
   - Impact Assessment section (affected components, risk level)
   - jira-writer output (if it suggested labels)

   **Label categories**:
   - Affected components: `component:frontend`, `component:api`, `component:database`
   - Risk level: `priority:high`, `priority:critical`, `priority:medium`
   - Technical domain: `type:bugfix`, `type:security`, `type:performance`

   **Sanitization rules** (apply to each label):
   - Convert to lowercase
   - Replace spaces with hyphens
   - Remove special characters except hyphens, underscores, and colons
   - Truncate to 255 characters maximum

5. **Validate jira-writer output**

   Check for required fields:
   - `**Summary:**` - must exist and be under 255 characters
   - `**Description:**` - must exist
   - `**Acceptance Criteria:**` - should have at least one criterion (warning if missing)

   - If **critical fields missing** (Summary or Description):
     - Ask user via AskUserQuestion: "Jira content is missing required fields. Proceed anyway?"
     - Options: "Yes, proceed" / "No, abort"

6. **Parse jira-writer output**

   Extract fields using marker patterns:

   | Marker | How to Extract | Target |
   |--------|----------------|--------|
   | `**Summary:**` | Text after marker until newline, trimmed | summary |
   | `**Description:**` | All content from marker until next `**` field marker or end | description |
   | `**Labels:**` | Parse as comma-separated list or bracketed array | labels array |
   | `**Acceptance Criteria:**` | Include in description | (part of description) |

7. **Determine priority and assignee** (COMMAND responsibility)

   **Auto-derive priority** from the Impact Assessment section of the debugging report:

   | Impact wording | Mapped priority |
   |----------------|-----------------|
   | "critical", "highest", "P0" | `Highest` |
   | "high", "P1" | `High` |
   | "medium", "P2", or unclear | `Medium` (default) |
   | "low", "P3", "minor" | `Low` |
   | "lowest", "trivial" | `Lowest` |

   Store as `derivedPriority`.

   **Resolve current user accountId**:
   - `JIRA_MODE = "MCP"`: Call `mcp__plugin_atlassian_atlassian__atlassianUserInfo()` and extract `accountId` + `displayName`.
   - `JIRA_MODE = "REST"`: Bash `python3 {SCRIPT_PATH} --action get-current-user --config .claude/jira-rest-config.json`. Parse stdout for `accountId` + `displayName`.
   - `JIRA_MODE = "OFFLINE"`: Skip — assignment will be left blank in the markdown draft.

   Store as `currentUser = {accountId, displayName}`.

   **Confirm with user** via a single `AskUserQuestion` call with two questions:

   - **Q1 — Priority**: "Set ticket priority?"
     - Options:
       - `Use auto-derived ({derivedPriority})` (Recommended) → `selectedPriority = derivedPriority`
       - `Highest` / `High` / `Medium` / `Low` (3 most common alternatives, omit Lowest unless `derivedPriority == Lowest`)
     - Store the result as `selectedPriority`.

   - **Q2 — Assignee** (skip in OFFLINE mode):
     - Options:
       - `Assign to me ({currentUser.displayName})` (Recommended) → `selectedAssigneeAccountId = currentUser.accountId`
       - `Leave unassigned` → `selectedAssigneeAccountId = null`
     - Store the result as `selectedAssigneeAccountId`.

---

### REST API Call Pattern

When `JIRA_MODE = "REST"`, all Jira operations follow this pattern:

1. Create `.claude/tmp/` directory if it doesn't exist
2. Write JSON payload to `.claude/tmp/jira-payload.json`
3. Execute: `python3 {SCRIPT_PATH} --action {action} --config .claude/jira-rest-config.json [--issue-key {KEY}] [--payload-file .claude/tmp/jira-payload.json]`
4. Parse stdout JSON: `{ "ok": true, ... }` on success or `{ "ok": false, "error": "..." }` on failure
5. If exit code != 0: degrade to OFFLINE mode for this operation
6. Clean up: delete `.claude/tmp/jira-payload.json`

**Mid-execution auth failure**: If REST returns exit code 1 (auth error) after Phase 0 validated successfully, fall directly to the OFFLINE branch. Do NOT re-prompt for credentials or restart the cascade.

### Phase 6: Output Generation

**Purpose**: Create the Jira issue, update an existing one, or generate markdown draft.

#### If UPDATE_MODE = true and JIRA_MODE = "MCP" (Update Existing Issue)

1. **Prepare update content**

   The update should contain ONLY the latest changes, NOT the entire report.

   Invoke the `jira-writer` agent via Task tool with:
   - `subagent_type`: `"agent-team-creator:jira-writer"`
   - `prompt`: Format as a Jira comment update:
     ```
     ## Update Context

     This is an UPDATE to existing Jira issue {EXISTING_JIRA_KEY}.
     Format ONLY the new findings below as a concise Jira comment.
     Do NOT reproduce the full report — just the new information.

     ## New Findings

     [Extract only the Timeline History sections added since last sync,
      or if no Timeline History exists, extract the key differences
      between this report and what was originally sent to Jira]
     ```
   - `description`: "Format update for Jira comment"

2. **Post comment to Jira issue**

   Call `mcp__plugin_atlassian_atlassian__addCommentToJiraIssue`:
   ```
   cloudId: [cached from Phase 1]
   issueIdOrKey: [EXISTING_JIRA_KEY]
   commentBody: [formatted update from jira-writer]
   ```

   - If **succeeds**:
     - Display: "Updated Jira issue {EXISTING_JIRA_KEY} with new findings."
     - Display: "URL: {EXISTING_JIRA_URL or https://[site].atlassian.net/browse/[KEY]}"
   - If **fails**:
     - Save draft to `.claude/reports/jira-drafts/update-{KEY}-{timestamp}.md`
     - Display: "Failed to update {EXISTING_JIRA_KEY}. Draft saved to: [path]"
     - Display: "You can manually add this as a comment in Jira."

3. **Update report frontmatter**

   Use Edit tool to update the source report's YAML frontmatter:
   - Set `last_synced: {current ISO timestamp}`
   - If `jira_key` not already present, add it

#### If UPDATE_MODE = true and JIRA_MODE = "REST" (Update via REST)

1. **Prepare update content** — same jira-writer invocation as the MCP update path above.

2. **Write comment payload**

   Write to `.claude/tmp/jira-payload.json`:
   ```json
   {
     "body": "[formatted update content from jira-writer]"
   }
   ```

3. **Post comment via REST**

   Bash: `python3 {SCRIPT_PATH} --action add-comment --config .claude/jira-rest-config.json --issue-key {EXISTING_JIRA_KEY} --payload-file .claude/tmp/jira-payload.json`

   - If **exit 0**:
     - Display: "Updated Jira issue {EXISTING_JIRA_KEY} with new findings."
     - Read `baseUrl` from `.claude/jira-rest-config.json`
     - Display: "URL: {baseUrl}/browse/{EXISTING_JIRA_KEY}"
   - If **exit != 0**:
     - Save draft to `.claude/reports/jira-drafts/update-{EXISTING_JIRA_KEY}-{timestamp}.md`
     - Display: "REST API failed. Draft saved to: [path]"

4. **Update report frontmatter** — same as MCP path: set `last_synced: {timestamp}`

5. **Clean up** — delete `.claude/tmp/jira-payload.json`

#### If UPDATE_MODE = true and JIRA_MODE = "OFFLINE" (Update — No MCP)

1. Save the update content to `.claude/reports/jira-drafts/update-{EXISTING_JIRA_KEY}-{timestamp}.md`
2. Display: "Jira unavailable. Update draft saved to: [path]"
3. Display: "Add this content as a comment to {EXISTING_JIRA_KEY} manually."

#### If UPDATE_MODE = false and JIRA_MODE = "OFFLINE" (Create — No MCP)

1. **Create output directory**

   Ensure `.claude/reports/jira-drafts/` directory exists.
   Use Write tool to create a placeholder file if directory doesn't exist.

2. **Generate draft filename**

   Format: `draft-YYYY-MM-DD-HHmm.md`
   Example: `draft-2026-01-04-1530.md`

3. **Write draft file**

   Content structure:
   ```markdown
   # Jira Task Draft

   > Generated: [current timestamp]
   > Mode: Fallback (Atlassian MCP unavailable)
   > Issue Type: [Bug/Task]
   > Priority: [selectedPriority from Phase 5 step 7, or "Medium" if step 7 was skipped in OFFLINE mode]

   ---

   [Full jira-writer output]

   ---

   ## Generated Labels

   [label1, label2, label3]

   ---

   ## Manual Creation Instructions

   1. Copy the Summary and Description above
   2. Create a new issue in your Jira project
   3. Set the issue type to: [Bug/Task]
   4. Set priority to: [selectedPriority]
   5. Assign to yourself or a teammate (was skipped in offline mode)
   6. Add the labels listed above
   7. **Attach the source debug report file**: [absolute path to source/debug/report.md]
   8. Review and adjust as needed
   ```

4. **Notify user**

   Display:
   - "Jira draft saved to: .claude/reports/jira-drafts/[filename]"
   - "Copy this content into Jira to create the task manually."
   - Brief summary: "Issue Type: [type], Summary: [first 50 chars of summary]..."

#### If UPDATE_MODE = false and JIRA_MODE = "REST" (Create via REST)

1. **Resolve project key**

   - Read `.claude/jira-project.json` for cached `projectKey`
   - If no cache: Ask user via AskUserQuestion: "Enter your Jira project key (e.g., PROJ):"
   - Store as `projectKey`

2. **Validate issue type exists in project**

   Bash: `python3 {SCRIPT_PATH} --action get-issue-types --config .claude/jira-rest-config.json --project {projectKey}`

   - Parse the `issueTypes` array from stdout JSON
   - Check if the determined issue type (Bug or Task) exists (case-insensitive name match)
   - If not found, look for alternatives:
     - "Bug" alternatives: "Defect", "Issue", "Task"
     - "Task" alternatives: "Story", "Development Task", "Bug"
   - If an alternative is found: Use that type, notify user: "Issue type '[original]' not available. Using '[alternative]' instead."
   - If no suitable type found:
     - List available types (excluding subtask types where `subtask: true`)
     - Ask user via AskUserQuestion: "Which issue type should be used?"
     - Options: Each available non-subtask type as an option
   - If `get-issue-types` fails (exit != 0): Warn but proceed with the original type (Jira may still accept it)

3. **Write issue payload**

   Write to `.claude/tmp/jira-payload.json`. Include `priority` and `assignee_account_id` from Phase 5 step 7 (omit `assignee_account_id` if user chose "Leave unassigned"):
   ```json
   {
     "project_key": "[projectKey]",
     "issue_type": "[validated issue type from step 2]",
     "summary": "[extracted from jira-writer output]",
     "description": "[extracted from jira-writer output]",
     "labels": ["[sanitized labels from Phase 5]"],
     "priority": "[selectedPriority from Phase 5 step 7]",
     "assignee_account_id": "[selectedAssigneeAccountId from Phase 5 step 7, or omit key if null]"
   }
   ```

4. **Create issue via REST**

   Bash: `python3 {SCRIPT_PATH} --action create-issue --config .claude/jira-rest-config.json --payload-file .claude/tmp/jira-payload.json`

   - If **exit 0**:
     - Parse response: `key`, `url`
     - Read `baseUrl` from `.claude/jira-rest-config.json`
     - Display success:
       ```
       Successfully created Jira issue via REST API!

       Issue: [key]
       URL: {baseUrl}/browse/[key]
       Type: [validated issue type]
       Summary: [summary]
       ```
   - If **exit != 0**:
     - Save draft to `.claude/reports/jira-drafts/draft-{timestamp}.md`
     - Display: "REST API failed. Draft saved to: [path]"

5. **Attach source debug report to the new issue** (REST mode only)

   The source debugging report (path determined in Phase 2) is attached as a markdown file so the full original artifact lives on the ticket alongside the formatted summary.

   Bash: `python3 {SCRIPT_PATH} --action attach-file --config .claude/jira-rest-config.json --issue-key {key} --file-path {abs/path/to/source/debug/report.md}`

   - If **exit 0**: Append to the success display: `Attachment: {filename} ({size} bytes)`.
   - If **exit != 0**: Non-fatal. Display: `Note: failed to attach source report to {key} — you can attach it manually in Jira. (error: [error message])`. Do NOT abort.

6. **Store Jira link in source report** — same frontmatter logic as MCP path, but use `{baseUrl}/browse/{key}` for `jira_url`

7. **Clean up** — delete `.claude/tmp/jira-payload.json`

#### If UPDATE_MODE = false and JIRA_MODE = "MCP" (Create New Issue)

1. **Validate issue type exists in project**

   Call `mcp__plugin_atlassian_atlassian__getJiraProjectIssueTypesMetadata`:
   ```
   cloudId: [cached]
   projectIdOrKey: [cached projectKey]
   ```

   - Check if the determined issue type (Bug or Task) exists in the project
   - If not found, look for alternatives:
     - "Bug" alternatives: "Defect", "Issue"
     - "Task" alternatives: "Story", "Development Task"
   - If no suitable type found:
     - List available types
     - Ask user via AskUserQuestion to select one

2. **Create the Jira issue**

   Call `mcp__plugin_atlassian_atlassian__createJiraIssue`:
   ```
   cloudId: [cached]
   projectKey: [cached]
   issueTypeName: [validated issue type]
   summary: [extracted from jira-writer output]
   description: [extracted from jira-writer output - preserve markdown formatting]
   additional_fields: {
     labels: [sanitized labels array],
     priority: { name: "[selectedPriority from Phase 5 step 7]" },
     assignee: { accountId: "[selectedAssigneeAccountId from Phase 5 step 7]" }  // omit assignee key entirely if user chose "Leave unassigned"
   }
   ```

   **Note**: file attachment is not supported by the Atlassian MCP tools today — in MCP mode the source debug report is NOT attached. The full report content is already embedded in the description via jira-writer.

3. **Handle success**

   - Extract issue key from response (e.g., "PROJ-123")
   - Construct issue URL: `https://[site].atlassian.net/browse/[issue-key]`
   - Display success message:
     ```
     Successfully created Jira issue!

     Issue: [ISSUE-KEY]
     URL: [issue URL]
     Type: [Bug/Task]
     Summary: [summary]
     Labels: [label1, label2, ...]
     ```

4. **Handle errors**

   If `createJiraIssue` fails:

   | Error Type | Recovery Action |
   |------------|-----------------|
   | 401/403 Unauthorized | "Authentication failed. Please run `claude mcp auth --server atlassian`" |
   | 400 Field Validation | Show which field failed, offer to save as draft |
   | 404 Project Not Found | Clear cache file, suggest re-running command |
   | Network Error | Retry once, then fall back to markdown |

   On any failure:
   - Save content to `.claude/reports/jira-drafts/draft-[timestamp].md`
   - Notify user: "Failed to create Jira issue: [error]. Saved draft to: [path]"

5. **Store Jira link in source report**

   Use Edit tool to add YAML frontmatter to the top of the source debugging report.

   If the report already starts with `---` (has frontmatter):
   - Add or update: `jira_key: {ISSUE-KEY}`
   - Add or update: `jira_url: https://[site].atlassian.net/browse/{ISSUE-KEY}`
   - Add or update: `last_synced: {current ISO timestamp}`

   If the report has no frontmatter:
   - Prepend to the file:
     ```
     ---
     jira_key: {ISSUE-KEY}
     jira_url: https://[site].atlassian.net/browse/{ISSUE-KEY}
     created: {timestamp extracted from report filename}
     last_synced: {current ISO timestamp}
     ---

     ```

   This establishes the bidirectional link so future runs detect update mode.

---

## Usage Examples

```
# Use most recent debugging report
/agent-team-creator:generate-jira-task

# Specify a particular report
/agent-team-creator:generate-jira-task .claude/reports/debugging/report-2026-01-03-1530.md
```

## Output

**Normal mode**: Jira issue key (e.g., PROJ-123) with URL

**Fallback mode**: Markdown draft file in `.claude/reports/jira-drafts/`
