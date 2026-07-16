# Research Protocol

## Evidence hierarchy

Prefer direct first-party customer or commercial evidence for buyer claims;
official/primary sources for market and regulatory facts; reputable secondary
sources for context; internal beliefs and inferred claims only as hypotheses.
Record `evidence_id`, source, source tier, timestamp, grade, confidence,
provenance, authority tier, `checked_at`, expiry, URL health, bias, and a concise
content summary. A source URL is not proof that the underlying claim is true.

## Question tree

For each phase, record a root question, sub-questions, required source type,
queries run, sources found, coverage (`covered`, `partial`, `uncovered`), bias,
counter-evidence result, contradiction status, and saturation. Use at least:

| Scope | Tree depth | Sources | Counter-evidence passes |
|---|---:|---:|---:|
| quick | 2 levels | 3 unique | 1 |
| standard | 3 levels | 5 unique | 2 |
| deep | 4 levels | 8 unique | 3 |

## Saturation and falsification

Stop only when every required level is covered, the source minimum is met,
repetition has occurred for the scope stop rule, and the counter-evidence passes
produce no unresolved contradiction. A contradiction is recorded even when the
team chooses a working interpretation. Unresolved contradictions block GO.

## Bias and claim handling

Label selection, self-report, survivorship, confirmation, recency, availability,
sponsorship, and other bias. Separate observed fact, sourced claim, hypothesis,
and inference. Never upgrade an inference because several copies repeat it.
Negative evidence and missing data are explicit evidence gaps.

## Research ledger minimum

Each state `research_log` entry contains `query_id` (`Q-###`), query text, phase,
source IDs/URLs, `saturation_reached`, contradiction status, counter-evidence,
and timestamp. Each final claim cites evidence IDs and the query IDs that support
and challenge it.
