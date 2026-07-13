# Scoring Rubric

Deterministic scoring formulas, confidence bands, ICP weight configuration, uncertainty model, and "insufficient evidence" handling.

## Confidence Score Formula

The composite confidence score is a weighted average of 5 subscores (0-100 each):

```
composite = (evidence_density * 0.30) + (adversarial_survival * 0.20) + (assumption_risk * 0.20) + (coverage_completeness * 0.15) + (triangulation_strength * 0.15)
```

### Subscore Definitions

| Subscore | Weight | Calculation | Target |
|----------|--------|-------------|--------|
| **evidence_density** | 30% | `(findings_with_2plus_sources / total_findings) * 100` | ≥ 80 |
| **adversarial_survival** | 20% | `(findings_survived_adversarial / total_findings) * 100` | ≥ 70 |
| **assumption_risk** | 20% | `100 - (unverified_load_bearing_assumptions * 20)` — clamped 0-100 | 100 (0 unverified) |
| **coverage_completeness** | 15% | `(perspectives_with_findings / applicable_perspectives) * 100` | 100 |
| **triangulation_strength** | 15% | `(findings_triangulated_2plus_sources / total_findings) * 100` — phases 3-5 only; phases 0-2 use evidence_density weight instead | ≥ 80 |

### Missing Data Handling

- **Missing subscore**: treated as 0, not excluded from average
- **≥ 2 missing subscores**: automatic "insufficient evidence" outcome — do not compute composite
- **Zero findings in phase**: evidence_density = 0, coverage_completeness = 0 → triggers RECYCLE
- **All findings from single source**: evidence_density = 0 → triggers improvisation loop

### Confidence Bands

| Band | Composite Score | Action |
|------|----------------|--------|
| **Proceed** | ≥ 95 | Request gate review |
| **Improvisation loop** | 80-94 | Target specific gap, re-research/re-analyze, re-score. Loop until ≥ 95 or 3 iterations max |
| **Extended loop** | 60-79 | Re-examine assumptions, re-run adversarial with fresh personas, seek additional sources. Loop until ≥ 95 or 3 iterations max |
| **RECYCLE** | < 60 | Do not request gate. Restart phase with different approach. Escalate to user if second attempt also < 60 |
| **Insufficient evidence** | N/A (triggered by missing data) | STOP — return qualitative ranking with "insufficient evidence" label. Do not proceed to gate |

## ICP Scoring — Configurable Hypotheses

The ICP 4-dimension weights are **hypotheses, not validated constants**. Each must have rationale, sensitivity test, and minimum viable evidence.

### Default Weights (Hypotheses)

| Dimension | Default Weight | Rationale | Sensitivity |
|-----------|---------------|-----------|-------------|
| **Firmographic** | 40% | Industry/company size is the strongest predictor of B2B purchase fit | ±10% weight change should not change top-3 ranking; if it does, flag instability |
| **Behavioral** | 25% | Content engagement and hiring signals indicate active evaluation | ±10% weight change should not change top-3 ranking |
| **Intent** | 20% | Category research and RFP signals indicate near-term purchase | ±10% weight change should not change top-3 ranking |
| **Technographic** | 15% | Stack match enables integration but is not a primary purchase driver | ±10% weight change should not change top-3 ranking |

### Sensitivity Test (Mandatory in standard/deep)

1. Score all segments with default weights
2. Re-score with each weight ±10% (4 variations)
3. If top-3 ranking changes in any variation: flag as "ranking unstable" and document which weight causes instability
4. If ranking is stable across all variations: report "ranking stable within ±10% weight sensitivity"

### Scoring Bands (Hypotheses)

| Band | Default Threshold | Falsification Criterion | Action |
|------|------------------|------------------------|--------|
| **Outreach trigger** | 70+ | If < 50% of 70+ segments convert to meetings within 30 days, threshold is wrong | Trigger outreach |
| **Nurture** | 40-69 | If > 50% of 40-69 segments convert, threshold is too high | Nurture sequence |
| **Disqualify** | < 40 | If any < 40 segment later converts, disqualifier is too aggressive | Disqualify |

### Minimum Viable Evidence Per Segment

Before a segment can be ranked in the top 3:
- ≥ 2 independent sources for the pain point (not duplicating same study)
- ≥ 1 source for market size/reachability
- ≥ 1 source for willingness-to-pay signal
- ≥ 1 negative evidence search completed (actively searched for reasons this segment is bad)

### "Fewer Than Three Viable Segments" Outcome

If fewer than 3 segments meet the minimum viable evidence threshold:

1. **Do not fabricate segments** to reach 3
2. Report the viable segments found (0, 1, or 2)
3. Label as "insufficient evidence for full top-3 ranking"
4. Recommend actions:
   - 0 viable: "Market research insufficient — expand search criteria or reconsider product-market fit"
   - 1 viable: "Single segment identified — consider beachhead focus before expanding"
   - 2 viable: "Two segments identified — proceed with 2 rather than forcing a third"
5. Gate 2 outcome: CONDITIONAL GO (not STOP) — proceed with available segments, flag the gap

## Uncertainty Model

### Confidence Intervals

Every ICP score must be reported with a confidence interval:

```
ICP_score ± margin

margin = (100 - evidence_density_subscore) * 0.1
```

Example: ICP score 78, evidence_density = 80 → margin = (100-80)*0.1 = 2.0 → report "78 ± 2"

### Ranking Stability

Report whether the top-3 ranking is stable:
- **Stable**: No position change across all sensitivity variations
- **Unstable**: Position change in any variation — document which positions swapped and why

## Positioning Lens Scoring (Phase 4)

Each of the 8 lenses is scored 1-10 with a one-sentence evidence line. The scoring is qualitative but must be reproducible:

| Score Range | Label | Criteria |
|-------------|-------|----------|
| 1-3 | Failing | Lens absent or actively working against positioning |
| 4-6 | Present but soft | Inconsistent, underproven, or contradicted |
| 7-8 | Working | Consistent, evidenced, defensible against sharp competitor |
| 9-10 | Canonical | Shaping how the market talks about the product |

### Reproducibility Rule

Two independent reviewers scoring the same evidence should arrive within ±1 of each other. If scores differ by > 1, the evidence is insufficient for that lens — flag as "contested" and seek additional evidence.

## Pre-Gate Self-Assessment

5 dimensions, 1-5 each, composite 5-25:

| Dimension | 1 (Ad Hoc) | 3 (Periodic) | 5 (Continuous) |
|-----------|------------|--------------|----------------|
| Documentation completeness | No structure | Key findings documented | All findings with citations |
| Evidence currency | Stale/single source | Multiple, not cross-validated | Multiple independent, current |
| Coverage breadth | Only obvious areas | Main areas, some blind spots | All perspectives, blind spots listed |
| Traceability | Cannot trace to source | Key findings trace | Full trace + forward to recommendations |
| Issue resolution | Open questions unaddressed | Most addressed | All addressed or deferred with rationale |

**Thresholds**: standard/deep ≥ 15/25; quick ≥ 12/25. Below threshold = automatic RECYCLE.
