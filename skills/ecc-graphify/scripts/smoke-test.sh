#!/usr/bin/env bash
# smoke-test.sh — Verify ecc-graphify skill installation is complete and functional
# Usage: bash smoke-test.sh
# Exit 0 = all checks pass, 1 = one or more checks failed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="$(cd "$SKILL_DIR/../.." && pwd)"

PASS=0
FAIL=0
SKIP=0

check() {
    local description="$1"
    local condition="$2"
    if [ "$condition" = true ]; then
        echo "  PASS  $description"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $description"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== ecc-graphify Smoke Test ==="
echo ""

# 1. SKILL.md exists and has valid frontmatter
echo "--- Skill File ---"
SKILL_FILE="$SKILL_DIR/SKILL.md"
if [ -f "$SKILL_FILE" ]; then
    # Check YAML frontmatter
    if head -1 "$SKILL_FILE" | grep -q "^---"; then
        # Check name field
        if grep -q "^name: ecc-graphify" "$SKILL_FILE"; then
            check "SKILL.md exists with valid frontmatter" true
        else
            check "SKILL.md has 'name: ecc-graphify' in frontmatter" false
        fi
    else
        check "SKILL.md starts with YAML frontmatter (---)" false
    fi
else
    check "SKILL.md exists" false
fi

# 2. Scripts pass syntax check
echo "--- Scripts ---"
for script in "$SKILL_DIR"/scripts/*.sh; do
    if [ -f "$script" ]; then
        SCRIPT_NAME=$(basename "$script")
        if bash -n "$script" 2>/dev/null; then
            check "$SCRIPT_NAME passes bash syntax check" true
        else
            check "$SCRIPT_NAME passes bash syntax check" false
        fi
    fi
done

# 3. Reference files exist
echo "--- References ---"
EXPECTED_REFS=(
    "query-path-explain.md"
    "multimodal-extraction.md"
    "obsidian-wiki-export.md"
    "mcp-neo4j-integration.md"
    "platform-install.md"
)
for ref in "${EXPECTED_REFS[@]}"; do
    if [ -f "$SKILL_DIR/references/$ref" ]; then
        check "references/$ref exists" true
    else
        check "references/$ref exists" false
    fi
done

# 4. Capability contract exists and is machine-readable
echo "--- Capability Contract ---"
CONTRACT_FILE="$SKILL_DIR/schemas/cli-contract.json"
if [ -f "$CONTRACT_FILE" ] && python3 -c 'import json, sys; json.load(open(sys.argv[1], encoding="utf-8"))' "$CONTRACT_FILE" 2>/dev/null; then
    check "schemas/cli-contract.json is valid JSON" true
else
    check "schemas/cli-contract.json is valid JSON" false
fi

# 5. Graphify CLI is available
echo "--- Graphify CLI ---"
if command -v graphify >/dev/null 2>&1; then
    check "graphify CLI on PATH" true
    VERSION=$(graphify --version 2>/dev/null || echo "unknown")
    check "graphify --version returns ($VERSION)" true
else
    check "graphify CLI on PATH" false
fi

# 6. Health check script works
echo "--- Health Check ---"
if bash "$SKILL_DIR/scripts/graphify-health.sh" >/dev/null 2>&1; then
    check "graphify-health.sh exits 0 (healthy)" true
else
    check "graphify-health.sh exits 0 (healthy)" false
fi

# 7. Health check JSON mode works
if bash "$SKILL_DIR/scripts/graphify-health.sh" --json 2>/dev/null | grep -q '"healthy":true'; then
    check "graphify-health.sh --json returns valid JSON" true
else
    check "graphify-health.sh --json returns valid JSON" false
fi

# 8. Symlinks exist in all 5 platform directories
echo "--- Platform Symlinks ---"
PLATFORM_DIRS=(
    "$HOME/.codeium/windsurf/skills"
    "$HOME/.claude/skills"
    "$HOME/.agents/skills"
    "$HOME/.devin/skills"
    "$HOME/.codex/skills"
)
for PLATFORM_DIR in "${PLATFORM_DIRS[@]}"; do
    PLATFORM_NAME=$(basename "$(dirname "$PLATFORM_DIR")")
    LINK_PATH="$PLATFORM_DIR/ecc-graphify"
    if [ -L "$LINK_PATH" ]; then
        TARGET=$(readlink "$LINK_PATH")
        if [ "$TARGET" = "$SKILL_DIR" ]; then
            check "symlink in $PLATFORM_NAME -> correct target" true
        else
            check "symlink in $PLATFORM_NAME -> correct target (got: $TARGET)" false
        fi
    else
        check "symlink in $PLATFORM_NAME exists" false
    fi
done

# 9. SKILL.md is under 400 lines (progressive disclosure)
echo "--- Skill Size ---"
LINE_COUNT=$(wc -l < "$SKILL_FILE" | tr -d ' ')
if [ "$LINE_COUNT" -lt 400 ]; then
    check "SKILL.md is under 400 lines ($LINE_COUNT lines)" true
else
    check "SKILL.md is under 400 lines ($LINE_COUNT lines)" false
fi

# Summary
echo ""
echo "=== Summary ==="
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo "  Total:  $((PASS + FAIL))"

if [ "$FAIL" -eq 0 ]; then
    echo ""
    echo "All local smoke checks passed. External host/runtime proof remains manual."
    exit 0
else
    echo ""
    echo "FAILED: $FAIL check(s) failed. Review above."
    exit 1
fi
