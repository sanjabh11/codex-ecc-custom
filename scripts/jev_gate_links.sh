#!/usr/bin/env bash
# jev_gate_links.sh — install/revoke global discovery links for the
# JEV-gate skills (and any skills listed) across IDE skill roots.
#
# Usage:
#   scripts/jev_gate_links.sh status    # show link state (default)
#   scripts/jev_gate_links.sh install   # create missing symlinks
#   scripts/jev_gate_links.sh revoke    # remove ONLY links we created
#                                       # (identified by pointing into this repo)
#
# Auto-revocable by design: revoke removes symlinks whose target lives
# inside this repository — a link left by a copy-based projection or by
# hand to a different location is never touched. For the github MCP bridge
# config change, restore ~/.config/devin/mcp_config.json.bak.<timestamp>.
set -euo pipefail

REPO="/Users/sanjayb/codex-ecc-custom"
SKILLS=(
  jev-browser-verify
  jev-decision-batch
  jev-doc-ingest
  jev-escalate
  jev-evidence
  jev-github-watch
  jev-pack-evals
  jev-sandbox-run
  jev-security-gate
  moneyprinterturbo-video
)
ROOTS=(
  "$HOME/.codex/skills"
  "$HOME/.agents/skills"
  "$HOME/.claude/skills"
  "$HOME/.devin/skills"
)

cmd="${1:-status}"

for root in "${ROOTS[@]}"; do
  [ -d "$root" ] || { echo "skip (missing): $root"; continue; }
  for skill in "${SKILLS[@]}"; do
    src="$REPO/skills/$skill"
    dst="$root/$skill"
    [ -d "$src" ] || continue
    case "$cmd" in
      install)
        if [ -e "$dst" ]; then
          echo "exists: $dst"
        else
          ln -s "$src" "$dst"
          echo "linked: $dst -> $src"
        fi
        ;;
      revoke)
        if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
          rm "$dst"
          echo "revoked: $dst"
        elif [ -e "$dst" ]; then
          echo "kept (not our link): $dst"
        fi
        ;;
      status)
        if [ -L "$dst" ]; then
          echo "linked: $dst"
        elif [ -e "$dst" ]; then
          echo "present(non-link): $dst"
        fi
        ;;
      *) echo "unknown command: $cmd" >&2; exit 1 ;;
    esac
  done
done
