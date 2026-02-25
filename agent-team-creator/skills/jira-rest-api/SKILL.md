---
name: Jira REST API
description: Knowledge for invoking the Jira REST API v2 via jira_client.py.
  Used by commands (generate-jira-task, update-generated-report) as a fallback
  when the Atlassian MCP plugin is unavailable. Contains credential configuration,
  script invocation syntax, action reference, error handling, and security guidance.
version: 1.0.0
---

# Jira REST API Client

This skill documents the REST API fallback tier for the Jira integration. When the
Atlassian MCP plugin is unavailable, commands use the `jira_client.py` script to
interact with Jira directly via REST API v2.

## Architecture

```
Phase 0 Cascade:
  1. Try MCP → JIRA_MODE = "MCP"
  2. Try REST → JIRA_MODE = "REST"
  3. Fallback → JIRA_MODE = "OFFLINE"
```

Agents are completely insulated — they produce identical output regardless of JIRA_MODE.
Only commands and this script interact with the transport layer.

## Script Location

Locate the script before invoking:

```
1. Glob: **/agent-team-creator/scripts/jira_client.py
2. Fallback: ~/.claude/plugins/agent-team-creator/scripts/jira_client.py
3. Not found → REST mode unavailable, fall to OFFLINE
```

## Invocation Syntax

```bash
python3 {SCRIPT_PATH} \
  --action {action-name} \
  --config .claude/jira-rest-config.json \
  [--issue-key PROJ-123] \
  [--project PROJ] \
  [--query "search term"] \
  [--payload-file .claude/tmp/jira-payload.json]
```

Credentials are ALWAYS read from the config file. Never pass tokens as CLI arguments.

## Action Reference

| Action | Required Flags | Optional Flags | Returns |
|--------|---------------|----------------|---------|
| `verify-auth` | `--config` | — | `{ok, email, displayName}` |
| `get-projects` | `--config` | `--query` | `{ok, projects: [{key,name,id}]}` |
| `search-issues` | `--config --payload-file` | — | `{ok, issues: [{key,summary,status}], total}` |
| `get-issue-types` | `--config --project` | — | `{ok, issueTypes: [{name,id}]}` |
| `create-issue` | `--config --payload-file` | — | `{ok, key, url}` |
| `get-issue` | `--config --issue-key` | — | `{ok, key, summary, description, status, comments}` |
| `add-comment` | `--config --issue-key --payload-file` | — | `{ok, commentId}` |
| `get-accessible-resources` | `--config` | — | `{ok, baseUrl}` (alias for verify-auth) |

## Exit Codes

| Code | Meaning | Command Recovery |
|------|---------|-----------------|
| 0 | Success | Parse stdout JSON |
| 1 | Auth failure | Fall to OFFLINE, suggest re-running credential setup |
| 2 | Validation error | Fix payload/config, retry |
| 3 | Network error | Fall to OFFLINE |
| 4 | Jira API error | Show error message, fall to OFFLINE |

## Credential Configuration

Config file: `.claude/jira-rest-config.json` (MUST be in .gitignore)

```json
{
  "baseUrl": "https://your-site.atlassian.net",
  "email": "your-email@company.com",
  "apiToken": "your-api-token",
  "configuredAt": "2026-02-24T10:00:00Z"
}
```

Generate API tokens at: https://id.atlassian.com/manage-profile/security/api-tokens

**Security**: API tokens have full account scope. The config file must NEVER be committed.

## MCP-to-REST Parameter Mapping

| MCP Parameter | REST Equivalent | Notes |
|--------------|-----------------|-------|
| `cloudId` | (not needed) | REST uses `baseUrl` from config |
| `issueIdOrKey` | `--issue-key` | Same value |
| `commentBody` | `body` field in payload file | Written as JSON file |
| `jql` | `jql` field in payload file | Written as JSON file |
| `maxResults` | `maxResults` in payload | Part of payload JSON |
| `projectKey` | `--project` or `project_key` in payload | Depends on action |
| `searchString` | `--query` | URL-encoded by script |

## Response Normalization

MCP and REST return different structures. Commands must normalize:

| Data | MCP Path | REST Script Path |
|------|----------|------------------|
| Summary | `fields.summary` | `summary` |
| Description | `fields.description` | `description` |
| Status | `fields.status.name` | `status` |
| Comments | `fields.comment.comments[]` | `comments[]` |
| Comment author | `comments[].author.displayName` | `comments[].author` |
| Comment body | `comments[].body` | `comments[].body` |

## URL Construction

When `JIRA_MODE = REST`, construct issue URLs from the config:

```
{baseUrl}/browse/{issueKey}
```

Do NOT use MCP site resolution for URL construction in REST mode.

## Temp File Pattern

For actions requiring `--payload-file`:

1. Create dir: `.claude/tmp/` (if needed)
2. Write JSON: `.claude/tmp/jira-payload.json`
3. Invoke script
4. Parse stdout
5. Delete temp file (command responsibility)

## Wiki Markup

REST API v2 uses Jira wiki markup (not markdown, not ADF) for `description` and
`comment` body fields. The script converts markdown to wiki markup automatically.
See `references/wiki-markup-guide.md` for the full translation table.

## Rate Limiting

Jira Cloud: ~100 requests/minute per user. The script handles 429 responses automatically
(parses `Retry-After`, sleeps, retries up to 2x). Commands typically make <10 requests
per invocation.
