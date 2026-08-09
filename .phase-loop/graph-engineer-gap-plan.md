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
| UTC snapshot | `2026-08-09T18:55:17.380478Z` | verified-local |
| Checkout | `/Users/sanjayb/codex-ecc-custom`, HEAD `980a6e18aea582ab15f03892a26e6039ee543e7a` | verified-local |
| Git status | 76 tracked/staged entries; 71 collapsed untracked; 401 full untracked | verified-local |
| Package inventory | 49 content-hashed files, recorded in the snapshot | verified-local |
| Canonical graph | `pir-panjal-repair-graph-v1.1.json`, SHA-256 `61d6fa004ad129f99cb6e5d94e8fcbc806384b1b59bdf7e45fd360cf0315248d` | artifact-only; untracked |
| Graph schema | SHA-256 `6258d6573685dce15070a3a655c55afd52eca4fc2a07e4508078fd2585687a7d` | verified-local |
| Node schema | SHA-256 `7c12d8cc23b56025b54b5477b8a6e42932140b03d65d9376efae81e3d26c9101` | verified-local |
| Validator | SHA-256 `ba029ed000b5311137f8ebbbd678009151751e94a7259b92e292d74401420f1a` | verified-local |
| Runtime gate | SHA-256 `21c749e84dc11b61069b97953b787ac2fe565ffd61135b04975a9bfe3f43254b` | verified-local |
| Evidence recorder | SHA-256 `767c75c25c8a457f049222f75f21313879e0da61895ac9c6c153b56c4d75673d` | verified-local |
| Shared format checker | SHA-256 `be48b2d43ef0f597b3e20133431902dde3875bdc25c0a68d9506b2b1cca77344` | verified-local |
| Dependency contract | `requirements.txt` SHA-256 `0de2bef24e72c35423c6bd81d388e75c1a30da1bc3a1ab05fd8213ecf5aa1b8c` | verified-local |
| Runtime policy | SHA-256 `eae49edb21f91b92ff8ca05530e9be88022f48ff38e2e8de0e957a91f9c68bdb` | verified-local |
| Disk state | Snapshot captured the local filesystem state; current free space remains an operational risk | verified-local / operational risk |

The complete hash inventory and raw command outputs are authoritative only in
the JSON snapshot; this table is a navigable summary.

## Phase completion

| Phase | Architecture outcome | Status |
|---|---|---|
| P0 | One command-driven provenance snapshot owns status, timestamp, hashes, disk, and results | verified-local |
| P1 | `pytest` and `unittest discover` execute the complete suite; all positive fixtures pass | verified-local |
| P2 | v1/v1.1 semantics, conditional v1.1 fields, local schema bundle, standalone node schema, strict formats | verified-local |
| P3 | Exact v1.1 reviewer binding, typed-port compatibility, clean malformed-input boundaries, joins, budgets | verified-local |
| P4 | Mandatory manifest, runtime package/content hash, validator/policy/host identity binding, unknown-tool block | verified-local |
| P5 | Node-aware evidence lifecycle, approval binding, schema validation, redaction, locking, completion gate | verified-local |
| P6 | Shared activation metadata and seven discovery paths; host activation remains metadata-only | verified-local / host-unverified |
| P7 | Bounded adversarial and portability coverage, no-traceback checks, diff hygiene | verified-local |

## Frozen verification ledger

| Command | Result | Proof level |
|---|---:|---|
| `python3 -m pytest -q -p no:cacheprovider skills/graph-engineer/tests` | 46 passed, 65 subtests, exit 0 | verified-local |
| `python3 -m unittest discover -s skills/graph-engineer/tests -p 'test*.py'` | 46 tests, OK, exit 0 | verified-local |
| `python3 skills/graph-engineer/tests/test_validate.py` | 23/23, exit 0 | verified-local |
| `python3 skills/graph-engineer/tests/test_triggers.py` | 22/22, metadata-only, exit 0 | verified-local / host-unverified |
| Canonical v1.1 graph validation | 678 checks passed, 0 failed, 0 warnings, exit 0 | verified-local |
| `git diff --check -- skills/graph-engineer` | exit 0 | verified-local |
| `python3 -S` validator probe | nonzero, clean fail-closed `jsonschema_available` result | verified-local |
| Standalone node schema probe | validates a v1 node without a dangling relative `$ref` | verified-local |

## Remaining gaps and gates

| Gap | Severity | Why it remains | Next action |
|---|---|---|---|
| Canonical graph is untracked | High | Local artifact provenance is not repository provenance | Commit or intentionally package it; rerun the snapshot afterward |
| Seven paths are not seven integrations | High | Symlink discovery is not authenticated loader execution | Add host-specific smoke tests for six logical host families |
| Trigger proof is metadata-only | High | No host trigger engine is exposed in this checkout | Run supported-host activation tests; keep metadata-only label until then |
| Runtime gate is pre-run only | High | It cannot terminate already-running or bypassed processes | Integrate with an executor/supervisor only as a separately approved architecture |
| Human approval is unexercised | High | Local manifests model approval but do not prove an independent approver | Run a bounded pilot with a real approval record and expiry |
| Clean-checkout/CI proof absent | Medium | Current proof is from a dirty local checkout | Run the frozen snapshot in a clean checkout/CI job |
| Budgets are structurally checked, not enforced at execution | Medium | No graph executor exists in scope | Bind counters to the future executor before claiming runtime budget enforcement |
| Disk headroom is low | Medium | Earlier ENOSPC interrupted verification | Add a preflight headroom check in CI or before long suites |

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
