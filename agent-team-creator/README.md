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

**Report Storage:**
- Reports are saved to `.claude/reports/debugging/report-{timestamp}.md`
- Use these reports as input to `/generate-jira-task`

### Generate Jira Task from Debugging Report

After a debugging session, create a structured Jira task:

```
/generate-jira-task
```

Or specify a particular report:
```
/generate-jira-task .claude/reports/debugging/report-2026-01-03-1530.md
```

The command will:
1. Load and validate the debugging report
2. Design an implementation plan via `implementation-planner` agent
3. Format Jira content via `jira-writer` agent
4. Check for duplicate issues (if Atlassian MCP available)
5. Create the issue in Jira (or generate markdown draft if unavailable)

**Requirements:**
- Atlassian MCP plugin for direct Jira creation (optional - falls back to markdown)
- Debugging report from `/generate-debugger` workflow

**Output:**
- **Normal mode**: Jira issue key (e.g., PROJ-123) with URL
- **Fallback mode**: Markdown draft in `.claude/reports/jira-drafts/`

**Features:**
- Automatic project key caching (configured once per git project)
- Duplicate detection before creating new issues
- Issue type inference (Bug vs Task) from report content
- Label generation and sanitization for Jira compatibility
- Graceful fallback when Atlassian MCP is unavailable

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
- `/generate-jira-task` - Transform debugging reports into Jira tasks

### Agents
- `team-architect` - Orchestrates the analysis and team generation process
- `implementation-planner` - Designs implementation plans from debugging reports
- `jira-writer` - Formats content for Jira with evidence preservation

### Skills
- `agent-generation` - Best practices for creating effective agents

## License

MIT
