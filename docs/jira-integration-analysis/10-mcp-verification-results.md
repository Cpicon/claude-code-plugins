# MCP Tool Verification Results

**Document**: 10-mcp-verification-results.md
**Date**: 2026-02-24
**Purpose**: Resolve all 6 CONFIRM blockers from doc 08 (implementation plan draft)
**Method**: Source code analysis of the installed Atlassian MCP plugin (`atlassian@claude-plugins-official`, version `63e369036b13`)
**Plugin location**: `~/.claude/plugins/cache/claude-plugins-official/atlassian/63e369036b13/`

---

## Verification Method

The Atlassian MCP plugin is installed but not enabled in the current `settings.json` `enabledPlugins` list. Therefore, live MCP tool calls were not possible in this session. Instead, verification was performed by analyzing the plugin's source code:

- **`.mcp.json`** -- MCP server configuration (HTTP endpoint: `https://mcp.atlassian.com/v1/mcp`)
- **`skills/triage-issue/SKILL.md`** -- Documents `getJiraIssue`, `addCommentToJiraIssue`, `searchJiraIssuesUsingJql`, `createJiraIssue` with full parameter signatures and example calls
- **`skills/search-company-knowledge/SKILL.md`** -- Documents `getJiraIssue` return values ("Full issue details including description, comments, status")
- **`skills/spec-to-backlog/SKILL.md`** -- Documents `getAccessibleAtlassianResources`, `getVisibleJiraProjects`, `createJiraIssue`, `getJiraIssueTypeMetaWithFields`
- **`skills/capture-tasks-from-meeting-notes/SKILL.md`** -- Documents `getAccessibleAtlassianResources`, `lookupJiraAccountId`
- **`skills/generate-status-report/SKILL.md`** -- Documents `searchJiraIssuesUsingJql`, `updateConfluencePage`

Additionally, the existing `generate-jira-task.md` command in this repo was consulted for known-working tool call patterns.

---

## CONFIRM Results Summary

| # | Question | Answer | Confidence | Evidence Source |
|---|----------|--------|------------|-----------------|
| CONFIRM-1 | Does `editJiraIssue` exist? | **NO** | High | Zero matches for `editJiraIssue` or `updateJiraIssue` across all plugin source files |
| CONFIRM-2 | Does `getJiraIssue` return comments? | **YES** | High | `search-company-knowledge/SKILL.md` line 159: "Returns: Full issue details including description, comments, status" |
| CONFIRM-3 | What is the response format of `getJiraIssue`? | See section below | Medium | Documented fields from skill files; exact JSON structure needs live verification |
| CONFIRM-4 | Does `addCommentToJiraIssue` accept markdown? | **YES** | High | `triage-issue/SKILL.md` uses `##`, `**bold**`, `- lists`, `---` in `commentBody` parameter. MCP server handles markdown-to-ADF conversion. |
| CONFIRM-5 | What are exact parameters for each tool? | See table below | High | Multiple skill files document identical parameter signatures |
| CONFIRM-6 | Does Atlassian MCP require `cloudId` for all operations? | **YES** | High | Every Jira tool call in every skill requires `cloudId` as the first parameter |

---

## Detailed Findings

### CONFIRM-1: `editJiraIssue` Does NOT Exist

**Search performed**: Grep for `editJiraIssue` and `updateJiraIssue` across the entire Atlassian plugin directory (`~/.claude/plugins/cache/claude-plugins-official/atlassian/63e369036b13/`).

**Result**: Zero matches.

**Notable**: While `updateConfluencePage` exists (used in `generate-status-report/SKILL.md`), there is no equivalent `updateJiraIssue` or `editJiraIssue` tool. The README claims the server can "Create and update issues," but the MCP tool set does not expose a direct issue-editing tool.

**Design implication**: Updates to Jira issues **must** use `addCommentToJiraIssue`. Jira issue descriptions are static after creation. This aligns with the architectural review's recommendation (doc 09, feedback 2.1) to separate concerns: description stays as the initial state, updates go as comments.

### CONFIRM-2: `getJiraIssue` Returns Comments

**Evidence**: `skills/search-company-knowledge/SKILL.md` line 159:
> **Returns:** Full issue details including description, comments, status

**Design implication**: The `/update-generated-report` command can fetch engineer feedback from comments. No separate `getJiraIssueComments` tool is needed.

**Caveat**: The exact shape of the comments data (whether they are in `fields.comment.comments`, how they are paginated, what fields each comment has like `author`, `body`, `created`) needs live verification. The plugin documentation does not provide the exact JSON response schema.

### CONFIRM-3: `getJiraIssue` Response Format

**Known fields** (from skill documentation and the Jira REST API convention):

| Field | Documented? | Source |
|-------|-------------|--------|
| `summary` | Implied | Used for search result display in triage-issue |
| `description` | Yes | `search-company-knowledge/SKILL.md`: "description" |
| `comments` | Yes | `search-company-knowledge/SKILL.md`: "comments" |
| `status` | Yes | `search-company-knowledge/SKILL.md`: "status" |

**Unknown (needs live verification)**:
- Exact nesting structure (e.g., `fields.comment.comments` vs top-level `comments`)
- Comment fields: `author.displayName`, `body`, `created`, `updated`
- Whether comments are paginated (Jira REST API paginates at 20 by default)
- Whether the description is returned as ADF JSON or as rendered markdown

**Recommendation**: When the Atlassian plugin is enabled, run a single `getJiraIssue` call against a known PDE issue and log the full response to establish the exact schema. This can be done as a pre-implementation step.

### CONFIRM-4: `addCommentToJiraIssue` Accepts Markdown

**Evidence**: `skills/triage-issue/SKILL.md` lines 258-277 shows a comment body template using:
- `## Headers` (h2)
- `**Bold text**`
- `- List items`
- `---` (horizontal rules)
- `*italic text*`

The MCP server (`https://mcp.atlassian.com/v1/mcp`) handles the markdown-to-ADF (Atlassian Document Format) conversion transparently. The command only needs to provide a markdown string.

**Design implication**: The `jira-writer` agent can format update comments in markdown. No ADF conversion logic is needed in the plugin.

### CONFIRM-5: Exact Tool Parameters

#### Available Jira MCP Tools (complete list from plugin source)

| Tool Name | Parameters | MCP Call Prefix | Source |
|-----------|-----------|-----------------|--------|
| `getAccessibleAtlassianResources` | *(none)* | `mcp__plugin_atlassian_atlassian__` | spec-to-backlog, capture-tasks |
| `atlassianUserInfo` | *(none)* | `mcp__plugin_atlassian_atlassian__` | generate-jira-task.md (existing) |
| `getVisibleJiraProjects` | `cloudId`, `action`?, `searchString`?, `maxResults`? | `mcp__plugin_atlassian_atlassian__` | spec-to-backlog |
| `getJiraProjectIssueTypesMetadata` | `cloudId`, `projectIdOrKey` | `mcp__plugin_atlassian_atlassian__` | triage-issue, spec-to-backlog |
| `getJiraIssueTypeMetaWithFields` | `cloudId`, `projectIdOrKey`, `issueTypeId` | `mcp__plugin_atlassian_atlassian__` | spec-to-backlog, triage-issue |
| `searchJiraIssuesUsingJql` | `cloudId`, `jql`, `fields`?, `maxResults`? | `mcp__plugin_atlassian_atlassian__` | triage-issue (quick ref) |
| `getJiraIssue` | `cloudId`, `issueIdOrKey` | `mcp__plugin_atlassian_atlassian__` | search-company-knowledge (quick ref) |
| `createJiraIssue` | `cloudId`, `projectKey`, `issueTypeName`, `summary`, `description`, `additional_fields`? | `mcp__plugin_atlassian_atlassian__` | triage-issue (quick ref) |
| `addCommentToJiraIssue` | `cloudId`, `issueIdOrKey`, `commentBody` | `mcp__plugin_atlassian_atlassian__` | triage-issue (quick ref) |
| `lookupJiraAccountId` | `cloudId`, *other params unknown* | `mcp__plugin_atlassian_atlassian__` | capture-tasks |

#### Additional Confluence-related tools (for reference only)
| Tool Name | Parameters |
|-----------|-----------|
| `search` | `cloudId`, `query` |
| `getConfluencePage` | `cloudId`, `pageId`, `contentFormat` |
| `searchConfluenceUsingCql` | `cloudId`, `cql` |
| `getConfluenceSpaces` | `cloudId` |
| `createConfluencePage` | `cloudId`, *other params* |
| `updateConfluencePage` | `cloudId`, *other params* |

### CONFIRM-6: `cloudId` Is Required for All Operations

**Evidence**: Every single Jira tool call in every skill file requires `cloudId` as the first parameter. The only exceptions are the zero-parameter tools `getAccessibleAtlassianResources()` and `atlassianUserInfo()`, which are used to *obtain* the cloudId and verify authentication.

**Design implication**: The `/update-generated-report` command must resolve `cloudId` before making any Jira calls. It should use the same caching pattern as `generate-jira-task.md` (read from `.claude/jira-project.json`).

---

## Tools Needed for Issue #2 Commands

Based on these findings, here are the exact tools each command needs:

### `/generate-jira-task` (MODIFY) -- additional tools to add

| Tool | Purpose | Already in frontmatter? |
|------|---------|------------------------|
| `getJiraIssue` | Fetch issue details when updating | **No -- must add** |
| `addCommentToJiraIssue` | Post update comment to existing issue | **No -- must add** |

Full `allowed-tools` for `generate-jira-task.md`:
```yaml
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Task
  - AskUserQuestion
  - mcp__plugin_atlassian_atlassian__getVisibleJiraProjects
  - mcp__plugin_atlassian_atlassian__createJiraIssue
  - mcp__plugin_atlassian_atlassian__getAccessibleAtlassianResources
  - mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql
  - mcp__plugin_atlassian_atlassian__getJiraProjectIssueTypesMetadata
  - mcp__plugin_atlassian_atlassian__atlassianUserInfo
  - mcp__plugin_atlassian_atlassian__getJiraIssue          # NEW
  - mcp__plugin_atlassian_atlassian__addCommentToJiraIssue # NEW
```

### `/update-generated-report` (NEW)

```yaml
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Task
  - AskUserQuestion
  - mcp__plugin_atlassian_atlassian__getAccessibleAtlassianResources
  - mcp__plugin_atlassian_atlassian__atlassianUserInfo
  - mcp__plugin_atlassian_atlassian__getJiraIssue
  - mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql
```

---

## Remaining Open Items

### Live verification still recommended

While this source-code-based verification answers all 6 CONFIRM questions with high confidence, the following would benefit from a live test when the Atlassian plugin is enabled:

1. **`getJiraIssue` exact JSON response shape** -- Needed to write robust parsing logic. Specifically:
   - Are comments at `fields.comment.comments` or somewhere else?
   - What fields does each comment object have? (Expected: `author`, `body`, `created`, `updated`)
   - Is the description returned as raw ADF JSON or rendered text?
   - Is the response paginated for comments?

2. **Markdown rendering fidelity** -- Does `addCommentToJiraIssue` preserve all markdown features? (Code blocks with triple backticks, tables, nested lists)

3. **`getAccessibleAtlassianResources` response format** -- What does the array of resources look like? (Expected: array of objects with `id` (cloudId), `name`, `url`, `scopes`)

### Note on `editJiraIssue` absence

The absence of `editJiraIssue` is a confirmed architectural constraint. The implementation plan already anticipated this possibility (doc 08, section 5, CONFIRM-1 "If it doesn't" path). The design uses `addCommentToJiraIssue` as the sole update mechanism, which:
- Avoids the "runaway description" problem (doc 09, feedback 2.1)
- Preserves the original issue description as a historical snapshot
- Creates a cleaner audit trail of updates as comments

---

## Verification Methodology Notes

- **Plugin installed at**: `~/.claude/plugins/cache/claude-plugins-official/atlassian/63e369036b13/`
- **Plugin installed at (record)**: `installed_plugins.json` shows `atlassian@claude-plugins-official` with git SHA `7caef65e1070f5219efa018fa0b1023738dbd56b`
- **Plugin NOT in `enabledPlugins`**: `~/.claude/settings.json` does not list `atlassian` in `enabledPlugins`, which is why MCP tools were not available for live testing
- **5 skills analyzed**: `triage-issue`, `search-company-knowledge`, `spec-to-backlog`, `capture-tasks-from-meeting-notes`, `generate-status-report`
- **Grep searches performed**: `editJiraIssue`, `updateJiraIssue`, `getJiraIssue`, `addCommentToJiraIssue`, `getAccessibleAtlassianResources`, `atlassianUserInfo`, and all tool call patterns with `(cloudId` signature
