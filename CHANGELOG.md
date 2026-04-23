# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.1] - 2026-04-20

### Fixed
- `/generate-debugger`: orchestrator was reading code directly instead of dispatching specialists (Issue #10). Replaced with a mandatory 4-step procedural workflow that requires `Agent` dispatch before synthesis.
- `/generate-debugger`: Phase 5 verification now actively reads back and Greps the generated file for all required sections, dispatch gate, and `Agent(...)` allowlist. Previously a passive checklist that did not prevent missing sections.
- `/generate-debugger`: section name mismatch — verification table now references the canonical `Impact Assessment & Solutions`.
- `/generate-debugger`: Save Policy uses idempotent `mkdir -p` for directory creation and explicitly handles the case where a referenced Jira key has no prior report (asks instead of silently falling back).
- `team-architect`: removed obsolete `Task` tool reference (renamed to `Agent` in Claude Code v2.1.63) and clarified that specialist agents do not need `Task`/`Agent` in their tool list.

### Added
- `/generate-debugger`: **HARD RULE** enforcing the generated agent's `name:` is exactly `project-debugger` and path is `.claude/agents/project-debugger.md`. Enables a single shell alias (`claudebug='claude --agent project-debugger'`) to work across every project.
- `/generate-debugger`: observable `### Specialists Dispatched` table requirement in synthesis — proves the dispatch step actually occurred.
- `/generate-debugger`: Phase 1 handling for malformed agent files (missing frontmatter, name/filename mismatch) — stops cleanly instead of generating a partial registry.
- `/generate-debugger`: Placeholder Conventions subsection distinguishing `{curly-braces}` (verbatim substitution) from `[square brackets]` (descriptive substitution).
- README guidance: explicit warning that `project-debugger` MUST be invoked as the main thread (`claude --agent project-debugger`), not via `@mention` or Agent-tool dispatch — documents why subagent invocation silently breaks the `Agent(...)` allowlist (subagents cannot spawn other subagents).
- `.docignore` and `docs/superpowers/` `.gitignore` entry — local planning artifacts stay out of the published marketplace.

### Changed
- Filename format documentation in `/generate-debugger` clarifies new investigations use `{YYYY-MM-DD-HHmm}` while continuing investigations use the compact `{YYYYMMDD-HHmm}` to keep key-prefixed names manageable.

## [1.1.0] - 2026-02-24

### Added
- REST API fallback tier for Jira integration (MCP -> REST -> OFFLINE cascade)
- Release automation script (`scripts/bump-version.sh`)
- Release guide documentation (`RELEASING.md`)
- Python REST client (`agent-team-creator/scripts/jira_client.py`) with 8 actions, zero external dependencies
- Jira REST API knowledge skill (`agent-team-creator/skills/jira-rest-api/`)
- Wiki markup reference guide for REST API v2 format
- REST fallback testing section in TESTING-GUIDE.md

### Changed
- `/generate-jira-task` Phase 0: three-tier cascade replaces binary FALLBACK_MODE
- `/generate-jira-task` Phase 6: six-branch state matrix (UPDATE_MODE x JIRA_MODE)
- `/update-generated-report` Phase 0: three-tier cascade replaces binary JIRA_AVAILABLE
- `/update-generated-report` Phase 1: REST branch for issue data fetching
- State variable unified to JIRA_MODE across both Jira commands
- `.gitignore`: credential file and temp directory protection added

## [1.0.0] - 2026-01-02

### Added

#### Commands
- `/generate-agent-team` - Analyze codebase and generate specialized agent team
- `/generate-debugger` - Create project-specific orchestrator debugger agent
- `/generate-jira-task` - Generate Jira tasks from debugging reports

#### Agents
- `team-architect` - Orchestrates four-phase codebase analysis and agent generation
- `context-summarizer` - Summarizes Jira task context and dependencies (planned)
- `implementation-planner` - Creates implementation plans from debugging reports (planned)
- `jira-writer` - Formats content for Jira ticket creation (planned)

#### Skills
- `agent-generation` - Templates and best practices for creating project-aware agents

#### Documentation
- Plugin development guide with reusable templates
- Testing guide with validation workflows
- Plugin development lessons and technical findings

### Technical Details
- Hybrid architecture pattern for MCP tool access limitations
- Multi-phase command execution with agent orchestration
- Graceful fallback modes when external services unavailable

[Unreleased]: https://github.com/Cpicon/claude-code-plugins/compare/v1.1.1...HEAD
[1.1.1]: https://github.com/Cpicon/claude-code-plugins/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/Cpicon/claude-code-plugins/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Cpicon/claude-code-plugins/releases/tag/v1.0.0
