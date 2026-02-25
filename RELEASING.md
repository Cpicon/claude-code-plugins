# Releasing Claude Code Plugins

This guide documents the complete release process for the claude-code-plugins marketplace.

## Quick Reference

```bash
# Bug fix release (most common)
./scripts/bump-version.sh patch --push

# New feature release
./scripts/bump-version.sh minor --push

# Breaking change release
./scripts/bump-version.sh major --push

# Preview changes without applying
./scripts/bump-version.sh patch --dry-run
```

---

## How Updates Reach Users

When you push to the `main` branch on GitHub:

1. **Auto-update enabled users**: Receive updates automatically on next Claude Code restart
2. **Manual update users**: Run `/plugin marketplace update` then restart

| Marketplace Type | Default Behavior |
|------------------|------------------|
| Official (Anthropic) | Auto-updates enabled |
| Third-party (this repo) | Requires user opt-in |

**User command to enable auto-updates:**
```
/plugin marketplace edit cpicon-claude-plugins
# Set auto-update: true
```

---

## Prerequisites Checklist

Before releasing, ensure:

- [ ] All changes are tested locally
- [ ] Working directory is clean (`git status` shows no changes)
- [ ] You're on the `main` branch
- [ ] CHANGELOG.md is updated (for non-trivial releases)
- [ ] `jq` is installed (`brew install jq` if not)

---

## Development & Debug Workflow

### The Multi-Location Sync Issue

When you install a plugin, files exist in **three locations**:

| Location | Path | Description |
|----------|------|-------------|
| Source | `./agent-team-creator/` | Where you edit code |
| Installed | `~/.claude/plugins/agent-team-creator/` | Active plugin copy |
| Cache | `~/.claude/plugins/cache/*/agent-team-creator/` | Versioned cache |

**Problem**: Editing source files doesn't update the installed/cached versions.

### Local Testing Workflow

```bash
# 1. Make your changes in the source directory
#    Edit files in ./agent-team-creator/

# 2. Reinstall the plugin to apply changes
#    In Claude Code:
/plugin uninstall agent-team-creator
/plugin install agent-team-creator

# 3. Restart Claude Code

# 4. Test your changes
/generate-agent-team
# or other commands
```

### Alternative: Symlink Development (Advanced)

For faster iteration, symlink the cache to your source:

```bash
# Remove existing cache
rm -rf ~/.claude/plugins/cache/local-marketplace/agent-team-creator/

# Create symlink
ln -s /path/to/claude-code-plugins/agent-team-creator \
      ~/.claude/plugins/cache/local-marketplace/agent-team-creator/dev
```

Note: This may require editing `~/.claude/plugins/installed_plugins.json` to point to the "dev" version.

---

## Release Workflow

### Automated Release (Recommended)

The `bump-version.sh` script handles everything:

```bash
# Step 1: Ensure clean working directory
git status  # Should show no changes

# Step 2: Update CHANGELOG.md manually (for significant releases)
# Add entry under [Unreleased] section

# Step 3: Commit CHANGELOG if updated
git add CHANGELOG.md
git commit -m "docs: update changelog for X.Y.Z release"

# Step 4: Run the release script
./scripts/bump-version.sh patch --push
```

**What the script does:**
1. Parses current version from `plugin.json`
2. Calculates new version based on bump type
3. Updates `agent-team-creator/.claude-plugin/plugin.json`
4. Updates `.claude-plugin/marketplace.json`
5. Creates git commit with conventional message
6. Creates annotated git tag
7. Pushes to GitHub (if `--push` flag used)

### Script Options

```bash
./scripts/bump-version.sh [type] [options]

Types:
  patch   Bug fixes (1.0.0 → 1.0.1)
  minor   New features (1.0.0 → 1.1.0)
  major   Breaking changes (1.0.0 → 2.0.0)

Options:
  --push     Push to GitHub after creating commit/tag
  --dry-run  Preview changes without applying
  --help     Show help message
```

---

## Manual Release (Fallback)

If the script fails or you prefer manual control:

### Step 1: Update Version Numbers

**File 1:** `agent-team-creator/.claude-plugin/plugin.json`
```json
{
  "version": "1.0.1"  // ← Update this
}
```

**File 2:** `.claude-plugin/marketplace.json`
```json
{
  "plugins": [
    {
      "name": "agent-team-creator",
      "version": "1.0.1"  // ← Update this too
    }
  ]
}
```

### Step 2: Update CHANGELOG.md

```markdown
## [1.0.1] - 2026-01-10

### Fixed
- Description of what was fixed
```

### Step 3: Commit Changes

```bash
git add .
git commit -m "chore(release): bump version to 1.0.1

- Fixed: description
- Updated plugin.json and marketplace.json"
```

### Step 4: Create Annotated Tag

```bash
git tag -a v1.0.1 -m "Release v1.0.1

Bug fix release.
See CHANGELOG.md for details."
```

### Step 5: Push to GitHub

```bash
git push origin main
git push origin v1.0.1
```

---

## Versioning Guidelines

### When to Bump Each Type

| Bump Type | When to Use | Example Changes |
|-----------|-------------|-----------------|
| **patch** | Bug fixes, typos, minor improvements | Fix null reference, correct spelling |
| **minor** | New features, new commands/agents | Add `/new-command`, new agent |
| **major** | Breaking changes | Change output format, remove features |

### Version Number Rules

- Use semantic versioning: `MAJOR.MINOR.PATCH`
- Start at `1.0.0` (already done)
- Keep both JSON files in sync
- Tags use `v` prefix: `v1.0.1`

---

## CHANGELOG Format

Use [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [Unreleased]

## [1.1.0] - 2026-01-15

### Added
- New `/review-code` command for code reviews

### Changed
- Improved agent trigger detection accuracy

## [1.0.1] - 2026-01-10

### Fixed
- Fixed team-architect agent not recognizing Python files
```

### Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes

---

## Troubleshooting

### Script fails with "jq not found"

```bash
# Install jq
brew install jq
```

### Script fails with "Working directory not clean"

```bash
# Commit or stash your changes first
git stash
./scripts/bump-version.sh patch --push
git stash pop
```

### Tag already exists

```bash
# Delete local tag
git tag -d v1.0.1

# Delete remote tag (if pushed)
git push origin :refs/tags/v1.0.1

# Then retry
./scripts/bump-version.sh patch --push
```

### Users not receiving updates

1. Check if they have auto-update enabled:
   ```
   /plugin marketplace edit cpicon-claude-plugins
   ```

2. Have them manually update:
   ```
   /plugin marketplace update
   ```

3. Verify by checking installed version:
   ```
   /plugin list
   ```

### Version mismatch between JSON files

Both files must have matching versions. Fix manually:

```bash
# Check current versions
jq '.version' agent-team-creator/.claude-plugin/plugin.json
jq '.plugins[0].version' .claude-plugin/marketplace.json

# If different, update the one that's wrong and commit
```

---

## Release Checklist

```markdown
## Release Checklist for vX.Y.Z

### Before Release
- [ ] All changes tested locally (reinstall and run commands)
- [ ] Working directory is clean
- [ ] On `main` branch
- [ ] CHANGELOG.md updated (if needed)

### Release
- [ ] Ran `./scripts/bump-version.sh [type] --push`
- [ ] Verified tag exists: `git tag -l | grep vX.Y.Z`
- [ ] Verified push succeeded: check GitHub

### After Release
- [ ] Tested update flow on fresh install (optional)
- [ ] Announced release if significant (optional)
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/bump-version.sh` | Automated version bump script |
| `CHANGELOG.md` | Version history |
| `agent-team-creator/.claude-plugin/plugin.json` | Plugin version |
| `.claude-plugin/marketplace.json` | Marketplace plugin listing |
