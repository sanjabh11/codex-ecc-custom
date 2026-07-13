# Audit Governance

ISO 19011:2026-aligned governance: auditor-role separation, conflict of interest, risk-based scope, independent review, human approval thresholds, and operating cadence.

## ISO 19011:2026 Principles Mapping

| Principle | How This Skill Implements It |
|-----------|----------------------------|
| **Integrity** | Findings are evidence-based; no score without a cited source; adversarial review is mandatory |
| **Fair presentation** | Artifacts include negative evidence, contradictions, and limitations — not just supportive findings |
| **Due professional care** | Confidence scoring, pre-gate self-assessment, and "insufficient evidence" outcomes prevent overclaiming |
| **Confidentiality** | Data classification and redaction-before-storage (see state-schema.md); portfolio opt-in required |
| **Independence** | Auditor-role separation (below); load-bearing findings require independent review pass |
| **Evidence-based approach** | Research ledger, provenance registry, evidence grading (HIGH/MEDIUM/LOW), PRISMA-aligned protocol |
| **Risk-based approach** | Audit depth proportional to finding risk; high-reversal findings get maximum scrutiny |

## Auditor-Role Separation

The executing agent must distinguish between two roles during the audit:

### Role 1: Evidence Gatherer
- Conducts research, reads codebase, scores findings
- Produces phase artifacts and confidence scores
- Self-assesses on 5 dimensions before requesting gate review

### Role 2: Gate Reviewer
- Reviews the evidence gatherer's output with fresh context
- Checks for: unsupported claims, missing negative evidence, score inflation, assumption blindness
- For load-bearing findings: must be a **separate pass** (new context window or `ecc-advisor` call)
- Produces gate decision: GO / CONDITIONAL GO / RECYCLE / STOP

### Implementation

- **Standard mode**: Gate review is a self-review with explicit "reviewer hat" framing — the agent must re-read findings as if they were someone else's work
- **Deep mode**: Gate review for Phases 3, 4, 5 must use `ecc-advisor` (if available) or a fresh context pass as the independent reviewer
- **Quick mode**: Gate review is combined (evidence gatherer also reviews) — documented as a governance limitation

## Conflict of Interest (COI)

If the executing agent also built or contributed to the codebase being audited:

1. **Flag COI** in Phase 0 artifact: "Agent has prior contribution history with this codebase"
2. **Mandatory human review** for all high-reversal findings (see below)
3. **Adversarial review strengthened**: all 3 personas must be explicitly hostile to the agent's prior work
4. **Independent review**: if `ecc-advisor` is available, it MUST be used for gate review on Phases 3, 4, 5
5. **Document COI impact**: note which findings might be biased by prior knowledge

## Risk-Based Scope Selection

Audit depth should be proportional to the risk of the findings:

| Risk Level | Finding Characteristics | Audit Response |
|------------|------------------------|----------------|
| **Critical** | Financial impact > $100K, legal/regulatory exposure, high-reversal-cost recommendations | Maximum scrutiny: independent review, human approval, sensitivity analysis, 2+ sources required |
| **High** | Significant roadmap impact, medium financial impact, medium reversal cost | Independent review, adversarial review, 2+ sources for load-bearing claims |
| **Medium** | Moderate roadmap impact, low reversal cost | Standard gate process, 1+ source per claim |
| **Low** | Minor adjustments, low impact, easily reversible | Standard process, codebase evidence sufficient |

## Independent Review Rule

For **load-bearing findings** in Phases 3, 4, and 5:

1. **Standard mode**: Re-read the finding with explicit "is this actually supported?" framing
2. **Deep mode**: Call `ecc-advisor` with the finding and ask "Challenge this finding — what evidence would prove it wrong?"
3. **If advisor unavailable**: Document "independent review skipped — advisor unavailable" and flag the finding for human review
4. **If finding fails independent review**: downgrade evidence grade by one level and seek additional evidence

## Human Approval Thresholds

The following findings **require explicit human approval** before they can be load-bearing:

| Finding Type | Threshold | Action Without Approval |
|-------------|-----------|------------------------|
| Financial impact claims | > $100K projected impact | Finding is non-load-bearing; flag as "requires human validation" |
| Legal/regulatory findings | Any legal or regulatory claim | Finding is non-load-bearing; flag for legal review |
| High-reversal recommendations | Reversal cost rated "High" | Finding documented but not actioned without user sign-off |
| Strategic pivot recommendations | "Change target segment" or "reposition product" | Requires APPROVAL GATE (Phase 4) — user must explicitly approve |
| Data deletion recommendations | "Remove feature" or "delete code" | Requires user confirmation before Phase 6 action |

## Operating Cadence

### Quarterly Strategic Audit (Full)
- **Frequency**: Every quarter (Q1, Q2, Q3, Q4)
- **Scope**: Full 7-phase pipeline (standard or deep)
- **Owner**: Product/positioning lead
- **Output**: Complete artifact set, drift comparison vs prior quarter

### Monthly Drift Signals (Lightweight)
- **Frequency**: Monthly between quarterly audits
- **Scope**: 8-lens scorecard refresh only (no full pipeline)
- **Owner**: PMM or product manager
- **Trigger**: Calendar reminder
- **Output**: 1-page scorecard comparison vs last quarter; if any lens drops ≥ 2 points, trigger immediate quarterly audit

### Weekly/Biweekly Evidence Refresh (Continuous Discovery)
- **Frequency**: Weekly or biweekly
- **Scope**: New market signals, competitor moves, customer feedback scan
- **Owner**: Product trio (PM, designer, engineer)
- **Trigger**: Calendar reminder or automated signal (competitor release, customer interview)
- **Output**: Brief note in `.positioning-audit/evidence-refresh.log` — 1-3 sentences per signal
- **Alignment**: Teresa Torres continuous discovery — weekly customer touchpoints, small research activities, assumption testing

### Drift Trigger Thresholds

| Signal | Threshold | Action |
|--------|-----------|--------|
| Lens score drop | ≥ 2 points from last quarter | Trigger immediate quarterly audit |
| Competitor release | New competitor enters top 3 | Trigger monthly drift signal + evidence refresh |
| Customer feedback shift | > 3 customer signals contradict current positioning | Trigger evidence refresh + Phase 2 light re-run |
| Feature launch | Major feature shipped | Trigger monthly drift signal (does positioning still fit?) |
| Team change | PMM or head of sales departs | Trigger quarterly audit (new owner needs baseline) |

## Audit Program Risk Prioritization

When multiple codebases are in the portfolio, prioritize audit scheduling by risk:

1. **Highest risk**: Codebase with lens score drop ≥ 2 points since last audit
2. **High risk**: Codebase with > 6 months since last audit
3. **Medium risk**: Codebase with major feature launch since last audit
4. **Low risk**: Codebase with stable scores and recent audit (< 3 months)

This ensures audit resources go where positioning drift is most likely.
