---
name: jev-github-watch
description: >-
  JEV-gated GitHub inspection — decide when repo/issue/PR inspection is
  warranted instead of polling everything, then act via the github MCP or
  `gh` CLI. Includes the bridge script that repairs the github MCP auth
  (token resolved from `gh auth token` at spawn, never stored).
---

# JEV GitHub Watch

Combo #16: a decision layer in front of repo/issue/PR inspection. JEV
asks "is this worth looking at now" (repo-watch judgment via existing
packs — drift, sessions, project-triage) and only then does the agent hit
GitHub. The `github` MCP server is the preferred surface; `gh` CLI is the
verified fallback.

## MCP repair (done 2026-09-27)

The `github` MCP entry in `~/.config/devin/mcp_config.json` previously ran
`npx -y mcp-remote https://api.githubcopilot.com/mcp/` with no credentials
— OAuth was registered (`~/.mcp-auth/mcp-remote-*/…_client_info.json`) but
no token grant ever completed, so `list_tools` failed.

`scripts/github-mcp-bridge.sh` now wraps the spawn: resolves
`gh auth token` (account sanjabh11, scopes repo/workflow/read:org/gist)
into an `Authorization: Bearer` header at launch. Verified: `initialize`
returns HTTP 200 with the gh token. The token lives only in the spawned
process env — never persisted in config.

Restart Devin (or the MCP host) after config changes to pick up the bridge.

## Usage pattern

```text
1. gather state: open PRs/issues surfaced by `gh` or periodic checks
2. ask JEV (existing packs — project-triage, drift) whether inspection
   is warranted now
3. warranted -> act via github MCP tools (or `gh api` fallback)
4. log the decision as a pack-decision ledger record
```

## Boundaries

- `gh` scopes cover repo/workflow/read:org/gist — no admin/delete scopes;
  destructive repo ops stay out of this lane entirely.
- The bridge requires `gh auth login` to stay fresh; if `gh auth token`
  fails, the bridge exits 1 and the MCP tool list degrades to absent.
