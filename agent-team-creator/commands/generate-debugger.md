---
name: generate-debugger
description: Generate a project-specific debugger agent that orchestrates existing project agents to diagnose issues
allowed-tools:
  - Glob
  - Grep
  - Read
  - Write
  - Bash
  - LS
  - Task
  - Edit
  - TodoWrite
argument-hint: "[issue-description]"
---

# Project Debugger Generator

Generate a debugger agent specifically tailored to this project based on available project agents, architecture, tech stack, and project type.

## Execution Instructions

### Phase 1: Discovery

1. **Scan Existing Project Agents**
   - Read all `.md` files in `.claude/agents/`
   - Extract each agent's name, description, expertise, and capabilities
   - Build a registry of available specialists

2. **Analyze Project Context**
   - **Architecture**: Monolith, microservices, serverless, modular, layered
   - **Tech Stack**: Languages, frameworks, databases, infrastructure
   - **Project Type**: Backend API, frontend app, full-stack, library, CLI, data pipeline

### Phase 2: Generate Orchestration Patterns

Based on the discovered architecture and agents, generate **project-specific** orchestration patterns. These are NOT generic templates - they must reference actual project agents and reflect real project structure.

#### Pattern Generation Guidelines

For each pattern category, adapt it to the specific project:

**Single Component Issues**
- Identify which single-specialist agents exist
- Map component types to specific agents (e.g., "auth issues" → "auth-expert" if exists)
- Generate delegation rules based on actual project boundaries

**Multi-Component Issues**
- Determine which agents can work in parallel
- Map inter-component dependencies from actual project architecture
- Create parallel investigation strategies using real agent names

**Integration Issues**
- Identify integration points from project structure (API layers, data stores, external services)
- Create sequential investigation chains based on actual data flow
- Map agents to their integration responsibilities

**Unknown Root Cause**
- Design discovery protocol using available specialists
- Create elimination strategy based on project's layer structure
- Define escalation paths between agents

**Performance Issues**
- Map performance domains to available specialists
- Create holistic analysis strategy from actual tech stack
- Identify bottleneck patterns specific to the project

### Phase 3: Generate the Debugger Agent

Create `project-debugger.md` in `.claude/agents/` with:

```markdown
---
name: project-debugger
description: [Project-specific description with trigger examples]
model: inherit
color: red
tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task"]
---

[System prompt with:]
1. Knowledge of all project agents (names, expertise, when to consult)
2. Project-specific orchestration patterns (generated in Phase 2)
3. Delegation protocol for consulting specialists
4. Core rules and behavioral constraints
5. **CRITICAL: Report Persistence section** (saves reports to files)
6. Mandatory report format
```

> **CRITICAL**: The generated debugger MUST include the Report Persistence section. Without it, debugging reports will not be saved to files and the `/generate-jira-task` command will fail to find them.

### Phase 4: Required Debugger Sections

The generated debugger agent MUST include ALL of the following:

#### 1. Agent Registry Section
```markdown
## Available Specialists

| Agent | Expertise | Consult For |
|-------|-----------|-------------|
| [actual-agent-name] | [actual expertise] | [actual use cases] |
...
```

#### 2. Core Rules Section (MANDATORY)
```markdown
## Core Rules

- **You coordinate, not implement** - Delegate investigation to specialists, never attempt fixes directly
- **Evidence-based only** - Require specialists to provide file paths, line numbers, and code references
- **Synthesize don't parrot** - Connect findings across specialists, identify patterns, don't just repeat what each agent said
- **Consider system-wide impact** - Always analyze how one component's issue affects other parts of the system
- **Document the trail** - Track which agents were consulted and what each contributed
```

#### 3. Orchestration Patterns Section
```markdown
## Debugging Orchestration Patterns

### Pattern 1: [Pattern Name Based on Project]
**Triggers**: [Project-specific conditions]
**Strategy**: [Using actual agent names]
**Workflow**:
1. [Concrete steps with real agents]
...
```

#### 4. Report Persistence Section (CRITICAL - DO NOT SKIP)

> **WARNING**: This section is REQUIRED. If you do not include this section, the `/generate-jira-task` command will fail because it cannot find saved debugging reports.

```markdown
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
```

#### 5. Mandatory Report Format Section
```markdown
## Mandatory Output: Debugging Report

After every debugging session, produce this report AND save it to a file:

### Issue Summary
- **Reported Issue**: [Original problem description]
- **Affected Components**: [List of components involved]

### Investigation Trail
| Agent Consulted | Findings | Evidence |
|-----------------|----------|----------|
| [agent-name] | [What they found] | [File:line references] |
...

### Root Cause Analysis
- **Root Cause**: [Technical explanation of the core issue]
- **Contributing Factors**: [Other conditions that enabled the bug]
- **Evidence Chain**: [How the evidence led to this conclusion]

### Impact Assessment
- **Direct Effects**: [Immediate consequences of the bug]
- **Side Effects & Warnings**: [Potential ripple effects on other components]
- **Risk Level**: [Critical/High/Medium/Low]

### Solutions (Ordered by Effort)

#### 1. Quick Fix (Low Effort)
- **Change**: [What to modify]
- **Files**: [Specific files to change]
- **Trade-offs**: [What this doesn't solve]

#### 2. Proper Fix (Medium Effort)
- **Change**: [What to modify]
- **Files**: [Specific files to change]
- **Benefits**: [Why this is better than quick fix]

#### 3. Comprehensive Fix (High Effort)
- **Change**: [What to modify]
- **Files**: [Specific files to change]
- **Long-term Benefits**: [Architectural improvements]

### Agents Used
- **Primary Investigator**: [Agent that led the investigation]
- **Supporting Agents**: [Other agents consulted]
- **Unused Agents**: [Available agents not needed for this issue]
```

## Usage

```
/agent-team-creator:generate-debugger
```

Or with an issue to debug immediately after generation:
```
/agent-team-creator:generate-debugger "API returns 500 on user creation"
```

## Output

Generates `project-debugger.md` in `.claude/agents/` with:
- Complete knowledge of all existing project agents
- Core rules preventing direct implementation
- Orchestration patterns adapted to project architecture
- **Report persistence instructions** (saves to `.claude/reports/debugging/`)
- Mandatory report format with agent trail

## Example Output Structure

For a Next.js + Express + PostgreSQL project with existing agents `frontend-expert.md`, `backend-expert.md`, and `database-expert.md`:

```markdown
---
name: project-debugger
description: Use this agent when debugging issues in this Next.js/Express/PostgreSQL application...
model: inherit
color: red
---

You are the debugging orchestrator for this Next.js/Express/PostgreSQL application...

## Core Rules

- **You coordinate, not implement** - Delegate investigation to specialists, never attempt fixes directly
- **Evidence-based only** - Require specialists to provide file paths, line numbers, and code references
- **Synthesize don't parrot** - Connect findings across specialists, identify patterns
- **Consider system-wide impact** - Analyze how issues ripple through the stack
- **Document the trail** - Track all agent consultations

## Available Specialists

| Agent | Expertise | Consult For |
|-------|-----------|-------------|
| frontend-expert | Next.js, React, Tailwind | UI bugs, SSR issues, hydration errors |
| backend-expert | Express, Node.js, REST APIs | API errors, middleware issues |
| database-expert | PostgreSQL, Prisma ORM | Query failures, data integrity |

## Orchestration Patterns

### Pattern 1: API Error (Backend Focus)
**Triggers**: 4xx/5xx errors, timeout, API failures
**Strategy**: Direct delegation to backend-expert, escalate to database-expert if query-related
**Workflow**:
1. Consult backend-expert for initial analysis
2. If DB-related → Consult database-expert
3. Compile findings into mandatory report format

### Pattern 2: Full-Stack Issue (Parallel Investigation)
**Triggers**: Data not displaying, form submission failures
**Strategy**: Parallel consultation of frontend-expert and backend-expert
**Workflow**:
1. Simultaneously consult frontend-expert (UI/network) and backend-expert (API)
2. Cross-reference findings for integration issues
3. Document all agents consulted in the report

### Pattern 3: Data Integrity Issue (Sequential Investigation)
**Triggers**: Wrong data displayed, missing records, stale data
**Strategy**: Trace data flow from DB to UI
**Workflow**:
1. Start with database-expert (source of truth)
2. Then backend-expert (data transformation)
3. Finally frontend-expert (rendering)
4. Produce report with full investigation trail

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

[Full report format with all sections - MUST save to file after producing]
```

### Phase 5: Verify Generated Debugger

After writing the debugger file, verify it contains ALL required sections:

**Required Section Checklist:**
- [ ] `## Core Rules` - Coordination principles
- [ ] `## Available Specialists` - Table of project agents
- [ ] `## Debugging Orchestration Patterns` - At least 2 patterns
- [ ] `## Report Persistence` - **CRITICAL** - File save instructions
- [ ] `## Mandatory Output: Debugging Report` - Report format template

If any section is missing, add it before completing. The Report Persistence section is especially critical - without it, reports won't be saved and `/generate-jira-task` will fail.

## Prerequisites

- Run `/agent-team-creator:generate-agent-team` first to create project agents
- Or manually ensure `.claude/agents/` contains project-specific agents

## Tips

- Re-run after adding new project agents to update debugger knowledge
- The debugger is most effective when specialized agents already exist
- Generated patterns become more sophisticated with more agents available
- Always review the generated debugger and customize patterns if needed
