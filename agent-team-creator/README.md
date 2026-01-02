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

Navigate to any project directory and run:

```
/agent-team-creator:generate-agent-team
```

Or if namespace is unavailable:
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

## Generated Agent Types

Depending on your project, you may get agents like:

- **React Expert** - Understands your component patterns, hooks usage, state management
- **API Specialist** - Knows your endpoints, data flow, authentication patterns
- **Database Expert** - Understands your schema, queries, ORM patterns
- **Testing Specialist** - Knows your test patterns, fixtures, mocking strategies
- **DevOps Expert** - Understands deployment, CI/CD, infrastructure

## Components

- **Command**: `/agent-team-creator:generate-agent-team` - Main entry point
- **Agent**: `team-architect` - Orchestrates the analysis and generation process
- **Skill**: `agent-generation` - Best practices for creating effective agents

## License

MIT
