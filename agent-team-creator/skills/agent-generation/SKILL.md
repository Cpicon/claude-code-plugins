---
name: Agent Generation
description: This skill provides knowledge for generating effective Claude Code agents tailored to specific projects. It is used internally by the agent-team-creator plugin when analyzing codebases and creating specialized agent teams. Contains templates, best practices, and patterns for writing project-aware agents.
version: 1.0.0
---

# Agent Generation for Project-Specific Teams

This skill provides the knowledge and templates needed to generate high-quality Claude Code agents that are experts on a specific codebase.

## Core Principles

### 1. Project-Aware Agents

Generated agents must understand the specific project, not just general concepts:

- Reference actual file paths and directories from the project
- Mention specific frameworks, libraries, and versions used
- Include project-specific conventions and patterns
- Use terminology from the codebase (class names, module names, etc.)

### 2. Complementary Team Design

Each agent should have a distinct role without overlapping:

| Agent Type | Focus Area | Avoids |
|------------|------------|--------|
| Tech-Stack Expert | Frameworks, libraries, tooling | Business logic |
| Architecture Expert | Structure, patterns, conventions | Implementation details |
| Domain Expert | Business logic, data models, APIs | Infrastructure |
| Testing Specialist | Test patterns, fixtures, coverage | Production code |
| DevOps Expert | CI/CD, deployment, infrastructure | Application code |

### 3. Strong Trigger Conditions

Each agent needs specific, non-overlapping trigger phrases in the `description:` field, using `|` literal block scalar with keyword-rich prose:

```yaml
description: |
  Use this agent when the user asks about React component patterns,
  hook usage in this project, state management with Redux, or needs
  help understanding how the frontend architecture works.
```

## Agent Structure Template

Every generated agent **must** follow this structure. The system prompt goes in the **markdown body after the closing `---`**, not inside the frontmatter:

```markdown
---
name: project-role-expert
description: |
  Use this agent when working on [specific domain]. Covers [capability 1],
  [capability 2], and [capability 3] in this project.

model: inherit
color: blue
tools: ["Glob", "Grep", "Read", "Edit", "Write", "Bash", "LS", "Task", "WebFetch", "WebSearch"]
---

[Comprehensive system prompt with project knowledge goes here as markdown body]
```

**Required fields:** `name`, `description` (using `|` literal block scalar with keyword-rich prose), `model`, `color`
**Optional fields:** `tools` (omit for full access)
**Valid colors:** `blue`, `cyan`, `green`, `yellow`, `magenta`, `red`
**Valid models:** `inherit` (recommended), `sonnet`, `opus`, `haiku`

## Analysis-to-Agent Mapping

### Tech Stack Analysis

Analyze these files to identify tech stack:
- `package.json`, `requirements.txt`, `Cargo.toml`, `go.mod`
- Framework config files: `next.config.js`, `vite.config.ts`, `django/settings.py`
- Build configs: `tsconfig.json`, `webpack.config.js`, `babel.config.js`

Generate agents for each major technology:
- One agent per primary framework (React, FastAPI, Django, etc.)
- Combined agents for related libraries (testing libraries together)

### Architecture Analysis

Analyze these patterns:
- Directory structure depth and organization
- Module/package boundaries
- Import patterns and dependencies
- Design patterns in use (MVC, Clean Architecture, etc.)

Generate architecture agent covering:
- Project structure and navigation
- Code organization conventions
- Module relationships
- Naming conventions

### Domain Analysis

Analyze these elements:
- Data models and schemas
- API endpoints and routes
- Business logic modules
- Database migrations and queries

Generate domain agents for:
- Data model understanding
- API structure and contracts
- Business rule implementation

## Color Palette for Agent Types

Use consistent named colors by agent type (only these values are valid):

| Agent Type | Named Color |
|------------|-------------|
| Tech-Stack | `blue` |
| Architecture | `magenta` |
| Domain/Business | `green` |
| Testing | `yellow` |
| DevOps/Infra | `red` |
| Security | `magenta` |
| Performance | `cyan` |

## Writing Effective System Prompts

### Structure

1. **Role Definition** (1-2 sentences)
   ```
   You are an expert on the [Project Name] codebase, specializing in [domain].
   ```

2. **Project Context** (3-5 sentences)
   ```
   This project uses [tech stack]. The codebase is organized with [structure].
   Key directories include [paths]. The project follows [patterns/conventions].
   ```

3. **Expertise Areas** (bullet list)
   ```
   Your expertise includes:
   - Specific area 1 with project context
   - Specific area 2 with file references
   - Specific area 3 with convention details
   ```

4. **Guidance Principles** (3-5 bullets)
   ```
   When helping:
   - Always reference existing patterns in [path]
   - Follow the [convention] established in [file]
   - Ensure consistency with [standard]
   ```

### Include Project-Specific Knowledge

Always embed actual project details in the **markdown body** (after the closing `---`), not inside the frontmatter:

```markdown
---
name: acme-dashboard-react-expert
description: |
  Use this agent when the user asks about React patterns in this project,
  Next.js features, component architecture, or hooks usage. Covers
  frontend implementation following project conventions.

model: inherit
color: blue
---

You are an expert on the **Acme Dashboard** React application.

## Project Overview
This is a Next.js 14 application using the App Router. The codebase uses:
- TypeScript with strict mode
- Tailwind CSS for styling
- React Query for server state
- Zustand for client state

## Key Directories
- `src/app/` - Next.js app router pages
- `src/components/` - Reusable UI components
- `src/hooks/` - Custom React hooks
- `src/lib/` - Utility functions and API clients

## Conventions
- Components use PascalCase: `UserProfile.tsx`
- Hooks use camelCase with 'use' prefix: `useAuth.ts`
- API routes follow REST conventions
- All components have co-located test files
```

## Example Descriptions by Agent Type

The `description:` field controls when Claude triggers an agent. It must use `|` literal block scalar with keyword-rich prose.

### Tech-Stack Expert Description

```yaml
description: |
  Use this agent when the user asks about React patterns in this project,
  how hooks are used here, component architecture, state management approach,
  Next.js configuration, or TypeScript types. Covers frontend implementation
  following project conventions.
```

### Architecture Expert Description

```yaml
description: |
  Use this agent when the user asks about code placement, project organization,
  module structure, import conventions, project conventions, or directory layout.
  Provides guidance on code organization and architectural decisions.
```

### Domain Expert Description

```yaml
description: |
  Use this agent when the user asks about user authentication flow, order
  processing, data model relationships, API endpoint structure, or business
  rules. Covers domain-specific logic and data flows.
```

## Dynamic Team Sizing

Determine team size based on project complexity:

| Project Signals | Team Size | Agent Types |
|-----------------|-----------|-------------|
| Single framework, <50 files | 2-3 | Tech + Architecture |
| Multiple frameworks, 50-200 files | 4-5 | Tech (2) + Arch + Domain |
| Monorepo or >200 files | 5-8 | Full coverage per service |
| Microservices | 3-4 per service | Service-specific teams |

## Additional Resources

### Reference Files

For detailed templates and examples:
- **`references/agent-templates.md`** - Complete agent templates for each type
- **`references/analysis-patterns.md`** - Patterns for codebase analysis

### Example Files

Working examples in `examples/`:
- **`tech-stack-expert.md`** - Complete tech-stack agent example
- **`architecture-expert.md`** - Complete architecture agent example
- **`domain-expert.md`** - Complete domain agent example
