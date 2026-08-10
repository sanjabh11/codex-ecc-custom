# Graph-engineer core — current architecture and release gate

## Decision

The Graph-engineer package is locally verified as a design-time graph validator
with a strict, content-bound pre-run gate and schema-validated evidence
recorder. It is not a graph executor, process supervisor, authenticated host
runtime, or production-ready globally auto-revocable platform.

This artifact is generated from the frozen snapshot at
`.phase-loop/graph-engineer-pilots/graph-engineer-audit-snapshot.json`.

## Current provenance

| Item | Current evidence | Proof level |
|---|---|---|
| UTC snapshot | `2026-08-09T23:30:54.332750Z` | verified-local |
| Checkout | `/Users/sanjayb/codex-ecc-custom`, HEAD `f8fe020c404bb46f625845928962f2ef78c8afce` | verified-local |
| Git status | 75 tracked/staged entries; 67 collapsed untracked; 397 full untracked | verified-local |
| Package inventory | 49 content-hashed files, recorded in the snapshot | verified-local |
| Canonical graph | `pir-panjal-repair-graph-v1.1.json`, SHA-256 `61d6fa004ad129f99cb6e5d94e8fcbc806384b1b59bdf7e45fd360cf0315248d`, committed in `f8fe020` | verified-local |
| Graph schema | SHA-256 `6258d6573685dce15070a3a655c55afd52eca4fc2a07e4508078fd2585687a7d` | verified-local |
| Node schema | SHA-256 `7c12d8cc23b56025b54b5477b8a6e42932140b03d65d9376efae81e3d26c9101` | verified-local |
| Activation policy | SHA-256 `1de37772fbac93dfde69634e52cfe3732899a37ffd581de9273ea605dbcf18fd` | verified-local |
| Activation policy schema | SHA-256 `402fbeff498a0b82554d4c9f44ffb389863021256445b0fd288448f0323f3208` | verified-local |
| Validator | SHA-256 `bc5b86e31efd737e3ad6c00ecc8042f25097c612a6e350cfdf2aedd41988942f` | verified-local |
| Runtime gate | SHA-256 `d44b8d0bb109e6835bcc3ca883180647630ddf9a1d3341ff784d3a27a0f6e9fc` | verified-local |
| Evidence recorder | SHA-256 `98c0ecca8c31f4351b189b0b792966c82c2cdc3fcc7e05fbad7843beed031d2c` | verified-local |
| Shared format checker | SHA-256 `be48b2d43ef0f597b3e20133431902dde3875bdc25c0a68d9506b2b1cca77344` | verified-local |
| Dependency contract | `requirements.txt` SHA-256 `0de2bef24e72c35423c6bd81d388e75c1a30da1bc3a1ab05fd8213ecf5aa1b8c` | verified-local |
| Runtime policy | SHA-256 `2f691500c3e61a646863f9d43f2898dfc468e2355f0ca9cfe0713650841b07d1` | verified-local |
| Disk state | Snapshot captured the local filesystem state; current free space remains an operational risk | verified-local / operational risk |

The complete hash inventory and raw command outputs are authoritative only in
the JSON snapshot; this table is a navigable summary.

## Phase completion

| Phase | Architecture outcome | Status |
|---|---|---|
| P0 | One command-driven provenance snapshot owns status, timestamp, hashes, disk, and results | verified-local |
| P1 | `pytest` and `unittest discover` execute the complete suite; all positive fixtures pass | verified-local |
| P2 | v1/v1.1 semantics, conditional v1.1 fields, local schema bundle, standalone node schema, strict formats | verified-local |
| P3 | Exact v1.1 reviewer binding, conservative typed-port compatibility, clean malformed-input boundaries, joins, budgets | verified-local |
| P4 | Mandatory manifest, runtime package/content hash, validator/policy/host identity binding, unknown-tool block | verified-local |
| P5 | Node-aware evidence lifecycle, content-bound review artifacts, graph/run binding, approval binding, schema validation, redaction, locking, completion gate | verified-local |
| P6 | Shared activation metadata and seven discovery paths; host activation remains metadata-only | verified-local / host-unverified |
| P7 | Bounded adversarial and portability coverage, no-traceback checks, diff hygiene | verified-local |

## Frozen verification ledger

| Command | Result | Proof level |
|---|---:|---|
| `python3 -m pytest -q -p no:cacheprovider skills/graph-engineer/tests` | 53 passed, 65 subtests, exit 0 | verified-local |
| `python3 -m unittest discover -s skills/graph-engineer/tests -p 'test*.py'` | 53 tests, OK, exit 0 | verified-local |
| `python3 skills/graph-engineer/tests/test_validate.py` | 23/23, exit 0 | verified-local |
| `python3 skills/graph-engineer/tests/test_triggers.py` | 22/22, metadata-only, exit 0 | verified-local / host-unverified |
| Canonical v1.1 graph validation | 678 checks passed, 0 failed, 0 warnings, exit 0 | verified-local |
| `git diff --check -- skills/graph-engineer` | exit 0 | verified-local |
| `python3 -S` validator probe | nonzero, clean fail-closed `jsonschema_available` result | verified-local |
| Standalone node schema probe | validates a v1 node without a dangling relative `$ref` | verified-local |

## Advisor cross-verification and second remediation

The independent `ecc-advisor` review was run against the committed core and
fresh probes. It identified two local false-greens that the prior handoff had
not tested:

| Finding | Fresh evidence | Remediation | Proof level |
|---|---|---|---|
| Reviewer `pass` could be recorded without a report or digest | Recorder accepted a bare reviewer event with exit 0 | Review events now require an evidence-root-contained JSON report, exact SHA-256, schema validation, reviewer binding, and status/result agreement | verified-local |
| Constrained object ports passed when only `type` matched | `worker_only` source schema to `reviewer_only` destination schema exited 0 | Typed-port relation is now conservative: exact/equal references, safe unconstrained destinations, or proven required/property compatibility; unknown relations fail | verified-local |
| Same run could mix graph identities | Existing JSONL was filtered by run ID without comparing the current graph hash | Same-run mixed graph hashes are rejected under the append lock | verified-local |
| Terminal successful attempts could be reopened | A second `pass` attempt was accepted before remediation | Passing/skipped nodes cannot reopen unless an explicit failed review opens one bounded retry; failed reviews require a newer worker attempt | verified-local |

The advisor also confirmed that the manifest remains unsigned and that no graph
executor exists. Those are explicit residual architecture boundaries, not
claims of local completion.

## Remaining gaps and gates

| Gap | Severity | Why it remains | Next action |
|---|---|---|---|
| Working tree remains dirty outside the scoped core commit | Medium | Other user changes remain in the checkout | Keep unrelated changes unstaged and run the clean-checkout gate separately |
| Seven paths are not seven integrations | High | Symlink discovery is not authenticated loader execution | Add host-specific smoke tests for six logical host families |
| Trigger proof is metadata-only | High | No host trigger engine is exposed in this checkout | Run supported-host activation tests; keep metadata-only label until then |
| Runtime gate is pre-run only | High | It cannot terminate already-running or bypassed processes | Integrate with an executor/supervisor only as a separately approved architecture |
| Human approval is unexercised | High | Local manifests model approval but do not prove an independent approver | Run a bounded pilot with a real approval record and expiry |
| Clean-checkout/CI proof absent | Medium | Current proof is from a dirty local checkout | Run the frozen snapshot in a clean checkout/CI job |
| Budgets are structurally checked, not enforced at execution | Medium | No graph executor exists in scope | Bind counters to the future executor before claiming runtime budget enforcement |
| Manifest and approval are unsigned | High | The gate validates content and identity but has no cryptographic authority | Add a separately approved signing/key-management design before tamper-proof or production authorization claims |
| Disk headroom is low | Medium | Earlier ENOSPC interrupted verification | Add a preflight headroom check in CI or before long suites |
| Phase-loop JS helper is not runnable in this checkout | Low | Root package ESM mode conflicts with the helper's CommonJS `require` | Repair helper packaging or use the repository-native Python snapshot generator; do not treat the failed helper invocation as a release failure |

## Proof boundary

Use this wording:

> Locally verified design-time Graph-engineer validator with a strict optional
> pre-run gate and auditable evidence contracts.

Do not use “fully verified,” “production-ready,” “globally integrated,” or
“auto-revocable runtime” until the host, clean-checkout, executor, and human
approval gates above are independently evidenced.

## Superseded historical baselines

These numbers are retained for traceability only and must not be used as the
current release result:

- Earlier graph baseline: 221 checks, 0 failed, 1 warning.
- Earlier Graph-engineer suite: 41 passed, 63 subtests.
- Earlier fifth/sixth audit reports: 405/0 Avalanche expanded, 428/0 Avalanche
  P7, and 248/0 Avalanche adversarial. Avalanche is a separate optional pilot
  and is not part of this Graph-engineer core gate.
- First audit: 161/1 expanded and 27/27 P7.

## Next adjustment

Keep the core package bounded and local. The next release-readiness review
should begin with committing or explicitly retaining the graph artifact,
running a clean-checkout snapshot, and obtaining authenticated host-loader and
human-gate evidence. No Avalanche implementation is required for this core
gate.
