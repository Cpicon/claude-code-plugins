# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-05-08

### Added
- `jira_client.py`: `update-issue` action — patch summary, description, labels, priority, assignee, or any raw field on an existing issue via `PUT /rest/api/2/issue/{key}`. Includes a `fields` escape hatch for custom fields the script doesn't model directly.
- `jira_client.py`: `attach-file` action — upload any local file (markdown, logs, screenshots) as a Jira attachment via multipart `POST /rest/api/2/issue/{key}/attachments`. Sends `X-Atlassian-Token: no-check` as required by Atlassian.
- `jira_client.py`: `delete-issue` action — `DELETE /rest/api/2/issue/{key}`. Cascades to subtasks by default; `--no-cascade` flag refuses deletion when subtasks exist.
- `jira_client.py`: `get-current-user` action — clearer-named alias for `verify-auth`. Returns `{accountId, email, displayName}` for the authenticated user. Useful for self-assignment without the user having to know their accountId.
- `jira_client.py`: new CLI flags `--file-path` (for `attach-file`) and `--no-cascade` (for `delete-issue`).
- `jira-rest-api` skill: documented the 5 new actions with payload patterns and invocation examples. Skill version bumped to `1.2.0`.
- `/generate-jira-task` Phase 5 step 7: derives priority from impact assessment, resolves the current user's accountId, and prompts the user (single batched `AskUserQuestion`) for priority and assignee selection. Defaults are Recommended in both questions.
- `/generate-jira-task` Phase 6 (REST mode): now attaches the source debugging report `.md` to the new Jira issue after creation, so the original artifact lives on the ticket alongside the formatted summary. Non-fatal — attachment failure does not abort issue creation.

### Changed
- `jira_client.py`: `create-issue` payload accepts three new optional fields: `priority` (string name, e.g. "High"), `assignee_account_id` (Atlassian accountId), and `parent_key` (parent issue key for subtasks). Existing callers that don't pass these fields see identical behavior.
- `/generate-jira-task` Phase 6 (REST and MCP create paths): tickets are now created with priority + assignee in a single API call instead of being created with defaults and immediately patched.
- `/generate-jira-task` Phase 6 (OFFLINE draft): markdown draft now includes priority and an explicit instruction to attach the source debug report when manually creating the ticket.
- `/generate-jira-task` Phase 6 (MCP create): `additional_fields` now includes `priority.name` and (when not unassigned) `assignee.accountId`. Note: file attachment is not supported by the Atlassian MCP tools today; only REST mode attaches the source report.

### Internal
- `jira_client.py`: `create-issue` body construction refactored to build the `fields` dict incrementally before submission, accommodating the new optional fields without nesting conditionals inside the request body literal.

## [1.1.2] - 2026-05-07

### Fixed
- `jira_client.py`: `search-issues` action migrated from the removed `/rest/api/2/search` endpoint to `POST /rest/api/3/search/jql`. Atlassian returned `HTTP 410: The requested API has been removed` on the old route, which broke duplicate detection during `/generate-jira-task` in REST mode. See [Atlassian CHANGE-2046](https://developer.atlassian.com/changelog/#CHANGE-2046).

### Changed
- `jira_client.py`: `search-issues` response now reports `total` from a separate non-fatal call to `POST /rest/api/3/search/approximate-count` (the new endpoint no longer returns `total`). If the secondary call fails, `total` falls back to `len(issues)` so the search still returns useful data. The response also exposes `nextPageToken` when more results are available, since the new endpoint uses token-based pagination instead of `startAt`.
- `jira-rest-api` skill: documentation updated to reflect the new endpoint, approximate `total` semantics, and `nextPageToken` pagination model. Skill version bumped to `1.1.0`.

### Internal
- `jira_client.py`: extracted `_build_authed_request` helper shared by `make_request` and the new non-fatal `try_request` (used for the optional approximate-count call). No behavior change to existing actions.

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

[Unreleased]: https://github.com/Cpicon/claude-code-plugins/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/Cpicon/claude-code-plugins/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/Cpicon/claude-code-plugins/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/Cpicon/claude-code-plugins/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/Cpicon/claude-code-plugins/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Cpicon/claude-code-plugins/releases/tag/v1.0.0
