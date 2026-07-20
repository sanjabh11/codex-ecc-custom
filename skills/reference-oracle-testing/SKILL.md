---
name: reference-oracle-testing
description: >-
  Build a deliberately simple, single-threaded, obviously-correct reference
  implementation for differential testing against the optimized implementation.
  "What should this return" is a program, not a debate. Use when building complex
  algorithms where correctness must be proven through differential testing.
  TRIGGER when: "reference oracle", "differential testing", "oracle testing",
  "reference implementation testing", "correctness oracle",
  "simple implementation comparison", "obviously correct reference".
  DO NOT TRIGGER when: the system is simple enough that unit tests suffice,
  or when no optimized implementation exists to compare against.
---

# Reference Oracle Testing

## When to Use

- Building complex algorithms (query planners, schedulers, consensus protocols, compression codecs)
- When the optimized implementation is too complex to verify by inspection
- When "what should this return" needs to be a program, not a debate
- When property-based testing alone is insufficient
- When you need confidence that optimizations don't change semantics

## Core Philosophy

**"What should this return" is a program, not a debate.**

Build a deliberately simple, single-threaded, obviously-correct reference implementation. It should be so simple that its correctness is self-evident. Then run both implementations on the same inputs and compare outputs.

```
Input → [Reference Oracle] → Expected Output
Input → [Optimized Impl]  → Actual Output
                              ↓
                        Compare: Expected == Actual?
```

## Reference Oracle Properties

1. **Simple:** No optimizations, no caching, no parallelism. The straightforward implementation.
2. **Single-threaded:** No concurrency complexity.
3. **Obviously correct:** A reader should be able to verify correctness by inspection.
4. **Compiled for tests only:** Not shipped in production. Lives in `tests/oracle/`.
5. **Complete:** Handles all cases the optimized implementation handles (possibly slower).
6. **Independent:** Does not share code with the optimized implementation.

## Implementation Pattern

### Step 1: Write the Oracle
```rust
// tests/oracle/query_planner.rs
/// Deliberately simple query planner — brute force all join orderings.
/// O(n!) but obviously correct.
pub fn plan_query_oracle(query: &Query) -> Plan {
    let tables = query.tables();
    let all_orderings = tables.iter().permutations(tables.len());
    let mut best = None;
    for ordering in all_orderings {
        let cost = estimate_cost(&ordering, query);
        if best.is_none() || cost < best.as_ref().unwrap().1 {
            best = Some((ordering.clone(), cost));
        }
    }
    Plan::from_ordering(best.unwrap().0)
}
```

### Step 2: Write the Optimized Implementation
```rust
// src/query/planner.rs
/// Optimized query planner using dynamic programming.
/// O(n^2 * 2^n) — much faster but harder to verify.
pub fn plan_query(query: &Query) -> Plan {
    // ... complex DP algorithm ...
}
```

### Step 3: Differential Test
```rust
// tests/differential.rs
#[test]
fn differential_query_planner() {
    for query in generate_random_queries(1000) {
        let oracle_plan = oracle::plan_query_oracle(&query);
        let optimized_plan = planner::plan_query(&query);
        assert_eq!(
            oracle_plan.estimated_cost(),
            optimized_plan.estimated_cost(),
            "Cost mismatch for query: {:?}",
            query
        );
    }
}
```

## Continuous Consistency Oracles

For databases and transactional systems, use consistency oracles that check history validity:

### Snapshot Isolation (SI) Oracle
```python
def check_si_history(history: list[Transaction]):
    """Check that a history is valid under Snapshot Isolation."""
    for txn in history:
        snapshot = txn.snapshot_timestamp
        for write in txn.writes:
            # No other transaction with overlapping write set
            # committed between snapshot and txn.commit
            for other in history:
                if other.id == txn.id:
                    continue
                if other.commit_time > snapshot and other.commit_time < txn.commit_time:
                    if overlap(other.write_set, txn.write_set):
                        return False
    return True
```

### Serializable Snapshot Isolation (SSI) Oracle
```python
def check_ssi_history(history: list[Transaction]):
    """Check that a history is valid under SSI."""
    # Check SI first
    if not check_si_history(history):
        return False
    # Check for write-skew cycles
    # ... SSI cycle detection ...
    return True
```

### Elle-class History Checking
- Parse execution history into a graph
- Check for cycles that violate consistency models
- Supports: strict serializable, serializable, snapshot isolation, read committed, causal

## Property-Based Testing Integration

Combine reference oracle with property-based testing:

```rust
proptest! {
    #[test]
    fn planner_matches_oracle(ref query in arbitrary_query()) {
        let oracle_cost = oracle::plan_query_oracle(&query).estimated_cost();
        let opt_cost = planner::plan_query(&query).estimated_cost();
        prop_assert_eq!(oracle_cost, opt_cost);
    }
}
```

## When to Use vs. Alternatives

| Method | When | Cost | Confidence |
|---|---|---|---|
| Unit tests | Simple functions, known cases | Low | Low |
| Property-based testing | Invariants expressible as properties | Medium | Medium |
| **Reference oracle** | Complex algorithms, need ground truth | Medium | **High** |
| Formal methods (TLA+/Lean) | Safety-critical protocols | High | Highest |
| Deterministic simulation | Concurrent/distributed systems | High | High |

## Integration with ECC

- Use with `deterministic-simulation-testing` — the oracle checks invariants during simulation
- Use with `invariant-registry` — oracle serves as the checker for correctness invariants
- Use with `conformance-gate` — differential test results are conformance evidence
- Use with `fuzz-regression` — convert oracle-discovered mismatches into regression tests
- Use with `santa-method` — dual-review of oracle correctness (is the oracle actually correct?)

## Oracle Maintenance

- **Keep it simple:** If the oracle becomes complex, it's no longer an oracle
- **Update first:** When behavior changes, update the oracle before the optimized impl
- **Never optimize:** The oracle's job is correctness, not performance
- **Test the oracle:** Sanity-check the oracle against known cases independently
