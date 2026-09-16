# Code Optimization Contract

Use this contract whenever a commercial launch audit proposes, plans, implements, retries, or reviews repo-side code changes.

The goal is not a theoretical global optimum. The goal is the smallest safe verified implementation that satisfies the launch gap, fits the repo, and does not add unnecessary code surface.

## Policy Modes

| Mode | Required Behavior |
|---|---|
| `off` | No extra optimization review task. Normal `coding-judgment` still applies. |
| `safe` | Compare simple options and choose the smallest safe change before implementation. |
| `strict` | Require variant comparison, rejected-variant ledger, focused verification, and code-optimization review for any code change. |
| `measured` | Use `strict` plus benchmark or performance measurements when latency, throughput, memory, bundle size, cost, or build/test duration is involved. |

Default mode: `strict`.

## Pre-Implementation Gate

Before editing code, record:

| Field | Requirement |
|---|---|
| Acceptance check | Exact behavior, test, command, or proof that makes the gap resolved. |
| Repo pattern | Existing file, function, component, helper, config, or test pattern being reused. |
| Variants considered | At least no-code/defer, config-only, test/doc-only, minimal code patch, and broader refactor when relevant. |
| Chosen variant | The smallest safe variant that satisfies the acceptance check. |
| Rejected variants | Why larger or riskier options were rejected. |
| Verification plan | Focused commands, tests, browser/API checks, or not-run reasons. |

## Minimality Rules

- Prefer no-code, config-only, test-only, doc-only, or existing helper reuse when that actually resolves the gap.
- Do not introduce a dependency, abstraction, generated file, framework change, schema change, global state, or broad refactor unless the smaller options fail by evidence.
- Match current repo conventions even when a different style is attractive.
- Keep writes bounded to the gap and preserve unrelated dirty worktree changes.
- Split independent fixes only when their write surfaces do not collide.

## Measured Optimization

Use measured mode only when there is a real metric:

- page or API latency
- throughput
- memory
- bundle size
- cost per run
- build/test duration
- database query time

Measured mode requires a baseline, a correctness gate, one-variable variants, repeated or explained delta, and rollback path. Use `benchmark-optimization-loop` for deeper measured loops.

## Reviewer Task

Add a `code-optimization-reviewer` review task for the safe-fix lane when optimization policy is not `off`.

Reviewer prompt requirements:

- identify unnecessary code, files, dependencies, abstractions, or broad refactors
- check that the smallest viable variant was chosen
- verify that tests/checks map to the acceptance criterion
- challenge missing rollback or proof-bucket boundaries
- reject code changes that cannot be tied to a launch gap

## Evidence JSON Fields

When files are changed, final evidence must include:

- `implementation_decisions`: chosen variant, acceptance check, proof, changed files, and tests run
- `rejected_variants`: options rejected with reason and tradeoff
- `code_optimization_reviews`: reviewer verdict, minimality score, evidence, and remaining risk

Audit-only runs may keep those arrays empty.

## Stop Gates

Stop before:

- dependency installation without evidence
- broad refactor or architecture migration
- generated code bulk additions
- production deploys, migrations, data deletion, credential changes, or payment changes
- code changes that cannot be verified locally or through existing proof buckets
