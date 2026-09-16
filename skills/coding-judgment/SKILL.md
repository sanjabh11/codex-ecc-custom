---
name: coding-judgment
description: Apply repo-first, simple, surgical coding discipline for implementation, bug fixing, refactoring, code review, architecture decisions, and unclear technical requests. Use when the user asks to code, fix, debug, refactor, review, simplify, diagnose a bug or performance regression, choose an implementation approach, or avoid overengineering while preserving proof boundaries.
---

# Coding Judgment

## Purpose

Use this skill to keep coding work grounded, small, and verifiable. It adapts four practical rules for Codex/ECC: inspect before assuming, prefer simple implementations, change only what the goal requires, and verify before claiming success.

## Activation

Use this skill when the user asks to code, fix, debug, diagnose, refactor, simplify, review, choose an implementation approach, harden a regression, or evaluate whether a change is overengineered.

Auto-trigger parameters:

- a repo path, stack, file, failing test, bug report, runtime error, or feature request is present
- the task asks for implementation or code review rather than reusable instruction improvement
- the user asks for "best way", "simplest", "surgical", "safe", "debug", "root cause", or "avoid overengineering"

Use `skill-optimizer` instead when the artifact being improved is a `SKILL.md`, prompt, agent, workflow, or routing rule. Use `commercial-launch-readiness-orchestrator` when the main goal is one-repo commercial readiness, market pain, launch decision, or outreach planning.

## Workflow

1. Inspect first.
   - Read the relevant files, tests, config, docs, and runtime evidence before deciding.
   - State important assumptions only after checking what can be discovered locally.
   - If the request has multiple plausible meanings, surface the options and pick the safest bounded default unless the choice is risky.

2. Define success.
   - Convert the request into a concrete acceptance check.
   - Prefer repo-native tests, build, lint, typecheck, browser smoke, or command evidence.
   - Separate proven behavior from local-only, artifact-only, candidate, or roadmap claims.

3. Choose the simplest lever.
   - Do not add abstractions, configurability, framework changes, or broad rewrites without evidence.
   - Match the existing codebase style even when another style is personally preferable.
   - If a simpler approach exists, call it out and use it when it satisfies the goal.

4. Change surgically.
   - Touch only files needed for the user goal.
   - Preserve unrelated dirty worktree changes.
   - Mention unrelated issues instead of fixing them opportunistically.

5. Diagnose before fixing unclear bugs.
   - Reproduce the issue or identify the closest available evidence.
   - Minimize the failing surface.
   - Form one or two testable hypotheses.
   - Instrument or inspect before changing code.
   - Fix the confirmed cause and add or run a regression check.

6. Verify and hand off.
   - Run the narrowest useful verification first.
   - Report commands run, failures, not-run reasons, and residual risk.
   - Do not claim production, security, readiness, or performance status without matching proof.

## Quality Gate

A coding answer is acceptable only when:

- relevant repo files, configs, tests, logs, or runtime surfaces were inspected before the change
- assumptions are stated and do not replace cheap local verification
- the change is the smallest viable lever for the acceptance check
- unrelated dirty worktree changes are preserved
- verification is run or the not-run reason is explicit
- final claims are assigned to the correct proof bucket

For unclear bugs, do not edit before the diagnosis loop has at least one concrete reproduction, log, failing command, or narrowed evidence source.

## Stop Gates

Stop and ask before destructive actions, production deploys, credential changes, payment changes, migrations, broad formatting, large refactors, or changes that require secrets or external account access.

## Reference

Read `references/checklist.md` when the task is ambiguous, high-risk, or likely to sprawl.
Read `references/ecc-skill-suite-contract.md` before changing this skill or using it as part of a broader ECC skill-suite update.
