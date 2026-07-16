# Scope DAG and Lifecycle

## Paths

| Scope | Ordered path | Terminal state |
|---|---|---|
| quick | P0 → P1 → P2 → P3-lite → P4-lite | terminal; no hypotheses or validation claim |
| standard | P0 → P1 → P2 → P3 → P4 → approval → P5 design | `VALIDATION_PENDING` |
| deep, no code | P0 → P1 → P2 → P3 → P4 → approval → P5 → P7 | terminal after results/refresh |
| deep, code | P0 → P1 → P2 → P3 → P4 → approval → P5 → P6 → P7 | terminal after results/refresh |

P3-lite uses the top three P2 needs without full scoring. P4-lite classifies gaps
only. Standard P5 designs experiments but does not execute or claim validation.
P6 never validates demand and is skipped when no codebase exists.

## Dependencies

P0 is mandatory. P1 requires the audit brief; P2 requires Product Truth; P3
requires market research; P4 requires segments; P5 requires P4 plus user
approval; P6 requires P5 design plus a codebase; P7 requires recorded experiment
results and P6 when applicable. A skipped phase must be recorded with its reason.

## Gate transitions

Use only `GO`, `CONDITIONAL_GO`, `RECYCLE`, or `STOP`. Evidence-limited mode and
designed-only experiments cap every subsequent gate at `CONDITIONAL_GO`. A
terminal standard artifact is analysis-complete and market-validation-pending,
not a validated market decision.
