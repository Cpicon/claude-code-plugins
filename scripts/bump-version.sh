#!/bin/bash

# bump-version.sh - Semantic version bumper for Claude Code plugins
# Usage: ./scripts/bump-version.sh [patch|minor|major] [--push] [--dry-run]
#
# Examples:
#   ./scripts/bump-version.sh patch        # 1.0.0 → 1.0.1
#   ./scripts/bump-version.sh minor        # 1.0.0 → 1.1.0
#   ./scripts/bump-version.sh major        # 1.0.0 → 2.0.0
#   ./scripts/bump-version.sh patch --push # Also pushes to GitHub
#   ./scripts/bump-version.sh patch --dry-run # Preview changes without applying

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - paths relative to repository root
PLUGIN_JSON="agent-team-creator/.claude-plugin/plugin.json"
MARKETPLACE_JSON=".claude-plugin/marketplace.json"
PLUGIN_NAME="agent-team-creator"

# Get script directory and navigate to repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

# Function to print colored output
print_color() {
    printf "${2}${1}${NC}\n"
}

# Function to print step header
print_step() {
    printf "\n${BLUE}▶ ${1}${NC}\n"
}

# Function to check if jq is installed
check_dependencies() {
    if ! command -v jq &> /dev/null; then
        print_color "Error: jq is required but not installed." "$RED"
        print_color "Install with: brew install jq" "$YELLOW"
        exit 1
    fi
}

# Function to check if git working directory is clean
check_git_clean() {
    if [[ -n $(git status -s) ]]; then
        print_color "Error: Working directory is not clean. Commit or stash changes first." "$RED"
        git status -s
        exit 1
    fi
}

# Function to parse semantic version into components
parse_version() {
    local version=$1
    # Remove 'v' prefix if present
    version="${version#v}"
    echo "$version" | sed -E 's/^([0-9]+)\.([0-9]+)\.([0-9]+).*$/\1 \2 \3/'
}

# Function to bump version based on type
bump_version() {
    local version=$1
    local bump_type=$2

    # Parse current version
    IFS=' ' read -r major minor patch <<< "$(parse_version "$version")"

    # Validate parsing
    if [[ -z "$major" || -z "$minor" || -z "$patch" ]]; then
        print_color "Error: Could not parse version '$version'" "$RED"
        exit 1
    fi

    # Bump based on type
    case "$bump_type" in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
        *)
            print_color "Error: Invalid bump type '$bump_type'. Use: patch, minor, or major" "$RED"
            exit 1
            ;;
    esac

    echo "${major}.${minor}.${patch}"
}

# Function to get current version from plugin.json
get_current_version() {
    if [[ ! -f "$PLUGIN_JSON" ]]; then
        print_color "Error: $PLUGIN_JSON not found" "$RED"
        exit 1
    fi
    jq -r '.version' "$PLUGIN_JSON"
}

# Function to update version in plugin.json
update_plugin_json() {
    local new_version=$1
    local temp_file="${PLUGIN_JSON}.tmp"

    jq --arg v "$new_version" '.version = $v' "$PLUGIN_JSON" > "$temp_file"
    mv "$temp_file" "$PLUGIN_JSON"
    print_color "  ✓ Updated $PLUGIN_JSON" "$GREEN"
}

# Function to update version in marketplace.json for specific plugin
update_marketplace_json() {
    local new_version=$1
    local temp_file="${MARKETPLACE_JSON}.tmp"

    if [[ ! -f "$MARKETPLACE_JSON" ]]; then
        print_color "  ⚠ Warning: $MARKETPLACE_JSON not found, skipping..." "$YELLOW"
        return
    fi

    # Update version for the specific plugin
    jq --arg name "$PLUGIN_NAME" --arg v "$new_version" \
        '(.plugins[] | select(.name == $name).version) = $v' \
        "$MARKETPLACE_JSON" > "$temp_file"
    mv "$temp_file" "$MARKETPLACE_JSON"
    print_color "  ✓ Updated $MARKETPLACE_JSON" "$GREEN"
}

# Function to create git commit and tag
create_git_release() {
    local current_version=$1
    local new_version=$2
    local bump_type=$3

    # Stage changed files
    git add "$PLUGIN_JSON" "$MARKETPLACE_JSON" 2>/dev/null || true

    # Create commit
    git commit -m "chore(release): bump version to ${new_version}

- Type: ${bump_type} release
- Previous: ${current_version}
- New: ${new_version}

Updated files:
- ${PLUGIN_JSON}
- ${MARKETPLACE_JSON}"

    print_color "  ✓ Created commit" "$GREEN"

    # Create annotated tag
    git tag -a "v${new_version}" -m "Release v${new_version}

Type: ${bump_type} release
Previous version: ${current_version}
Date: $(date '+%Y-%m-%d %H:%M:%S')

See CHANGELOG.md for details."

    print_color "  ✓ Created tag v${new_version}" "$GREEN"
}

# Function to push to remote
push_to_remote() {
    local new_version=$1

    print_step "Pushing to remote..."
    git push origin main
    git push origin "v${new_version}"
    print_color "  ✓ Pushed commit and tag to origin" "$GREEN"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [patch|minor|major] [options]"
    echo ""
    echo "Bump Types:"
    echo "  patch   Increment patch version (1.0.0 → 1.0.1)"
    echo "  minor   Increment minor version (1.0.0 → 1.1.0)"
    echo "  major   Increment major version (1.0.0 → 2.0.0)"
    echo ""
    echo "Options:"
    echo "  --push     Push commit and tag to remote after creating"
    echo "  --dry-run  Show what would happen without making changes"
    echo "  --help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 patch              # Bug fix release"
    echo "  $0 minor --push       # Feature release, push immediately"
    echo "  $0 major --dry-run    # Preview major version bump"
}

# Main function
main() {
    local bump_type="patch"
    local push_to_remote_flag=false
    local dry_run=false

    # Parse arguments
    for arg in "$@"; do
        case $arg in
            patch|minor|major)
                bump_type="$arg"
                ;;
            --push)
                push_to_remote_flag=true
                ;;
            --dry-run)
                dry_run=true
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                print_color "Unknown argument: $arg" "$RED"
                show_usage
                exit 1
                ;;
        esac
    done

    # Header
    echo ""
    print_color "╔════════════════════════════════════════╗" "$BLUE"
    print_color "║   Claude Code Plugin Version Bumper    ║" "$BLUE"
    print_color "╚════════════════════════════════════════╝" "$BLUE"

    if [[ "$dry_run" == "true" ]]; then
        print_color "\n🔍 DRY RUN MODE - No changes will be made\n" "$YELLOW"
    fi

    # Check dependencies
    print_step "Checking dependencies..."
    check_dependencies
    print_color "  ✓ jq is installed" "$GREEN"

    # Check git status (unless dry run)
    if [[ "$dry_run" != "true" ]]; then
        print_step "Checking git status..."
        check_git_clean
        print_color "  ✓ Working directory is clean" "$GREEN"
    fi

    # Get current version
    print_step "Getting current version..."
    current_version=$(get_current_version)
    print_color "  Current: $current_version" "$YELLOW"

    # Calculate new version
    new_version=$(bump_version "$current_version" "$bump_type")
    print_color "  New:     $new_version ($bump_type bump)" "$GREEN"

    if [[ "$dry_run" == "true" ]]; then
        print_step "Would update files..."
        print_color "  → $PLUGIN_JSON: $current_version → $new_version" "$YELLOW"
        print_color "  → $MARKETPLACE_JSON: $current_version → $new_version" "$YELLOW"
        print_color "  → git commit with message: 'chore(release): bump version to ${new_version}'" "$YELLOW"
        print_color "  → git tag: v${new_version}" "$YELLOW"
        if [[ "$push_to_remote_flag" == "true" ]]; then
            print_color "  → Push to origin/main" "$YELLOW"
        fi
        print_color "\n✅ Dry run complete. Use without --dry-run to apply changes." "$GREEN"
        exit 0
    fi

    # Update version files
    print_step "Updating version files..."
    update_plugin_json "$new_version"
    update_marketplace_json "$new_version"

    # Create git commit and tag
    print_step "Creating git commit and tag..."
    create_git_release "$current_version" "$new_version" "$bump_type"

    # Push if requested
    if [[ "$push_to_remote_flag" == "true" ]]; then
        push_to_remote "$new_version"
    fi

    # Summary
    echo ""
    print_color "╔════════════════════════════════════════╗" "$GREEN"
    print_color "║         ✅ Version Bump Complete        ║" "$GREEN"
    print_color "╚════════════════════════════════════════╝" "$GREEN"
    echo ""
    echo "  Version: $current_version → $new_version"
    echo "  Tag:     v${new_version}"
    echo ""

    if [[ "$push_to_remote_flag" != "true" ]]; then
        print_color "To push changes, run:" "$YELLOW"
        echo "  git push origin main"
        echo "  git push origin v${new_version}"
        echo ""
        echo "Or run this script with --push flag next time."
    else
        print_color "Changes pushed to GitHub!" "$GREEN"
        echo "Users will receive the update on their next Claude Code restart."
    fi
    echo ""
}

# Run main function
main "$@"
