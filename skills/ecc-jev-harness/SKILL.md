---
name: ecc-jev-harness
description: >-
  Jev-gated agent harness in ~/jev-starter — mini-swe-agent-style chassis where
  every bash action passes exec_gate (allow/ask/deny) before running. Provides
  four entry points: agent_harness.py (single gated loop), lanes.py (multi-lane
  audit/impl worktree orchestration), plan_runner.py (numbered-plan executor
  with proof ledger), evals.py (golden-set pass@k evals with regression gate).
  Auto-invocable for gated execution, parallel audit lanes, plan execution,
  and agent regression testing.
allowed-tools: Read, Write, Bash
---

# ecc-jev-harness — Jev-Gated Agent Harness

> **Usage hint:** `gated agent run, audit lanes, implement this plan, golden-set eval, exec gate`

An owned, inspectable agent loop where **no action executes without a Jev
verdict**. Built for the operator who was manually pasting agent transcripts
for approval — the gate does that in-line now.

Engine: `~/jev-starter` (Python 3.14 venv at `~/jev-starter/.venv/bin/python`).

## Entry Points

| Tool | Command | Purpose |
|---|---|---|
| Single gated loop | `python3 ~/jev-starter/agent_harness.py --task "..." --repo . --model <spec>` | One agent, task packet, gated actions, trajectory JSONL |
| Audit lanes | `python3 ~/jev-starter/lanes.py audit --repo R --lanes R1,R2,R3 --focus "..."` | N read-only lanes in worktrees → synthesis.md |
| Cross-model adjudication | `lanes.py audit --model-map R1=litellm:a,R2=litellm:b --arbiter-model litellm:c` | Different model per lane + arbiter merge |
| Impl lanes | `python3 ~/jev-starter/lanes.py impl --repo R --packet a.yaml --packet b.yaml` | Governed write lanes, conflict-checked, diff harvest → merge-report.md |
| Plan executor | `python3 ~/jev-starter/plan_runner.py --plan plan.md --repo R --write-root R` | Numbered steps → per-step packets → steps.json ledger |
| Golden evals | `python3 ~/jev-starter/evals.py --cases gold.jsonl --repo R --model <spec>` | pass@1/pass@k, cost, baseline regression |
| Skill forge | `python3 ~/jev-starter/skill_forge.py --source notes.md --name x --model <spec>` | Mine → SKILL.md → validate → eval-gate → sandbox candidate |
| Cron gate | `python3 ~/jev-starter/cron_gate.py run --name j --cmd "..." --expect exit:0` | Contract-checked jobs + escalations.jsonl |
| Voice delegate | `python3 ~/jev-starter/delegate.py --transcript t.txt --repo .` | Transcript → task-packet → gated run |

**Fleet kill switch:** `export JEV_HARNESS_DISABLE=1` — every loop entry
point refuses (`HarnessDisabled`/`gated`). Gate rollback separately:
`JEV_FEATURES=off`.

## Gate Semantics (inherited, enforced)

- `allow` → command runs (timeout + process-group kill)
- `ask` → default **block**: model sees "NOT executed — choose safer alternative
  or submit"; logged to `pending_asks.jsonl`. `--ask-mode confirm|fail` override.
- `deny` → never runs (secrets, SSH keys, env files, obfuscated substitutions)
- Writes allowed only under `JEV_EXEC_ALLOW_ROOTS` / `--write-root` / impl-lane
  worktrees — everything else stays gated.

## Model Specs

- `litellm:<provider/model>` — any litellm id (needs `pip install litellm`)
- `cmd:<command>` — external CLI; messages JSON on stdin, reply on stdout
  (this is how `claude -p`, `codex exec`, or any shim plugs in)
- `scripted:<file.jsonl>` — replay `{"text": ...}` lines (offline tests/replays)
- `echo` — smoke test
- `scripted:...step_{step}.jsonl` — `{step}` expands per plan step

## Recipes Mapped to Existing Workflows

- **"Read-only audit lane R1/R2/R3"** → `lanes.py audit` — no more hand-spawned
  worktrees or pasted reviewer prompts
- **"PLEASE IMPLEMENT THIS PLAN"** → `plan_runner.py --plan` — `cmd:` lines in
  step bodies are gated evidence; failed steps halt; `--resume` re-enters
- **"You are Agent 1/Agent 2 in a governed implementation"** → `lanes.py impl`
  — write-path conflicts refused before dispatch
- **Skill/agent regression** → `evals.py --baseline` — nonzero exit on regression
- **Proceed/continue elimination** — the loop runs to submit/limit; no nudges

## Run Artifacts

Every run dir holds `trajectory.jsonl` (replayable), `telemetry.jsonl`
(sha-only, non-secret), `result.json`, `pending_asks.jsonl`, `checkpoint.json`
(resumable). Lane runs add `lanes.json` (live registry), `synthesis.md` or
`merge-report.md` + `diffs/*.patch`.

## Revocation (auto-revocable by construction)

The skill is pure declaration — symlinked dirs only, no hooks/settings/MCP
registration. Revoke completely:

```bash
rm ~/.codex/skills/ecc-jev-harness ~/.cursor/skills/ecc-jev-harness \
   ~/.config/devin/skills/ecc-jev-harness \
   ~/.codeium/windsurf/skills/ecc-jev-harness          # symlinks
rm -rf ~/codex-ecc-custom/skills/ecc-jev-harness       # canonical dir
```

The engine in `~/jev-starter` is untouched by revocation. Rollback the
gate itself via `JEV_FEATURES=off` / `policy.json` (decision-contract.v1).
