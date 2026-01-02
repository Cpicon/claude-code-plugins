# Agent Team Creator

Automatically analyze your codebase and generate a team of specialized Claude Code agents that are experts on your specific project.

## Features

- **Deep Codebase Analysis**: Scans project structure, tech stack, frameworks, and patterns
- **Dynamic Team Generation**: Creates the right number of agents based on project complexity
- **Project-Specific Expertise**: Generated agents understand YOUR codebase, not just generic knowledge
- **Full Integration**: Agents save directly to `.claude/agents/` for immediate use

## Installation

```bash
claude --plugin-dir ~/.claude/plugins/agent-team-creator
```

Or add to your Claude Code settings.

## Usage

### Generate Agent Team

Navigate to any project directory and run:

```
/generate-agent-team
```

The plugin will:
1. Analyze your project's architecture and tech stack
2. Identify key frameworks, libraries, and patterns
3. Generate specialized agents for:
   - Tech-stack expertise (frameworks + libraries)
   - Architecture knowledge (structure, patterns, conventions)
   - Domain understanding (business logic, data models, APIs)
4. Save agents to your project's `.claude/agents/` directory

### Generate Project Debugger

After generating your agent team, create a project-specific debugger:

```
/generate-debugger
```

The debugger will:
1. Discover all existing project agents in `.claude/agents/`
2. Analyze project architecture and tech stack
3. Generate orchestration patterns tailored to YOUR project
4. Create a `project-debugger.md` that knows how to consult your specialists

**The generated debugger follows these core rules:**
- **Coordinates, doesn't implement** - Delegates investigation to specialists
- **Evidence-based only** - Requires file paths, line numbers, and code references
- **Synthesizes findings** - Connects insights across agents, identifies patterns
- **Considers system-wide impact** - Analyzes how issues ripple through the stack

**Debugging Report Output:**
- Issue summary and affected components
- Investigation trail (which agents were consulted)
- Root cause analysis with evidence chain
- Impact assessment and side effects
- Solutions ordered by effort (quick/proper/comprehensive)

## Generated Agent Types

Depending on your project, you may get agents like:

- **React Expert** - Understands your component patterns, hooks usage, state management
- **API Specialist** - Knows your endpoints, data flow, authentication patterns
- **Database Expert** - Understands your schema, queries, ORM patterns
- **Testing Specialist** - Knows your test patterns, fixtures, mocking strategies
- **DevOps Expert** - Understands deployment, CI/CD, infrastructure

## Components

### Commands
- `/generate-agent-team` - Analyze project and generate specialized agent team
- `/generate-debugger` - Generate project-specific debugger that orchestrates agents

### Agents
- `team-architect` - Orchestrates the analysis and team generation process

### Skills
- `agent-generation` - Best practices for creating effective agents

## License

MIT
