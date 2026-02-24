---
name: update-generated-report
description: Update an existing debugging report with Jira feedback, user input, and specialist analysis
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - LS
  - Task
  - AskUserQuestion
  - TodoWrite
  - mcp__plugin_atlassian_atlassian__getJiraIssue
  - mcp__plugin_atlassian_atlassian__addCommentToJiraIssue
  - mcp__plugin_atlassian_atlassian__getAccessibleAtlassianResources
  - mcp__plugin_atlassian_atlassian__atlassianUserInfo
  - mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql
argument-hint: "JIRA-KEY or report-path"
---

# Update Generated Report

Update an existing debugging report with feedback from Jira comments, user observations, and specialist agent analysis.

## Architecture Note

This command follows the same **HYBRID architecture** as `/generate-jira-task`:
- **Command handles**: All MCP operations (Jira API), file I/O, cloudId resolution, user interaction
- **Agents handle**: Specialist analysis via Task tool delegation

This command does NOT push updates to Jira. It only updates the local report.
To sync changes back to Jira, run `/agent-team-creator:generate-jira-task {report-path}` after this command completes.

---

## Execution Flow

Execute phases 0-5 in order.

### Phase 0: Parse Input and Validate Prerequisites

**Purpose**: Determine input mode, validate MCP availability, and resolve cloudId.

1. **Determine input mode from argument**

   The command receives a single text argument. Detect the mode:

   - **Jira Key Mode**: Argument matches regex pattern `^[A-Z][A-Z0-9]+-\d+$`
     - Example: `PROJ-123`, `TEAM-42`, `BUG-7`
     - Store as `INPUT_JIRA_KEY`

   - **Local Report Mode**: Argument is a file path that exists on disk
     - Use Read tool to verify the file exists
     - Store path as `INPUT_REPORT_PATH`

   - **Interactive Mode**: No argument provided (empty)
     - Use Glob to find files matching `.claude/reports/debugging/report-*.md`
     - Sort by modification time (most recent first)
     - If reports found: Ask user via AskUserQuestion to confirm using the most recent report
     - If no reports found: Error — "No debugging reports found. Run the project debugger first, or provide a Jira key or report path."

   - **Invalid input**: Argument doesn't match any pattern
     - Error: "Invalid input: '{argument}'. Provide a Jira issue key (e.g., PROJ-123) or a path to a debugging report."

2. **Check Atlassian MCP availability** (if Jira Key Mode or if report has frontmatter)

   Call `mcp__plugin_atlassian_atlassian__getAccessibleAtlassianResources()`.

   - If **succeeds**: Set `JIRA_AVAILABLE = true`
   - If **fails**: Set `JIRA_AVAILABLE = false`

   If Jira Key Mode and `JIRA_AVAILABLE = false`:
   - Search for local report linked to the key:
     - Glob: `.claude/reports/debugging/report-*{INPUT_JIRA_KEY}*.md`
     - Grep through `.claude/reports/debugging/report-*.md` for `jira_key: {INPUT_JIRA_KEY}`
   - If found: Switch to Local Report Mode with warning: "Atlassian MCP unavailable. Found local report linked to {KEY}. Proceeding with local data only."
   - If not found: Error — "Cannot reach Jira and no local report found for {KEY}. Ensure Atlassian MCP is configured or provide a report path."

3. **Resolve cloudId** (if `JIRA_AVAILABLE = true`)

   Use Read tool to check if `.claude/jira-project.json` exists.

   - If file exists and contains `cloudId`:
     - Parse and store `cloudId`
   - If file does not exist or is missing `cloudId`:
     - Extract `cloudId` from the `getAccessibleAtlassianResources()` response (already called above)
     - Store for use in subsequent phases

---

### Phase 1: Gather Existing Context

**Purpose**: Fetch Jira issue data and locate the linked local report.

#### If Jira Key Mode (INPUT_JIRA_KEY is set)

1. **Fetch Jira issue**

   Call `mcp__plugin_atlassian_atlassian__getJiraIssue`:
   ```
   cloudId: [resolved in Phase 0]
   issueIdOrKey: [INPUT_JIRA_KEY]
   ```

   Extract and store:
   - `JIRA_SUMMARY` from `fields.summary`
   - `JIRA_DESCRIPTION` from `fields.description`
   - `JIRA_STATUS` from `fields.status.name`
   - `JIRA_UPDATED` from `fields.updated`
   - `JIRA_COMMENTS` from `fields.comment.comments` (array, may be empty or absent)

   If the tool call fails (404 or error):
   - Error: "Jira issue {INPUT_JIRA_KEY} not found. Verify the issue key and try again."

   If `fields.comment.comments` is absent or empty:
   - Set `JIRA_COMMENTS = []`
   - Note: "No comments found on {INPUT_JIRA_KEY}. Will proceed with description only."

2. **Find linked local report**

   Search for a local report linked to this Jira key:

   a. Glob: `.claude/reports/debugging/report-*{INPUT_JIRA_KEY}*.md`
   b. If not found: Grep through `.claude/reports/debugging/report-*.md` for `jira_key: {INPUT_JIRA_KEY}`
   c. If multiple found: Use the most recently modified file

   - If found: Read the report, store as `LOCAL_REPORT_CONTENT` and `LOCAL_REPORT_PATH`
   - If not found: Set `LOCAL_REPORT_PATH = null` (Phase 4 will create a new report seeded from Jira)

#### If Local Report Mode (INPUT_REPORT_PATH is set)

1. **Read the local report**

   Use Read tool to load `INPUT_REPORT_PATH`. Store as `LOCAL_REPORT_CONTENT` and `LOCAL_REPORT_PATH`.

2. **Extract Jira link from frontmatter**

   If the report starts with `---`, parse the YAML frontmatter:
   - If `jira_key` is present and non-empty: Store as `INPUT_JIRA_KEY`
   - If `jira_url` is present: Store as `EXISTING_JIRA_URL`

3. **Fetch Jira data** (if `INPUT_JIRA_KEY` was extracted and `JIRA_AVAILABLE = true`)

   Follow the same `getJiraIssue` call as Jira Key Mode above.

   If `JIRA_AVAILABLE = false` or no `jira_key` in frontmatter:
   - Set `JIRA_COMMENTS = []`
   - Note: "No Jira data available. Proceeding with local report and user feedback only."

---

### Phase 2: Collect User Feedback

**Purpose**: Give the user an opportunity to add their own observations or analysis.

1. **Display current state summary**

   Show the user what context has been gathered:

   ```
   Report Update Context:
   - Local report: {LOCAL_REPORT_PATH or "None — will create new from Jira data"}
   - Jira issue: {INPUT_JIRA_KEY or "None — local update only"}
   - Jira status: {JIRA_STATUS or "N/A"}
   - Jira comments: {count of JIRA_COMMENTS} new comment(s)
   - Current root cause: {extracted from LOCAL_REPORT_CONTENT Root Cause section, first 100 chars}
   ```

2. **Ask for user feedback**

   Ask user via AskUserQuestion: "Would you like to add your own analysis or observations to this update?"

   Options:
   - "Yes, I have additional context to add"
   - "No, proceed with Jira feedback only"

   If yes: Prompt for text input. Store as `USER_FEEDBACK`.
   If no: Set `USER_FEEDBACK = null`.

---

### Phase 3: Consult Specialist Agents

**Purpose**: Get targeted analysis from project specialist agents based on the new information.

> **SKIP** this phase if there are no Jira comments, no user feedback, AND no local report to analyze. Display: "No new context to analyze. Skipping specialist consultation."

1. **Discover available specialists**

   Use Glob to find `.claude/agents/*.md`.

   Filter out:
   - `project-debugger.md` (orchestrator, not specialist — invoking it would cause nesting)

   If no agents found:
   - Display: "No project specialist agents found. Skipping specialist analysis. Run /agent-team-creator:generate-agent-team to create project specialists."
   - Skip to Phase 4.

2. **Select relevant specialists**

   Read each agent's `description` field from frontmatter. Match against the content of:
   - The Jira comments (if any)
   - The user feedback (if any)
   - The report's Affected Components section

   Select up to 3 most relevant agents. If unsure, prefer agents whose descriptions mention the components listed in the report's Issue Summary.

3. **Invoke specialists via Task tool**

   For each selected specialist agent, call the Task tool:

   ```
   subagent_type: "[agent-name from frontmatter]"
   description: "Analyze new feedback for {INPUT_JIRA_KEY or 'debugging report update'}"
   prompt: |
     You are being consulted as part of a debugging report update.

     ## Current Report Summary
     {Issue Summary and Root Cause sections from LOCAL_REPORT_CONTENT}

     ## New Information Since Last Analysis

     ### Jira Comments ({count} comments)
     {For each comment in JIRA_COMMENTS:}
     - **{comment.author}** ({comment.created}): {comment.body}

     ### User Observations
     {USER_FEEDBACK or "No additional user input."}

     ## Your Task
     Based on this new information and your area of expertise:
     1. Does this new information change or refine the root cause assessment?
     2. Does it affect the recommended solution approach?
     3. Are there new risks or considerations?
     4. Any additional investigation needed in your domain?

     Provide a focused, concise analysis (under 500 words).
   ```

   Store each agent's response as `SPECIALIST_FINDINGS[agent-name]`.

---

### Phase 4: Synthesize and Update Report

**Purpose**: Combine all new information into a Timeline History session and update the report.

#### If LOCAL_REPORT_PATH exists (updating an existing report)

1. **Build the Timeline History session**

   Construct a new section in this format:

   ```markdown

   ---

   ## Timeline History

   ### Session: {YYYY-MM-DD HH:mm} — Update from {source description}

   **Sources**:
   - Jira comments: {count} from {list of comment authors} (or "None")
   - User feedback: {present/absent}
   - Specialists consulted: {list of agent names} (or "None")

   **Jira Comment Summary**:
   {For each comment, summarize in 1-2 lines:}
   - **{author}** ({date}): {key point}

   **User Feedback**:
   {USER_FEEDBACK or "No additional feedback provided."}

   **Specialist Analysis**:
   | Agent | Key Findings |
   |-------|-------------|
   {For each agent in SPECIALIST_FINDINGS:}
   | {agent-name} | {2-3 sentence summary of their findings} |

   **Impact on Diagnosis**:
   - **Root cause**: {Unchanged / Refined: [new understanding]}
   - **Recommended solution**: {Unchanged / Updated: [new recommendation]}
   - **New considerations**: {List or "None identified"}
   ```

2. **Append to report**

   Use Edit tool to append the Timeline History session to the end of `LOCAL_REPORT_PATH`.

   If the report already has a `## Timeline History` section:
   - Append the new session AFTER the existing Timeline History content (do not replace it)

   If the report does not have a `## Timeline History` section:
   - Append at the end of the file

3. **Update frontmatter** (if present)

   If the report has YAML frontmatter:
   - Update `last_updated: {current ISO timestamp}`

   If the report has no frontmatter but `INPUT_JIRA_KEY` is known:
   - Prepend frontmatter:
     ```
     ---
     jira_key: {INPUT_JIRA_KEY}
     jira_url: https://[site].atlassian.net/browse/{INPUT_JIRA_KEY}
     created: {timestamp from filename}
     last_updated: {current ISO timestamp}
     ---

     ```

#### If LOCAL_REPORT_PATH is null (creating new local report from Jira data)

1. **Create a new report file**

   Filename: `report-{INPUT_JIRA_KEY}-{YYYYMMDD-HHmm}.md`
   Location: `.claude/reports/debugging/`

   Content:
   ```markdown
   ---
   jira_key: {INPUT_JIRA_KEY}
   jira_url: https://[site].atlassian.net/browse/{INPUT_JIRA_KEY}
   created: {current timestamp}
   last_updated: {current timestamp}
   ---

   # Debugging Report

   ## Issue Summary
   - **Reported Issue**: {JIRA_SUMMARY}
   - **Jira Status**: {JIRA_STATUS}
   - **Source**: Imported from Jira issue {INPUT_JIRA_KEY}

   ## Jira Description

   {JIRA_DESCRIPTION}

   ## Timeline History

   ### Session: {YYYY-MM-DD HH:mm} — Initial sync from Jira

   {Same Timeline Session format as above, with Jira comments, user feedback, specialist analysis}
   ```

   Write file using Write tool. Store path as `LOCAL_REPORT_PATH`.

---

### Phase 5: Confirm and Guide Next Steps

**Purpose**: Confirm the update and tell the user what to do next.

1. **Display completion summary**

   ```
   Report updated successfully.

   Report: {LOCAL_REPORT_PATH}
   Sources incorporated:
   - {count} Jira comment(s)
   - User feedback: {yes/no}
   - {count} specialist agent(s) consulted
   ```

2. **Guide next steps**

   - "To sync this updated report back to Jira, run:"
   - "  /agent-team-creator:generate-jira-task {LOCAL_REPORT_PATH}"
   - ""
   - "To incorporate more Jira feedback later, run:"
   - "  /agent-team-creator:update-generated-report {INPUT_JIRA_KEY}"

---

## Usage Examples

```
# Update from Jira key — fetches comments, finds linked local report
/agent-team-creator:update-generated-report PROJ-123

# Update from local report — extracts Jira key from frontmatter
/agent-team-creator:update-generated-report .claude/reports/debugging/report-PROJ-123-20260210-1000.md

# Interactive — finds most recent report
/agent-team-creator:update-generated-report
```
