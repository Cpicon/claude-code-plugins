---
name: Jira REST API
description: Knowledge for invoking the Jira REST API via jira_client.py.
  Used by commands (generate-jira-task, update-generated-report) as a fallback
  when the Atlassian MCP plugin is unavailable. Contains credential configuration,
  script invocation syntax, action reference, error handling, and security guidance.
version: 1.2.0
---

# Jira REST API Client

This skill documents the REST API fallback tier for the Jira integration. When the
Atlassian MCP plugin is unavailable, commands use the `jira_client.py` script to
interact with Jira directly via REST API v2 — except for issue search, which uses
the v3 `/search/jql` endpoint after Atlassian removed the v2/v3 `/search` routes
(HTTP 410, see [CHANGE-2046](https://developer.atlassian.com/changelog/#CHANGE-2046)).

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
  [--payload-file .claude/tmp/jira-payload.json] \
  [--file-path /abs/path/to/file] \
  [--no-cascade]
```

Credentials are ALWAYS read from the config file. Never pass tokens as CLI arguments.

## Action Reference

| Action | Required Flags | Optional Flags | Returns |
|--------|---------------|----------------|---------|
| `verify-auth` | `--config` | — | `{ok, email, displayName, accountId}` |
| `get-current-user` | `--config` | — | `{ok, email, displayName, accountId}` (clearer-named alias for `verify-auth`) |
| `get-projects` | `--config` | `--query` | `{ok, projects: [{key,name,id}]}` |
| `search-issues` | `--config --payload-file` | — | `{ok, issues: [{key,summary,status,created}], total, nextPageToken?}` |
| `get-issue-types` | `--config --project` | — | `{ok, issueTypes: [{name,id,subtask}]}` |
| `create-issue` | `--config --payload-file` | — | `{ok, key, url}` |
| `update-issue` | `--config --issue-key --payload-file` | — | `{ok, key, url, updated: [field-names]}` |
| `delete-issue` | `--config --issue-key` | `--no-cascade` | `{ok, key, deleted, cascade}` |
| `attach-file` | `--config --issue-key --file-path` | — | `{ok, key, attachmentId, filename, size}` |
| `get-issue` | `--config --issue-key` | — | `{ok, key, summary, description, status, comments}` |
| `add-comment` | `--config --issue-key --payload-file` | — | `{ok, commentId}` |
| `get-accessible-resources` | `--config` | — | `{ok, baseUrl}` (alias for `verify-auth`) |

### Notes on `search-issues`

- Endpoint: `POST /rest/api/3/search/jql` (the v2/v3 `/search` routes were removed by Atlassian).
- `total` is an **approximate** count fetched from `/rest/api/3/search/approximate-count`
  in a separate non-fatal call. If that secondary call fails, `total` falls back to
  `len(issues)` so the search still returns useful data.
- Pagination is **token-based**, not offset-based. When more results exist beyond
  `maxResults`, the response includes `nextPageToken`; pass it back in the next
  payload's `nextPageToken` field to fetch the next page. There is no `startAt`.
- Default `maxResults` is `5`; payload may override (Jira caps at 100).

### Payload pattern: `create-issue`

```json
{
  "project_key": "GCI",
  "issue_type": "Task",
  "summary": "Short title",
  "description": "Markdown body. Converted to wiki markup automatically.",
  "labels": ["claude-code", "automation"],
  "priority": "Medium",
  "assignee_account_id": "712020:abc-...",
  "parent_key": "GCI-40"
}
```

- `project_key`, `issue_type`, `summary` are required; everything else is optional.
- `priority` accepts the **name** as it appears in Jira (e.g. `Highest`, `High`, `Medium`,
  `Low`, `Lowest`, or custom names like `P0`–`P3` if defined).
- `assignee_account_id` must be an Atlassian accountId (get yours via `get-current-user`).
- `parent_key` makes the new issue a child. Pair with `issue_type: "Subtask"` when the
  project's subtask type is named `Subtask` (call `get-issue-types --project KEY` to
  confirm the exact name).

### Payload pattern: `update-issue`

```json
{
  "summary": "New title (optional)",
  "description": "New markdown body (optional)",
  "labels": ["replaces", "existing", "labels"],
  "priority": "Low",
  "assignee_account_id": "712020:abc-...",
  "fields": { "duedate": "2026-12-31" }
}
```

- All top-level keys are optional but at least one must be set.
- `labels` **replaces** the existing label list (Jira's PUT semantics).
- Set `assignee_account_id` to `null` to unassign.
- `fields` is a raw escape hatch: any key/value here is merged into the Jira `fields`
  object verbatim. Use for fields the script doesn't model (e.g., `duedate`, `customfield_10001`).

### Invocation pattern: `attach-file`

```bash
python3 {SCRIPT_PATH} \
  --action attach-file \
  --config .claude/jira-rest-config.json \
  --issue-key GCI-40 \
  --file-path /abs/path/to/report.md
```

- No payload file. The file is uploaded as `multipart/form-data`.
- Endpoint sends header `X-Atlassian-Token: no-check` (required by Atlassian for attachments).
- Markdown attachments display inline in the Jira UI; logs/screenshots/PDFs are linked.
- Multiple files require multiple invocations.

### Invocation pattern: `delete-issue`

```bash
python3 {SCRIPT_PATH} \
  --action delete-issue \
  --config .claude/jira-rest-config.json \
  --issue-key GCI-40 \
  [--no-cascade]
```

- Default cascades subtask deletion (`?deleteSubtasks=true`).
- `--no-cascade` makes Jira refuse to delete an issue that has subtasks.
- This is irreversible — commands should confirm with the user first.

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
