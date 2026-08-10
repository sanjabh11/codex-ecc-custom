# Graph-to-Runtime Mapping

This document maps graph-engineer jobs to available ECC execution surfaces. It is an audit aid and selection guide, not a synchronized registry or execution engine. Availability must be checked in the current session before claiming a route is live.

## Proof levels

`validate_graph.py` proves local graph/schema conformance. `check_runtime.py`
adds a deterministic pre-run decision when a manifest binds the exact graph,
runtime contents, host identity, tool snapshot, run, artifact, action, target,
and expiry. Neither command proves host-loader compatibility, agent execution,
process supervision, deployment, or buyer/production proof.

## Runtime mapping

| Graph job | Preferred local surface | Use it for | Boundary |
|---|---|---|---|
| `planner` | `ecc-plan` or a native planning pass | Decompose the objective and emit the graph definition | Do not let the planner silently execute write-capable work |
| `worker` (read-only research) | `parallel-research-delegation` when exposed; otherwise a bounded native subtask | Independent research or analysis lanes | Keep workers independent and cap fan-out |
| `worker` (repository audit) | `ecc-devfleet` or a bounded local script | Isolated audit lanes or deterministic scans | Verify worktree/runtime availability before dispatch |
| `reviewer` | `ecc-code-review`, `hermaguard`, or a distinct review prompt | One-dimensional verification of a worker output | Reviewer must not be the worker and must ask one question |
| `synthesizer` | Native executor pass or `dynamic-workflow-backlog` when available | Merge only reviewed survivors into a structured report | Preserve provenance and failed-output exclusions |
| `human-gate` | `ask_user_question` or the host's approval surface | Approval before publish, send, refund, invoice, deploy, or delete | Never replace approval with an agent assertion |
| deterministic validation | `scripts/validate_graph.py` | Validate graph structure, contracts, caps, and optional local runtime refs | Run before any agent/tool execution |
| strict pre-run gate | `scripts/check_runtime.py` | Revalidate graph and verify manifest/hash/tool/approval bindings | Requires `--manifest`, `--run-id`, and `--artifact-digest`; does not supervise a running process |
| evidence ledger | `scripts/record_evidence.py` | Append schema-valid lifecycle, node, review, gate, and terminal JSONL records | Requires a valid graph, known node IDs, evidence-root containment, and `run_started` first |
| skill evaluation | `ecc-eval` | Capture capability/regression evidence and separate execution from grading | Do not grade only the agent's repaired state |

## Availability protocol

1. Check the graph definition with `scripts/validate_graph.py` before selecting a runtime.
2. Check whether the named skill or CLI is actually installed and healthy in the current session.
3. Prefer read-only or dry-run execution for the first run.
4. Pass only explicit node inputs to a worker; do not accumulate unrelated conversation state by default.
5. Record the runtime, model/provider route, retries, output artifact, and proof level (`local`, `live`, `artifact-only`, or `unverified`).
6. If a runtime is unavailable, mark the node unavailable and route to a human or fallback; do not silently substitute a different capability.

For a strict pre-run check:

```bash
python3 scripts/check_runtime.py \
  --graph graph.json --runtime-root /path/to/repository \
  --manifest run.manifest.json --run-id RUN_ID \
  --artifact-digest ARTIFACT_DIGEST
```

Use `scripts/create_manifest.py` to create the content-bound manifest after
the graph and approval decision are known; it records the caller-supplied
decision and is not a human approval surface.

Record `run_started` first, then node/review events, any gate decision, and
`run_finished` or `run_aborted`. Reviewer events must point to a schema-valid
review report stored inside the evidence root and carry its full SHA-256
content digest. Evidence is append-locked and redacts secret-like strings;
it still does not establish reviewer independence by itself.

The runtime manifest and approval binding are content-validated but unsigned
caller-supplied JSON. They detect accidental or one-sided tampering of the
graph, package, policy, tools, run, and artifact; they are not a cryptographic
authority against an actor who can rewrite both the manifest and the runtime.
Use a separately approved signing/key-management design before making a
tamper-proof or production authorization claim.

## Context and state boundaries

- `inputs` identify upstream node IDs whose outputs are required; they are not permission to share all prior transcripts.
- `outputs` are artifact contracts. Prefer JSON or another structured format for machine-consumed outputs.
- `contract.preconditions`, `contract.postconditions`, and `contract.failure_output` are optional node-level declarations; validate them when present.
- A failure edge is recovery control flow, not a normal data dependency. It must return reviewer feedback to a bounded worker.
- One writer owns a given output file. A synthesizer should write a new report rather than mutate a worker's artifact in place.

## Safe runtime selection examples

### Read-only skill audit

```text
validate graph → run three independent read-only audit workers → review each dimension → synthesize → human review
```

Use `--runtime-root` to verify `runtime_refs` locally; graphs with runtime references fail closed without it. Do not deploy fixes in the same run unless the human gate approves the exact artifact and target.

### Code change graph

```text
plan → parallel audits → synthesize findings → human gate → one bounded implementation lane → deterministic tests → separate review
```

The human gate belongs before the deploy, not necessarily before drafting or testing. Keep implementation and review ownership separate.

## Unsupported assumptions

- This package does not provide a scheduler, persistent checkpoint store, model router, token meter, or live agent dispatcher.
- A `runtime_refs` entry proves only that a local skill file exists when checked with `--runtime-root`; it does not prove that the skill's dependencies or connectors are healthy.
- Agent count caps are safety bounds, not cost estimates. Do not translate them into dollar amounts without provider pricing and execution telemetry.
