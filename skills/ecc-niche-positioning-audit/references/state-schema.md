# State, Privacy, and Migration

## Canonical layout

Persist `.positioning-audit/state.json`, `evidence-corpus.json`, `hypotheses.json`,
`experiments.json`, `research-questions.json`, `artifacts/`, `history/`, and
optional `extras/`. The five JSON schemas are v8 contracts; current instances
must use `schema_version: "v8"`.

State must include audit identity, product context, scope, timestamps, phase,
confidence, evidence-type list, limitations, completed phases, gates, and
experiment counts. State evidence types must equal the corpus types, and the
experiments/hypotheses/evidence documents must carry the same `audit_id`.

## Safe persistence

Redact secrets, access tokens, personal contact data, and unnecessary customer
identifiers. Use stable pseudonymous IDs. Write artifacts and state atomically;
never overwrite a prior artifact when superseding. Keep immutable history when
drift comparison is requested. Portfolio aggregation is opt-in manual output.

## Migration

For a v5–v7 state, run:

```text
python3 scripts/migrate_state.py --input old/state.json --output new/state.json
```

The script converts phase/gate forms, fills v8 lifecycle defaults, drops unknown
legacy fields with a report, validates the output, and never overwrites input.
Migrate before schema validation; do not make the current schemas accept old
instances.
