---
name: jev-security-gate
description: >-
  Semgrep scan judged by the security-findings JEV pack — deterministic
  findings first, JEV scores real-vs-false-positive and severity in context,
  code bands each finding block/fix/accept. Use before commits or when
  reviewing generated skill code for secrets, injection, and unsafe patterns.
---

# JEV Security Gate

Judgment-layered SAST. Semgrep produces findings deterministically; JEV only
answers whether each finding is real and how severe it is in context; code
applies the `block` / `fix` / `accept` band. This is combo #5 from the JEV
route-the-work set — findings judged, rules enforced by code.

## Prerequisites

- `semgrep` on PATH (`uv tool install semgrep`).
- `~/jev-starter` engine with `.venv` (packs.py + security-findings pack).
- No secrets in output: snippets are truncated to 200 chars; `.env`-style
  files should be reviewed manually, not shipped to the model wholesale.

## Usage

```bash
# scan a directory or staged-diff target
python3 skills/jev-security-gate/scripts/security_gate_scan.py --path skills/

# free dry-run: JEV answers are simulated, semgrep still runs live
python3 skills/jev-security-gate/scripts/security_gate_scan.py --path . --simulate

# different ruleset (default: auto registry rules)
python3 skills/jev-security-gate/scripts/security_gate_scan.py \
    --path src/ --rules-config p/python
```

Exit codes: `0` = no blocking findings, `1` = semgrep failed to run,
`2` = at least one finding banded `block`.

Each finding lands in the ledger as a `pack-decision` record in
`.phase-loop/phase-ledger.jsonl`.

## Boundaries

- Judged bands are advisory: `block` findings should stop a commit, but the
  human/agent makes the final call — this is a review gate, not a hook yet.
- Never pass raw secrets as finding snippets; the scanner truncates and the
  pack state carries rule id + path + a bounded snippet only.
- Batch runs go through `~/jev-starter` (`packs.py`) — never per-finding
  LLM loops; `--simulate` is the free pre-flight.
