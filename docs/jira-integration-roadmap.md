# Jira Integration Roadmap

> **File**: `jira-integration-roadmap.md`
> **Created**: 2026-01-03
> **Updated**: 2026-01-03 (Session 2: Deep Analysis & Updates)
> **Status**: In Progress - Agents Ready, Command Next
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
/generate-debugger → Debugging Report → /generate-jira-task → Jira Task
        ↓                                       ↓
   Evidence-based                     Command orchestrates:
   investigation                      • Phase 1-3: MCP operations (command)
   with specialists                   • Phase 4: implementation-planner (agent)
                                      • Phase 5: jira-writer (agent)
                                      • Phase 6: MCP create issue (command)
```

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
├── team-architect.md           # Original - orchestrates team creation
├── implementation-planner.md   # CREATED - designs fix approaches (no MCP)
├── jira-writer.md              # UPDATED - formats Jira content with debugging context (no MCP)
└── context-summarizer.md       # RESERVED - for future Jira context analysis
```

### Agent Roles in This Feature

| Agent | Purpose | MCP Needed? | Status |
|-------|---------|-------------|--------|
| `implementation-planner` | Analyze debugging report, design implementation steps | No | CREATED |
| `jira-writer` | Format content into Jira-compatible structure (with debugging context support) | No | UPDATED |
| `context-summarizer` | Reserved for future Jira context analysis | No | NOT USED (v1) |

### Removed Agents

| Agent | Reason | Replacement |
|-------|--------|-------------|
| `duplicate-detector` | MCP operations must be at command level (bug workaround) | Command-level JQL search in Phase 3 |

---

## Future Work: Duplication & Context Features

These capabilities are planned for future versions but not included in v1:

### Duplicate Detection Enhancement (v2)
- **Current**: Command-level JQL search with basic keyword matching
- **Future**: Semantic similarity analysis using agent intelligence
- **Approach**: After Phase 3 JQL search, invoke an analysis agent to score similarity
- **Benefit**: Reduce false positives, better duplicate matching

### Context Summarization (v2)
- **Current**: Not implemented
- **Future**: Before creating a task, fetch related Jira issues and summarize context
- **Approach**: Command fetches issues via MCP, `context-summarizer` agent analyzes relationships
- **Benefit**: Prevent duplicate work, understand related tasks, link issues appropriately

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
   - If fails → Set `FALLBACK_MODE = true` (markdown output only)
   - If succeeds → Continue with full flow

2. **If FALLBACK_MODE**:
   - Skip Jira API calls in later phases
   - Generate markdown file to `.claude/jira-task-draft-{timestamp}.md`
   - Provide instructions for manual Jira creation

### Phase 1: Project Resolution (COMMAND - MCP)

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
   - Most recent `debugging-report-*.md` in `.claude/` directory, OR
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

### Phase 3: Duplicate Check (COMMAND - MCP)

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
   - Input: Debugging report + implementation plan from Phase 4
   - Output: Jira-formatted content:
     - **Summary**: Action verb + component + outcome
     - **Description**: Background, root cause, impact, implementation plan
     - **Acceptance Criteria**: GIVEN/WHEN/THEN format
     - **Labels**: Suggested labels array

2. **Command determines issue type** (not agent):
   - Scan for keywords: "error", "bug", "defect", "crash" → "Bug"
   - Otherwise → "Task"

3. **Command formats labels**:
   - Affected components → `component:frontend`, `component:api`
   - Risk level → `priority:high`, `priority:critical`
   - Technical domain → `type:security`, `type:performance`

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

### Phase 6: Create Jira Issue (COMMAND - MCP)

1. **If FALLBACK_MODE**:
   - Write formatted content to `.claude/jira-task-draft-{timestamp}.md`
   - Display file path and instructions
   - End

2. **If normal mode**, call Atlassian plugin:
   ```
   mcp__plugin_atlassian_atlassian__createJiraIssue({
     cloudId: [cached],
     projectKey: [cached],
     issueTypeName: [Bug|Task],
     summary: [from jira-writer],
     description: [from jira-writer],
     additional_fields: {
       labels: [generated array]
     }
   })
   ```

3. **Return result**:
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
description: Use this agent when you need to design an implementation plan from a debugging report or problem description. This agent analyzes root causes, selects appropriate solution tiers, and creates step-by-step implementation guidance. Does not require MCP access.

<example>
Context: A debugging report identified a root cause and multiple solution options.
user: "Design an implementation plan for this bug fix"
assistant: "I'll use the implementation-planner agent to analyze the solutions and create a detailed plan."
</example>

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
/agent-team-creator:generate-jira-task .claude/debugging-report-2026-01-03.md

## Output

- Jira issue key (e.g., PROJ-123)
- Issue URL for quick access
- Summary of what was created
```

---

## Files to Create/Modify

| File | Action | Status | Purpose |
|------|--------|--------|---------|
| `agent-team-creator/agents/implementation-planner.md` | CREATE | ✅ DONE | Designs fix approach (no MCP) |
| `agent-team-creator/agents/jira-writer.md` | MODIFY | ✅ DONE | Added debugging context support |
| `agent-team-creator/agents/duplicate-detector.md` | DELETE | ✅ DONE | Removed (MCP at command level) |
| `agent-team-creator/commands/generate-jira-task.md` | CREATE | ⏳ NEXT | Orchestration command with MCP |
| `agent-team-creator/README.md` | MODIFY | ⏳ PENDING | Document new command |
| `README.md` (marketplace) | MODIFY | ⏳ PENDING | Update plugin description |
| `docs/jira-integration-problem-description.md` | MODIFY | ✅ DONE | Synced with architecture decisions |
| `docs/jira-integration-roadmap.md` | MODIFY | ✅ DONE | Added validation, future work |

---

## Implementation Order

### Sprint 1: Foundation
1. [x] Create `implementation-planner.md` agent (standalone, testable)
2. [ ] Test implementation-planner with sample debugging reports

### Sprint 2: MVP Command (Markdown Only)
3. [ ] Create `generate-jira-task.md` command skeleton
4. [ ] Implement Phase 0: Prerequisite check with fallback mode
5. [ ] Implement Phase 2: Load and validate debugging report
6. [ ] Implement Phase 4: Invoke implementation-planner agent
7. [ ] Implement Phase 5: Invoke jira-writer agent
8. [ ] Test end-to-end markdown generation (fallback mode)

### Sprint 3: Jira Integration
9. [ ] Implement Phase 1: Project resolution with caching
10. [ ] Implement Phase 3: Duplicate check via MCP
11. [ ] Implement Phase 6: Create Jira issue via MCP
12. [ ] Test end-to-end with real Jira

### Sprint 4: Polish
13. [ ] Add label generation logic
14. [ ] Add issue type inference logic
15. [ ] Update documentation
16. [ ] End-to-end testing

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

## Risk Analysis (Updated)

### Resolved Risks

| Risk | Status | Resolution |
|------|--------|------------|
| Global agent dependency | ✅ RESOLVED | Agents bundled in plugin |
| MCP access in agents | ✅ RESOLVED | MCP operations at command level |
| CLI dependency | ✅ RESOLVED | MCP plugin only |

### Remaining Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Atlassian plugin unavailable | MEDIUM | Fallback to markdown output |
| Report format variability | MEDIUM | Validation step with warnings |
| Jira field validation | LOW | Query metadata before creating |
| Context loss between phases | LOW | Explicit data passing |

---

## Questions Resolved

| Question | Answer |
|----------|--------|
| Can commands invoke agents? | Yes, via Task tool |
| Can agents invoke other agents? | Yes, but only 1 level deep |
| Can plugin agents use MCP? | Unreliable (bug) - avoid |
| Should we use CLI or MCP? | MCP only |
| Where do MCP operations go? | Command level only |

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| `implementation-planner.md` | ✅ CREATED | Designs implementation steps from debugging reports |
| `jira-writer.md` | ✅ UPDATED | Added debugging context support |
| `duplicate-detector.md` | 🗑️ REMOVED | Replaced by command-level MCP |
| `generate-jira-task.md` | ⏳ NEXT | Command to implement |
| Problem description | ✅ UPDATED | Synced with architecture decisions |
| Roadmap validation | ✅ UPDATED | Added output validation between phases |

---

## Next Steps

1. ~~**Create `implementation-planner.md` agent**~~ - ✅ DONE
2. ~~**Update `jira-writer.md` with debugging context**~~ - ✅ DONE
3. **Create `generate-jira-task.md` command** - MVP with fallback mode
4. **Test implementation-planner** with sample debugging reports
5. **Test end-to-end** - Validate the hybrid architecture works
