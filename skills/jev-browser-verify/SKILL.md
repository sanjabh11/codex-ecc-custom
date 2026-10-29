---
name: jev-browser-verify
description: >-
  Verify a rendered web artifact actually works — Playwright captures the
  page (agent-side via playwright MCP), JEV judges the snapshot against the
  stated expectation, code bands pass/review/fail. Use after building HTML
  pages, decks, dashboards, or before marking browser-facing tasks done.
---

# JEV Browser Verify

Verify-the-result lane. The agent captures evidence with the `playwright`
MCP server (navigate + snapshot/screenshot), saves it, then the pack judges
it. JEV never drives the browser — it only judges evidence; code bands.

## Prerequisites

- `playwright` MCP server exposed in-session (verified: this repo's
  sessions expose it).
- `~/jev-starter` engine for the `browser-verify` pack.

## Flow

```text
1. playwright MCP: browser_navigate -> browser_snapshot (or screenshot)
2. save snapshot text / screenshot description to a file
3. python3 skills/jev-browser-verify/scripts/browser_verify.py \
       --evidence <file> --expect "what success looks like" --url <url>
4. band pass -> proceed; review -> inspect; fail -> fix and re-verify
```

## Usage

```bash
# free dry-run (simulated JEV answers)
python3 skills/jev-browser-verify/scripts/browser_verify.py \
    --evidence /tmp/page-snapshot.txt \
    --expect "deck title visible, 5 slides in nav" --simulate
```

Exit codes: `0` pass, `2` review (inspect before proceeding), `1` fail or
infra error. Each verdict appends a `pack-decision` record to
`.phase-loop/phase-ledger.jsonl`.

## Boundaries

- Evidence in, judgment out — snapshots are capped at 8000 chars; never
  send full HTML dumps or credential-bearing pages to the model.
- `fail` means the stated expectation is unmet or the page is broken;
  cosmetic issues band `review`, not `fail`.
- Batch runs go through `~/jev-starter` packs.py; `--simulate` is the
  free pre-flight.
