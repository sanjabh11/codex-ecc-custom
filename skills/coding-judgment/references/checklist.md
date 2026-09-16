# Coding Judgment Checklist

## Think Before Coding

- What exact user outcome is being requested?
- What repo facts have been inspected?
- What assumptions remain after inspection?
- Is there a safer bounded default?
- Is clarification required because the wrong choice would be expensive or risky?

## Simplicity First

- Can the goal be met by editing existing code instead of adding a new abstraction?
- Is this flexibility requested, or speculative?
- Is the error handling for a real failure mode?
- Would a senior maintainer call the change too broad for the request?

## Surgical Changes

- Does every changed line trace back to the user goal?
- Are unrelated formatting, cleanup, renames, and dependency changes avoided?
- Are dirty worktree changes preserved?
- Are new files justified by repeated logic, deterministic reliability, or established repo patterns?

## Diagnosis Loop

1. Reproduce: find the failing command, route, test, screen, or log.
2. Minimize: isolate the smallest file, input, state, or dependency boundary.
3. Hypothesize: write down the likely cause and what would disprove it.
4. Instrument: inspect logs, add temporary diagnostics only if needed, or run targeted commands.
5. Fix: make the smallest confirmed correction.
6. Regression-test: prove the reported issue and adjacent behavior.

## Proof Buckets

- Hosted/live: verified in the deployed or live environment.
- Local: verified on this machine.
- Repo artifact: supported by files, tests, docs, or static analysis only.
- Candidate/shadow: implemented but not promoted or proven in the target environment.
- Roadmap: planned but not implemented.

Never present a lower proof bucket as a higher one.

## Final Handoff

Include:

- changed files
- verification commands and outcomes
- unresolved blockers
- proof bucket for any important claim
- next smallest useful step

## 1-5 Judgment Scorecard

Score each lane from 1 to 5 before calling a non-trivial coding change complete.

| Lane | 1 | 3 | 5 |
|---|---|---|---|
| Repo truth | Acts mostly from assumptions | Reads obvious files but misses adjacent contracts | Inspects the real files, tests, config, runtime, or docs needed for the claim |
| Simplicity | Adds speculative abstractions | Uses a workable but slightly broad approach | Chooses the smallest viable lever that fits existing patterns |
| Surgical scope | Touches unrelated files or formatting | Mostly scoped with minor incidental churn | Every changed line traces to the user goal |
| Diagnosis | Fixes before root cause evidence | Uses partial reproduction or plausible logs | Reproduces, narrows, hypothesizes, fixes confirmed cause, and regression-tests |
| Proof | Claims success without matching checks | Runs some checks but leaves proof buckets vague | Reports exact checks, failures, not-run reasons, and proof buckets |

Hold the change when any lane scores below 3 for a Tier 1 task, or below 4 for security, deployment, production, payment, migration, or launch-critical work.
