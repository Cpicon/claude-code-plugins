---
name: generate-jira-task
description: Generate a Jira task from a debugging report with implementation guidance
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Task
  - AskUserQuestion
  - mcp__plugin_atlassian_atlassian__getVisibleJiraProjects
  - mcp__plugin_atlassian_atlassian__createJiraIssue
  - mcp__plugin_atlassian_atlassian__getAccessibleAtlassianResources
  - mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql
  - mcp__plugin_atlassian_atlassian__getJiraProjectIssueTypesMetadata
  - mcp__plugin_atlassian_atlassian__atlassianUserInfo
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

Execute phases 0-6 in order. Track `FALLBACK_MODE` state throughout.

### Phase 0: Prerequisite Check

**Purpose**: Determine if Atlassian MCP is available and authenticated.

1. **Check Atlassian plugin availability**

   Call `mcp__plugin_atlassian_atlassian__getAccessibleAtlassianResources()`.

   - If the tool call **fails** (tool not found or error):
     - Set `FALLBACK_MODE = true`
     - Notify user: "Atlassian MCP plugin not available. Will generate markdown draft for manual Jira creation."
   - If **succeeds**: Continue to authentication check

2. **Verify Atlassian authentication** (only if plugin available)

   Call `mcp__plugin_atlassian_atlassian__atlassianUserInfo()`.

   - If **fails** (401/403 or empty response):
     - Set `FALLBACK_MODE = true`
     - Notify user: "Not authenticated with Atlassian. Please run `claude mcp auth --server atlassian` to authenticate. Generating markdown draft instead."
   - If **succeeds**: User is logged in, continue with normal mode

3. **Communicate mode to user**

   - If `FALLBACK_MODE = true`: "Running in fallback mode - will generate markdown draft for manual Jira creation."
   - If `FALLBACK_MODE = false`: "Connected to Jira. Will create issue directly."

**FALLBACK_MODE Effects**:
- Skip Phase 1 (Project Resolution) - requires MCP
- Skip Phase 3 (Duplicate Check) - requires MCP
- Continue Phases 2, 4, 5 - work without MCP
- Phase 6: Write to markdown file instead of creating Jira issue

---

### Phase 1: Project Resolution

> **SKIP if FALLBACK_MODE = true**. Proceed directly to Phase 2.

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

---

### Phase 3: Duplicate Check

> **SKIP if FALLBACK_MODE = true**. Proceed directly to Phase 4.

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
       - "Create new task anyway"
       - "Abort - I'll update an existing issue"

4. **Handle user choice**

   - If "Create new task": Continue to Phase 4
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

---

### Phase 6: Output Generation

**Purpose**: Create the Jira issue or generate markdown draft.

#### If FALLBACK_MODE = true (Markdown Output)

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
   4. Add the labels listed above
   5. Review and adjust as needed
   ```

4. **Notify user**

   Display:
   - "Jira draft saved to: .claude/reports/jira-drafts/[filename]"
   - "Copy this content into Jira to create the task manually."
   - Brief summary: "Issue Type: [type], Summary: [first 50 chars of summary]..."

#### If FALLBACK_MODE = false (Create Jira Issue)

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
     labels: [sanitized labels array]
   }
   ```

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
