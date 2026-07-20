---
name: plan-certificates
description: >-
  Make every result an auditable, replayable artifact with plan hash, tie-break
  policy, snapshot seq, per-operator observed-vs-bound counts, and a decision-path
  hash. Use when results must be reproducible and auditable for regulated pipelines,
  agent memory, compliance, or any system where "same input = same output" is a
  product feature.
  TRIGGER when: "plan certificate", "auditable result", "replayable result",
  "result certificate", "deterministic output", "byte-reproducible",
  "decision card", "plan hash", "tie-break policy", "complexity witness".
  DO NOT TRIGGER when: task is a one-off script with no reproducibility requirements.
---

# Plan Certificates

## When to Use

- Regulated pipelines where results must be auditable and reproducible
- Agent memory systems where the same query must return the same result
- Compliance-critical systems requiring traceable execution evidence
- Any system where "same input + same policy = same output" is a product feature
- When adaptive decisions need replayable evidence (decision cards)

## Core Concept

Every query result is an auditable artifact. Given the same certificate, snapshot, and seed, the result can be reproduced byte-for-byte.

```
replay(certificate, snapshot_seq, seed) → identical result
```

## Certificate Structure

```json
{
  "plan_certificate": {
    "plan_hash": "blake3:a1b2c3d4...",
    "tie_break_policy": "CGSE_LEXICOGRAPHIC",
    "snapshot_seq": 42,
    "policy_epoch": "2024-01-15T00:00:00Z",
    "operators": [
      {
        "operator_id": "scan_edges",
        "observed_count": 1542,
        "bound_count": 2000,
        "within_bound": true,
        "replan_triggered": false
      },
      {
        "operator_id": "hash_join",
        "observed_count": 87,
        "bound_count": 100,
        "within_bound": true,
        "replan_triggered": false
      }
    ],
    "decision_path_hash": "blake3:e5f6g7h8...",
    "replan_events": [],
    "result_digest": "blake3:i9j0k1l2..."
  }
}
```

## Fields

| Field | Purpose |
|---|---|
| `plan_hash` | Hash of the query plan structure (BLAKE3) |
| `tie_break_policy` | How ties are broken (e.g., CGSE lexicographic, by-ID) |
| `snapshot_seq` | Which MVCC snapshot was used |
| `policy_epoch` | Versioned policy under which the decision was made |
| `operators` | Per-operator observed-vs-bound counts |
| `decision_path_hash` | Hash of all adaptive decisions made during execution |
| `replan_events` | List of times the plan was adapted mid-execution |
| `result_digest` | Hash of the actual result bytes |

## Complexity Witnesses

Every operator carries a complexity witness: the observed operation count vs. the declared bound.

```
observed_count ≤ bound_count → within_bound: true
observed_count > bound_count → within_bound: false (complexity violation)
```

CI enforcement: complexity-witness regression locks fail CI if an operator's observed count exceeds its bound.

```python
def check_complexity_witnesss(certificate):
    for op in certificate["operators"]:
        if op["observed_count"] > op["bound_count"]:
            raise ComplexityViolation(
                f"Operator {op['operator_id']}: observed {op['observed_count']} "
                f"exceeds bound {op['bound_count']}"
            )
```

## Decision Cards

Every adaptive decision emits a replayable decision card:

```json
{
  "decision_card": {
    "decision_id": "adapt_join_strategy",
    "policy_epoch": "2024-01-15T00:00:00Z",
    "state": {"cardinality_estimate": 1500},
    "actions": ["switch_to_hash_join"],
    "features": {"table_size": 1500, "memory_available": "4GB"},
    "logged_probabilities": {"switch_to_hash_join": 0.8, "keep_nested_loop": 0.2},
    "fallback": "nested_loop_join",
    "evidence": {
      "alpha": 0.05,
      "support": 100,
      "overlap": 0.3,
      "effective_sample_size": 70,
      "loss": 0.02
    }
  }
}
```

## Replay Protocol

```python
def replay(certificate, snapshot_seq, seed):
    """Reproduce a result byte-for-byte from its certificate."""
    # 1. Load snapshot at snapshot_seq
    snapshot = load_snapshot(snapshot_seq)

    # 2. Restore plan from plan_hash
    plan = restore_plan(certificate["plan_hash"])

    # 3. Apply tie-break policy
    plan.set_tie_break_policy(certificate["tie_break_policy"])

    # 4. Set RNG seed
    set_seed(seed)

    # 5. Execute plan
    result = execute(plan, snapshot)

    # 6. Verify result digest matches
    actual_digest = blake3(result.bytes())
    assert actual_digest == certificate["result_digest"], \
        "Replay failed: result digest mismatch"

    return result
```

## STRICT vs. Non-Strict Results

- **STRICT:** Byte-reproducible. Same certificate + snapshot + seed = identical bytes. Eligible for audit.
- **Non-strict:** Best-effort. May vary due to adaptive decisions, approximate algorithms, or non-deterministic sources. Still carries a certificate for traceability.

Mark results as STRICT only when all of:
1. Tie-break policy is deterministic
2. No adaptive decisions changed the plan
3. All operators are within complexity bounds
4. No external non-determinism was consulted

## CI Enforcement

```yaml
# .github/workflows/certificate-regression.yml
name: Certificate Regression
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Replay all STRICT certificates
        run: |
          python3 scripts/replay_certificates.py \
            --registry certificates/ \
            --fail-on-mismatch
      - name: Check complexity witnesses
        run: python3 scripts/check_complexity.py
```

## Integration with ECC

- Use with `conformance-gate` — certificates are conformance evidence
- Use with `invariant-registry` — certificate replay is the checker for determinism invariants
- Use with `deterministic-simulation-testing` — certificates from simulation runs are replayable
- Use with `spec-first-doctrine` — certificates are part of the verification doctrine
- Use with `verification-loop` — certificate replay is a verification step
