# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Release automation script (`scripts/bump-version.sh`)
- Release guide documentation (`RELEASING.md`)

## [1.1.0] - 2026-02-24

### Added
- REST API fallback tier for Jira integration (MCP -> REST -> OFFLINE cascade)
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

[Unreleased]: https://github.com/Cpicon/claude-code-plugins/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/Cpicon/claude-code-plugins/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Cpicon/claude-code-plugins/releases/tag/v1.0.0
