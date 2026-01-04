# Problem Description: Debugging Report to Jira Task Pipeline

> **File**: `jira-integration-problem-description.md`
> **Created**: 2026-01-03
> **Updated**: 2026-01-04
> **Status**: In Progress - Ready for Command Implementation
> **Related**: `jira-integration-roadmap.md` (authoritative implementation details)
> **Author**: Christian Picon Calderon

---

## Plugin Overview: agent-team-creator

### What Is This Plugin?

The `agent-team-creator` plugin is a Claude Code plugin that automatically generates **project-specific agent teams** by analyzing codebases. Unlike generic agents, these generated agents understand YOUR specific project—its tech stack, architecture, conventions, and domain logic.

### Current Plugin Status

| Component | Status | Description |
|-----------|--------|-------------|
| `/generate-agent-team` | ✅ Complete | Analyzes codebase, creates specialized agents |
| `/generate-debugger` | ✅ Complete | Creates orchestrating debugger agent |
| `/generate-jira-task` | 🔧 In Development | Converts debugging reports to Jira tasks |
| `team-architect` agent | ✅ Complete | Orchestrates analysis and agent generation |
| `implementation-planner` agent | ✅ Created | Designs implementation plans from debugging reports |
| `jira-writer` agent | ✅ Updated | Formats content for Jira (with debugging context) |
| `agent-generation` skill | ✅ Complete | Templates and best practices for agents |

### Plugin Structure

```
agent-team-creator/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── commands/
│   ├── generate-agent-team.md   # ✅ Command: Create project agents
│   ├── generate-debugger.md     # ✅ Command: Create debugger agent
│   └── generate-jira-task.md    # 🔧 IN PROGRESS: Create Jira tasks
├── agents/
│   ├── team-architect.md        # ✅ Agent: Orchestrates team creation
│   ├── implementation-planner.md # ✅ Agent: Designs fix approaches (CREATED)
│   ├── jira-writer.md           # ✅ Agent: Formats Jira content (UPDATED)
│   └── context-summarizer.md    # 📋 Agent: Reserved for v2 context analysis
├── skills/
│   └── agent-generation/        # ✅ Skill: Agent creation knowledge
│       ├── SKILL.md
│       ├── references/
│       │   ├── analysis-patterns.md
│       │   └── agent-templates.md
│       └── examples/
│           ├── tech-stack-expert.md
│           ├── architecture-expert.md
│           └── domain-expert.md
└── README.md
```

---

## Existing Commands

### 1. `/generate-agent-team` - Create Project-Specific Agents

**Purpose**: Analyze a codebase and generate a team of specialized Claude Code agents that become experts on that specific project.

**Workflow**:
```
User runs /generate-agent-team
        ↓
team-architect agent activates
        ↓
Phase 1: Project Discovery
  - Identify language, frameworks, dependencies
  - Analyze package.json, requirements.txt, etc.
        ↓
Phase 2: Domain Analysis
  - Find data models and schemas
  - Map business logic and API structure
        ↓
Phase 3: Team Composition
  - Decide which agents to create
  - Scale team size to project complexity
        ↓
Phase 4: Agent Generation
  - Create agent files with project-specific knowledge
  - Save to .claude/agents/
        ↓
Agents immediately available in Claude Code
```

**Generated Agent Types**:

| Agent Type | Focus | Example Triggers |
|------------|-------|-----------------|
| Tech-Stack Expert | Frameworks, libraries, tooling | "React patterns", "hook usage" |
| Architecture Expert | Structure, patterns, conventions | "where should I put this code" |
| Domain Expert | Business logic, data models, APIs | "user authentication flow" |
| Testing Specialist | Test patterns, fixtures, coverage | "how to test this component" |
| DevOps Expert | CI/CD, deployment, infrastructure | "deployment configuration" |

**Output Example** (for a Next.js + Prisma project):
```
.claude/agents/
├── acme-nextjs-expert.md
├── acme-architecture-expert.md
├── acme-domain-expert.md
└── acme-prisma-expert.md
```

---

### 2. `/generate-debugger` - Create Orchestrating Debugger

**Purpose**: Create a project-specific debugging agent that orchestrates investigations by delegating to specialist agents and producing structured reports.

**Workflow**:
```
User runs /generate-debugger
        ↓
Scan existing agents in .claude/agents/
        ↓
Analyze project architecture and tech stack
        ↓
Generate orchestration patterns tailored to:
  - Available specialist agents
  - Project architecture type
  - Common debugging scenarios
        ↓
Create project-debugger.md with:
  - Agent registry (who to consult)
  - Core rules (coordinate, don't implement)
  - Orchestration patterns
  - Mandatory report format
```

**Key Debugger Rules**:
1. **Coordinate, don't implement** - Delegates to specialists, never fixes directly
2. **Evidence-based only** - Requires file paths, line numbers, code references
3. **Synthesize, don't parrot** - Connects findings across agents
4. **Consider system-wide impact** - Analyzes ripple effects
5. **Document the trail** - Tracks which agents contributed what

**Debugging Report Format** (output from debugger):
```markdown
### Issue Summary
- **Reported Issue**: [Original problem]
- **Affected Components**: [List]

### Investigation Trail
| Agent Consulted | Findings | Evidence |
|-----------------|----------|----------|
| frontend-expert | React hydration error | src/app/page.tsx:42 |
| backend-expert | API returns stale data | src/api/users.ts:156 |

### Root Cause Analysis
- **Root Cause**: [Technical explanation]
- **Contributing Factors**: [Other conditions]
- **Evidence Chain**: [How evidence led to conclusion]

### Impact Assessment
- **Direct Effects**: [Immediate consequences]
- **Side Effects & Warnings**: [Ripple effects]
- **Risk Level**: Critical/High/Medium/Low

### Solutions (Ordered by Effort)
#### 1. Quick Fix (Low Effort)
#### 2. Proper Fix (Medium Effort)
#### 3. Comprehensive Fix (High Effort)

### Agents Used
- **Primary Investigator**: [Agent]
- **Supporting Agents**: [List]
```

---

## The Connection: From Debugging to Jira

### Current Gap

The workflow currently ends at the debugging report:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT WORKFLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  /generate-agent-team → Creates specialist agents               │
│           ↓                                                      │
│  /generate-debugger → Creates orchestrating debugger            │
│           ↓                                                      │
│  Bug discovered → User describes issue                          │
│           ↓                                                      │
│  Debugger investigates → Consults specialists                   │
│           ↓                                                      │
│  Debugging Report generated                                      │
│           ↓                                                      │
│  ═══════════════════════════════════════════════════════════    │
│           ↓ MANUAL GAP                                           │
│  ═══════════════════════════════════════════════════════════    │
│           ↓                                                      │
│  Developer manually reads report                                 │
│           ↓                                                      │
│  Developer manually creates Jira task                           │
│           ↓                                                      │
│  Developer manually writes implementation plan                   │
│           ↓                                                      │
│  Work begins                                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The Problem

After a debugging session produces findings:

| Problem | Impact |
|---------|--------|
| **Manual translation** | Developer must interpret debugging output and write Jira task |
| **Context loss** | Important details (evidence, file paths, agent findings) often lost |
| **Inconsistent quality** | Jira task descriptions vary wildly in quality and completeness |
| **Implementation gap** | Debugging reports identify problems but don't provide step-by-step fixes |
| **Repeated effort** | Each task creation requires re-thinking structure, criteria, labels |
| **Time waste** | 15-30 minutes per task, repeated for every bug |

---

## 1. What We Want to Achieve

### The Goal

Create a `/generate-jira-task` command that **automatically transforms debugging reports into well-structured Jira tasks** with implementation guidance.

### Proposed Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROPOSED WORKFLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  /generate-agent-team → Creates specialist agents               │
│           ↓                                                      │
│  /generate-debugger → Creates orchestrating debugger            │
│           ↓                                                      │
│  Bug discovered → User describes issue                          │
│           ↓                                                      │
│  Debugger investigates → Consults specialists                   │
│           ↓                                                      │
│  Debugging Report generated                                      │
│           ↓                                                      │
│  User reviews report (optional editing)                          │
│           ↓                                                      │
│  ═══════════════════════════════════════════════════════════    │
│                   /generate-jira-task                            │
│  ═══════════════════════════════════════════════════════════    │
│           ↓                                                      │
│  implementation-planner agent designs fix                       │
│           ↓                                                      │
│  jira-writer agent formats content                              │
│           ↓                                                      │
│  Atlassian plugin creates Jira issue                            │
│           ↓                                                      │
│  Developer receives PROJ-123 with full implementation guide     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Success Criteria

| Criteria | Current | Target |
|----------|---------|--------|
| Time to create Jira task | 15-30 min | < 2 min |
| Quality consistency | Variable | 100% structured |
| Context preservation | Partial | Complete with evidence |
| Implementation clarity | Missing | Step-by-step guide |
| Automation level | 0% | 100% (single command) |

---

## 2. Integration with Jira

### Workflow Steps

```
/generate-jira-task [debugging-report-path]
        ↓
Phase 0: Check MCP Availability
  - If unavailable → FALLBACK_MODE (skip Phase 1, 3)
        ↓
Phase 1: Project Resolution (MCP) [SKIP in fallback]
  - Check for cached Jira project key
  - If first run: prompt, search, confirm, cache
        ↓
Phase 2: Load Debugging Report
  - Read from argument or find recent in .claude/reports/debugging/
  - Extract issue summary, root cause, impact, solutions
        ↓
Phase 3: Duplicate Check (MCP) [SKIP in fallback]
  - Command-level JQL search
  - Warn if similar task exists
        ↓
Phase 4: Implementation Planning
  - Invoke implementation-planner agent
  - Design step-by-step fix approach
        ↓
Phase 5: Jira Content Generation
  - Invoke jira-writer agent
  - Format into Jira-compatible structure
  - Determine issue type (Bug vs Task)
  - Generate labels
        ↓
Phase 6: Create Jira Issue
  - Call Atlassian plugin API (or write to .claude/reports/jira-drafts/ in fallback)
  - Return issue key and URL
```

### Report Storage Location

Debugging reports are stored in a plugin-agnostic location for reuse by other tools:

```
.claude/reports/
├── debugging/           # Debugging investigation reports
│   └── report-{timestamp}.md
└── jira-drafts/         # Fallback Jira drafts (when MCP unavailable)
    └── draft-{timestamp}.md
```

### Input: Debugging Report

The command expects the structured report from `/generate-debugger`, saved to `.claude/reports/debugging/`:

- **Issue Summary** → Becomes task title
- **Root Cause Analysis** → Problem description
- **Impact Assessment** → Risk level, affected components → Labels
- **Solutions** → Implementation guidance

### Output: Jira Task

```markdown
**Summary**: Fix [Component]: [Specific Outcome]
**Type**: Bug | Task
**Labels**: component:frontend, priority:high, type:bugfix

**Description**:
## Background
[Context from debugging report]

## Root Cause
[Technical explanation with evidence]

## Implementation Plan
### Step 1: [Action]
- File: path/to/file.ext
- Change: [Specific modification]

### Step 2: [Action]
...

## Acceptance Criteria
- [ ] GIVEN [context] WHEN [action] THEN [outcome]

## Testing Requirements
- [ ] Unit tests for affected code
- [ ] Integration tests for flow
```

### Bundled Jira Agents

> **Architecture Decision**: Agents are bundled in the plugin (not global) to ensure the plugin is self-contained and distributable. See roadmap for details.

| Agent | Purpose | Role in Pipeline | Status |
|-------|---------|-----------------|--------|
| `implementation-planner` | Designs implementation steps from debugging reports | Phase 4: Planning | ✅ Created |
| `jira-writer` | Transforms debugging findings into Jira content | Phase 5: Formatting | ✅ Updated |
| `context-summarizer` | Analyzes Jira work items for context | Reserved for v2 | 📋 Future |

> **Note**: `duplicate-detector` and `jira-cli-executor` were removed. Duplicate detection is now handled at the command level via MCP. CLI access was replaced by MCP-only approach (Jira Cloud).

---

## 3. Constraints

### Technical Constraints

| Constraint | Impact | Workaround |
|------------|--------|------------|
| **Atlassian plugin required** | Users without plugin can't create directly | Fall back to markdown output |
| **Jira API rate limits** | Bulk operations throttled | Single task per invocation |
| **Project field variability** | Different projects need different fields | Query metadata first |
| **Label format restrictions** | No spaces or special characters | Use hyphen-separated format |

### Workflow Constraints

| Constraint | Decision |
|------------|----------|
| **Debugging report must exist** | Command requires report input |
| **Separate command** | Not auto-triggered; user reviews first |
| **Unassigned by default** | Assignment is human decision |
| **No sprint/epic assignment** | Requires planning context |

### Explicitly Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-assign to developer | Requires team knowledge |
| Sprint assignment | Requires planning context |
| Epic creation | Too complex |
| Sub-task creation | Needs more context |
| Story point estimation | Subjective |

### Quality Constraints

| Constraint | Requirement |
|------------|-------------|
| Accuracy | Task must reflect debugging findings exactly |
| No hallucination | Implementation steps grounded in actual codebase |
| Evidence preservation | File paths and line numbers retained |
| Duplicate prevention | Check before creating |

---

## Summary

### The Core Problem

> The `agent-team-creator` plugin generates project-specific agents and a debugging orchestrator, but there's a **manual gap** between debugging investigation and task creation. Valuable findings get lost or poorly translated into Jira tasks.

### The Solution

> Add `/generate-jira-task` command that reads debugging reports, designs implementation plans, and creates structured Jira tasks—completing the automation pipeline from bug discovery to actionable work item.

### How It Fits

```
┌────────────────────────────────────────────────────────────────┐
│                    agent-team-creator PLUGIN                    │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  /generate-agent-team ─────→ Project-specific agents           │
│          │                                                      │
│          ↓                                                      │
│  /generate-debugger ───────→ Orchestrating debugger            │
│          │                                                      │
│          ↓                                                      │
│  [Debugging happens] ──────→ Debugging Report                  │
│          │                                                      │
│          ↓                                                      │
│  /generate-jira-task ──────→ Jira Task (🔧 IN DEVELOPMENT)     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### Key Constraints Summary

1. **Depends on Atlassian plugin** for Jira API access
2. **Requires debugging report** as input
3. **Separate command** (user-triggered after review)
4. **No assignee/sprint** (human decisions)
5. **Project key cached** (configured once per git project)

---

## Related Documents

- **Implementation Roadmap**: `docs/jira-integration-roadmap.md` ← **Authoritative source for implementation details**
- **Plugin README**: `agent-team-creator/README.md`
- **Debugging Report Format**: Defined by `commands/generate-debugger.md`
- **Bundled Agents**: `agent-team-creator/agents/` (not global agents)

---

## Architecture Decisions Log

| Decision | Date | Choice | Rationale |
|----------|------|--------|-----------|
| Agent location | 2026-01-03 | Bundled in plugin | Self-contained, distributable |
| Jira integration | 2026-01-03 | MCP plugin only | Native integration, no CLI dependency |
| MCP in agents | 2026-01-03 | Command-level only | Known bug: plugin agents can't reliably access MCP |
| Duplicate detection | 2026-01-03 | Command-level JQL | Agent would need MCP (blocked by bug) |
| Output validation | 2026-01-03 | Between phases | Prevent silent failures in pipeline |
