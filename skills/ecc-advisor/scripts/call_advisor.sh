#!/usr/bin/env bash
# call_advisor.sh — Bootstrap wrapper for ecc-advisor
# Resolves the advisor_cli.py path regardless of CWD or git availability.
#
# Usage:
#   bash skills/ecc-advisor/scripts/call_advisor.sh --status
#   bash skills/ecc-advisor/scripts/call_advisor.sh "your context here"
#   bash skills/ecc-advisor/scripts/call_advisor.sh --json "context"
#
# Path resolution order:
#   1. FABLE_DIR env var (explicit project override)
#   2. Canonical advisor_cli.py beside the real shared skill symlink target
#   3. Canonical shared repository (~.../codex-ecc-custom/fable)
#   4. git rev-parse --show-toplevel (legacy project-local fallback)
set -euo pipefail

CANONICAL_REPO_CLI="${HOME}/codex-ecc-custom/fable/advisor_cli.py"

if [[ -n "${FABLE_DIR:-}" && -f "${FABLE_DIR}/advisor_cli.py" ]]; then
    ADV_CLI="${FABLE_DIR}/advisor_cli.py"
else
    # Resolve symlinks before walking back to the canonical shared repository.
    SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
    CANONICAL_CLI="${SCRIPT_DIR}/../../../fable/advisor_cli.py"
    if [[ -f "$CANONICAL_CLI" ]]; then
        ADV_CLI="$CANONICAL_CLI"
    elif [[ -f "$CANONICAL_REPO_CLI" ]]; then
        # Skill copy installed outside codex-ecc-custom (e.g. ~/.windsurf/skills)
        # still lands on the one canonical fable runtime and shared state.
        ADV_CLI="$CANONICAL_REPO_CLI"
    elif git rev-parse --show-toplevel >/dev/null 2>&1; then
        ADV_CLI="$(git rev-parse --show-toplevel)/fable/advisor_cli.py"
    else
        ADV_CLI="$CANONICAL_REPO_CLI"
    fi
fi

# If policy is revoked, the canonical advisor_cli.py blocks before any backend call.
if [[ ! -f "$ADV_CLI" ]]; then
    echo "[Advisor] Cannot locate advisor_cli.py. Tried: $ADV_CLI" >&2
    echo "[Advisor] Set FABLE_DIR=/path/to/fable or run from inside a git repo." >&2
    exit 1
fi

exec python3 "$ADV_CLI" "$@"
