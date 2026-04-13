# Issue #10 — Orchestrator Delegation Fix: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the generated project-debugger dispatch specialist subagents instead of investigating source code directly.

**Architecture:** Modify the `generate-debugger.md` command template so the debugger it produces includes `Agent(specialist1, ...)` in its tools field, a mandatory procedural workflow that gates analysis behind dispatch, and a consolidated report format. Minimal awareness note added to `team-architect.md`.

**Tech Stack:** Claude Code plugin system (markdown agent/command files with YAML frontmatter). No code — all changes are markdown templates.

**Spec:** `docs/superpowers/specs/2026-04-13-issue-10-orchestrator-delegation-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `agent-team-creator/commands/generate-debugger.md` | Modify | Phase 1 guard, Phase 3 tools template, Phase 4 procedural workflow + report format, Phase 5 checklist, example output |
| `agent-team-creator/agents/team-architect.md` | Modify | Add orchestrator note to Agent Quality Standards |

---

### Task 1: Add Phase 1 Agent Discovery Guard

**Files:**
- Modify: `agent-team-creator/commands/generate-debugger.md:23-33`

- [ ] **Step 1: Replace Phase 1 Discovery section**

Replace lines 23-33 (the current Phase 1: Discovery section) with explicit Glob/Grep discovery and a guard:

```markdown
### Phase 1: Discovery

1. **Discover Existing Project Agents**
   - Run **Glob** on `.claude/agents/*.md` to list all agent files
   - If **no agent files are found**, stop immediately and tell the user:
     ```
     No specialist agents found in .claude/agents/. The debugger requires
     a team of specialists to delegate to.

     Run /agent-team-creator:generate-agent-team first to create your
     project's specialist agents, then re-run /generate-debugger.
     ```
   - Read each discovered agent file
   - Extract each agent's name, description, expertise, and tools
   - Run **Grep** on `.claude/agents/` for `name:`, `description:`, `tools:` to validate agents are well-formed
   - Build a registry of available specialists

2. **Analyze Project Context**
   - **Architecture**: Monolith, microservices, serverless, modular, layered
   - **Tech Stack**: Languages, frameworks, databases, infrastructure
   - **Project Type**: Backend API, frontend app, full-stack, library, CLI, data pipeline
```

- [ ] **Step 2: Verify the edit**

Read `generate-debugger.md` lines 23-45 and confirm:
- Glob on `.claude/agents/*.md` is step 1
- Guard (stop + message) is step 2 within the discovery
- Grep validation is present
- "Analyze Project Context" is preserved as sub-step 2

- [ ] **Step 3: Commit**

```bash
git add agent-team-creator/commands/generate-debugger.md
git commit -m "fix(#10): add Phase 1 agent discovery guard with Glob/Grep"
```

---

### Task 2: Update Phase 3 Tools Field Template

**Files:**
- Modify: `agent-team-creator/commands/generate-debugger.md:68-88`

- [ ] **Step 1: Replace the Phase 3 template frontmatter**

In the Phase 3 code block (lines 72-88), replace the `tools` line and system prompt outline. The full replacement for lines 72-88:

```markdown
```markdown
---
name: project-debugger
description: [Project-specific description with trigger examples]
model: inherit
color: red
tools: Agent({agent-names-from-registry}), Read, Write, Grep, Glob, Bash
---

You are the debugging orchestrator for this [project-description].
This agent coordinates specialist agents to diagnose issues. It never
implements fixes directly. The agent investigates and synthesizes
findings across specialists and produces structured reports.

[System prompt with:]
1. Knowledge of all project agents (names, expertise, when to consult)
2. Project-specific orchestration patterns (generated in Phase 2)
3. Mandatory 4-step procedural workflow for dispatching specialists
4. **CRITICAL: Report Persistence section** (saves reports to files)
5. Mandatory report format
6. Role reminder (closing reinforcement)
```
```

Note: `{agent-names-from-registry}` is a placeholder that Phase 3 dynamically fills with the actual agent names from Phase 1 (e.g., `Agent(acme-backend-expert, acme-database-expert, acme-react-expert)`).

- [ ] **Step 2: Verify the edit**

Read `generate-debugger.md` lines 68-92 and confirm:
- `tools:` uses `Agent({agent-names-from-registry}), Read, Write, Grep, Glob, Bash`
- `Task` is no longer in the tools list
- Role definition opening paragraph is present after the `---`
- System prompt outline lists "Mandatory 4-step procedural workflow" and "Role reminder"

- [ ] **Step 3: Commit**

```bash
git add agent-team-creator/commands/generate-debugger.md
git commit -m "fix(#10): update Phase 3 tools field with Agent(...) and role definition"
```

---

### Task 3: Replace Core Rules with Procedural Workflow

**Files:**
- Modify: `agent-team-creator/commands/generate-debugger.md:106-115`

- [ ] **Step 1: Replace Phase 4 Section 2 (Core Rules)**

Replace the "#### 2. Core Rules Section (MANDATORY)" block (lines 106-115) with:

```markdown
#### 2. Mandatory Procedural Workflow Section (MANDATORY — replaces Core Rules)
```markdown
## MANDATORY WORKFLOW

You MUST follow these 4 steps in order. You CANNOT skip or reorder steps.
You CANNOT proceed to Step 3 without completing Step 2.

### Step 1: Understand the Problem
Read the user's message and any referenced files/logs to understand what's being reported.
You MAY use Read/Grep here for quick context only.

### Step 2: Dispatch Specialists (REQUIRED -- DO NOT SKIP)
You MUST use the Agent tool to dispatch at least one specialist
BEFORE you write any analysis.

If you find yourself about to write "Root Cause" or "Analysis"
without having dispatched an Agent, STOP and dispatch one first.

#### When to use Single Dispatch
Use when debugging follows a linear flow: a request-response chain,
a data transformation pipeline, or a single component failure.

**Example:**
Dispatch the backend specialist to trace a request flow:

Agent tool call:
- subagent_type: "{project-slug}-backend-expert"
- prompt: "Investigate: The /api/users endpoint returns 500.
  Trace the request from route handler through middleware to
  the database query. Return: affected files with line numbers,
  error chain, and your assessment of the root cause."

#### When to use Parallel Dispatch
Use when the issue spans multiple services or domains:
- One service is down while another is up (e.g., backend down, database up)
- The user explicitly mentions several services are involved
- Logs show errors across multiple components

**Example:**
Dispatch backend and database specialists in parallel:

Agent call 1:
- subagent_type: "{project-slug}-backend-expert"
- prompt: "Investigate: API returning 503. Check service health,
  connection pools, and error handlers. Return: affected files
  with line numbers, error traces, and whether the backend
  is the origin of the failure."

Agent call 2:
- subagent_type: "{project-slug}-database-expert"
- prompt: "Investigate: Database connectivity during API 503.
  Check connection config, pool exhaustion, query timeouts.
  Return: connection status evidence, slow query logs,
  and whether the database is contributing to the failure."

### Step 3: Synthesize
AFTER all dispatched specialists return, combine their findings
into the full Debugging Report format below (all 5 sections:
Investigation Trail, Root Cause, Impact & Solutions, Version Impact,
Scope Boundaries).

### Step 4: Save Report
Save the completed debugging report to a file and inform the user.
```
```

- [ ] **Step 2: Verify the edit**

Read the updated section and confirm:
- Section title says "Mandatory Procedural Workflow" not "Core Rules"
- 4 steps are present in order
- Single dispatch and parallel dispatch examples are present with `subagent_type` references
- Step 3 references all 5 report sections by name

- [ ] **Step 3: Commit**

```bash
git add agent-team-creator/commands/generate-debugger.md
git commit -m "fix(#10): replace Core Rules with mandatory procedural workflow"
```

---

### Task 4: Replace Report Format

**Files:**
- Modify: `agent-team-creator/commands/generate-debugger.md:183-238`

- [ ] **Step 1: Replace Phase 4 Section 5 (Mandatory Report Format)**

Replace lines 183-238 (the "#### 5. Mandatory Report Format Section") with:

```markdown
#### 5. Mandatory Report Format Section
```markdown
## Mandatory Output: Debugging Report

After every debugging session, produce this report AND save it to a file:

If a Jira key is known, include YAML frontmatter at the top:
---
jira_key: {JIRA-KEY}
jira_url: {URL}
created: {YYYY-MM-DD HH:mm}
last_updated: {YYYY-MM-DD HH:mm}
---

### 1. Investigation Trail
| Agent Consulted | Findings | Evidence (File:Line) |
|-----------------|----------|----------------------|
| [agent-name] | [What they discovered] | [file:line references] |

### 2. Root Cause Analysis
- **Root Cause**: [Technical explanation]
- **Evidence Chain**: [How evidence led to this conclusion]

### 3. Impact Assessment & Solutions

#### Impact
- **Direct Effects**: [Immediate consequences]
- **Risk Level**: Critical / High / Medium / Low

#### Solutions

Provide one or more solutions. Multiple solutions are only needed when
they represent genuinely different approaches with distinct trade-offs.
If a change works on its own without architectural trade-offs, list it
as a single solution -- do not artificially split into quick/proper/comprehensive.

When multiple solutions ARE warranted, differentiate them by:
- **Architectural decisions**: Does this change the system's structure?
- **Business impact**: What does each approach enable or limit?
- **Trade-offs**: What are you giving up with each option?
- **Effort & resources**: Team time, dependencies, migration cost

**Format per solution:**
#### Solution [N]: [Name]
- **Change**: [What to modify]
- **Files**: [Specific files]
- **Architectural impact**: [None / Minor / Significant]
- **Business impact**: [What this enables or limits]
- **Trade-offs**: [What you gain vs. what you give up]
- **Effort**: [Low / Medium / High]

### 4. Version Impact
- **Affected Versions**: [Which versions exhibit the bug]
- **Introduced In**: [Commit/release where it appeared, if identifiable]
- **Fix Compatibility**: [Will the fix require version bumps or migrations]

### 5. Scope Boundaries
- **In Scope**: [Components/services directly affected]
- **Out of Scope**: [Related areas NOT affected]
- **Boundary Risks**: [Edge cases where scope might expand]
```
```

- [ ] **Step 2: Verify the edit**

Read the updated section and confirm:
- 5 sections: Investigation Trail, Root Cause, Impact & Solutions, Version Impact, Scope Boundaries
- Solutions section does NOT force three tiers
- Solutions differentiation criteria: architectural decisions, business impact, trade-offs, effort
- No "Issue Summary", "Contributing Factors", "Side Effects & Warnings", or "Agents Used" sections

- [ ] **Step 3: Commit**

```bash
git add agent-team-creator/commands/generate-debugger.md
git commit -m "fix(#10): update report format with consolidated investigation trail"
```

---

### Task 5: Update Example Output Structure

**Files:**
- Modify: `agent-team-creator/commands/generate-debugger.md:260-341`

- [ ] **Step 1: Replace the example output**

Replace lines 262-341 (the example output code block) with an updated example that reflects all changes: `Agent(...)` in tools, role sandwich, procedural workflow instead of Core Rules, and the new report format. The example should show:

1. Updated frontmatter with `tools: Agent(frontend-expert, backend-expert, database-expert), Read, Write, Grep, Glob, Bash`
2. Role definition opening paragraph after the `---`
3. Available Specialists table (unchanged)
4. Procedural workflow section (replacing Core Rules)
5. Orchestration patterns (unchanged)
6. Report Persistence (unchanged)
7. New Mandatory Output report format
8. Role Reminder closing reinforcement as the final section

```markdown
For a Next.js + Express + PostgreSQL project with existing agents `frontend-expert.md`, `backend-expert.md`, and `database-expert.md`:

```markdown
---
name: project-debugger
description: Use this agent when debugging issues in this Next.js/Express/PostgreSQL application...
model: inherit
color: red
tools: Agent(frontend-expert, backend-expert, database-expert), Read, Write, Grep, Glob, Bash
---

You are the debugging orchestrator for this Next.js/Express/PostgreSQL application.
This agent coordinates specialist agents to diagnose issues. It never implements
fixes directly. The agent investigates and synthesizes findings across specialists
and produces structured reports.

## Available Specialists

| Agent | Expertise | Consult For |
|-------|-----------|-------------|
| frontend-expert | Next.js, React, Tailwind | UI bugs, SSR issues, hydration errors |
| backend-expert | Express, Node.js, REST APIs | API errors, middleware issues |
| database-expert | PostgreSQL, Prisma ORM | Query failures, data integrity |

## MANDATORY WORKFLOW

You MUST follow these 4 steps in order. You CANNOT skip or reorder steps.
You CANNOT proceed to Step 3 without completing Step 2.

### Step 1: Understand the Problem
Read the user's message and any referenced files/logs to understand what's being reported.
You MAY use Read/Grep here for quick context only.

### Step 2: Dispatch Specialists (REQUIRED -- DO NOT SKIP)
You MUST use the Agent tool to dispatch at least one specialist
BEFORE you write any analysis.

If you find yourself about to write "Root Cause" or "Analysis"
without having dispatched an Agent, STOP and dispatch one first.

### Step 3: Synthesize
AFTER all dispatched specialists return, combine their findings
into the full Debugging Report format (all 5 sections).

### Step 4: Save Report
Save the completed debugging report to a file and inform the user.

## Debugging Orchestration Patterns

### Pattern 1: API Error (Backend Focus)
**Triggers**: 4xx/5xx errors, timeout, API failures
**Strategy**: Direct delegation to backend-expert, escalate to database-expert if query-related
**Workflow**:
1. Dispatch backend-expert for initial analysis
2. If DB-related → Dispatch database-expert
3. Synthesize findings into report

### Pattern 2: Full-Stack Issue (Parallel Investigation)
**Triggers**: Data not displaying, form submission failures
**Strategy**: Parallel dispatch of frontend-expert and backend-expert
**Workflow**:
1. Simultaneously dispatch frontend-expert (UI/network) and backend-expert (API)
2. Cross-reference findings for integration issues
3. Synthesize findings into report

### Pattern 3: Data Integrity Issue (Sequential Investigation)
**Triggers**: Wrong data displayed, missing records, stale data
**Strategy**: Trace data flow from DB to UI
**Workflow**:
1. Dispatch database-expert (source of truth)
2. Then dispatch backend-expert (data transformation)
3. Finally dispatch frontend-expert (rendering)
4. Synthesize findings into report

## Report Persistence

**MANDATORY**: After EVERY debugging session, you MUST save the report to a file.

### Save Location
- **Directory**: `.claude/reports/debugging/`
- **Create directory if it doesn't exist**: Use Write tool to create the path

### File Naming
- **Format**: `report-{YYYY-MM-DD-HHmm}.md`
- **Example**: `report-2026-01-03-1530.md`

### Save Policy
- Always create a NEW file with timestamp (preserve history, never overwrite)
- Save the COMPLETE debugging report (all sections)

### After Saving
Tell the user:
1. "Report saved to: .claude/reports/debugging/report-{timestamp}.md"
2. "To create a Jira task from this report, run: /agent-team-creator:generate-jira-task"

## Mandatory Output: Debugging Report

[Full report format with all 5 sections - MUST save to file after producing]

## Role Reminder

This agent coordinates and synthesizes. It never implements fixes
directly. It delegates investigation to specialists, connects findings
across domains, and produces structured debug reports.
```
```

- [ ] **Step 2: Verify the edit**

Read the example output and confirm:
- `tools:` includes `Agent(frontend-expert, backend-expert, database-expert)`
- Role definition is the first paragraph after `---`
- "MANDATORY WORKFLOW" section replaces "Core Rules"
- Orchestration patterns use "Dispatch" language instead of "Consult"
- "Role Reminder" is the final section

- [ ] **Step 3: Commit**

```bash
git add agent-team-creator/commands/generate-debugger.md
git commit -m "fix(#10): update example output with procedural workflow and role sandwich"
```

---

### Task 6: Update Phase 5 Verification Checklist

**Files:**
- Modify: `agent-team-creator/commands/generate-debugger.md:343-354`

- [ ] **Step 1: Replace Phase 5 checklist**

Replace the Phase 5 checklist (lines 347-354) with:

```markdown
**Required Section Checklist:**
- [ ] `## Available Specialists` - Table of project agents
- [ ] `## MANDATORY WORKFLOW` - 4-step procedural workflow with dispatch gate
- [ ] `## Debugging Orchestration Patterns` - At least 2 patterns
- [ ] `## Report Persistence` - **CRITICAL** - File save instructions
- [ ] `## Mandatory Output: Debugging Report` - Report format with 5 sections
- [ ] `## Role Reminder` - Closing reinforcement of coordination role

If any section is missing, add it before completing. The Report Persistence section is especially critical - without it, reports won't be saved and `/generate-jira-task` will fail.
```

- [ ] **Step 2: Verify the edit**

Read Phase 5 and confirm:
- "Core Rules" is no longer in the checklist
- "MANDATORY WORKFLOW" is present
- "Role Reminder" is present
- All 6 required sections are listed

- [ ] **Step 3: Commit**

```bash
git add agent-team-creator/commands/generate-debugger.md
git commit -m "fix(#10): update Phase 5 checklist for procedural workflow"
```

---

### Task 7: Update Output Summary Section

**Files:**
- Modify: `agent-team-creator/commands/generate-debugger.md:253-258`

- [ ] **Step 1: Update the Output section**

Replace lines 253-258 with:

```markdown
Generates `project-debugger.md` in `.claude/agents/` with:
- `Agent(specialist1, ...)` in tools field for subagent dispatching
- Role definition opening (coordination, not implementation)
- Mandatory 4-step procedural workflow gating analysis behind dispatch
- Orchestration patterns adapted to project architecture
- **Report persistence instructions** (saves to `.claude/reports/debugging/`)
- Mandatory report format with investigation trail
- Role reminder closing reinforcement
```

- [ ] **Step 2: Commit**

```bash
git add agent-team-creator/commands/generate-debugger.md
git commit -m "fix(#10): update output summary to reflect new structure"
```

---

### Task 8: Add Orchestrator Note to team-architect.md

**Files:**
- Modify: `agent-team-creator/agents/team-architect.md:159-169`

- [ ] **Step 1: Add orchestrator guidance to Agent Quality Standards**

After line 169 (after item 7 "Provide guidance"), add a new item:

```markdown
8. **Include `Agent(...)` for orchestrators** - If the agent coordinates other agents (e.g., a debugger), its `tools` field must include `Agent(agent1, agent2, ...)` listing the agents it can dispatch. Without this, the agent cannot spawn subagents when running via `claude --agent`. See the [official docs](https://code.claude.com/docs/en/sub-agents#restrict-which-subagents-can-be-spawned).
```

- [ ] **Step 2: Verify the edit**

Read `team-architect.md` lines 159-175 and confirm:
- Item 8 is present with `Agent(...)` guidance
- The URL to official docs is included
- Existing items 1-7 are unchanged

- [ ] **Step 3: Commit**

```bash
git add agent-team-creator/agents/team-architect.md
git commit -m "fix(#10): add orchestrator Agent(...) guidance to team-architect"
```

---

### Task 9: Manual Verification

This is a markdown template project with no automated tests. Verification requires generating a debugger and checking its behavior.

- [ ] **Step 1: Review all changes**

```bash
git diff main...HEAD --stat
git log --oneline main..HEAD
```

Confirm all 8 commits are present and only 2 files were modified.

- [ ] **Step 2: Read the final `generate-debugger.md`**

Read the complete file and verify against the acceptance criteria:
- Phase 1 runs Glob/Grep with guard
- Phase 3 template has `Agent(...)` in tools
- Phase 4 has procedural workflow (not Core Rules)
- Phase 4 has single + parallel dispatch examples
- Phase 4 has role definition at top
- Report format has 5 sections (no forced three-tier solutions)
- Phase 5 checklist includes MANDATORY WORKFLOW and Role Reminder
- Example output reflects all changes
- Role Reminder is the last section in the example

- [ ] **Step 3: Read the final `team-architect.md`**

Read lines 159-175 and confirm item 8 about orchestrator `Agent(...)` is present.

- [ ] **Step 4: (Manual) Generate a test debugger**

Navigate to any project with existing agents in `.claude/agents/` and run:

```bash
/agent-team-creator:generate-debugger
```

Then run the generated debugger:

```bash
claude --agent project-debugger "Test: describe the project structure"
```

Verify the debugger dispatches specialists instead of reading code directly.
