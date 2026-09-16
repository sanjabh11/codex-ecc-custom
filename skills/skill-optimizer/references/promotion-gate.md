# Promotion Gate

## Modes

`strict-improve`

- Promote only when the candidate score is strictly higher than the baseline.
- Use for deliberate skill optimization.

`no-regression`

- Promote when the candidate score is at least as high as the baseline and no previously passing scenario fails.
- Use for maintenance, copy edits, trigger metadata updates, and reference cleanup.

## Reject

Reject or hold the candidate when:

- quick validation fails
- evidence schema is invalid
- scenario results are missing for core behavior
- `summary.score` or pass/fail totals do not match scenario results
- the candidate evidence removes any baseline scenario
- a previously passing scenario regresses under `no-regression`
- supportive, neutral, and competing prompt coverage is missing for trigger-sensitive skills
- the improvement is only self-reported and not evidence-backed
- the change duplicates an adjacent skill instead of improving this one

## Report

Every comparison report should include:

- baseline score
- candidate score
- pass/fail totals
- missing baseline scenario IDs
- added scenario IDs
- regressed scenario IDs
- newly passing scenario IDs
- blocking reasons
- decision: `promote`, `hold`, or `reject`
- next scenario or edit to try
