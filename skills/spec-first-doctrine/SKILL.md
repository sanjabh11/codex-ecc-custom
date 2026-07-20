---
name: spec-first-doctrine
description: >-
  Enforce spec-first implementation: read the comprehensive plan before writing
  any subsystem, implementation follows the plan not ad-hoc invention, and every
  design assumption must be promoted to enforced only after the checker exists.
  Use when starting work on a complex multi-subsystem project where the spec is
  the single source of truth.
  TRIGGER when: "spec-first", "spec first doctrine", "comprehensive plan",
  "implementation follows the plan", "single source of truth",
  "no ad-hoc invention", "spec-driven development", "design spec enforcement".
  DO NOT TRIGGER when: task is a single-file fix, a quick prototype,
  or when no spec/plan document exists.
---

# Spec-First Doctrine

## When to Use

- Starting work on a complex multi-subsystem project
- When a comprehensive plan or architecture document exists (or should exist)
- When implementation must follow the spec, not ad-hoc invention
- When multiple agents or developers work on the same system
- When design assumptions must be tracked and enforced

## Core Rules

### Rule 1: Read Before Writing
Read the comprehensive plan before writing any subsystem. The reading order:
1. **The comprehensive plan** — architecture, the bets, every subsystem, verification doctrine, workstream/gate sequencing
2. **The invariant registry** — every load-bearing invariant with its stable ID, statement, and enforcement mechanism
3. **The on-disk formats and contracts** — the normative contracts a new module must honor

### Rule 2: The Spec is the Single Source of Truth
Implementation follows the plan, not ad-hoc invention. If the plan says "use a graph-structured LSM with three temperature tiers," you implement that — not a B-tree because it's easier.

### Rule 3: No Subsystem Ships Against an Unenforced Invariant
A workstream exit gate cannot pass while any invariant it depends on lacks a live checker. Promote a design assumption to enforced only after the checker exists.

### Rule 4: Violations are Reverts
Violating any constitutional rule is a revert, memorialized in `docs/NEGATIVE_EVIDENCE.md`.

## Constitutional Constraints

Define non-negotiable rules at the project level. Example:

```markdown
# Engineering Doctrine

1. The dependency universe is closed. [List allowed dependencies]
2. Memory safety is structural. [unsafe policy]
3. Cx everywhere. [capability context threading rule]
4. Determinism by default. Same input + same query + same policy = same output.
5. Simulation-first. The entire system runs under a lab runtime in testing.
6. Spec-first. Read the plan before writing code.
```

## Workflow

```
1. SPEC EXISTS?
   ├── YES → Read it (plan → invariants → formats → contracts)
   └── NO → Write it first (use `blueprint` skill)

2. DESIGN ASSUMPTIONS
   ├── Identify invariants the subsystem depends on
   ├── Check invariant registry: are they enforced?
   └── If not enforced → create checker BEFORE implementing

3. IMPLEMENT
   ├── Follow the spec exactly
   ├── No ad-hoc invention
   └── Every deviation → update spec + record in NEGATIVE_EVIDENCE.md

4. VERIFY
   ├── Run invariant checkers
   ├── Run simulation tests
   └── Exit gate: all dependent invariants enforced?

5. SHIP
   └── Only after exit gate passes
```

## Negative Evidence Log

When a constitutional rule is violated or a spec deviation occurs:

```markdown
# docs/NEGATIVE_EVIDENCE.md

## Violation: 2024-01-15 — Ad-hoc Invention
- **What:** Implemented B-tree index instead of graph-structured LSM per spec
- **Why:** Seemed easier at the time
- **Resolution:** Reverted, implemented per spec
- **Lesson:** The spec exists for a reason. Follow it.

## Violation: 2024-02-01 — Unenforced Invariant Shipped
- **What:** Shipped G2 gate without INV-03 checker
- **Why:** Checker was "planned" but not implemented
- **Resolution:** Rolled back, implemented checker, re-shipped
- **Lesson:** No subsystem ships against an unenforced invariant.
```

## Spec Drift Detection

Spec drift occurs when implementation diverges from the spec. Detect it:

1. **Periodic spec audits:** Compare implementation against spec quarterly
2. **CI spec checks:** Automated checks that implementation matches spec contracts
3. **Deviation log:** Every deviation must be recorded in NEGATIVE_EVIDENCE.md
4. **Reconciliation:** Either update the spec (with justification) or fix the implementation

## Integration with ECC

- Use with `blueprint` to create the comprehensive plan
- Use with `invariant-registry` to track and enforce invariants
- Use with `deterministic-simulation-testing` for simulation-first verification
- Use with `conformance-gate` to prove spec compliance before shipping
- Use with `plan-certificates` for auditable, replayable results
- Use with `agents-md-generator` to encode the doctrine in AGENTS.md

## Spec Template

```markdown
# Comprehensive Plan for [Project Name]

## Mission
[One paragraph: what we're building and why]

## Bets
[Bold architectural decisions and why they're feasible]

## Subsystems
[Each subsystem: purpose, interfaces, invariants, verification]

## Verification Doctrine
[Simulation-first, reference oracle, consistency oracles, formal anchors, plan certificates]

## Workstream/Gate Sequencing
[G1 → G2 → G3 → G4 with exit criteria]

## Appendices
A. On-disk formats
B. Operation vocabulary
C. Protocol specifications
D. Invariant registry (or link to invariants.toml)
E. Cost registry
F. Normative contracts
```
