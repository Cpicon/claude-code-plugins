# Implementation Plan Draft: Integrate Jira Comments (GitHub Issue #2)

**Document**: 08-implementation-plan-draft.md
**Status**: IMPLEMENTED — All tasks complete (2026-02-24)
**Date**: 2026-02-21
**Reviewers needed**: TBD
**Reviews incorporated**: 09-architectural-review.md (partial — see review log below)

---

## 1. What Is the Goal?

Enable the debug-to-Jira pipeline to **update existing reports and Jira tasks** instead of creating duplicates when engineers provide feedback through Jira comments.

**Desired end state**:
```
Day 1: User debugs issue → Report created → Jira task PROJ-123 created
Day 2: Engineers comment on PROJ-123 with findings
Day 3: User runs /update-generated-report PROJ-123
        → System fetches Jira comments
        → Updates the local debugging report
        → User runs /generate-jira-task to sync back
        → PROJ-123 is updated (not duplicated)
```

---

## 2. What Is the Issue?

**GitHub Issue #2**: "Integrate JIRA commends"

### Current broken behavior

The pipeline is **one-directional and stateless**:

1. **No bidirectional link** — When `/generate-jira-task` creates a Jira issue from a report, no reference is stored back in the report. The report doesn't know which Jira task it belongs to.

2. **No update mechanism** — `/generate-jira-task` can only CREATE issues. It cannot update an existing one.

3. **Always-new report policy** — `generate-debugger.md` explicitly instructs: "Always create a NEW file with timestamp (preserve history, never overwrite)." There is no concept of updating a report.

4. **No Jira feedback ingestion** — No command exists to fetch comments from Jira back into local reports.

### Root cause locations

| Root Cause | File | Line(s) |
|------------|------|---------|
| No Jira link stored after creation | `commands/generate-jira-task.md` | Phase 6 (~360-475) |
| Create-only policy in debugger template | `commands/generate-debugger.md` | 147-148 |
| No update/edit MCP tools in allowed-tools | `commands/generate-jira-task.md` | 4-16 |
| No command for fetching Jira feedback | N/A (doesn't exist) | N/A |

---

## 3. What Is the Plan?

### Architecture: Single-command approach with user-controlled sync

Based on the analysis in docs 01-07, the agreed architecture is:

- **New command**: `/update-generated-report` — Fetches Jira feedback, collects user input, consults specialists, updates the local report
- **Modified command**: `/generate-jira-task` — Detect linked Jira issues in reports and update them instead of creating duplicates
- **Modified template**: `generate-debugger.md` — Update the debugger agent template to produce reports with Jira metadata
- **No new agents needed** — The command orchestrates existing specialists directly

### Key design decisions (from analysis docs)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Who orchestrates? | Command (not agent) | Commands are top-level; avoids subagent nesting issues |
| How are reports linked to Jira? | YAML frontmatter in report file | Simpler than separate metadata files |
| When does Jira sync happen? | User-controlled (manual `/generate-jira-task`) | User decides when to push; separation of concerns |
| Report naming for linked reports | `report-{KEY}-{YYYYMMDD-HHmm}.md` | Preserves history, searchable by key |
| Backward compatibility | Lazy upgrade on first Jira interaction | No migration needed; old reports work as-is |

### Proposed changes by file

#### A. `agent-team-creator/commands/generate-debugger.md` (MODIFY)

- Update the **Save Policy** template section to support both new and Jira-linked investigations
- Add YAML frontmatter (`jira_key`, `jira_url`, `created`, `last_updated`) to the mandatory report format template
- Update the "After Saving" guidance to mention the update command

#### B. `agent-team-creator/commands/generate-jira-task.md` (MODIFY)

- Add MCP tools to `allowed-tools`: `getJiraIssue`, `addCommentToJiraIssue`, and possibly `editJiraIssue`
- Add **update mode detection** in Phase 2: parse YAML frontmatter for `jira_key`
- Add **"Update existing"** option in Phase 3 duplicate check
- Add **update path** in Phase 6 with content separation:
  - Jira **description** stays as-is (set at creation, reflects initial state)
  - Jira **comment** receives only the latest Timeline Session (formatted by `jira-writer`)
  - Fallback: save draft to `.claude/reports/jira-drafts/update-{KEY}-{timestamp}.md`
  - This prevents the "runaway description" problem where growing Timeline History hits Jira's 32KB description limit or produces unreadable comment spam
- Add **Jira link write-back** after successful issue creation (write frontmatter to source report)

#### C. `agent-team-creator/commands/update-generated-report.md` (NEW)

Five-phase command:
- Phase 0: Parse input (Jira key vs file path vs interactive), validate MCP availability, **resolve `cloudId`** from cached `.claude/jira-project.json` (required by all Atlassian MCP calls)
- Phase 1: Gather context (fetch Jira issue + comments using resolved `cloudId`, find linked local report)
- Phase 2: Collect optional user feedback
- Phase 3: Consult project specialist agents via Task tool
- Phase 4: Synthesize and append Timeline History session to report
- Phase 5: Confirm and guide user to sync via `/generate-jira-task`

---

## 4. What Are the Findings?

### From codebase exploration

1. **Verified MCP tools in `generate-jira-task.md` frontmatter**: `createJiraIssue`, `getVisibleJiraProjects`, `searchJiraIssuesUsingJql`, `getJiraProjectIssueTypesMetadata`, `getAccessibleAtlassianResources`, `atlassianUserInfo`

2. **The `jira-writer` agent** (model: opus) already supports "Debugging-to-Jira" mode with evidence preservation. No changes needed to this agent.

3. **The `implementation-planner` agent** produces structured plans from debugging reports. No changes needed.

4. **Commands can invoke agents via Task tool** without subagent nesting issues. This is confirmed as the correct orchestration pattern.

5. **Claude Code commands receive arguments as a single text string** — no `--flag` parsing. Input detection must use regex/path-exists checks.

### From expert review (doc 06)

7 critical issues were identified. Here is their status:

| # | Issue | Status |
|---|-------|--------|
| C1 | Command-to-command invocation not supported | **Resolved** — Final solution (07) separates into two user-invoked commands |
| C2 | `editJiraIssue` tool unverified | **UNRESOLVED** — Must verify before implementation |
| C3 | `getJiraIssueComments` tool uncertain | **UNRESOLVED** — Must verify if `getJiraIssue` returns comments |
| C4 | Missing Phase 0 prerequisite check | **Resolved** — Included in final solution |
| C5 | Subagent nesting violation | **Resolved** — Command orchestrates directly, no debugger-as-subagent |
| C6 | Report title change breaks parsing | **Resolved** — Keep original title, use YAML frontmatter for metadata |
| C7 | `--update` flag doesn't work | **Resolved** — Use input detection (regex for Jira key vs file path) |

### From analysis documents (docs 01-07)

- 7 documents produced across Jan 11-12, 2026
- Problem statement, current workflow, solution proposals, decision matrix, refined solution, expert review, and final solution
- The team iterated from a complex dual-agent architecture to a simplified single-command approach based on user feedback

---

## 5. What Needs to Be Confirmed?

These are **blockers** — implementation should not begin until each is resolved.

### CONFIRM-1: Does `editJiraIssue` exist as an MCP tool?

**Why it matters**: This determines whether we can update Jira issue descriptions directly, or must rely solely on posting comments.

**How to verify**: Call `mcp__plugin_atlassian_atlassian__editJiraIssue` with a test issue in a live Claude Code session with Atlassian MCP configured.

**If it exists**: Include in `allowed-tools`, use as primary update mechanism.
**If it doesn't**: Design around `addCommentToJiraIssue` as the only update mechanism. Jira descriptions stay static after creation; updates go in as comments.

### CONFIRM-2: Does `getJiraIssue` return comments in its response?

**Why it matters**: The `/update-generated-report` command needs to fetch Jira comments. There is no confirmed `getJiraIssueComments` tool.

**How to verify**: Call `getJiraIssue` with a test issue that has comments. Inspect the response for `fields.comment.comments` or similar.

**If comments are included**: Extract them from the response directly.
**If comments are NOT included**: The command can only use the Jira issue description, not individual comments. This significantly limits the "incorporate engineer feedback" feature.

### CONFIRM-3: What is the exact response format of `getJiraIssue`?

**Why it matters**: The command needs to parse specific fields (summary, description, status, comments, updated timestamp). The field structure must be known.

**How to verify**: Call `getJiraIssue` and log the full response structure.

### CONFIRM-4: Does `addCommentToJiraIssue` accept markdown formatting?

**Why it matters**: Update comments need to be readable in Jira. If plain text only, the formatting strategy changes.

**How to verify**: Call `addCommentToJiraIssue` with a markdown-formatted body and check rendering in Jira.

### CONFIRM-5: What are the exact parameters for each MCP tool?

**Why it matters**: The command instructions reference specific parameter names (`cloudId`, `issueKey`, `body`, etc.) but these are based on assumptions from the `createJiraIssue` tool's interface.

**How to verify**: Test each tool call and document the exact parameter names and required fields.

### CONFIRM-6: Does the Atlassian MCP require `cloudId` for all operations?

**Why it matters**: The current `generate-jira-task.md` caches `cloudId` in `.claude/jira-project.json`. The new command needs to know if it must also resolve and cache `cloudId`.

**How to verify**: Check if `getJiraIssue` requires `cloudId` or works with just the issue key.

---

## Plan Finalization To-Dos

These must be completed **before** implementation begins.

### Phase A: MCP Verification

- [ ] **A1**: Set up a test Jira project with a test issue that has comments
- [ ] **A2**: Call `getJiraIssue` — document full response structure (CONFIRM-2, CONFIRM-3, CONFIRM-6)
- [ ] **A3**: Call `editJiraIssue` — document if it exists and its parameters (CONFIRM-1, CONFIRM-5)
- [ ] **A4**: Call `addCommentToJiraIssue` — document parameters and markdown support (CONFIRM-4, CONFIRM-5)
- [ ] **A5**: Document all confirmed tool names, parameters, and response formats in a reference table

### Phase B: Design Finalization

- [ ] **B1**: Based on A1-A5 results, finalize the fallback chain for Jira updates
- [ ] **B2**: Based on A2 result, decide if `/update-generated-report` Phase 1 can fetch comments or is description-only
- [ ] **B3**: Write the exact `allowed-tools` list for both modified/new commands (no assumptions)
- [ ] **B4**: Define the exact YAML frontmatter schema (field names, types, required vs optional)
- [ ] **B5**: Write a sample Timeline History session showing the exact markdown format

### Phase C: Review

- [ ] **C1**: Have reviewer(s) validate the architecture (single-command approach, no new agents)
- [ ] **C2**: Have reviewer(s) validate the report format changes (YAML frontmatter, backward compat)
- [ ] **C3**: Have reviewer(s) validate the user workflow (two-command flow: update-report then generate-jira-task)
- [ ] **C4**: Have reviewer(s) sign off on the MCP verification results and fallback design
- [ ] **C5**: Final approval to proceed with implementation

---

## Reference: Key Files

| File | Role | Path |
|------|------|------|
| Debugger generator (command) | Template for project-debugger agents | `agent-team-creator/commands/generate-debugger.md` |
| Jira task creator (command) | Creates Jira issues from reports | `agent-team-creator/commands/generate-jira-task.md` |
| Implementation planner (agent) | Creates implementation plans | `agent-team-creator/agents/implementation-planner.md` |
| Jira writer (agent) | Formats content for Jira | `agent-team-creator/agents/jira-writer.md` |
| Plugin manifest | Plugin metadata | `agent-team-creator/.claude-plugin/plugin.json` |
| Problem statement | Issue analysis | `docs/jira-integration-analysis/01-problem-statement.md` |
| Expert review | Critical issues found | `docs/jira-integration-analysis/06-expert-review.md` |
| Final solution | Agreed architecture | `docs/jira-integration-analysis/07-final-solution.md` |
| Example debugging report | Report format reference | `docs/app/.claude/reports/debugging/report-2026-02-19-2100.md` |

---

## Reference: Prior Analysis Documents

| Doc | Title | Key Content |
|-----|-------|-------------|
| 01 | Problem Statement | 4 root causes, impact assessment, constraints |
| 02 | Current Workflow | Detailed flow from debug to Jira creation |
| 03 | Solution Proposals | Multiple approaches evaluated |
| 04 | Decision Matrix | Criteria-based comparison of solutions |
| 05 | Refined Solution | Jira-driven update workflow (predates simplification) |
| 06 | Expert Review | 7 critical issues, 8 medium issues, 4 open questions |
| 07 | Final Solution | Simplified single-command architecture (current plan basis) |
| 08 | Implementation Plan Draft | This document |
| 09 | Architectural Review | Review feedback on this plan |

---

## Review Log

### Review: 09-architectural-review.md (2026-02-21)

| # | Feedback | Verdict | Action |
|---|----------|---------|--------|
| 2.1 | "Runaway Description" bug — pushing entire growing report to Jira hits 32KB limit or spams comments | **Accepted** | Updated Step B (generate-jira-task) to separate concerns: description stays static, updates go as comments with only the latest Timeline Session |
| 2.2 | Missing duplicate check bypass when `jira_key` detected | **Rejected** | The draft already states "Skip Phase 3 (duplicate check) — target issue already known" in Step 2b. Reviewer missed this. |
| 2.3 | `cloudId` dependency missing in new command | **Accepted** | Updated Step C Phase 0 to include `cloudId` resolution from `.claude/jira-project.json` |
| 3 | Guidance on CONFIRM items (assume editJiraIssue absent, getJiraIssue returns comments, etc.) | **Noted** | Useful directional hints but do not replace MCP verification. User explicitly chose to verify tools first. |
| 4 | Refined execution flow with empty YAML frontmatter on initial reports | **Partially rejected** | Flow is mostly redundant with existing plan. "Empty frontmatter" (`jira_key: ""`) rejected — omitting frontmatter entirely when no Jira key is known is cleaner and unambiguous. |
| 5 | REST API fallback via Claude Code Skill (Python client, credential storage, ADF conversion) | **Rejected** | Out of scope for Issue #2. Adds Python dependency, credential management, ADF conversion to a pure-markdown plugin. The existing markdown-draft fallback already handles MCP unavailability. Should be a separate feature request if needed. |
