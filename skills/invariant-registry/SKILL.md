---
name: invariant-registry
description: >-
  Maintain a machine-readable invariant registry with stable IDs, CI enforcement
  that every invariant has a live checker, and a hard rule that no subsystem ships
  against an unenforced invariant. Use when building safety-critical, correctness-critical,
  or compliance-critical systems where invariants must be explicitly tracked and verified.
  TRIGGER when: "invariant registry", "invariant enforcement", "CI invariant check",
  "unenforced invariant", "safety invariant", "correctness invariant",
  "invariant ID", "formal invariant", "system invariant tracking".
  DO NOT TRIGGER when: task is a simple script with no correctness requirements,
  or when the system has no load-bearing invariants to track.
---

# Invariant Registry

## When to Use

- Building safety-critical systems (databases, distributed systems, financial systems)
- When invariants must be explicitly tracked, enforced, and auditable
- When CI must prove that every invariant has a live checker
- When shipping a subsystem requires proof that its invariants are enforced
- Compliance-critical systems requiring traceable correctness guarantees

## Core Principle

**No subsystem ships against an unenforced invariant.**

A workstream exit gate (G1-G4) cannot pass while any invariant it depends on lacks a live checker in the invariant registry. Promote a design assumption to enforced only after the checker exists.

## Registry Format

Create `invariants.toml` (or `invariants.yaml`) at the project root:

```toml
# invariants.toml — Machine-readable invariant registry
# Every load-bearing invariant has a stable ID, statement, and enforcement mechanism.
# CI cross-checks that every ID has a live checker.

[[invariant]]
id = "INV-01"
name = "MVCC Visibility"
statement = "A transaction reads a consistent snapshot: it sees exactly the versions committed before its snapshot timestamp."
enforcement = "runtime_oracle"  # one of: lean, tla_plus, runtime_oracle, property_test, ci_gate
checker = "tests/invariants/test_mvcc_visibility.py"
status = "enforced"  # enforced | assumed | planned
workstream = "G1"  # which exit gate depends on this

[[invariant]]
id = "INV-02"
name = "SSI Conflict Safety"
statement = "Serializable Snapshot Isolation detects all write-skew anomalies under concurrent execution."
enforcement = "tla_plus"
checker = "models/ssi_conflict.tla"
status = "enforced"
workstream = "G1"

[[invariant]]
id = "INV-03"
name = "Crash Recovery"
statement = "After any crash at any point, the database recovers to a consistent state without data loss."
enforcement = "property_test"
checker = "tests/invariants/test_crash_recovery.rs"
status = "enforced"
workstream = "G2"

[[invariant]]
id = "INV-04"
name = "No Silent Data Corruption"
statement = "Bit flips in storage are detected and corrected before they affect query results."
enforcement = "runtime_oracle"
checker = "tests/invariants/test_bit_rot_detection.py"
status = "assumed"  # not yet enforced — cannot ship G3
workstream = "G3"
```

## Enforcement Mechanisms

| Mechanism | When to Use | Strength |
|---|---|---|
| `lean` | Mathematical proof of invariant (e.g., MVCC visibility, type safety) | Strongest — formal proof |
| `tla_plus` | Protocol/algorithm modeling (e.g., commit protocol, consensus, branch merge) | Strong — model checking |
| `runtime_oracle` | Runtime checks embedded in the system (e.g., assertion-based oracles) | Medium — catches violations at runtime |
| `property_test` | Property-based testing (e.g., QuickCheck, proptest) | Medium — probabilistic coverage |
| `ci_gate` | CI pipeline gate (e.g., build check, lint rule, dependency audit) | Weakest — but automatable |

## CI Enforcement

### Cross-Check Script
```python
#!/usr/bin/env python3
"""CI cross-check: every invariant ID must have a live checker."""
import tomllib
import sys
from pathlib import Path

def check_invariants():
    registry = tomllib.loads(Path("invariants.toml").read_text())
    errors = []
    for inv in registry["invariant"]:
        if inv["status"] == "enforced":
            checker_path = Path(inv["checker"])
            if not checker_path.exists():
                errors.append(f"INV-{inv['id']}: checker not found at {checker_path}")
            elif not checker_path.is_file():
                errors.append(f"INV-{inv['id']}: checker path is not a file: {checker_path}")
        elif inv["status"] == "assumed":
            errors.append(f"INV-{inv['id']}: ASSUMED but not enforced — cannot ship {inv['workstream']}")
    if errors:
        for e in errors:
            print(f"  INVARIANT ERROR: {e}")
        sys.exit(1)
    print(f"All {len(registry['invariant'])} invariants verified.")

if __name__ == "__main__":
    check_invariants()
```

### Workstream Exit Gate Check
```yaml
# .github/workflows/invariant-gate.yml
name: Invariant Gate
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify all invariants have live checkers
        run: python3 scripts/check_invariants.py
      - name: Run all invariant checkers
        run: |
          python3 scripts/run_invariant_checks.py --workstream ${{ matrix.workstream }}
    strategy:
      matrix:
        workstream: [G1, G2, G3, G4]
```

## Invariant Lifecycle

```
DESIGNED → ASSUMED → ENFORCED
    ↑         |          |
    |         v          v
    |    Cannot ship   Can ship
    |    (block G-gate) (pass G-gate)
    |
    +--- New invariant identified during design
```

1. **Designed:** Invariant identified during architecture/design phase
2. **Assumed:** Invariant is stated but no checker exists — blocks shipping
3. **Enforced:** Checker exists and runs in CI — unblocks shipping

### Promotion Rule
A design assumption is promoted to enforced **only after** the checker exists and passes in CI. No exceptions.

## Negative Evidence Log

When an invariant is violated (in testing or production), record it:

```markdown
# docs/NEGATIVE_EVIDENCE.md

## INV-03 Violation — 2024-01-15
- **What:** Crash recovery failed after simulated power loss during compaction
- **Root cause:** Compaction publish/retire race condition
- **Resolution:** Added two-fsync commit protocol (INV-03 checker updated)
- **Regression test:** tests/invariants/test_crash_during_compaction.rs
```

## Integration with ECC

- Use with `deterministic-simulation-testing` to check invariants under DST
- Use with `conformance-gate` to prove invariant coverage before shipping
- Use with `spec-first-doctrine` to define invariants before implementation
- Use with `verification-loop` to run invariant checks as part of verification
- Use with `santa-method` for dual-review of invariant correctness

## Template

Copy `invariants.toml` template above and adapt to your project. Start with 3-5 critical invariants and grow as the system matures. Every invariant should be:
- **Stable:** ID never changes once assigned
- **Clear:** Statement is unambiguous and testable
- **Enforced:** Has a live checker that runs in CI
- **Tracked:** Status is monitored and blocking when unenforced
