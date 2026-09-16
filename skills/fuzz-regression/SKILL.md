---
name: fuzz-regression
description: "Turn edge cases and malformed inputs into durable fuzz or regression tests."
origin: ECC
---

# Fuzz Regression Skill

Use this skill when the user asks for adversarial testing, fuzzing, edge-case hardening, parser validation, malformed payload checks, or a durable regression test for a previously observed failure.

## Trigger Phrases

- "fuzz regression"
- "adversarial test"
- "edge cases"
- "malformed input"
- "property test"
- "regression fixture"
- "crash reproducer"

## Workflow

1. Identify the contract boundary: parser, API payload, file import, geometry transform, model input, command arguments, or UI route.
2. Collect seeds from real failures, fixtures, docs, or minimal examples.
3. Find existing fuzz or property-test infrastructure:
   ```bash
   rg -n "fuzz|quickcheck|proptest|hypothesis|fast-check|property|fixture" .
   ```
4. Run the narrow existing test target first, if present.
5. Add or update the smallest durable regression:
   - A fixture for the exact failure.
   - A property test for an invariant.
   - A bounded fuzz target for malformed input families.
6. Verify the new test fails without the fix when practical, then passes with the fix.

## Useful Command Patterns

```bash
cargo test <regression-test>
cargo fuzz run <target>
pytest <test-file>
npm run test -- <test-file>
go test ./... -run <test>
```

For web/API projects, mutate JSON payloads, missing fields, bbox order, empty arrays, huge values, invalid enum strings, and stale artifact references.

## Output Contract

Return:
- `Boundary`: what input contract is being hardened.
- `Seeds`: where test cases came from.
- `Regression`: fixture or test added.
- `Verification`: command and result.
- `Residual risk`: untested input families or tooling limits.

## Safety Rules

- Bound fuzz runs in interactive sessions; do not launch unbounded jobs.
- Do not generate massive corpora or delete existing corpora without approval.
- Keep regression fixtures small and reviewable.
- Treat one fuzz pass as evidence, not a proof of absence of bugs.
