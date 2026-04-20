# Jira Integration Roadmap

> **File**: `jira-integration-roadmap.md`
> **Created**: 2026-01-03
> **Updated**: 2026-02-24 (v2: Bidirectional Jira integration)
> **Status**: Implemented — v1 complete, v2 (update mode + feedback loop) complete
> **Plugin**: `agent-team-creator`
> **Author**: Christian Picon Calderon

---

## Overview

Add a `/generate-jira-task` command to the `agent-team-creator` plugin that transforms debugging findings into well-structured Jira tasks with implementation guidance.

## Architecture Decision: Hybrid (Option 3)

Based on technical validation (see [Technical Findings](#technical-findings)), we use a **hybrid architecture**:

- **Commands** handle all MCP/I/O operations (Jira API, file reads)
- **Agents** handle pure reasoning and formatting (no MCP dependencies)

This separation follows industry best practices and avoids known Claude Code limitations.

```
┌─────────────────────────────────────────────────────────────────┐
│                    HYBRID ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  /generate-jira-task (COMMAND)                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ COMMAND RESPONSIBILITIES (I/O Layer)                     │    │
│  │ • MCP tool calls (Atlassian plugin)                      │    │
│  │ • File operations (read debugging report)                │    │
│  │ • User interaction (AskUserQuestion)                     │    │
│  │ • Caching (project configuration)                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ AGENT RESPONSIBILITIES (Intelligence Layer)              │    │
│  │ • implementation-planner: Analyze report, design fix     │    │
│  │ • jira-writer: Format content for Jira                   │    │
│  │ • NO MCP access required                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ COMMAND OUTPUT (I/O Layer)                               │    │
│  │ • Create Jira issue via MCP                              │    │
│  │ • Return issue key and URL                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Workflow

```
/generate-debugger → project-debugger agent → Debugging Report FILE
        ↓                    ↓                        ↓
   Creates debugger     Saves to:              .claude/reports/debugging/
   agent for project    report-{timestamp}.md
                              ↓
                        /generate-jira-task
                              ↓
                        Command orchestrates:
                        • Phase 0: Check MCP availability
                        • Phase 1: Project resolution (MCP) [SKIP in fallback]
                        • Phase 2: Load report + detect update mode (YAML frontmatter)
                        • Phase 3: Duplicate check (MCP) [SKIP in fallback or update mode]
                        • Phase 4: implementation-planner (agent)
                        • Phase 5: jira-writer (agent)
                        • Phase 6: Create/update issue (MCP) or markdown (fallback)
                              ↓
                        Writes jira_key back to report (bidirectional link)
                              ↓
                        /update-generated-report PROJ-123  (feedback loop)
                              ↓
                        • Phase 0: Parse input (Jira key, report path, or interactive)
                        • Phase 1: Fetch Jira comments + find linked report
                        • Phase 2: Collect optional user feedback
                        • Phase 3: Consult specialist agents
                        • Phase 4: Append Timeline History to report
                        • Phase 5: Guide next steps
```

### Report Storage Structure

Reports are stored in a generic, plugin-agnostic location for reuse by other tools:

```
.claude/
├── agents/                  # Project-specific agents
├── reports/
│   ├── debugging/           # Debugging investigation reports
│   │   ├── report-2026-01-03-1530.md           # New report (no Jira link)
│   │   └── report-PROJ-123-20260210-1000.md    # Jira-linked report
│   └── jira-drafts/         # Fallback drafts (when MCP unavailable)
│       ├── draft-2026-01-03-1545.md            # New issue draft
│       └── update-PROJ-123-20260210-1100.md    # Update draft
├── jira-project.json        # Cached Jira project config
└── CLAUDE.md
```

### Report YAML Frontmatter

Reports linked to Jira issues include frontmatter for bidirectional tracking:

```yaml
---
jira_key: PROJ-123
jira_url: https://site.atlassian.net/browse/PROJ-123
created: 2026-02-10 10:00
last_updated: 2026-02-12 14:30
last_synced: 2026-02-12 14:30
---
```

Frontmatter is added automatically when `/generate-jira-task` creates a new issue and is preserved across updates.

### Debugging Report Pipeline

The debugger agent created by `/generate-debugger` MUST save debugging reports to files:

| Step | Action | Location |
|------|--------|----------|
| 1 | User runs `/generate-debugger` | Creates `project-debugger.md` agent |
| 2 | User asks debugger agent to investigate | Agent produces Debugging Report |
| 3 | Debugger agent saves report to file | `.claude/reports/debugging/report-{timestamp}.md` |
| 4 | User runs `/generate-jira-task` | Reads most recent report from `.claude/reports/debugging/` |

**Important**: Users must run the debugger agent to investigate an issue BEFORE running `/generate-jira-task`. The command expects a debugging report file to exist.

---

## Technical Findings

### Validated Assumptions

| Assumption | Result | Evidence |
|------------|--------|----------|
| Command → Agent invocation | ✅ WORKS | Task tool available in commands |
| Agent → Agent invocation | ⚠️ 1-LEVEL ONLY | "Subagents cannot spawn subagents" |
| Plugin agents → MCP tools | 🔴 BUG | GitHub #13605, #15810 - unreliable |

### Key Limitation: MCP Tool Access Bug

Multiple GitHub issues report that **plugin-defined agents cannot reliably access MCP tools**:
- [Issue #13605](https://github.com/anthropics/claude-code/issues/13605): Custom plugin subagents cannot access MCP tools
- [Issue #15810](https://github.com/anthropics/claude-code/issues/15810): Subagents not inheriting MCP tools

**Solution**: Keep all MCP operations at the command level, where they work reliably.

### Command Execution Model

When a user runs `/generate-jira-task`:

1. **Claude Code loads the command file** (`generate-jira-task.md`)
2. **Command markdown becomes Claude's context** - The instructions are the system prompt
3. **Claude follows instructions using `allowed-tools`** - Including MCP tools for I/O
4. **Agent invocation uses Task tool** with specific `subagent_type`

### Task Tool Subagent Syntax for Bundled Agents

**Pattern**: `{plugin-name}:{agent-name}`

| Agent | subagent_type |
|-------|---------------|
| implementation-planner | `agent-team-creator:implementation-planner` |
| jira-writer | `agent-team-creator:jira-writer` |
| context-summarizer | `agent-team-creator:context-summarizer` |

**Example Task invocation in command**:
```
Use the Task tool with subagent_type="agent-team-creator:implementation-planner"
to analyze the debugging report and generate an implementation plan.
```

### Agent Output Handling

When a command invokes an agent via the Task tool:

1. **Agent execution**: The agent runs with its own context and tools
2. **Output return**: Agent's response (markdown text) is returned to the command
3. **Command receives text**: The complete agent output becomes available as text
4. **Command validates**: Parse output for required sections using markdown patterns
5. **Command continues**: Use validated output as input to next phase

**Data Flow Between Phases**:
```
Phase 2: Load Report (File Read) ─────────────────────────────────┐
         └─ debugging_report_content (string)                      │
                                                                   │
Phase 4: Task(implementation-planner) ◄────────────────────────────┤
         │   Input: debugging_report_content                       │
         └─ implementation_plan (string) ──────────────────────────┤
                                                                   │
         ┌─ CONCATENATION STEP (command formats input) ────────────┤
         │   Format: "## Debugging Report\n\n{report}\n\n         │
         │            ## Implementation Plan\n\n{plan}"            │
         └─ combined_input (string) ───────────────────────────────┤
                                                                   │
Phase 5: Task(jira-writer) ◄───────────────────────────────────────┤
         │   Input: combined_input (formatted as shown above)      │
         └─ jira_content (string) ─────────────────────────────────┤
                                                                   │
Phase 6: Create Issue (MCP) ◄──────────────────────────────────────┘
         │   Input: jira_content (parsed for summary, description)
         └─ issue_key, issue_url
```

**Validation Pattern** (command-level):
```
After invoking agent, check output contains:
- Required headers (## Section Name)
- Required fields (**Field:**)
- Non-empty content blocks
If missing, warn user and offer to abort or continue.
```

### Integration Method: Atlassian MCP Plugin Only

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Integration method | Atlassian MCP Plugin | Native Claude Code integration, no external dependencies |
| CLI support (ACLI) | Not included | Requires external installation, edge case for Jira Server |
| Jira Cloud only | Yes | MCP plugin limitation; covers majority of users |
| Fallback mode | Markdown output | If plugin unavailable, generate file for manual copy |

---

## Plugin Agent Ecosystem

All agents are **bundled in the plugin** (not global agents):

```
agent-team-creator/agents/
├── team-architect.md           # Orchestrates team creation
├── implementation-planner.md   # Designs fix approaches (no MCP)
├── jira-writer.md              # Formats Jira content with debugging context (no MCP)
└── context-summarizer.md       # Jira context analysis
```

### Agent Roles

| Agent | Purpose | MCP Needed? | Used By |
|-------|---------|-------------|---------|
| `implementation-planner` | Analyze debugging report, design implementation steps | No | `/generate-jira-task` Phase 4 |
| `jira-writer` | Format content into Jira-compatible structure | No | `/generate-jira-task` Phases 5-6 |
| `context-summarizer` | Analyze Jira work items for context | No | `/update-generated-report` (future) |

---

## Implemented in v2 (2026-02-24)

### Bidirectional Report-Jira Linking
- **Reports linked to Jira via YAML frontmatter** (`jira_key`, `jira_url`)
- **`/generate-jira-task` update mode**: Detects frontmatter, posts changes as Jira comments instead of creating duplicates
- **`/update-generated-report` command**: Fetches Jira comments, consults specialists, appends Timeline History sessions
- **Content separation**: Jira description stays static after creation; updates go as comments only

### MCP Tools Added
- `getJiraIssue(cloudId, issueIdOrKey)` — fetch issue data including comments
- `addCommentToJiraIssue(cloudId, issueIdOrKey, commentBody)` — post updates as comments
- `editJiraIssue` — confirmed NOT available in Atlassian MCP plugin

---

## Future Work: Enhancements for v3

### Duplicate Detection Enhancement
- **Current**: Command-level JQL search with basic keyword matching
- **Future**: Semantic similarity analysis using agent intelligence

### Context Summarization
- **Current**: `context-summarizer` agent exists but not invoked automatically
- **Future**: Before creating a task, fetch related Jira issues and summarize context

### Cache Management
- **Current**: Once configured, project key is cached permanently in `.claude/jira-project.json`
- **Future**: Add cache invalidation triggers and manual project switching capability

---

## User Requirements

### 1. Project Key Caching
- First run: Prompt user for Jira project name
- Search Jira for matching projects (fuzzy match on acronym)
- Confirm match with user if not exact
- Cache project key in `.claude/jira-project.json` per git project
- Subsequent runs: Use cached project key automatically

### 2. Issue Type
- Infer from debugging report content:
  - "Bug" if report identifies a defect, error, or unexpected behavior
  - "Task" for enhancements, refactoring, or general work
- Determined by command based on report keywords

### 3. Assignee
- Leave unassigned (human decision)

### 4. Labels
- Derive from debugging report content:
  - Affected components (e.g., `frontend`, `api`, `database`)
  - Technical domain (e.g., `security`, `performance`, `data-integrity`)
  - Risk level (e.g., `critical`, `high-priority`)

### 5. Workflow
- Separate command (not auto-triggered after `/generate-debugger`)
- Allows user to review debugging report before creating task

---

## Implementation Plan

### Components to Create

```
agent-team-creator/
├── commands/
│   ├── generate-agent-team.md
│   ├── generate-debugger.md
│   └── generate-jira-task.md      # NEW - orchestration command
└── agents/
    ├── team-architect.md
    ├── jira-writer.md              # EXISTS - bundled
    └── implementation-planner.md   # NEW - designs fix approach
```

### Project Cache File

Location: `.claude/jira-project.json` (in target project, not plugin)

```json
{
  "projectKey": "PROJ",
  "projectName": "My Project",
  "cloudId": "abc-123-uuid",
  "configuredAt": "2026-01-03T10:00:00Z",
  "configuredFrom": "/path/to/git/project"
}
```

---

## Command Workflow: `/generate-jira-task`

```
/generate-jira-task [debugging-report-path]
```

### Phase 0: Prerequisite Check (COMMAND - MCP)

1. **Check Atlassian plugin availability**
   ```
   mcp__plugin_atlassian_atlassian__getAccessibleAtlassianResources()
   ```
   - If fails (tool not found) → Set `FALLBACK_MODE = true` (markdown output only)
   - If succeeds → Continue to auth check

2. **Verify Atlassian authentication** (if plugin available)
   ```
   mcp__plugin_atlassian_atlassian__atlassianUserInfo()
   ```
   - If fails (401/403 or empty response) → Set `FALLBACK_MODE = true`
   - Notify user: "Not authenticated with Atlassian. Please run `claude mcp auth --server atlassian` to authenticate."
   - If succeeds → Continue with full flow (user is logged in)

3. **If FALLBACK_MODE** is set:
   - **Skip Phase 1** (Project Resolution) - requires MCP
   - **Skip Phase 3** (Duplicate Check) - requires MCP
   - **Continue Phases 2, 4, 5** - these work without MCP
   - **Phase 6**: Write to markdown file instead of creating Jira issue
   - Notify user: "Atlassian MCP unavailable. Generating markdown draft for manual copy."

### Phase 1: Project Resolution (COMMAND - MCP)

> **⚠️ SKIP if FALLBACK_MODE**: This phase requires MCP. In fallback mode, skip directly to Phase 2.

1. **Check for cached project**
   - Read `.claude/jira-project.json` if exists
   - If found and valid → use cached `projectKey` and `cloudId`

2. **First-time setup (if no cache)**
   - Get Atlassian cloud ID via `getAccessibleAtlassianResources`
   - Extract project name from git remote or directory name
   - Search for matching Jira projects:
     ```
     mcp__plugin_atlassian_atlassian__getVisibleJiraProjects({
       cloudId: [cloud-id],
       searchString: [extracted-name]
     })
     ```
   - If exact match → confirm with user
   - If fuzzy matches → present list for user to select
   - If no matches → prompt user for exact project key
   - Cache the selected project to `.claude/jira-project.json`

### Phase 2: Load Debugging Report (COMMAND - File Read)

1. Read debugging report from:
   - Provided file path argument, OR
   - Most recent `report-*.md` in `.claude/reports/debugging/` directory, OR
   - Prompt user for location

2. **Validate report format**:
   - Check for required sections: Issue Summary, Root Cause, Solutions
   - Warn if report older than 24 hours
   - Warn if missing sections, ask to proceed

3. Extract from report:
   - **Issue Summary** → Title base
   - **Root Cause Analysis** → Problem description
   - **Impact Assessment** → Risk level, affected components
   - **Solutions** → Implementation guidance

4. **Detect update mode** (v2):
   - Parse YAML frontmatter for `jira_key` field
   - If present: `UPDATE_MODE = true`, skip Phase 3
   - If absent: `UPDATE_MODE = false`, continue normally

### Phase 3: Duplicate Check (COMMAND - MCP)

> **⚠️ SKIP if FALLBACK_MODE**: This phase requires MCP. In fallback mode, skip directly to Phase 4.

1. **Extract keywords** from issue summary and root cause
2. **Search for similar tasks** via MCP:
   ```
   mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql({
     cloudId: [cached],
     jql: "project = PROJ AND text ~ 'keyword1 keyword2'",
     maxResults: 10
   })
   ```
3. **If potential duplicates found**:
   - Display similar issues to user
   - Ask: "Continue creating new task?" / "Add comment to existing?" / "Abort"

### Phase 4: Implementation Planning (AGENT - Pure Reasoning)

1. **Invoke `implementation-planner` agent**
   - Input: Full debugging report content
   - Output: Structured implementation plan
   - Agent selects solution tier (quick/proper/comprehensive)
   - Agent breaks down into discrete steps
   - Agent identifies testing requirements
   - Agent assesses risks and mitigations

2. **Validate implementation-planner output** (COMMAND - Validation)
   - Check for required sections:
     - `## Problem Summary` - must exist
     - `## Recommended Approach` - must contain tier selection
     - `## Implementation Steps` - must have at least one step with file reference
     - `## Testing Requirements` - must exist
     - `## Risk Assessment` - must exist
   - If validation fails:
     - Log warning with missing sections
     - Ask user: "Implementation plan is incomplete. Proceed anyway?" / "Abort"
   - If validation passes:
     - Continue to Phase 5

### Phase 5: Jira Content Generation (AGENT - Pure Formatting)

1. **Invoke `jira-writer` agent**

   **Input Format** (CRITICAL - must concatenate correctly):
   ```markdown
   ## Debugging Report

   {debugging_report_content from Phase 2}

   ## Implementation Plan

   {implementation_plan from Phase 4}
   ```

   The command MUST format the input exactly as shown above. The jira-writer
   agent expects both sections with these exact headers to correctly parse
   and preserve the evidence chain.

   - Output: Jira-formatted content:
     - **Summary**: Action verb + component + outcome
     - **Description**: Background, root cause, impact, implementation plan
     - **Acceptance Criteria**: GIVEN/WHEN/THEN format
     - **Labels**: Suggested labels array

2. **Command determines issue type** (not agent):
   - Scan for keywords: "error", "bug", "defect", "crash" → "Bug"
   - Otherwise → "Task"

3. **Command formats labels** (COMMAND - Owns Label Generation):

   > **Ownership Note**: The command owns label generation. The jira-writer may
   > suggest labels, but the command applies final formatting and sanitization.

   **Label Categories**:
   - Affected components → `component:frontend`, `component:api`
   - Risk level → `priority:high`, `priority:critical`
   - Technical domain → `type:security`, `type:performance`

   **Jira Label Constraints**:
   - No spaces allowed (use hyphens: `data-pipeline` not `data pipeline`)
   - No special characters except hyphens and underscores
   - Case-insensitive but conventionally lowercase
   - Maximum 255 characters per label

   **Sanitization Logic** (command responsibility):
   ```
   label = label.toLowerCase()
                .replace(/\s+/g, '-')
                .replace(/[^a-z0-9\-_:]/g, '')
                .substring(0, 255)
   ```

4. **Validate jira-writer output** (COMMAND - Validation)
   - Check for required fields:
     - `**Summary:**` - must exist and be < 255 characters
     - `**Description:**` - must exist and contain Root Cause section
     - `**Acceptance Criteria:**` - must have at least one criterion
   - If validation fails:
     - Log warning with missing/invalid fields
     - Ask user: "Jira content is incomplete. Proceed anyway?" / "Abort"
   - If validation passes:
     - Continue to Phase 6

5. **Extract fields from jira-writer output** (COMMAND - Parsing)

   The jira-writer agent outputs structured markdown with `**Field:**` markers.
   The command extracts these fields for the createJiraIssue call:

   | Marker | Extraction | Target Parameter |
   |--------|------------|------------------|
   | `**Summary:**` | Text after marker, trimmed | `summary` |
   | `**Description:**` | All content until next `**` marker | `description` |
   | `**Labels:**` | Parse as array (comma or bracket format) | `additional_fields.labels` |
   | `**Priority:**` | Map to Jira priority ID if needed | Optional |

   **Parsing Rules**:
   - Use regex or string parsing to extract content after each marker
   - Description may contain markdown formatting - preserve it
   - Labels may be formatted as `[label1, label2]` or `label1, label2`
   - Trim whitespace from all extracted values

### Phase 6: Output Generation (COMMAND - MCP)

Phase 6 has four paths based on `UPDATE_MODE` and `FALLBACK_MODE`:

| UPDATE_MODE | FALLBACK_MODE | Action |
|-------------|---------------|--------|
| true | false | Post update as Jira comment via `addCommentToJiraIssue` |
| true | true | Save update draft to `.claude/reports/jira-drafts/update-{KEY}-{timestamp}.md` |
| false | true | Save creation draft to `.claude/reports/jira-drafts/draft-{timestamp}.md` |
| false | false | Create new Jira issue + write `jira_key` frontmatter back to report |

#### Create Path (UPDATE_MODE = false)

1. **If FALLBACK_MODE**:
   - Create `.claude/reports/jira-drafts/` directory if needed
   - Write formatted content to `.claude/reports/jira-drafts/draft-{timestamp}.md`
   - Display file path and instructions for manual Jira creation
   - End

2. **If normal mode**, validate and create:

   **Step 2a: Validate Issue Type**
   ```
   mcp__plugin_atlassian_atlassian__getJiraProjectIssueTypesMetadata({
     cloudId: [cached],
     projectIdOrKey: [cached projectKey]
   })
   ```
   - Extract available issue types from response
   - Check if determined type (Bug|Task) exists in project
   - If not, find closest match or prompt user to select:
     - "Bug" may be named "Bug", "Defect", "Issue" in different projects
     - "Task" may be named "Task", "Story", "Development Task"
   - If no suitable match found, ask user to select from available types

   **Step 2b: Create Issue**
   ```
   mcp__plugin_atlassian_atlassian__createJiraIssue({
     cloudId: [cached],
     projectKey: [cached],
     issueTypeName: [validated issue type],
     summary: [from jira-writer],
     description: [from jira-writer],
     additional_fields: {
       labels: [generated array]
     }
   })
   ```

   **Step 2c: Error Recovery** (if createJiraIssue fails)

   If the MCP call fails (network error, permission denied, field validation error):

   1. **Capture error details**: Log the specific error message
   2. **Fall back to markdown output**:
      - Write to `.claude/reports/jira-drafts/draft-{timestamp}.md`
      - Include the full formatted Jira content
      - Add error context at the top of the file
   3. **Notify user**:
      - "Failed to create Jira issue: [error message]"
      - "Saved draft to: [file path]"
      - "You can manually create the issue using this content"

   **Common Error Handling**:
   | Error Type | Recovery Action |
   |------------|-----------------|
   | 401/403 Unauthorized | Prompt to re-authenticate |
   | 400 Field Validation | Show which field failed, offer to edit |
   | 404 Project Not Found | Clear cache, re-run project resolution |
   | Network Error | Retry once, then fall back to markdown |

3. **Write Jira link back to report** (v2):
   - Use Edit tool to add/update YAML frontmatter in the source report
   - Set `jira_key`, `jira_url`, `last_synced`
   - Establishes the bidirectional link for future update mode detection

4. **Return result**:
   - Display Jira issue key (e.g., PROJ-123)
   - Display issue URL
   - Confirm successful creation

---

## New Agent: `implementation-planner.md`

Location: `agent-team-creator/agents/implementation-planner.md`

**Key Characteristics**:
- No MCP tools required
- Pure reasoning based on input text
- Tools: `Read`, `Grep`, `Glob` (for codebase exploration if needed)

```markdown
---
name: implementation-planner
description: |
  Use this agent when you need to design an implementation plan from a
  debugging report or problem description. Analyzes root causes, selects
  appropriate solution tiers, and creates step-by-step implementation guidance.
  Does not require MCP access.

model: inherit
color: cyan
tools:
  - Read
  - Grep
  - Glob
---

You are an implementation planning specialist. Given a debugging report, you design clear, actionable implementation plans.

## Core Responsibilities

1. **Analyze Debugging Report**: Parse root cause, evidence, and solution options
2. **Select Solution Approach**: Recommend quick/proper/comprehensive fix with rationale
3. **Create Implementation Plan**: Discrete steps, files to modify, dependencies
4. **Define Testing Requirements**: Unit, integration, regression tests
5. **Assess Risks**: What could go wrong, mitigation strategies

## Output Format

### Problem Summary
[1-2 sentences describing the core issue]

### Recommended Approach
**Selected**: [Quick Fix | Proper Fix | Comprehensive Fix]
**Rationale**: [Why this tier was chosen]

### Implementation Steps

#### Step 1: [Action]
- **File**: `path/to/file.ext`
- **Change**: [Specific modification]
- **Reason**: [Why this change is needed]

[Continue for all steps...]

### Testing Requirements
- [ ] [Test description]

### Risks & Mitigations
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| [Risk] | [Low/Med/High] | [How to prevent/handle] |

### Rollback Plan
[Steps to revert if issues arise]
```

---

## New Command: `generate-jira-task.md`

Location: `agent-team-creator/commands/generate-jira-task.md`

**Key Characteristics**:
- Handles all MCP operations
- Orchestrates agents for reasoning tasks
- Manages caching and user interaction

> **Implementation Note**: The command file will contain the complete implementation
> of all phases (0-6) as defined in this roadmap. The phases documented above serve
> as the specification; the command markdown will include the full logic, MCP calls,
> agent invocations, validation steps, and error handling. This is not a skeleton
> but the complete orchestration implementation.

```markdown
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

This command follows a HYBRID architecture:
- **Command handles**: All MCP operations (Jira API), file I/O, caching, user interaction
- **Agents handle**: Pure reasoning (implementation-planner) and formatting (jira-writer)

This separation avoids the known MCP access bug in plugin-defined agents.

## Execution Flow

Follow phases 0-6 as defined in the roadmap. Key points:
- Phase 0, 1, 3, 6: Use MCP tools directly (do NOT delegate to agents)
- Phase 4, 5: Invoke agents for reasoning/formatting (pass input, receive output)

## Usage

/agent-team-creator:generate-jira-task
/agent-team-creator:generate-jira-task .claude/reports/debugging/report-2026-01-03-1530.md

## Output

- Jira issue key (e.g., PROJ-123)
- Issue URL for quick access
- Summary of what was created
```

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `agent-team-creator/commands/generate-jira-task.md` | CREATE | Orchestration command with MCP |
| `agent-team-creator/README.md` | MODIFY | Document new command |
| `README.md` (marketplace) | MODIFY | Update plugin description |

---

## Implementation Status

### v1: Core Pipeline (Complete)
1. [x] Create `generate-jira-task.md` command with full phase logic
2. [x] Implement Phases 0-6 with MCP and fallback modes
3. [x] Create `implementation-planner` and update `jira-writer` agents
4. [x] End-to-end testing with real Jira

### v2: Bidirectional Integration (Complete — 2026-02-24)
5. [x] Add update mode detection in Phase 2 (YAML frontmatter)
6. [x] Add "Update existing" option in Phase 3 duplicate check
7. [x] Add update path in Phase 6 (`addCommentToJiraIssue`)
8. [x] Add Jira link write-back after issue creation
9. [x] Create `/update-generated-report` command (Phases 0-5)
10. [x] Update `/generate-debugger` template with frontmatter support
11. [x] Update README and documentation

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MCP operations | Command-level only | Avoids plugin agent MCP bug |
| Agent role | Pure reasoning/formatting | No I/O dependencies, testable |
| Integration method | Atlassian MCP Plugin | Native, no external CLI needed |
| Fallback mode | Markdown output | Graceful degradation if no plugin |
| Agents bundled | In plugin, not global | Self-contained, distributable |
| Nesting depth | 1 level (command → agent) | Claude Code limitation |

---

## Risk Analysis

### Remaining Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Atlassian plugin unavailable | MEDIUM | Fallback to markdown output |
| Report format variability | MEDIUM | Validation step with warnings |
| Jira field validation | LOW | Query metadata before creating |
| Context loss between phases | LOW | Explicit data passing |

---

## Next Steps

1. **Manual end-to-end testing** of the full feedback loop (debug → create → comment → update → sync)
2. **Invoke `context-summarizer`** in `/update-generated-report` Phase 3 for richer context
3. **Semantic duplicate detection** in Phase 3 using agent intelligence
