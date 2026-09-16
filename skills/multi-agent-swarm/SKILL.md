---
name: multi-agent-swarm
description: Supervise complex coding tasks with decomposition, verification, and subagent coordination. Use when a request is multi-step, ambiguous, risky, or benefits from explicit planning, fresh subagents, and evidence-based review.
---

# Multi-Agent Swarm

Use this skill when the task is complex enough that correctness depends on decomposition, fresh context, or independent verification.

## Core Behavior

1. Restate the goal in one or two sentences.
2. Separate facts from assumptions.
3. Build a minimal context pack:
   - goal
   - relevant files
   - current state
   - risks
   - verification targets
4. Decompose the work into the smallest independently verifiable steps.
5. Use fresh subagents only when the task boundaries are genuinely independent and the platform supports them.
6. Require evidence before claiming success.
7. Preserve existing user changes unless explicitly told otherwise.

## Codex-Native Subagent Launch Contract

Use Codex-native subagents only when the user or active goal explicitly asks for parallel agents, subagents, delegation, or multi-agent execution. Skill text alone is not enough. If explicit delegation is absent, prepare a decomposition plan or dynamic backlog and ask for the missing approval instead of spawning.

When native subagents are available:

- Default to 2-4 agents. Never exceed 6 agents in one wave.
- Use native subagents for read-heavy exploration, review, validation, or independent research.
- Use ECC `dynamic-workflow-backlog` plus tmux/worktree workers for write-heavy implementation, build/test execution, or any task that needs isolated git state.
- Give every agent a disjoint ownership scope: files, packages, subsystems, questions, or evidence targets.
- Prefer read-only reviewer roles when the task is review, mapping, or refutation.
- Do not allow nested spawning. A spawned worker must not spawn subagents or external agents.
- Record a proof ledger at `.codex/multi-agent-runs/<run>/STATUS.md` before final synthesis.
- Before launching or assigning a wave, write a five-step lookahead: the next five concrete steps, the expected evidence from each step, and the stop condition that would prevent the following step.

Every native subagent prompt must start with this isolation prefix:

```text
You are a delegated subagent for one bounded task. Inherited context is reference only. Do not create, resume, update, or complete Codex goals. Do not continue the parent thread or project goal. Perform only the named task below, stay inside the assigned scope, do not stage or commit unless explicitly authorized, do not spawn more agents, and report evidence back once.
```

The parent agent remains responsible for synthesis, verification, and the final answer.

## Next Five Steps Lookahead

Before any parallel wave, state:

1. the immediate repo/runtime fact to verify
2. the safe lane split and ownership boundaries
3. the execution surface for each lane: native read/review subagent, tmux/worktree worker, Codex app worktree, or serial main-thread work
4. the evidence each lane must return before synthesis
5. the next adjustment if a lane fails, overlaps, or lacks tool support

Keep the lookahead practical. Update it when evidence changes, and do not let it justify broad ownership expansion.

## Decision Rules

- Use parallel subagents only when work can proceed without shared mutable state.
- Do not spawn native subagents for broad write access in the same checkout; use isolated worktrees or run the work serially.
- If native subagent tool availability is unverified, state that and use a backlog or sequential fresh-context pass.
- Prefer local file reads, focused searches, and small context slices over broad dumps.
- If a requirement is ambiguous, define the ambiguity explicitly and carry it as a risk.
- If a change is destructive or hard to reverse, require a backup plan and explicit approval before proceeding.
- If verification fails repeatedly or confidence is too low to defend the result, stop and report the blocker.

## Execution Loop

1. Scope the task.
2. Plan the next concrete step.
3. Execute the step with the smallest useful context.
4. Verify with real evidence.
5. Synthesize what changed and what remains.
6. Repeat until the requested end state is true or a real blocker appears.

## Verification Standards

- Prefer command output, rendered artifacts, tests, or inspected runtime behavior over narrative claims.
- Do not mark work complete without checking the relevant artifact or command result.
- Distinguish:
  - complete
  - incomplete
  - unverified
  - blocked

## Reporting

When summarizing work, report:

- what changed
- what was verified
- what remains risky or unverified
- the next best step

Keep the report concise and specific.
