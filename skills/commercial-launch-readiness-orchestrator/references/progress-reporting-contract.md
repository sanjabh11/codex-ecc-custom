# Progress Reporting Contract

Use this contract for every long-running commercial launch readiness run.

## Trigger Rules

Emit a progress digest:

- after each phase completion
- after every worker wave launch or collection
- every 45 minutes while the run is active
- whenever no meaningful task, worker, evidence, or report status changes for 120 minutes
- immediately before continuing any run that has been active for 20 hours or more

This is a proactive reporting contract plus generated digest command. It is not a hidden daemon.

## Target Accomplishment Matrix

| Lane | Target Weight | Completion Rule |
|---|---:|---|
| Repo Map | 10% | Repo stack, routes, auth, APIs, data, envs, CI, deploy, docs, tests, and proof artifacts are mapped. |
| Security | 15% | P0-P3 findings are mapped to OWASP, NIST SSDF, CISA Secure by Design, and AI/LLM risk frameworks where relevant. |
| Readiness | 15% | Build/test/lint/typecheck/browser/API proof is run or explicitly blocked with evidence. |
| Sellability | 15% | Buyer-visible value, weak claims, onboarding, pricing/pilot readiness, and proof pack are scored. |
| Market Pain Research | 20% | Top 10 buyer pain points, substitutes, willingness-to-pay signals, and source URLs are gathered. |
| Target Customers + Outreach | 10% | Top 10 accounts or segments, decision makers, triggers, outreach angles, and proof assets are ranked. |
| Safe Fix Lane | 10% | Bounded P0/P1 fixes are implemented when mode allows, or approval-gated fix plans are produced. |
| Synthesis + Validation | 5% | Report, launch evidence JSON, validator result, and ECC ledger are complete. |

Use `pass = 100%`, `running = 45%`, `fail = 35%`, and `pending = 0%` as the default task-to-lane progress mapping unless stronger evidence exists.

## Required Digest Sections

| Section | Required Content |
|---|---|
| Accomplished | Completed lanes, evidence collected, files/reports/checks produced. |
| Target Matrix | Lane, target %, current %, status, evidence, confidence. |
| Pending | Remaining tasks, missing evidence, unresolved blockers. |
| Activities Remaining | Count of remaining actions in the current phase and next phase. |
| Current Bottleneck | Exact stuck task/subtask, elapsed time, last update, affected lane. |
| Root Cause | One taxonomy value from the section below. |
| Top 3 Fix Options | Concrete action, tradeoff, expected time saved, risk. |
| Market Synthetic Data | Labeled hypotheses only when real feedback/source evidence is unavailable. |

## Bottleneck Root-Cause Taxonomy

Use exactly one primary root cause:

- `context overload`
- `ambiguous requirements`
- `dependency issue`
- `testing loop`
- `search/exploration`
- `decision paralysis`
- `tool/execution delay`
- `worker failure`
- `evidence gap`

## Synthetic Market Data Rules

Synthetic market or customer data is allowed only as a planning aid when the app has not launched and real customer feedback is unavailable.

Rules:

- Label every synthetic item as `hypothesis`.
- Record why it was created and what real source would validate or refute it.
- Do not use synthetic-only evidence to mark `commercial-ready`.
- Synthetic data can support `blocked`, `pilot-only`, or `sellable-with-caveats` planning language only.
- Prefer real source evidence from buyer interviews, reviews, job posts, analyst reports, competitor docs, support forums, procurement signals, or public filings whenever available.
