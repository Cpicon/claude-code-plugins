# Local Plugin Development: Issues & Lessons Learned

**Plugin**: `agent-team-creator`
**Date**: January 2, 2026
**Author**: Christian Picon Calderon

---

## Executive Summary

This document captures the challenges encountered and lessons learned while developing the `agent-team-creator` plugin for Claude Code locally. The primary pain points revolved around marketplace configuration, plugin installation paths, and cache synchronization.

---

## Issues Encountered

### Issue 1: Plugin Installation Method Confusion

**Symptom**: Command appeared as `/create` instead of `/agent-team-creator:create`

**Root Cause**: Attempted to use plugin directly without proper marketplace registration. Claude Code plugins require installation through a marketplace, not direct directory references.

**Failed Approaches**:
```json
// ❌ Adding to settings.json - Invalid schema
"extraKnownMarketplaces": ["~/.claude/plugins/agent-team-creator"]
```

```bash
# ❌ Direct install - "Marketplace not found"
/plugin install ~/.claude/plugins/agent-team-creator
```

**Solution**: Create a proper marketplace structure, then use:
```bash
/plugin marketplace add ~/.claude/local-marketplace
/plugin install agent-team-creator
```

---

### Issue 2: Marketplace Schema Validation Errors

**Symptom**: Multiple schema validation failures when creating `marketplace.json`

**Errors & Fixes**:

| Error | Cause | Fix |
|-------|-------|-----|
| `name: Required` | Missing required field | Add `"name": "marketplace-name"` |
| `owner: Required` | Missing owner object | Add owner object with name/email |
| `owner: Expected object, received string` | Used string instead of object | Change `"owner": "Name"` to `"owner": {"name": "...", "email": "..."}` |
| `source: Invalid input` | Used `"."` for source | Change to `"./"` with trailing slash |

**Correct marketplace.json structure**:
```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "local-marketplace",
  "description": "Local plugins for Claude Code",
  "owner": {
    "name": "Your Name",
    "email": "your@email.com"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "description": "Plugin description",
      "version": "1.0.0",
      "author": {
        "name": "Author Name",
        "email": "author@email.com"
      },
      "source": "./",
      "category": "development"
    }
  ]
}
```

---

### Issue 3: Plugin Path Discrepancies

**Symptom**: Files exist in one location but plugin doesn't recognize them

**Root Cause**: Claude Code maintains multiple copies of plugin files:

```
~/.claude/
├── local-marketplace/           # Source (marketplace)
│   └── commands/
│       └── generate-debugger.md
├── plugins/
│   └── agent-team-creator/      # Installed plugin
│       └── commands/
│           └── (missing new command)
└── plugins/cache/
    └── local-marketplace/
        └── agent-team-creator/
            └── 1.0.0/
                └── commands/
                    └── (missing new command)
```

**Impact**: Adding new files to the marketplace source doesn't automatically propagate to:
1. The installed plugin directory
2. The plugin cache

**Solution**: Manually copy new files to all locations:
```bash
# Copy to installed plugin
cp ~/.claude/local-marketplace/commands/new-command.md \
   ~/.claude/plugins/agent-team-creator/commands/

# Copy to cache
cp ~/.claude/local-marketplace/commands/new-command.md \
   ~/.claude/plugins/cache/local-marketplace/agent-team-creator/1.0.0/commands/
```

---

### Issue 4: Command Not Recognized After Adding

**Symptom**: `/agent-team-creator:generate-debugger` returns "Unknown slash command"

**Root Cause**: Combination of:
1. New command only added to marketplace source
2. Plugin cache not updated
3. Claude Code session not restarted

**Solution**:
1. Copy command to all plugin locations (see Issue 3)
2. Restart Claude Code session
3. Verify with `/help` or tab completion

---

### Issue 5: Claude Code Freeze After Plugin Changes

**Symptom**: Claude Code became unresponsive after plugin modifications

**Probable Cause**: Invalid plugin configuration or syntax errors in plugin files

**Solution**:
1. Force quit Claude Code
2. Validate all JSON files for syntax errors
3. Check YAML frontmatter in command/agent files
4. Restart Claude Code

---

## Lessons Learned

### 1. Marketplace Structure is Mandatory

Claude Code plugins **must** be installed through a marketplace. There is no "loose" plugin installation.

**Action**: Always create a marketplace structure, even for local/personal plugins:
```
~/.claude/local-marketplace/
├── .claude-plugin/
│   ├── marketplace.json    # Marketplace manifest
│   └── plugin.json         # Plugin manifest
├── commands/
├── agents/
└── skills/
```

### 2. Schema Validation is Strict

Both `marketplace.json` and `plugin.json` have strict schemas. Common gotchas:
- `owner` must be an object, not a string
- `source` must be `"./"` not `"."`
- All required fields must be present

**Action**: Use the `$schema` field and validate before installation:
```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  ...
}
```

### 3. Plugin Changes Require Multi-Location Updates

When adding new commands, agents, or skills to an installed plugin:

| Location | Purpose | Update Method |
|----------|---------|---------------|
| Marketplace source | Original files | Direct edit |
| Installed plugin | Active plugin | Manual copy |
| Plugin cache | Cached version | Manual copy |

**Action**: Create a sync script for development:
```bash
#!/bin/bash
# sync-plugin.sh
PLUGIN_NAME="agent-team-creator"
MARKETPLACE="$HOME/.claude/local-marketplace"
INSTALLED="$HOME/.claude/plugins/$PLUGIN_NAME"
CACHE="$HOME/.claude/plugins/cache/local-marketplace/$PLUGIN_NAME/1.0.0"

rsync -av "$MARKETPLACE/commands/" "$INSTALLED/commands/"
rsync -av "$MARKETPLACE/commands/" "$CACHE/commands/"
rsync -av "$MARKETPLACE/agents/" "$INSTALLED/agents/"
rsync -av "$MARKETPLACE/agents/" "$CACHE/agents/"
echo "Plugin synced to all locations"
```

### 4. Restart Required for New Commands

New commands are not hot-reloaded. After adding commands:
1. Sync files to all locations
2. **Restart Claude Code**
3. Verify command availability

### 5. Documentation is Sparse

Official Claude Code plugin documentation is limited. Key resources:
- `claude-plugins-official` marketplace (examine structure)
- Community posts (e.g., clune.org)
- Trial and error

**Action**: Study existing official plugins for patterns:
```bash
ls ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/
```

---

## Recommended Development Workflow

### Initial Setup
```bash
# 1. Create marketplace structure
mkdir -p ~/.claude/local-marketplace/.claude-plugin
mkdir -p ~/.claude/local-marketplace/{commands,agents,skills}

# 2. Create marketplace.json with all required fields
# 3. Create plugin.json

# 4. Register marketplace
/plugin marketplace add ~/.claude/local-marketplace

# 5. Install plugin
/plugin install plugin-name
```

### Adding New Components
```bash
# 1. Add file to marketplace source
# 2. Run sync script (see Lesson 3)
# 3. Restart Claude Code
# 4. Test new component
```

### Debugging
```bash
# Check all plugin locations
find ~/.claude -name "command-name.md" 2>/dev/null

# Verify plugin is enabled
cat ~/.claude/settings.json | grep enabledPlugins

# Check for syntax errors
cat ~/.claude/local-marketplace/.claude-plugin/marketplace.json | jq .
```

---

## Quick Reference: File Locations

| File | Location |
|------|----------|
| Marketplace manifest | `~/.claude/local-marketplace/.claude-plugin/marketplace.json` |
| Plugin manifest | `~/.claude/local-marketplace/.claude-plugin/plugin.json` |
| Commands | `~/.claude/local-marketplace/commands/*.md` |
| Agents | `~/.claude/local-marketplace/agents/*.md` |
| Skills | `~/.claude/local-marketplace/skills/*/SKILL.md` |
| Installed plugins | `~/.claude/plugins/<plugin-name>/` |
| Plugin cache | `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` |
| Settings | `~/.claude/settings.json` |

---

## Conclusion

Local plugin development for Claude Code is functional but requires understanding of:
1. Marketplace registration requirements
2. Strict schema validation
3. Multi-location file synchronization
4. Session restart requirements

Following the recommended workflow and using sync scripts can significantly reduce friction during development.
