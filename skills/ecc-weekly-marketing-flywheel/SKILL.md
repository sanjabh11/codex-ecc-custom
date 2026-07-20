---
name: ecc-weekly-marketing-flywheel
description: >-
  Composite skill chaining three highest-leverage marketing skills into a single
  weekly workflow: positioning-audit → hormozi-funnel → growth-experiment-loop.
  Produces a seven-day evidence-backed marketing packet: 1 offer, 3 hooks,
  7-day content slice, 3 funnel fixes, 1 experiment registration, 1 proof-library
  update. Default mode is draft-only — no external writes, sends, or credential use.
  TRIGGER when: "weekly marketing", "marketing flywheel", "weekly GTM packet",
  "weekly marketing workflow", "marketing chain", "positioning to experiment",
  "weekly funnel build", "seven-day marketing packet".
  DO NOT TRIGGER when: no repository context is available, or the task is a
  single-asset request (use the individual skill instead).
---

# ecc-weekly-marketing-flywheel

Composite skill that chains three ECC marketing skills into a single weekly
workflow. Each stage consumes the output of the previous stage, producing
an evidence-backed marketing packet for one repository.

## Chain Architecture

```
Stage 1: ecc-niche-positioning-audit (bounded, quick/standard)
  → produces positioning-audit-export.json
Stage 2: ecc-hormozi-funnel (weekly mode)
  → consumes positioning-audit-export.json
  → produces offer.json, hooks.json, content-calendar.json,
    proof-library.json, funnel-audit.json
Stage 3: ecc-growth-experiment-loop
  → consumes positioning decision + funnel artifacts
  → produces experiment-registration.json
```

**`ecc-closed-loop-analytics`** is the following-week readback step — NOT in
the same-week chain. It requires an evidence window that has not yet elapsed.

## Required Inputs

| Parameter | Type | Required | Description |
|---|---|---|---|
| `repository` | string (abs path) | yes | Target repository path |
| `objective` | string | yes | One business question for the week |
| `week` | string (YYYY-MM-DD) | yes | Week start date |
| `mode` | enum | yes | `dry-run` or `draft-only` |
| `horizon_days` | integer | no | Default: 7 |
| `research_depth` | enum | no | `quick` or `standard` (default: `quick`) |
| `existing_positioning_export` | string (path) | no | Reuse existing audit if valid |

## Output Path

```
artifacts/marketing/weekly/<repo-slug>/<week>/
```

## Output Files

| File | Source stage | Content |
|---|---|---|
| `run-manifest.json` | Composite | Run parameters, stages, timestamps |
| `positioning-decision.md` | Stage 1 | Human-readable positioning summary |
| `positioning-audit-export.json` | Stage 1 | Machine-readable audit with evidence corpus |
| `funnel/offer.json` | Stage 2 | 1 evidence-backed offer |
| `funnel/hooks.json` | Stage 2 | 3 ranked evidence-cited hooks |
| `funnel/content-calendar.json` | Stage 2 | 7-day content/action slice |
| `funnel/proof-library.json` | Stage 2 | 1 proof-library update |
| `funnel/funnel-audit.json` | Stage 2 | 3 prioritized funnel fixes |
| `experiment-registration.json` | Stage 3 | 1 falsifiable experiment with guardrails |
| `evidence-ledger.json` | Composite | All evidence IDs cited across stages |
| `unavailable.json` | Composite | List of unavailable integrations/tools |
| `approval-required.md` | Composite | Human-readable approval gate |
| `hashes.json` | Composite | SHA-256 of each output file |

## Behavioral Rules

1. **Prefer existing positioning export.** If `existing_positioning_export` is
   provided and valid, skip Stage 1 and reuse it.
2. **Evidence traceability.** Pass only evidence IDs from the positioning export
   into Hormozi artifacts. Reject unknown IDs.
3. **One experiment.** Register exactly one experiment per weekly run.
4. **Draft-only by default.** Never send, publish, enroll, write CRM data,
   charge payment, or use credentials. Mode must be explicitly set to
   `draft-only` or `dry-run`.
5. **Missing tools → unavailable.json.** Missing analytics, Search Console,
   CRM, or advisor access returns `unavailable.json` with the missing
   component name and reason.
6. **No fabricated claims.** Never claim market validation, revenue, traction,
   scientific validity, official operational use, or forecast accuracy from
   local artifacts.
7. **No external writes.** No `requests.post`, no CRM API calls, no email sends,
   no social media publishing. All outputs are local files only.
8. **Preserve dirty worktree.** Write only to `artifacts/marketing/weekly/`.
   Never modify, stage, or revert unrelated files.

## Repository Profiles

See `references/repo-profiles.md` for per-repository objectives, evidence
boundaries, and safety gates.

## Evidence Contract

See `references/evidence-contract.md` for the evidence chain specification
between stages.

## Dependency Gating

- Stage 1 requires: repository path, objective, research_depth
- Stage 2 requires: valid `positioning-audit-export.json` from Stage 1
- Stage 3 requires: positioning decision + at least one funnel artifact
- If any stage's prerequisites are unmet, write `unavailable.json` and stop

## Platform Compatibility

This skill is Codex-native. It does not require Claude-only slash commands,
hooks, or MCP servers. All three chained skills have Codex-compatible
frontmatter and `agents/openai.yaml` files.

## Safety Gates

- No automatic external writes (no network calls, no CRM, no email)
- Missing credentials return `unavailable` (not error or empty string)
- No fabricated scarcity, deadlines, guarantees, or prices
- Evidence IDs must be traceable to the positioning audit corpus
- Dirty worktree files must be preserved
