---
name: jev-escalate
description: >-
  Escalate gated decisions to the human via Hermes messaging — when a
  tool-route or other pack verdict bands ask/deny, format a bounded
  message and send it to the configured Telegram channel so the human can
  allow or deny. Use as the escalation half of every judgment gate.
---

# JEV Escalate

The `escalate to a human` half of the JEV loop. Reads a verdict payload
(from `route_tool_call.py --json`, `browser_verify.py --json`, or any
`{"band": ...}` JSON on stdin), and if the band is in the escalate set,
sends a compact message through `hermes send` (Telegram home channel by
default).

## Prerequisites

- `hermes` CLI on PATH (`~/.local/bin/hermes`), gateway already configured
  (`hermes send --list` shows `telegram` targets).
- Verdicts come from the pack runners — this skill never judges itself.

## Usage

```bash
# pipe a verdict through the escalator (default: dry-run, prints message)
python3 skills/jev-decision-batch/scripts/route_tool_call.py \
    --command "git push --force" --json --simulate \
  | python3 skills/jev-escalate/scripts/escalate.py

# actually deliver to Telegram
python3 skills/jev-escalate/scripts/escalate.py --send < verdict.json

# escalate only on specific bands (default: ask, deny, review)
python3 skills/jev-escalate/scripts/escalate.py --send --on deny
```

Exit codes: `0` delivered (or nothing to escalate), `2` dry-run message
shown, `1` send failed / missing hermes.

Every escalation appends an `escalation` record to
`.phase-loop/phase-ledger.jsonl`.

## Boundaries

- Default is dry-run: delivery requires the explicit `--send` flag, so
  wiring can be tested without waking anyone's phone.
- Messages are bounded: commands truncated to 200 chars and common
  secret-shaped strings (`sk-…`, `KEY=…`, `token …`) are redacted before
  send — verdict payloads should never carry credentials, but belt and
  braces.
- Reply-handling (human answers back allow/deny) is out of scope for this
  script — Hermes `approvals`/`webhook` commands cover two-way flows.
