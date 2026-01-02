# Claude Code Plugins

A collection of Claude Code plugins by Christian Picon Calderon.

## Available Plugins

### agent-team-creator

Automatically analyze your codebase and generate a team of specialized Claude Code agents that are experts on your specific project.

**Features:**
- Deep codebase analysis (tech stack, architecture, patterns)
- Dynamic team generation based on project complexity
- Project-specific debugging with orchestration patterns
- Agents saved directly to `.claude/agents/` for immediate use

**Commands:**

#### `/generate-agent-team`
Analyze your project and create specialized agents based on:
- Tech stack (frameworks, libraries, languages)
- Architecture patterns (monolith, microservices, etc.)
- Domain knowledge (business logic, data models)

#### `/generate-debugger`
Generate a project-specific debugger agent that:
- Discovers all existing project agents in `.claude/agents/`
- Creates orchestration patterns tailored to YOUR project architecture
- Coordinates investigation by delegating to specialist agents
- Produces structured reports with:
  - Root cause analysis
  - Investigation trail (which agents were consulted)
  - Side effects and warnings
  - Solutions ordered by effort (quick/proper/comprehensive)

**Core Debugger Rules:**
- Coordinates, doesn't implement - delegates to specialists
- Evidence-based - requires file:line references
- Synthesizes findings across agents
- Considers system-wide impact

[View plugin details](./agent-team-creator/README.md)

## Installation

### 1. Add this marketplace

```bash
/plugin marketplace add Cpicon/claude-code-plugins
```

### 2. Install a plugin

```bash
/plugin install agent-team-creator
```

### 3. Use the plugin

Navigate to any project directory and run:

```bash
# Generate specialized agents for your project
/generate-agent-team

# Generate a project-specific debugger
/generate-debugger
```

## Updating

To get the latest version of plugins:

```bash
/plugin marketplace update
```

## Documentation

- [Plugin Development Lessons](./docs/plugin-development-lessons.md) - Issues encountered and lessons learned while developing Claude Code plugins locally

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - see [LICENSE](./LICENSE) for details.

## Author

**Christian Picon Calderon**
- GitHub: [@Cpicon](https://github.com/Cpicon)
- Email: c.picon@uniandes.edu.co
