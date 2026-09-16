# Skill Optimization Method

## Local First

This skill uses a small local harness before reaching for a full optimizer. The target model, tool surface, and execution environment stay fixed; only the skill or prompt text changes.

## Evidence Loop

1. Inventory: identify the target file, adjacent skills, trigger metadata, references, scripts, and validation commands.
2. Scenarios: create representative prompts that exercise the target behavior.
3. Rollout evidence: capture command outputs, transcripts, reviewer notes, artifact paths, and pass/fail results.
4. Reflection: compare successes and failures to identify reusable procedural changes.
5. Bounded edits: apply only the smallest add, delete, or replace operations supported by evidence.
6. Gate: accept the candidate only when held-out or before/after results pass the selected promotion gate.
7. Ledger: record accepted edits, rejected edits, remaining gaps, and next scenarios.

## Bounded Edit Rules

- Prefer one focused lever per optimization pass.
- Do not rewrite the whole skill unless the existing file is structurally unusable.
- Keep `SKILL.md` concise; move details into `references/`.
- Use scripts for deterministic checks that would otherwise be rewritten repeatedly.
- Reject plausible edits that do not improve evidence, and record why.
- Do not change shared ECC behavior unless the target skill, router, and installed cache are all verified and validated.

## Matt-Style Alignment Questions

Use these before creating scenarios when the target is ambiguous:

- What exact behavior should the skill cause that a general agent would not reliably do?
- What wrong behavior are we trying to prevent?
- What repo, file, or workflow context must the skill inspect before acting?
- What should the agent ask before proceeding?
- What should remain out of scope even if the prompt tempts the agent to expand?
- What proof should be required before the agent claims success?

## Optional Full SkillOpt Upgrade

`skillopt` is now available as an external package, but this v1 harness does not install it. Consider full SkillOpt only when local scenarios are stable, scored, repeatable, and worth running through a larger rollout and validation loop.
