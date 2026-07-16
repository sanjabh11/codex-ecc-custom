# Scoring and Outcome Rubric

## Decision confidence

Decision confidence is a deterministic decision aid, not statistical confidence:

```text
composite = quality(0..30) + coverage(0..25) + consistency(0..20)
          + counter(0..15) + validation(0..10)
```

The state and artifact composite must equal the five subscore sum. Keep iteration
count and improvements. Bands are High (85–100), Moderate (60–84), Low (40–59),
and Critical (<40), but evidence mode and lifecycle gates can cap the decision.

## Evidence bundles

Every load-bearing claim has a bundle of evidence IDs. The bundle is satisfied by
at least one non-stale HIGH item or two non-stale MEDIUM items. A zero threshold
disables that branch; it never satisfies a claim by itself. LOW evidence cannot be
the sole support. Unknown evidence IDs, stale items, incorrect `satisfied` flags,
and supported hypotheses without a satisfied bundle fail validation.

## Unified outcome matrix

| Condition | Decision | Meaning |
|---|---|---|
| Target confidence and required evidence | GO | Advance only within path |
| Partial evidence, designed experiments, or limitations | CONDITIONAL_GO | Continue with explicit queue |
| Contradiction, stale proof, or insufficient coverage | RECYCLE | Re-research or re-test |
| Fundamental assumption disproven/no viable segment | STOP | Reframe |

No experiment design adds validation points. With zero executed experiments,
validation is exactly zero and the lifecycle is `VALIDATION_PENDING`.
