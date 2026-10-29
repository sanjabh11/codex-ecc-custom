#!/usr/bin/env bash
# github-mcp-bridge — spawn GitHub's remote MCP with auth sourced from
# the local `gh` CLI keychain at spawn time. The token is resolved in
# memory and never written to config or disk.
set -euo pipefail

GH_CRED="$(gh auth token 2>/dev/null || true)"
if [ -z "$GH_CRED" ]; then
  echo "github-mcp-bridge: gh auth token unavailable — run 'gh auth login'" >&2
  exit 1
fi

exec npx -y mcp-remote "https://api.githubcopilot.com/mcp/" \
  --header "Authorization: Bearer $GH_CRED" \
  2> >(sed -E 's/Bearer [A-Za-z0-9_.-]+/Bearer [redacted]/g' >&2)
