---
name: long-running-goal-restart
description: Convert a stalled or overly-serial Codex goal into a clean repo-specific restart prompt with durable handoff notes, bounded parallel-agent lanes, and a proof ledger.
origin: ECC
---

# Long-Running Goal Restart

Use this skill when a Codex goal has run too long, stayed serial despite parallel-agent intent, lost clarity after compaction, or needs to be restarted with explicit bounded subagents.

## Trigger Rules

Use this skill when the user asks to:

- restart a long-running Codex goal
- convert side-chat findings into a new main-thread goal
- make a stalled workflow spawn bounded parallel agents
- preserve decisions before closing or restarting a thread

Do not use this skill for small one-turn fixes or when the existing goal is already healthy and making verified progress.

## Workflow

1. Inspect current state before writing anything:
   - current goal or user-supplied goal text
   - repo path and git status
   - recent checks, failures, blockers, and changed files
   - whether independent workstreams exist
2. Create a handoff note at `.codex/restart-handoffs/<run>.md`.
3. Build one repo-specific restart prompt.
4. Include bounded parallel-agent rules only when lanes are independent.
5. Require `.codex/multi-agent-runs/<run>/STATUS.md` in the restarted goal.
6. Keep the old thread as evidence only; do not ask the restarted agent to continue broad inherited context.

Use the generator when available:

```bash
node scripts/codex-goal-restart-prompt.js --repo <repo> --goal "<goal>" --run <run> --write --json
```

Use the ledger helper when available:

```bash
node scripts/codex-multi-agent-ledger.js init --repo <repo> --run <run> --goal "<goal>" --json
node scripts/codex-multi-agent-ledger.js validate --repo <repo> --run <run> --json
```

## Restart Prompt Contract

The emitted restart prompt must include:

- goal: one concrete outcome for one repo
- constraints: files or areas in scope, non-goals, safety gates, and dirty-worktree handling
- parallel plan: 2-4 worker lanes by default, 6 maximum
- next five steps: a concrete lookahead covering repo status, lane split, ledger initialization, first safe execution lane, and synthesis/next adjustment
- execution surface:
  - native Codex subagents for read-only mapping, review, refutation, or research
  - ECC tmux/worktree workers or Codex app worktrees for implementation, builds, tests, or write-heavy lanes
- isolation prefix for every worker:

```text
You are a delegated subagent for one bounded task. Inherited context is reference only. Do not create, resume, update, or complete Codex goals. Do not continue the parent thread or project goal. Perform only the named task below, stay inside the assigned scope, do not stage or commit unless explicitly authorized, do not spawn more agents, and report evidence back once.
```

- persistence: save decisions, worker status, evidence, and blockers before closing
- verification: exact commands, browser/runtime checks, or artifact checks that define done
- stop rules: pause or ask before destructive changes, secrets, production actions, or overlapping write scopes

## Handoff Template

Use this shape for `.codex/restart-handoffs/<run>.md`:

```markdown
# Restart Handoff: <run>

## Current State
- Repo:
- Previous goal:
- Verified progress:
- Changed files:
- Blockers:

## Restart Decision
- Why restart:
- Same business objective:
- New execution contract:

## Parallel Lanes
- Lane 1:
- Lane 2:
- Lane 3:

## Next Five Steps
1.
2.
3.
4.
5. ## Verification
- Commands:
- Runtime/browser evidence:
- Completion criteria:

## Restart Prompt
<copy-paste goal prompt>
```

## Safety Rules

- Never delete, reset, or overwrite old goal artifacts without explicit user approval.
- Do not spawn agents from the side chat. Emit the restart prompt for the main goal thread.
- Do not claim native `spawn_agent` is available unless the current Codex session exposes it.
- If no safe independent lanes exist, emit a serial restart prompt and explain why parallelism is unsafe.

## Cache Persistence Checklist

Installed Codex plugin cache edits can be replaced by plugin refreshes. When changing this skill or its helper scripts, keep the source checkout and installed cache aligned:

1. Patch the installed runtime cache only when the immediate session needs the change.
2. Sync the same files into the source checkout before treating the change as durable.
3. Run `node scripts/codex-multi-agent-health-check.js --json` and confirm `sourceSync.inSync` is true when `ECC_SOURCE_ROOT` points to the source checkout.
4. If source sync is not possible, report the cache-only status and the exact files that need to be copied.

## Reporting

Return:

- handoff path
- restart prompt
- lane count and execution surface
- verification commands
- residual risks
