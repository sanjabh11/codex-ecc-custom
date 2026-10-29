#!/usr/bin/env bash
# graphify-platform-install.sh — Symlink ecc-graphify skill to all platform skill directories
# Usage: bash graphify-platform-install.sh [--uninstall] [--force]
#
# Creates symlinks from the canonical skill source to:
#   ~/.codeium/windsurf/skills/ecc-graphify  (Windsurf — canonical)
#   ~/.claude/skills/ecc-graphify            (Claude Code)
#   ~/.agents/skills/ecc-graphify            (Generic Agent-Skills)
#   ~/.devin/skills/ecc-graphify             (Devin CLI)
#   ~/.codex/skills/ecc-graphify             (Codex)
#
# The canonical source is the repo at /Users/sanjayb/codex-ecc-custom/skills/ecc-graphify

set -euo pipefail

UNINSTALL=false
FORCE=false
for ARG in "$@"; do
    case "$ARG" in
        --uninstall) UNINSTALL=true ;;
        --force) FORCE=true ;;
        *) echo "ERROR: unknown option: $ARG" >&2; exit 2 ;;
    esac
done

# Resolve the canonical skill source (this script's parent dir)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$(cd "$SCRIPT_DIR/.." && pwd)"

# Verify the skill source exists
if [ ! -f "$SKILL_SRC/SKILL.md" ]; then
    echo "ERROR: SKILL.md not found at $SKILL_SRC"
    exit 1
fi

# Platform skill directories (user scope)
declare -a PLATFORM_DIRS=(
    "$HOME/.codeium/windsurf/skills"
    "$HOME/.claude/skills"
    "$HOME/.agents/skills"
    "$HOME/.devin/skills"
    "$HOME/.codex/skills"
)

SUCCESS_COUNT=0
SKIP_COUNT=0
FAIL_COUNT=0

for PLATFORM_DIR in "${PLATFORM_DIRS[@]}"; do
    PLATFORM_NAME=$(basename "$(dirname "$PLATFORM_DIR")")
    LINK_PATH="$PLATFORM_DIR/ecc-graphify"

    if [ "$UNINSTALL" = true ]; then
        if [ -L "$LINK_PATH" ]; then
            EXISTING_TARGET=$(readlink "$LINK_PATH")
            if [ "$EXISTING_TARGET" = "$SKILL_SRC" ] || [ "$FORCE" = true ]; then
                rm "$LINK_PATH"
                echo "  removed  ->  $LINK_PATH"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                echo "  skip     ->  $LINK_PATH (unexpected symlink target: $EXISTING_TARGET)"
                FAIL_COUNT=$((FAIL_COUNT + 1))
            fi
        elif [ -d "$LINK_PATH" ]; then
            echo "  skip     ->  $LINK_PATH (real directory, not symlink — not removing)"
            SKIP_COUNT=$((SKIP_COUNT + 1))
        else
            echo "  skip     ->  $LINK_PATH (not found)"
            SKIP_COUNT=$((SKIP_COUNT + 1))
        fi
        continue
    fi

    # Create platform dir if it doesn't exist
    if [ ! -d "$PLATFORM_DIR" ]; then
        mkdir -p "$PLATFORM_DIR"
    fi

    # Handle existing entry
    if [ -L "$LINK_PATH" ]; then
        EXISTING_TARGET=$(readlink "$LINK_PATH")
        if [ "$EXISTING_TARGET" = "$SKILL_SRC" ]; then
            echo "  exists   ->  $LINK_PATH (already points to correct source)"
            SKIP_COUNT=$((SKIP_COUNT + 1))
            continue
        else
            if [ "$FORCE" != true ]; then
                echo "  FAIL     ->  $LINK_PATH (unexpected symlink target: $EXISTING_TARGET; rerun with --force after review)"
                FAIL_COUNT=$((FAIL_COUNT + 1))
                continue
            fi
            echo "  update   ->  $LINK_PATH (was: $EXISTING_TARGET)"
            rm "$LINK_PATH"
        fi
    elif [ -d "$LINK_PATH" ]; then
        echo "  skip     ->  $LINK_PATH (real directory exists — backup and replace? manual intervention needed)"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi

    # Create symlink
    if ln -s "$SKILL_SRC" "$LINK_PATH" 2>/dev/null; then
        echo "  linked   ->  $LINK_PATH"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "  FAIL     ->  $LINK_PATH (ln -s failed)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

echo ""
if [ "$UNINSTALL" = true ]; then
    echo "Uninstall complete: $SUCCESS_COUNT removed, $SKIP_COUNT skipped, $FAIL_COUNT failed"
else
    echo "Install complete: $SUCCESS_COUNT linked, $SKIP_COUNT skipped, $FAIL_COUNT failed"
    echo ""
    echo "Skill source: $SKILL_SRC"
    echo "The skill is discoverable through the configured five user-scope paths. Host loader/runtime proof is separate."
fi

exit $FAIL_COUNT
