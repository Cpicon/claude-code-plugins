---
name: generate-agent-team
description: Analyze the current project and generate a team of specialized Claude Code agents that are experts on this codebase
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
argument-hint: "[options]"
---

# Agent Team Creator

Generate a team of specialized Claude Code agents tailored to the current project.

## Execution Instructions

Use the **team-architect** agent to orchestrate this workflow. The agent will:

1. **Analyze the Project**
   - Identify tech stack from package files (package.json, requirements.txt, etc.)
   - Map directory structure and architecture patterns
   - Detect coding conventions and standards
   - Find data models and business logic

2. **Determine Team Composition**
   - Based on project complexity, decide which agents to create
   - Ensure agents have complementary, non-overlapping roles
   - Scale team size to project needs

3. **Generate Agents**
   - Create agent markdown files with project-specific knowledge
   - Include real file paths, actual patterns, and concrete examples
   - Save to `.claude/agents/` in the project directory

4. **Report Results**
   - List all generated agents
   - Summarize each agent's expertise and trigger conditions

## Usage

```
/agent-team-creator:generate-agent-team
```

Or if namespace is unavailable:
```
/generate-agent-team
```

## What Gets Created

Depending on your project, you may get agents like:

| Agent Type | Expertise |
|------------|-----------|
| Tech-Stack Expert | Framework patterns, library usage |
| Architecture Expert | Project structure, conventions |
| Domain Expert | Business logic, data models |
| Testing Specialist | Test patterns, coverage |
| DevOps Expert | CI/CD, deployment |

## Output Location

All agents are saved to:
```
.claude/agents/
```

This directory is created if it doesn't exist.

## Tips

- Run this command from the project root directory
- Generated agents become immediately available in Claude Code
- Re-run after major project changes to update agent knowledge
- Review generated agents and customize if needed

## Invoke the Team Architect

Now invoke the **team-architect** agent to begin the analysis and generation process. Pass along any user-specified options or preferences.
