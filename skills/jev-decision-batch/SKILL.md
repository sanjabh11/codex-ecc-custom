---
name: jev-decision-batch
description: One-shot Jev decision batches — turn a local corpus into a static decision artifact (labels, sift, verdict, queue, map, or report) that plain code consumes afterward. Use when bulk-labeling or scoring files, sessions, skills, findings, drafts, claims, backlog items, or proposals; when gating new skills/projects with kill-fix-ship verdicts; or when triaging corpora at scale. NEVER for per-turn runtime calls — Jev is paid; batches run once and artifacts persist.
---

# Jev Decision Batch

The contract every pack follows:

```
extractor (pure code) → state.jsonl → pack YAML (questions+rules)
  → jev_batch.BatchRunner → labels.jsonl → decision artifacts
```

## Runtime

- **Engine:** `~/jev-starter/` — `packs.py` is the CLI. Packs live in
  `~/.agents/skills/jev-decision-batch/packs/*.yaml` (propagated to all skill roots).
- **Run a pack:**

  ```bash
  cd ~/jev-starter
  .venv/bin/python label_<x>.py                 # extractor → state.jsonl
  .venv/bin/python packs.py --pack <name> \
      --input artifacts/<x>-state.jsonl \
      --out-dir artifacts/pack-runs/<name> \
      --rate-limit 10                          # optional throttle
  ```

- **Zero-cost wiring check:** add `--simulate` — deterministic mock answers,
  no network, no key, no spend.
- **Evaluate a pack:** `.venv/bin/python evaluate_pack.py --pack <name>
  --golden tests/golden/<name>.golden.jsonl` → accuracy + confusion + $/item.

## Pack schema

```yaml
name: <pack>            # schema_version = jev-batch.v1:<name>.v<version>
version: "1"
extractor: python3 label_<x>.py
artifact: <output-file>
questions:              # one narrow judgment each; never "is this good?"
  <qid>: {type: noul|choice|score, instructions: ..., criteria: ...}
decision:
  kind: sift            # or verdict
  min_scores: {qid: floor}        # sift: score below floor → reject
  reject_nouls: {qid: ceil}       # sift: noul at/above ceil → reject
  min_confidence: 0.5             # sift: below → review band
verdict:                # verdict kind only — weighted composite → bands
  weights: {qid: w}
  max_level: 4
  bands: {ship: 65, fix: 40, kill: 0}
  band_order: [kill, fix, ship]
  veto_nouls: {qid: ceil}         # hard gate → veto_band
  veto_band: reject
  clarity_question: <noul-qid>
  clarity_floor: 0.3
pre_filter:             # host-side drops before any spend
  field: <state-field>; drop_blank: true; min_chars: N
state_max_chars: 32000            # context-rot guard
two_pass:               # optional family→member second call
  choice_question: <choice-qid>   # NOTE: use choice_question — bare `on:` parses as YAML bool
  families: {<choice>: {<questions>}}
```

## Outputs (`--out-dir`)

`clean.jsonl` (keep/verdict rows + answers) · `rejected.jsonl` ·
`review.jsonl` (low-confidence band) · `skipped.jsonl` (prefiltered /
oversized / unknown / budget) · `manifest.json` (counts, live calls, input
tokens, `est_cost_usd`, decision histogram — the audit/rollback record).

## Pack catalog

| pack | corpus | artifact | kind |
|---|---|---|---|
| reviewer | artifact files / SKILL.mds | review-report | sift |
| skill-gate-v2 | skill proposals + roster | create/extend/skip | verdict |
| project-triage | project-health.json | revive/fix/kill | verdict |
| backlog-triage | backlog/upstream/marketplace items | adopt/adapt/reject | verdict |
| sessions | session exports | session-labels | sift |
| crons | Hermes cron jobs | cron-labels | sift |
| drift | per-project session history | project-health | sift |
| findings | validator findings | findings-queue | sift |
| handoffs | session handoffs | handoff-gate | sift |
| harvest | reusable-pattern candidates | harvest-index | sift |
| learnings | lesson candidates | learning-labels | sift |
| projects | project records | project-labels | sift |
| claims | research outputs | claim-extract | sift |
| claims-audit | notes w/ checkable claims | claim-audit | sift |
| content-qa | decks/modules | content-qa | sift |
| outreach | draft messages | outreach-gate | sift |
| subscriptions | subscription candidates | subscription-labels | sift |
| traces | tool-call traces | trace-labels | sift |
| approvals | approval-gate decisions | approval-labels | sift |

## Engine capabilities (jev_batch.BatchRunner)

- Content-addressed atomic cache, crash-resume, `unknown` never replayed
  without `--retry-unknown`.
- Token-bucket `rate_limit` (req/s) + global 429/529 backoff honoring
  Retry-After; bounded in-run throttle retries, then `unknown`.
- `dry_run` mock: per-type deterministic answers, estimated usage — CI-safe.
- `pre_filter` + `state_max_chars`: host drops never touch the cache or API.
- `run_two_pass`: second narrow call only for items landing in a family.
- `build_criteria.py`: generated per-skill `not_for` sibling lists from
  dedup/confusion data → `routing-criteria.json` → router table v2.

## Rules

- One-shot only: extract → label → artifact → done. No per-turn Jev.
- Narrow questions, one check each; never "is this good?"
- Every run emits `manifest.json` with item ids + answers for audit/rollback.
- New corpus = new extractor + new pack YAML. Bump `version` when question
  or verdict semantics change (it re-keys the cache).
- Approval auto-triage stays code-only: `gate_check.py` + `risk-policy.json`.
