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

Each agent needs specific, non-overlapping trigger phrases in the `description:` field, using `<example>` blocks:

```yaml
description: Use this agent when the user asks about "React component patterns",
  "hook usage in this project", "state management with Redux", or needs help
  understanding how the frontend architecture works. Examples:

<example>
Context: User wants to create a React component
user: "How do I create a new component in this project?"
assistant: "I'll use the project-react-expert agent to guide you through the component patterns."
<commentary>
Framework-specific implementation questions trigger the tech-stack expert.
</commentary>
</example>
```

## Agent Structure Template

Every generated agent **must** follow this structure. The system prompt goes in the **markdown body after the closing `---`**, not inside the frontmatter:

```markdown
---
name: project-role-expert
description: Use this agent when... [specific triggers with project context]. Examples:

<example>
Context: [Scenario description]
user: "[User request]"
assistant: "[How assistant responds and uses this agent]"
<commentary>
[Why this agent should be triggered]
</commentary>
</example>

model: inherit
color: blue
tools: ["Glob", "Grep", "Read", "Edit", "Write", "Bash", "LS", "Task", "WebFetch", "WebSearch"]
---

[Comprehensive system prompt with project knowledge goes here as markdown body]
```

**Required fields:** `name`, `description` (with `<example>` blocks), `model`, `color`
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
description: Use this agent when... Examples:

<example>
...
</example>

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

The `description:` field controls when Claude triggers an agent. It must include `<example>` blocks.

### Tech-Stack Expert Description

```yaml
description: Use this agent when the user asks about "React patterns in this project",
  "how hooks are used here", "component architecture", "state management approach",
  "Next.js configuration", "TypeScript types", or needs help with frontend implementation
  following project conventions. Examples:

<example>
Context: User wants to create a React component following project patterns
user: "How do I create a new component in this project?"
assistant: "I'll use the acme-react-expert agent to show you the component patterns."
<commentary>
Framework-specific implementation questions trigger the tech-stack expert.
</commentary>
</example>

<example>
Context: User needs help with state management
user: "How does state management work in this app?"
assistant: "Let me use the acme-react-expert agent to explain the state management approach."
<commentary>
State management is a tech-stack concern handled by this agent.
</commentary>
</example>
```

### Architecture Expert Description

```yaml
description: Use this agent when the user asks "where should I put this code",
  "how is the project organized", "what's the module structure", "how do imports work",
  "project conventions", "directory layout", or needs guidance on code organization
  and architectural decisions. Examples:

<example>
Context: User is creating a new feature and needs placement guidance
user: "Where should I put this new feature?"
assistant: "I'll use the acme-architecture-expert agent to guide you on the correct location."
<commentary>
Code placement decisions require the architecture expert.
</commentary>
</example>

<example>
Context: User wants to understand project organization
user: "How is the project organized?"
assistant: "Let me use the acme-architecture-expert agent to explain the project structure."
<commentary>
Project structure questions are the architecture expert's domain.
</commentary>
</example>
```

### Domain Expert Description

```yaml
description: Use this agent when the user asks about "user authentication flow",
  "how orders are processed", "data model relationships", "API endpoint structure",
  "business rules for [feature]", or needs understanding of domain-specific logic
  and data flows. Examples:

<example>
Context: User wants to understand a business process
user: "How does the order fulfillment process work?"
assistant: "I'll use the acme-domain-expert agent to explain the business flow."
<commentary>
Business process questions require domain expertise.
</commentary>
</example>

<example>
Context: User needs to understand data model relationships
user: "What's the relationship between users and subscriptions?"
assistant: "Let me use the acme-domain-expert agent to explain the entity relationships."
<commentary>
Entity relationship questions are core domain expertise.
</commentary>
</example>
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
