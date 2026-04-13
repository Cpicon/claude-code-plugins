# Issue #9: Fix YAML Description Format Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all `<example>` blocks in agent `description:` fields that break project-level YAML parsing, replacing them with `description: |` keyword-rich prose.

**Architecture:** Pure documentation/template change. No code, no tests, no new files. Every change converts a YAML `description:` field from bare multi-line with `<example>` tags to literal block scalar (`|`) with keyword-rich prose. Some files also need body/content updates where they *teach* the `<example>` format to LLMs.

**Tech Stack:** YAML frontmatter in Markdown files, Claude Code plugin system.

**Spec:** `docs/superpowers/specs/2026-04-13-issue-9-yaml-description-fix-design.md`

**Worktree:** `.worktrees/fix-issue-9` (branch `fix/issue-9-yaml-parsing`)

---

## File Map

All paths relative to `agent-team-creator/` unless noted otherwise.

| File | Change Type | Description |
|------|-------------|-------------|
| `agents/team-architect.md` | Frontmatter + Body | Fix own description AND body instructions that teach `<example>` format |
| `agents/implementation-planner.md` | Frontmatter | Fix description field |
| `agents/jira-writer.md` | Frontmatter | Normalize description to `\|` format |
| `agents/context-summarizer.md` | Frontmatter | Normalize description to `\|` format |
| `skills/agent-generation/references/agent-templates.md` | Content + Prose | Fix all 5 template description code blocks AND introductory prose on line 7 |
| `skills/agent-generation/SKILL.md` | Content | Fix 7 locations teaching `<example>` format |
| `skills/agent-generation/examples/tech-stack-expert.md` | Content | Fix example description code block |
| `skills/agent-generation/examples/architecture-expert.md` | Content | Fix example description code block |
| `skills/agent-generation/examples/domain-expert.md` | Content | Fix example description code block |
| `commands/generate-debugger.md` | Content | Fix 2 template/example description locations |
| `docs/app/.claude/agents/project-debugger.md` | Frontmatter | Fix description field |
| `docs/app/.claude/agents/user-api-architecture-expert.md` | Frontmatter | Fix description field |
| `docs/app/.claude/agents/user-api-fastapi-expert.md` | Frontmatter | Fix description field |
| `docs/app/.claude/agents/user-api-security-expert.md` | Frontmatter | Fix description field |
| `docs/app/.claude/agents/user-api-testing-expert.md` | Frontmatter | Fix description field |
| `docs/jira-integration-roadmap.md` | Content | Fix agent code block description |

---

## Task 1: Fix plugin's own agents (4 files)

**Files:**
- Modify: `agent-team-creator/agents/team-architect.md` (frontmatter only — body is Task 4)
- Modify: `agent-team-creator/agents/implementation-planner.md`
- Modify: `agent-team-creator/agents/jira-writer.md`
- Modify: `agent-team-creator/agents/context-summarizer.md`

- [ ] **Step 1: Fix `team-architect.md` frontmatter description**

Replace the bare multi-line description (with 3 `<example>` blocks) with:

```yaml
description: |
  Use this agent when orchestrating the creation of project-specific Claude Code
  agent teams. Analyzes codebases to understand architecture, tech stack, and
  domain, then generates a complementary team of specialized agents. Covers
  agent team generation, codebase analysis, and agent composition planning.
```

Keep everything else in the frontmatter (`model`, `color`, `tools`) unchanged. Keep the closing `---` and body unchanged.

- [ ] **Step 2: Fix `implementation-planner.md` frontmatter description**

Replace the bare multi-line description (with 2 `<example>` blocks) with:

```yaml
description: |
  Use this agent when you need to design an implementation plan from a debugging
  report or problem description. Analyzes root causes, selects appropriate
  solution tiers (quick/proper/comprehensive), and creates step-by-step
  implementation guidance with file-level changes, testing requirements, and
  risk assessment. Does not require MCP access.
```

- [ ] **Step 3: Fix `jira-writer.md` frontmatter description**

Replace the single-line description (with escaped `\n` and `<example>` blocks) with:

```yaml
description: |
  Use this agent when you need to create or draft Jira tickets, user stories, or
  task descriptions from high-level requirements, rough ideas, or debugging
  reports. Excels at transforming vague or technical concepts into well-structured
  Jira issues with clear summaries, detailed descriptions, acceptance criteria,
  and deliverables. Particularly useful for AI/ML projects and for converting
  debugging reports with implementation plans into actionable bug tickets.
```

- [ ] **Step 4: Fix `context-summarizer.md` frontmatter description**

Replace the single-line description (with escaped `\n` and `<example>` blocks) with:

```yaml
description: |
  Use this agent to analyze and summarize Jira work item context from provided
  data. Takes Jira issue details as input and provides structured analysis of
  scope, dependencies, and blockers. NOTE: This agent does NOT fetch from Jira
  directly - the calling command or user should provide issue data as input.
```

- [ ] **Step 5: Verify all 4 files have valid YAML frontmatter**

Run from the worktree root:
```bash
for f in agent-team-creator/agents/{team-architect,implementation-planner,jira-writer,context-summarizer}.md; do
  echo "=== $f ===" && head -5 "$f"
done
```

Expected: Each file starts with `---`, then `name:`, then `description: |`, with indented prose.

- [ ] **Step 6: Commit**

```bash
git add agent-team-creator/agents/{team-architect,implementation-planner,jira-writer,context-summarizer}.md
git commit -m "fix(agents): convert description fields to YAML literal block scalar

Replace <example> blocks and escaped \n sequences in description fields
with description: | using keyword-rich prose. Fixes silent rejection by
Claude Code's project-level YAML parser.

Closes part of #9"
```

---

## Task 2: Fix example agent files in docs/ (5 files)

**Files:**
- Modify: `docs/app/.claude/agents/project-debugger.md`
- Modify: `docs/app/.claude/agents/user-api-architecture-expert.md`
- Modify: `docs/app/.claude/agents/user-api-fastapi-expert.md`
- Modify: `docs/app/.claude/agents/user-api-security-expert.md`
- Modify: `docs/app/.claude/agents/user-api-testing-expert.md`

- [ ] **Step 1: Fix `project-debugger.md` description**

Replace the bare multi-line description (with 3 `<example>` blocks) with:

```yaml
description: |
  Use this agent when the user reports a bug, error, unexpected behavior,
  something broken, or needs help diagnosing issues across the User Management
  API. Coordinates specialist agents to investigate, produces structured
  debugging reports with root cause analysis and fix recommendations.
```

- [ ] **Step 2: Fix `user-api-architecture-expert.md` description**

Replace with:

```yaml
description: |
  Use this agent when the user asks about code placement, project structure,
  module organization, refactoring, separation of concerns, or adding a
  database. Provides guidance on architectural decisions and evolving the
  User Management API project structure.
```

- [ ] **Step 3: Fix `user-api-fastapi-expert.md` description**

Replace with:

```yaml
description: |
  Use this agent when the user asks about FastAPI patterns, Pydantic models,
  endpoint implementation, request/response schemas, dependency injection,
  route handlers, or API validation in this User Management API project.
```

- [ ] **Step 4: Fix `user-api-security-expert.md` description**

Replace with:

```yaml
description: |
  Use this agent when the user asks about authentication, password hashing,
  session management, security vulnerabilities, token handling, input
  validation, authorization, bcrypt, or JWT in this User Management API.
```

- [ ] **Step 5: Fix `user-api-testing-expert.md` description**

Replace with:

```yaml
description: |
  Use this agent when the user asks about writing tests, pytest, FastAPI
  testing, TestClient, test coverage, fixtures, mocking, or integration
  tests for the User Management API.
```

- [ ] **Step 6: Verify all 5 files**

```bash
for f in docs/app/.claude/agents/*.md; do
  echo "=== $f ===" && head -5 "$f"
done
```

- [ ] **Step 7: Commit**

```bash
git add docs/app/.claude/agents/*.md
git commit -m "fix(docs): convert example agent descriptions to literal block scalar

Update all 5 example agents in docs/app/.claude/agents/ to use
description: | format, consistent with the new format standard.

Part of #9"
```

---

## Task 3: Fix generation templates (agent-templates.md)

**Files:**
- Modify: `agent-team-creator/skills/agent-generation/references/agent-templates.md`

This file has 5 template code blocks plus introductory prose. Each code block has a `description:` field with `<example>` blocks inside a markdown code fence. The code blocks teach the LLM what format to produce.

- [ ] **Step 1: Fix introductory prose on line 7**

Line 7 reads: `- \`description:\` with \`<example>\` blocks (not \`whenToUse:\`)`

Change to: `- \`description:\` using \`|\` literal block scalar with keyword-rich prose (not \`whenToUse:\`)`

- [ ] **Step 2: Fix Tech-Stack Expert Template description**

In the first template code block, replace the `description:` value. Change from bare multi-line with `<example>` blocks to:

```yaml
description: |
  Use this agent when the user asks about {{framework}} patterns,
  {{framework}} best practices, {{library}} usage, {{framework}}
  configuration, or needs help implementing features using the
  project's {{framework}} stack.
```

Remove the 3 `<example>` blocks that follow the description.

- [ ] **Step 3: Fix Architecture Expert Template description**

In the second template code block, replace similarly:

```yaml
description: |
  Use this agent when the user asks about code placement, project
  structure, module boundaries, import conventions, naming conventions,
  code organization, or needs guidance on architectural decisions.
```

Remove the 3 `<example>` blocks.

- [ ] **Step 4: Fix Domain Expert Template description**

In the third template code block, replace:

```yaml
description: |
  Use this agent when the user asks about {{domain-term-1}},
  {{domain-term-2}}, data models, business logic, API endpoints,
  entity relationships, or needs to understand the business domain
  and data flows.
```

Remove the 3 `<example>` blocks.

- [ ] **Step 5: Fix Testing Specialist Template description**

In the fourth template code block, replace:

```yaml
description: |
  Use this agent when the user asks about writing tests, test patterns,
  mocking, fixtures, test coverage, integration tests, e2e tests, or
  test utilities for this project.
```

Remove the 3 `<example>` blocks.

- [ ] **Step 6: Fix DevOps Expert Template description**

In the fifth template code block, replace:

```yaml
description: |
  Use this agent when the user asks about deployment, CI/CD, Docker,
  infrastructure, environment variables, build process, or
  configuration for this project.
```

Remove the 3 `<example>` blocks.

- [ ] **Step 7: Verify no `<example>` remains**

```bash
grep -n '<example>' agent-team-creator/skills/agent-generation/references/agent-templates.md
```

Expected: No matches.

- [ ] **Step 8: Commit**

```bash
git add agent-team-creator/skills/agent-generation/references/agent-templates.md
git commit -m "fix(templates): convert all 5 agent template descriptions to literal block scalar

Remove <example> blocks from description fields in Tech-Stack,
Architecture, Domain, Testing, and DevOps agent templates.

Part of #9"
```

---

## Task 4: Fix SKILL.md (7 locations) and team-architect.md body

**Files:**
- Modify: `agent-team-creator/skills/agent-generation/SKILL.md`
- Modify: `agent-team-creator/agents/team-architect.md` (body instructions only — frontmatter was fixed in Task 1)

- [ ] **Step 1: Fix SKILL.md — "Strong Trigger Conditions" section**

Find the heading "### 3. Strong Trigger Conditions". Two changes:

1. The prose text reads: `Each agent needs specific, non-overlapping trigger phrases in the \`description:\` field, using \`<example>\` blocks:`
   Change to: `Each agent needs specific, non-overlapping trigger phrases in the \`description:\` field, using \`|\` literal block scalar with keyword-rich prose:`

2. Replace the code block's `<example>` block with:

```yaml
description: |
  Use this agent when the user asks about React component patterns,
  hook usage in this project, state management with Redux, or needs
  help understanding how the frontend architecture works.
```

- [ ] **Step 2: Fix SKILL.md — "Agent Structure Template" section**

Find the code block under "## Agent Structure Template". Replace the `description:` line and `<example>` block within the code fence with:

```yaml
description: |
  Use this agent when working on [specific domain]. Covers [capability 1],
  [capability 2], and [capability 3] in this project.
```

No prose text outside the code fence needs changing here — the surrounding text says "Every generated agent must follow this structure" which is still correct.

- [ ] **Step 3: Fix SKILL.md — "Required fields" text**

Find line 79 that says: `**Required fields:** \`name\`, \`description\` (with \`<example>\` blocks), \`model\`, \`color\``

Change to: `**Required fields:** \`name\`, \`description\` (using \`|\` literal block scalar with keyword-rich prose), \`model\`, \`color\``

- [ ] **Step 4: Fix SKILL.md — "Include Project-Specific Knowledge" section**

Find the code block under this heading and replace the `<example>` block in the description with keyword-rich prose format.

- [ ] **Step 5: Fix SKILL.md — "Example Descriptions by Agent Type" section**

Two changes:

1. The heading prose reads: `The \`description:\` field controls when Claude triggers an agent. It must include \`<example>\` blocks.`
   Change to: `The \`description:\` field controls when Claude triggers an agent. It must use \`|\` literal block scalar with keyword-rich prose.`

2. Update all three description code blocks under:
   - "Tech-Stack Expert Description"
   - "Architecture Expert Description"
   - "Domain Expert Description"

   Each should show the new `description: |` format with keyword-rich prose instead of `<example>` blocks.

- [ ] **Step 6: Fix team-architect.md body — "Phase 4" template example**

Find the code block under "### Phase 4: Agent Generation" in the body. Replace the description format from `<example>` to `description: |`.

- [ ] **Step 7: Fix team-architect.md body — "Critical format rules"**

Find rule #2 that says: `**Description** (\`description:\`): Must start with "Use this agent when..." and include 2-3 \`<example>\` blocks`

Change to: `**Description** (\`description:\`): Must use \`description: |\` literal block scalar. Start with "Use this agent when..." followed by keyword-rich prose listing trigger phrases and capabilities. No XML tags.`

- [ ] **Step 8: Fix team-architect.md body — "Agent Quality Standards"**

Find rule #2 that says: `**Have proper \`<example>\` blocks**`

Change to: `**Have keyword-rich description** - Use \`description: |\` with trigger phrases and capability keywords that help Claude match the agent to user requests`

- [ ] **Step 9: Verify no `<example>` remains in description fields**

```bash
grep -n '<example>' agent-team-creator/skills/agent-generation/SKILL.md
grep -n '<example>' agent-team-creator/agents/team-architect.md
```

Expected: Zero matches in SKILL.md. Zero matches in team-architect.md (both frontmatter and body should be clean).

- [ ] **Step 10: Commit**

```bash
git add agent-team-creator/skills/agent-generation/SKILL.md agent-team-creator/agents/team-architect.md
git commit -m "fix(skill-docs): update SKILL.md and team-architect instructions to teach description: | format

Replace all 7 locations in SKILL.md and 3 sections in team-architect.md
body that taught the <example> block format. Now teaches description: |
with keyword-rich prose as the correct format.

Part of #9"
```

---

## Task 5: Fix example files and generate-debugger command

**Files:**
- Modify: `agent-team-creator/skills/agent-generation/examples/tech-stack-expert.md`
- Modify: `agent-team-creator/skills/agent-generation/examples/architecture-expert.md`
- Modify: `agent-team-creator/skills/agent-generation/examples/domain-expert.md`
- Modify: `agent-team-creator/commands/generate-debugger.md`
- Modify: `docs/jira-integration-roadmap.md`

- [ ] **Step 1: Fix tech-stack-expert.md example description**

Inside the markdown code fence, replace the `description:` field (which has 3 `<example>` blocks) with:

```yaml
description: |
  Use this agent when the user asks about React patterns in this project,
  Next.js features, component architecture, hooks usage, state management,
  Tailwind styling, or React Query patterns. Covers frontend implementation
  following project conventions.
```

- [ ] **Step 2: Fix architecture-expert.md example description**

Replace with:

```yaml
description: |
  Use this agent when the user asks about code placement, project
  organization, module boundaries, import conventions, file organization,
  directory layout, or needs guidance on architectural decisions.
```

- [ ] **Step 3: Fix domain-expert.md example description**

Replace with:

```yaml
description: |
  Use this agent when the user asks about user management, orders and
  checkout, data models, business logic, API endpoints, authentication
  flow, subscription handling, or entity relationships.
```

- [ ] **Step 4: Fix generate-debugger.md — Phase 3 template**

Find the code block under "### Phase 3: Generate the Debugger Agent" and change the description line from `description: [Project-specific description with trigger examples]` to:

```yaml
description: |
  [Project-specific description using keyword-rich prose.
  List trigger phrases and capabilities covered by this agent.]
```

- [ ] **Step 5: Fix generate-debugger.md — Example Output Structure**

Find the code block under "## Example Output Structure" and change the description from `description: Use this agent when debugging issues in this Next.js/Express/PostgreSQL application...` to:

```yaml
description: |
  Use this agent when debugging issues in this Next.js/Express/PostgreSQL
  application. Coordinates specialist agents to diagnose bugs, errors, and
  unexpected behavior across the full stack.
```

- [ ] **Step 6: Fix docs/jira-integration-roadmap.md agent code block**

Find the code block around line 640-655 and replace the `description:` field (which has an `<example>` block) with:

```yaml
description: |
  Use this agent when you need to design an implementation plan from a
  debugging report or problem description. Analyzes root causes, selects
  appropriate solution tiers, and creates step-by-step implementation guidance.
  Does not require MCP access.
```

- [ ] **Step 7: Verify changes applied**

```bash
grep -n '<example>' agent-team-creator/skills/agent-generation/examples/*.md
grep -n '<example>' docs/jira-integration-roadmap.md
grep -c 'description: |' agent-team-creator/commands/generate-debugger.md
```

Expected: No matches for the first two greps. The third should show `2` (confirming both template locations now use `description: |`).

- [ ] **Step 8: Commit**

```bash
git add agent-team-creator/skills/agent-generation/examples/*.md agent-team-creator/commands/generate-debugger.md docs/jira-integration-roadmap.md
git commit -m "fix(examples): convert remaining example and command descriptions to literal block scalar

Update 3 skill example files, generate-debugger command template, and
jira-integration-roadmap.md to use description: | format.

Part of #9"
```

---

## Task 6: Final verification sweep

**Files:** None (verification only)

- [ ] **Step 1: Full codebase grep for stray `<example>` tags**

```bash
grep -rn '<example>' agent-team-creator/ docs/ --include='*.md' | grep -v 'specs/' | grep -v 'plans/' | grep -v 'issue-report'
```

Expected: No matches. This catches any stray `<example>` tags in source files while excluding spec/plan documents that legitimately reference them in explanatory text.

- [ ] **Step 2: Verify all YAML frontmatter is valid**

```bash
for f in agent-team-creator/agents/*.md docs/app/.claude/agents/*.md; do
  echo "=== $f ===" && head -8 "$f" && echo ""
done
```

Expected: Every file shows `---`, `name:`, `description: |`, indented prose, then remaining fields.

- [ ] **Step 3: Check git log for all commits**

```bash
git log --oneline fix/issue-9-yaml-parsing ^main
```

Expected: Spec commit + 5 implementation commits.

- [ ] **Step 4: Commit verification complete (no commit needed)**

All changes are committed. Branch is ready for PR.
