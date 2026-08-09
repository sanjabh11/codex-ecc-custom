# Pir Panjal repair — Graph-engineer cross-verification record

Date: 2026-08-09

## Scope

This is a read-only architecture verification of the supplied Graph-engineer
explanation against the current Avalanche checkout. It does not certify a
deployment and does not modify the Avalanche repository.

The attached graph itself is also treated as an artifact under review. It is a
Mermaid/prose explanation, not a schema-valid v1.1 JSON graph.

## Results

- Focused Avalanche tests: `PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 pytest -q` on
  the decision-record loader, POC record, Modal poller, release orchestrator,
  registry root, and release gate tests: **161 passed, 1 failed**. The failing
  test is the intended-valid POC bundle fixture, which still uses the old
  Nepal/24-hour values after the consumer contract was strengthened.
- Decision-record/POC subset: **27 tests passed** under `unittest`.
- YAML syntax parse: both referenced workflows parse successfully.
- Selected relevant diff hygiene: `git diff --check` clean.
- The Avalanche checkout remains dirty and includes untracked repair files;
  source/test proof is therefore local and provenance-limited.

## Boundary matrix

| Boundary | Finding | Proof level |
|---|---|---|
| Workflow producer | POC derives scope and passes external registry/decision hashes | verified-local source + tests |
| Release consumer | Shared `poc_scope_contract.py` binds decision record, result, artifact manifest, and forecast semantics | source verified; suite red on stale positive fixture |
| Forecast consumer | Consumer-side horizon/ensemble/region/band rebinding is present in the shared contract | architecture present; independent tamper regression still needed |
| Modal submission/terminal identity | Independent run/compute IDs and required top-level fields are enforced | verified-local source + tests |
| Modal poll URL | Provider `call_id='../escape'` was accepted and interpolated into `.../result/../escape` in a controlled probe | architecture gap |
| POC binding parser | `int('not-an-integer')` raises `ValueError` from the shared contract instead of a controlled `PocScopeError` | architecture gap |
| Decision-record decoding | Invalid UTF-8 becomes `DecisionRecordError`; adversarial tests pass | verified-local source + tests |
| Human gate | Native SNOWPACK, live Modal, DGRE approval, and independent labels remain unavailable | blocked / runtime-unverified |

## Graph-claim sanity findings

| Claim in the explanation | Finding | Status |
|---|---|---|
| Three independent repair tracks | Diagram contains workers A/B/C plus independent D before the second join | artifact inconsistency |
| Every reviewer failure caps at three rounds and escalates | Explicit exhaustion edges are shown for A/B/C only; D and the later semantic reviewer have no drawn exhaustion edge | architecture gap |
| Full verification is 270 tests | No reproducible 270-test command/result was supplied; current focused evidence is 161/162 and 27/27 | unverified claim |
| Every join carries a structured artifact | Referenced artifacts are not represented in a schema-valid machine-readable graph | artifact-only |

## GLM handoff

1. Repair the intended-valid POC fixture to match the canonical decision ID,
   ensemble, Pir Panjal/middle manifest, and 48-hour forecast contract; keep
   the strengthened consumer gate intact.
2. Add a consumer-side tamper test for a self-consistent 72-hour or multi-member
   forecast; it must fail against the external decision record.
3. Validate/encode Modal `call_id` before constructing the poll URL; add path,
   query, fragment, and overlength regression cases.
4. Convert malformed POC binding types into structured gate errors and add
   no-traceback tests.
5. Re-run the focused suite and preserve separate local, CI-host, remote, and
   human-gate evidence.
6. Convert the graph explanation to a v1.1 JSON graph, correct the track count,
   add exhaustion routes for D/R2, and validate it with `validate_graph.py`.

Until these are complete, use the claim:

> The repair has locally verified boundary logic, but its focused suite is not
> green: one positive POC fixture is stale and two input-hardening follow-ups
> remain.

Do not use “fully verified,” “production-ready,” or “scientifically validated.”
