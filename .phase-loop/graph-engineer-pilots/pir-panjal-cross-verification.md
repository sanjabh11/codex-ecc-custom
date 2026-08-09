# Pir Panjal / Graph-engineer core cross-verification

Generated from the frozen local snapshot:
`.phase-loop/graph-engineer-pilots/graph-engineer-audit-snapshot.json`.

## Scope decision

This record verifies the Graph-engineer installation/core skill only. The
Avalanche integration is an optional GLM-owned pilot and is intentionally not
treated as evidence for this core release gate.

## Provenance

| Field | Value | Proof level |
|---|---|---|
| UTC timestamp | `2026-08-09T18:55:17.380478Z` | verified-local |
| Graph-engineer HEAD | `980a6e18aea582ab15f03892a26e6039ee543e7a` | verified-local |
| Tracked/staged status entries | 76 | verified-local |
| Untracked, collapsed | 71 | verified-local |
| Untracked, full | 401 | verified-local |
| Python executable | `/opt/homebrew/Cellar/python@3.14/3.14.5/Frameworks/Python.framework/Versions/3.14/bin/python3.14` | verified-local |
| Canonical graph | `.phase-loop/graph-engineer-pilots/pir-panjal-repair-graph-v1.1.json` | artifact-only; untracked |
| Canonical graph SHA-256 | `61d6fa004ad129f99cb6e5d94e8fcbc806384b1b59bdf7e45fd360cf0315248d` | artifact-only |
| Package inventory | 49 files; full map in snapshot | verified-local |
| Graph schema SHA-256 | `6258d6573685dce15070a3a655c55afd52eca4fc2a07e4508078fd2585687a7d` | verified-local |
| Node schema SHA-256 | `7c12d8cc23b56025b54b5477b8a6e42932140b03d65d9376efae81e3d26c9101` | verified-local |
| Validator SHA-256 | `ba029ed000b5311137f8ebbbd678009151751e94a7259b92e292d74401420f1a` | verified-local |
| Runtime gate SHA-256 | `21c749e84dc11b61069b97953b787ac2fe565ffd61135b04975a9bfe3f43254b` | verified-local |
| Evidence recorder SHA-256 | `767c75c25c8a457f049222f75f21313879e0da61895ac9c6c153b56c4d75673d` | verified-local |
| Shared format checker SHA-256 | `be48b2d43ef0f597b3e20133431902dde3875bdc25c0a68d9506b2b1cca77344` | verified-local |
| Dependency contract SHA-256 | `0de2bef24e72c35423c6bd81d388e75c1a30da1bc3a1ab05fd8213ecf5aa1b8c` | verified-local |

## Authoritative local results

| Check | Result |
|---|---:|
| `pytest` package suite | 46 passed, 65 subtests, exit 0 |
| Standard `unittest discover` | 46 tests, OK, exit 0 |
| Validator regression wrapper | 23/23, exit 0 |
| Trigger metadata regression wrapper | 22/22, exit 0; metadata-only |
| Pir Panjal v1.1 graph | 678 checks passed, 0 failed, 0 warnings |
| Schema resolver | Local `referencing.Registry`; no network resolution |
| Strict date-time validation | Shared RFC3339 checker used by graph, manifest, and evidence paths |
| `python3 -S` dependency probe | Clean nonzero fail-closed result |
| Diff hygiene | `git diff --check -- skills/graph-engineer`: exit 0 |

## Architecture verified

| Area | Finding | Proof level |
|---|---|---|
| Graph contract | v1.1 conditionally requires objective, criteria, full budget, and evidence policy | verified-local |
| Schema boundary | Unknown fields, malformed roots, invalid ports, malformed reports, and invalid formats fail without traceback | verified-local |
| Reviewer ownership | v1.1 reviewers bind exactly one worker; legacy v1 aggregate reviewers are not guessed as one worker | verified-local |
| Port contracts | Source/destination ports must exist, bind to the declared node/port, and have compatible schemas | verified-local |
| Failure routing | Failure edges target the reviewed worker for v1.1; legacy aggregate reviewers may route to their declared reviewed set | verified-local |
| Runtime package | Required package files, contents, safe symlinks, validator digest, policy digest, interpreter path, host profile, and hostname are bound | verified-local |
| Manifest | Missing, malformed, expired, revoked, graph-mismatched, runtime-mismatched, or approval-mismatched manifests block/revoke | verified-local |
| Tools | Unknown tools block by default; malformed policy fails closed; health/version checks are recorded where declared | verified-local |
| Evidence | JSONL records are node-valid, schema-valid, redacted, lifecycle-ordered, locked, and completion-gated | verified-local |
| Platform discovery | Seven physical paths resolve to one package; six logical host families are documented; authenticated loader proof is absent | host-unverified |

## Residual gaps / next gates

1. Commit or explicitly approve the untracked canonical graph and rerun the
   frozen snapshot.
2. Run a clean-checkout/CI verification; the current local checkout is dirty.
3. Execute six logical host-loader smoke tests; symlink presence is not loader
   compatibility proof.
4. Exercise the actual host trigger engine; current trigger tests validate
   shared metadata only.
5. Run one bounded pilot with an independent human approval record and expiry.
6. Add a real executor integration before claiming runtime budget enforcement or
   process revocation.
7. Maintain disk-headroom preflight before long multi-suite runs.

## Explicit boundaries

This artifact does not prove native SNOWPACK, live Modal execution, DGRE
approval, deployment, process supervision, buyer validation, or global IDE
compatibility. Those are externally dependent gates.

## Superseded historical results

Earlier records claimed 221 checks/1 warning and 41 tests/63 subtests. Those
results are historical baselines only. Earlier Avalanche counts (405/0,
428/0, and 248/0) belong to the separate optional pilot and are not merged into
the current Graph-engineer core proof.

## Interim claim

> Locally verified design-time Graph-engineer validator with a strict optional
> pre-run gate and auditable evidence contracts; host, executor, clean-checkout,
> and human-gate proof remain unverified.
