---
name: skill-optimizer
description: Improve, validate, compare, regress-test, or evolve Codex/ECC skills, prompts, agents, and reusable workflows using local scenario fixtures, evidence manifests, bounded edits, before/after comparisons, and promotion gates. Use when a user asks whether a SKILL.md is good enough, wants a skill optimized, wants a prompt/workflow regression harness, or asks to incorporate lessons without copying a full external skill pack.
---

# Skill Optimizer

## Purpose

Use this skill to make reusable instructions measurably better without turning every improvement into a full research project. The default route is local, lightweight, and evidence-gated: define scenarios, run or review results, make bounded edits, compare before and after, and promote only when the gate passes.

This is inspired by SkillOpt-style text-space optimization, but it is not the full SkillOpt runtime and does not install `skillopt` by default.

## Activation

Use this skill when the task mentions:

- improving, optimizing, validating, benchmarking, comparing, regress-testing, or evolving a `SKILL.md`, prompt, agent, command, or reusable workflow
- checking whether a new or edited skill is "good enough"
- creating scenario fixtures, pass/fail rubrics, before/after reports, or a regression ledger for agent behavior
- extracting lessons from external skill packs without wholesale copying

Do not use this skill for ordinary product code changes unless the artifact being improved is itself an agent instruction, skill, prompt, or workflow.

## Workflow

1. Inspect the target first.
   - Read the target `SKILL.md`, prompt, agent, or workflow.
   - Check adjacent skills for overlap before adding new rules.
   - If the work is broad or requires parallel review, run ECC `dynamic-workflow-backlog automode --dry-run` before creating a backlog.

2. Create or reuse scenarios.
   - Prefer 3 to 7 realistic scenarios.
   - Include supportive, neutral, and competing prompts when compliance under weak prompting matters.
   - Use `scripts/scaffold_skill_eval.py` for a repeatable scenario and evidence template.
   - Choose the right scaffold kind with `--target-kind skill|prompt|agent|workflow|commercial-launch|coding-discipline`.

3. Run or collect evidence.
   - Evidence can be deterministic commands, transcript review, model grading, or human review.
   - Store results in the schema described by `references/evidence-schema.md`.
   - Use `scripts/validate_skill_evidence.py` before trusting the evidence file.
   - For promotion checks, require scenario coverage tags, all required strictness lanes, and consistent summary counts.

4. Make bounded edits.
   - Add, delete, or replace only what the evidence supports.
   - Preserve working behavior and avoid broad rewrites.
   - Record rejected ideas in a regression ledger when an edit is plausible but unproven.

5. Compare before and after.
   - Use `scripts/compare_skill_runs.py`.
   - Use `strict-improve` for intentional optimization.
   - Use `no-regression` for maintenance edits.
   - Promote only when the chosen gate passes.

## Quality Gate

A skill change is promotable only when:

- the skill validates with Codex `quick_validate.py`
- at least three realistic scenarios exercise supportive, neutral, and competing behavior
- evidence maps each pass/fail result to a command, transcript, artifact, or reviewer note
- `summary.score`, pass/fail/not-run counts, and scenario results are internally consistent
- no baseline scenario disappears from the after-run evidence
- no higher-priority adjacent skill already covers the same behavior
- the comparison gate is `promote`

Stop and ask before deleting or merging skills, installing the full `skillopt` package, launching costly worker runs, or changing global routing behavior beyond the scoped request.

## Resources

- `references/method.md`: SkillOpt-inspired local method, bounded edit rules, and Matt-style alignment questions.
- `references/evidence-schema.md`: JSON shape for scenario runs and comparison inputs.
- `references/promotion-gate.md`: promotion, rejection, and rollback criteria.
- `references/ecc-skill-suite-contract.md`: shared contract for optimizer, coding judgment, and launch-readiness skill edits.
- `scripts/scaffold_skill_eval.py`: generate scenario and evidence templates.
- `scripts/validate_skill_evidence.py`: validate evidence shape and optional all-pass gates.
- `scripts/compare_skill_runs.py`: compare before/after evidence and return a promotion decision.
- `fixtures/`: baseline regression evidence for this skill, `coding-judgment`, and `commercial-launch-readiness-orchestrator`.
