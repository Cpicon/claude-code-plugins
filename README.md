# Claude Code Plugins

A collection of Claude Code plugins for software development lifecycle improvement.

> **Quality Marketplace** - Curated plugins that enhance Claude Code with specialized capabilities for code analysis, debugging, project management, and development workflow automation.

---

## Vision

```mermaid
flowchart LR
    subgraph "Development Lifecycle"
        A["Analyze"] --> B["Debug"]
        B --> C["Plan"]
        C --> D["Track"]
        D --> E["Review"]
        E --> A
    end

    subgraph "Plugin Support"
        P1["agent-team-creator"]
        P2["Future Plugins"]
    end

    P1 -.-> A
    P1 -.-> B
    P1 -.-> C
    P1 -.-> D
    P2 -.-> E
```

This marketplace provides plugins that augment Claude Code throughout the software development lifecycle:

| Phase | Current Support | Future Plugins |
|-------|-----------------|----------------|
| **Analyze** | `/generate-agent-team` - Create domain experts | Code metrics, dependency analysis |
| **Debug** | `/generate-debugger` - Orchestrated investigation | Performance profiling, log analysis |
| **Plan** | Implementation planning agents | Sprint planning, estimation |
| **Track** | `/generate-jira-task` - Issue creation | Multi-tracker support, status sync |
| **Review** | Debugging reports with solutions | PR review, code quality gates |

---

## Available Plugins

### agent-team-creator

Automatically analyze your codebase and generate a team of specialized Claude Code agents that are experts on your specific project.

```mermaid
flowchart TD
    subgraph "Agent Team Creator"
        CMD1["/generate-agent-team"]
        CMD2["/generate-debugger"]
        CMD3["/generate-jira-task"]
    end

    subgraph "Generated Artifacts"
        A1["Specialist Agents"]
        A2["Debugger Orchestrator"]
        A3["Jira Tasks"]
    end

    subgraph "Project Assets"
        P1[".claude/agents/"]
        P2[".claude/reports/"]
    end

    CMD1 --> A1 --> P1
    CMD2 --> A2 --> P1
    A2 -.-> P2
    CMD3 --> A3
    P2 -.-> CMD3
```

**Features:**
- Deep codebase analysis (tech stack, architecture, patterns)
- Dynamic team generation based on project complexity
- Project-specific debugging with orchestration patterns
- Jira integration for issue tracking
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
- **Saves reports** to `.claude/reports/debugging/` for downstream processing

#### `/generate-jira-task`
Transform debugging reports into well-structured Jira tasks:
- Reads debugging reports from `.claude/reports/debugging/`
- Invokes `implementation-planner` agent for fix design
- Invokes `jira-writer` agent for Jira formatting
- Creates issues via Atlassian MCP (or markdown fallback)
- Includes: summary, description, acceptance criteria, labels

```mermaid
flowchart LR
    A["Debug Issue"] --> B["Debugging Report"]
    B --> C["/generate-jira-task"]
    C --> D{"MCP Available?"}
    D -->|Yes| E["Jira Issue Created"]
    D -->|No| F["Markdown Draft"]
```

**Core Debugger Rules:**
- Coordinates, doesn't implement - delegates to specialists
- Evidence-based - requires file:line references
- Synthesizes findings across agents
- Considers system-wide impact

[View plugin details](./agent-team-creator/README.md)

---

## Plugin Roadmap

Planned plugins to extend the Quality Marketplace:

| Plugin | Purpose | Status |
|--------|---------|--------|
| `agent-team-creator` | Codebase analysis, agent generation, debugging, Jira | **Available** |
| `pr-review-toolkit` | Code review automation, PR analysis | Planned |
| `test-coverage-analyzer` | Test gap detection, coverage reports | Planned |
| `dependency-auditor` | Security scanning, update recommendations | Planned |
| `performance-profiler` | Bottleneck detection, optimization suggestions | Planned |
| `documentation-generator` | API docs, architecture diagrams | Planned |

---

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

# Create Jira task from debugging report
/generate-jira-task
```

---

## Workflow Example

```mermaid
sequenceDiagram
    participant U as User
    participant C as Claude Code
    participant A as Agents
    participant J as Jira

    rect rgb(240, 248, 255)
        Note over U,A: Setup Phase
        U->>C: /generate-agent-team
        C->>A: Create specialists
        U->>C: /generate-debugger
        C->>A: Create orchestrator
    end

    rect rgb(255, 248, 240)
        Note over U,J: Debug & Track Phase
        U->>C: "Debug the login issue"
        C->>A: Orchestrate investigation
        A-->>C: Debugging report saved
        U->>C: /generate-jira-task
        C->>J: Create issue (or markdown)
    end
```

---

## Updating

To get the latest version of plugins:

```bash
/plugin marketplace update
```

---

## Documentation

- [Plugin Development Guide](./docs/PLUGIN-DEVELOPMENT-GUIDE.md) - Templates and patterns for creating plugins
- [Testing Guide](./docs/TESTING-GUIDE.md) - How to test plugin workflows
- [Plugin Development Lessons](./docs/plugin-development-lessons.md) - Issues encountered and lessons learned

---

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Adding a New Plugin

1. Review the [Plugin Development Guide](./docs/PLUGIN-DEVELOPMENT-GUIDE.md)
2. Create your plugin directory with `plugin.json`
3. Add commands, agents, and skills as needed
4. Test using the workflow in [Testing Guide](./docs/TESTING-GUIDE.md)
5. Submit a PR

---

## License

MIT License - see [LICENSE](./LICENSE) for details.

---

## Author

**Christian Picon Calderon**
- GitHub: [@Cpicon](https://github.com/Cpicon)
- Email: c.picon@uniandes.edu.co
