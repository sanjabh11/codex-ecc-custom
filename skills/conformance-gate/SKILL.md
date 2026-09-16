---
name: conformance-gate
description: "Prove implementation conformance against an expected contract before claiming success."
origin: ECC
---

# Conformance Gate Skill

Use this skill when the user asks whether an implementation really matches a contract, oracle, design, API behavior, proof pack, release claim, or expected workflow.

## Trigger Phrases

- "conformance gate"
- "prove it matches"
- "verify the claim"
- "contract test"
- "release gate"
- "proof boundary"
- "current state audit"

## Workflow

1. State the expected contract in concrete terms: inputs, outputs, route, artifact, UI state, or behavior.
2. Locate the implementation path before testing:
   ```bash
   rg -n "<route|function|artifact|claim>" .
   ```
3. Map the contract to the narrowest available checks:
   - Unit or integration tests for pure behavior.
   - Browser or API smoke tests for web flows.
   - Build/type/lint checks for structural conformance.
   - Repo-specific gate scripts when present.
4. Run changed-file or contract-specific checks before broad test suites.
5. Classify the proof level:
   - `live`: verified against the hosted or running target.
   - `local`: verified in the local runtime.
   - `artifact-only`: files exist but runtime behavior was not proven.
   - `unverified`: no evidence yet.
6. Fail closed when evidence is missing. Do not upgrade proof level by inference.

## Useful Command Patterns

```bash
git diff --stat
rg -n "<contract-keyword>" .
npm run build
npm run test -- <focused-test>
cargo test <focused-test>
pytest <focused-test>
```

For repositories that provide conformance tooling, prefer their native gate scripts before inventing a new harness.

## Output Contract

Return:
- `Contract`: the expected behavior being gated.
- `Evidence`: commands run and short result.
- `Proof level`: live, local, artifact-only, or unverified.
- `Gaps`: missing evidence or failing checks.
- `Decision`: pass, fail, or inconclusive with the exact next fix.

## Safety Rules

- Do not claim success without command evidence.
- Do not treat documentation, dependencies, or dead code as implementation proof.
- Do not run destructive migrations or cleanup commands as part of conformance.
- Keep public-facing claims aligned to the proven proof level.
