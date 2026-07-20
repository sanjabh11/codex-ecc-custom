# Weekly Marketing Flywheel — Runbook

## Quick Start

### Dry Run (no artifacts written)

```bash
# Career Automation Insights Engine
python3 skills/ecc-weekly-marketing-flywheel/scripts/validate_weekly_marketing_flywheel.py

# Verify Hormozi is hardened
python3 skills/ecc-hormozi-funnel/scripts/validate_skill.py
python3 /Users/sanjayb/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/ecc-hormozi-funnel
```

### Draft Run (artifacts written locally, no external writes)

For each repository, run the three-stage chain:

#### 1. Career Automation Insights Engine

```
Objective: Select one career-coach proof-pack CTA and one message variant
that can increase sample-report requests.
Repository: /Users/sanjayb/career-automation-insights-engine-fresh
Mode: draft-only
```

Stage 1: Run `ecc-niche-positioning-audit` with `--scope quick` on the repo.
→ Output: `artifacts/marketing/weekly/career-automation/2026-07-20/positioning-audit-export.json`

Stage 2: Run `ecc-hormozi-funnel` in weekly mode:
```bash
python3 skills/ecc-hormozi-funnel/scripts/generate_weekly_artifacts.py \
  artifacts/marketing/weekly/career-automation/2026-07-20/positioning-audit-export.json \
  artifacts/marketing/weekly/career-automation/2026-07-20/funnel/ \
  2026-07-20
```
→ Output: 1 offer, 3 hooks, 7-day calendar, 3 funnel fixes, 1 proof update

Stage 3: Run `ecc-growth-experiment-loop` to register one experiment.
→ Output: `experiment-registration.json`

#### 2. Canada Energy Intelligence Platform

```
Objective: Select one consultancy proof-pack offer and one LinkedIn/intake experiment.
Repository: /Users/sanjayb/minimax/canada-energy-dashboard
Mode: draft-only
```
Same three-stage chain. Expect `evidence_limited: true` and `unavailable_components: [analytics, search_console]`.

#### 3. codex-ecc-custom

```
Objective: Select one skill-trigger or scenario-correction experiment that reduces operator effort.
Repository: /Users/sanjayb/codex-ecc-custom
Mode: draft-only
```
Same three-stage chain. Use deterministic or transcript evidence only.

#### 4. Strategic Intelligence Platform

```
Objective: Select one enterprise or public-sector pilot wedge and one reviewer-workflow experiment.
Repository: /Users/sanjayb/minimax/strategic-intelligence-platform
Mode: draft-only
Research depth: standard
```
Same three-stage chain. Keep geopolitical forecasts governed.

#### 5. Avalanche Insight Hub

```
Objective: Select one DRDO/DGRE scientist-collateral improvement and one validation-workflow uptake experiment.
Repository: /Users/sanjayb/avalanche-insight-hub
Mode: dry-run
```
Same three-stage chain. Experiment may be unavailable due to safety gates.

## Following Week

Pass `experiment-registration.json` to `ecc-closed-loop-analytics` for readback:

```
Decision: "Did the proof-pack CTA variant increase sample-report requests?"
Primary metric: sample-report request rate
Attribution window: 7 days
```

## Safety Rules

- **Do NOT publish or send anything from this workflow.**
- No automatic external writes, sends, enrollments, or payments.
- No fabricated claims or unsupported evidence.
- Never claim market validation, revenue, traction, scientific validity,
  official operational use, or forecast accuracy from local artifacts.
- Missing credentials return `unavailable` (not error or empty string).
