---
name: jev-sandbox-run
description: >-
  Execute untrusted or risky code in an E2B sandbox after JEV judges it —
  narrow decision first (tool-route pack), then sandboxed execution instead
  of local shell. Use when generated scripts, scraped snippets, or
  unfamiliar code must run but shouldn't touch the host.
---

# JEV Sandbox Run

Combo #5 in the set: narrow JEV decision + sandboxed execution. The
`tool-route` pack decides local-vs-sandbox; this skill runs the sandbox
half via the E2B SDK.

## Prerequisites

- `E2B_API_KEY` env var (get one at e2b.dev — free tier exists). Without
  it the script exits `10` with `MPT_NEEDS_INPUT`-style discovery:
  `NEEDS=E2B_API_KEY`.
- `e2b` python package (`uv tool`/`pip install e2b` or run via
  `uv run --with e2b`). The script reports a clear error if missing.
- Decision first: run `route_tool_call.py`; sandbox when band=ask/deny
  but the work must still happen (untrusted snippets, downloads, tests).

## Usage

```bash
# judge first, then sandbox
python3 skills/jev-decision-batch/scripts/route_tool_call.py \
    --command "python3 scraped_snippet.py" --context "untrusted snippet"

# run in sandbox (needs E2B_API_KEY)
python3 skills/jev-sandbox-run/scripts/sandbox_exec.py \
    --command "python3 -c 'print(1+1)'"

# via uv with the SDK pulled in transiently
E2B_API_KEY=... uv run --with e2b \
    skills/jev-sandbox-run/scripts/sandbox_exec.py --command "uname -a"
```

Exit codes: `0` ran in sandbox, `10` missing `E2B_API_KEY`,
`1` sandbox/runtime error, `2` e2b SDK unavailable.

Every run (or refused run) appends a `sandbox-run` ledger record.

## Boundaries

- Sandbox ≠ approval: sandboxed code can still exfiltrate anything pasted
  into it — never pass secrets into the sandboxed command itself.
- The e2b-mcp-server MCP is also exposed for agent-side use; this script
  is the scriptable lane that works outside MCP sessions.
- Local fallback is a deliberate choice by the caller, not automatic —
  a refused sandbox must never silently run locally.
