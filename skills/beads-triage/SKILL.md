---
name: beads-triage
description: "Triage Beads task graphs into a verified, dependency-aware next-action plan."
origin: ECC
---

# Beads Triage Skill

Use this skill when the user asks what to do next, how to prioritize a backlog, whether a Beads graph is healthy, or how to convert `.beads` tasks into a focused execution plan.

## Trigger Phrases

- "triage beads"
- "what should we do next"
- "pick the next task"
- "check .beads"
- "dependency graph"
- "blocked vs ready"

## Workflow

1. Verify whether the current repo has a Beads database:
   ```bash
   test -d .beads || test -f .beads
   ```
2. If Beads tooling is available, prefer non-interactive commands:
   ```bash
   command -v bv
   bv --robot-triage --db .beads --no-cache
   bv --robot-plan --db .beads --no-cache
   ```
3. If `br` is available, use it for durable task graph reads:
   ```bash
   command -v br
   br ready --json
   br list --json
   ```
4. Classify tasks into `ready`, `blocked`, `risky`, `needs evidence`, and `candidate cleanup`.
5. Pick the smallest task that advances the stated user goal without requiring destructive action.
6. Define acceptance criteria and verification commands before editing files.

## Output Contract

Return:
- `Ready now`: top 3 unblocked tasks and why they are next.
- `Blocked`: blockers with owner or missing evidence.
- `Recommended task`: one concrete next action.
- `Acceptance criteria`: observable completion conditions.
- `Verification`: commands or checks to prove completion.

## Safety Rules

- Do not create, close, or rewrite tasks unless the user explicitly asks.
- Do not treat missing `.beads` as failure; fall back to TODOs, issues, docs, and git diff.
- Do not use interactive Beads commands in Codex unless the user is present and the command is safe.
- Separate tool output from your prioritization judgment.
