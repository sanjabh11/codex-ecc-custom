---
name: dynamic-workflow-backlog
description: "Simulate Claude Code Dynamic Workflows in Codex using a file-backed JavaScript backlog runner, bounded worker plans, resumable state, and adversarial verification tasks."
origin: ECC
---

# Dynamic Workflow Backlog

Use this skill when a task is too large for one turn and the user wants Claude Code Dynamic Workflow-style behavior in Codex.

This is an ECC/Codex simulation, not Anthropic's native Dynamic Workflows runtime. Codex does not currently expose the same `/workflows` runtime in this session. This skill preserves the useful operating pattern: executable orchestration, bounded fan-out, file-backed state, resumability, adversarial verification, and a final converged report.

## Activation

Use when the user asks for:
- dynamic workflows
- workflow backlog
- ultracode-style orchestration
- many-agent decomposition
- multi-agent, multi-spawn, or multi-spawning execution
- subagents, spawn agents, spawn subagents, or agent team execution
- parallel audit, migration, or research
- resumable agent runs
- adversarial cross-checking

## Automatic Launch Gate

The model should decide automatically. Use `automode` as the default decision command:

```bash
node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js automode --task "<task>"
```

If you only need the decision without creating files, use:

```bash
node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js classify --task "<task>"
```

`automode` returns one of these actions:

| Action | Meaning |
|---|---|
| `skip` | Do not create a dynamic backlog; use normal `agent-phase-ratchet`. |
| `create-backlog` | Create `.dynamic-workflows/<run>/` and generated `workflow.js`; do not spawn workers. |
| `plan-only` | Create a safe backlog but stop before worker export/execution until approval. |
| `forced-backlog` | Create a backlog because the caller passed `--force` despite low score. |

## Codex Launch Ladder

Use this order for Codex parallel execution:

1. Classify with `automode --dry-run`.
2. Create or reuse the durable backlog.
3. Preview work with `run-workers --dry-run`.
4. Preflight `codex`, `git`, `tmux`, worker script, repo root, and writable run directory before `run-workers --execute`.
5. Choose the execution surface:
   - native Codex subagents for read-only mapping, review, refutation, or research
   - ECC tmux/worktree workers or Codex app worktrees for implementation, builds, tests, or any write-heavy lane
6. Execute only when the user or goal explicitly requested parallel workers and the dry-run plus preflight are safe.
7. Collect evidence, update the backlog, and synthesize only after verification.

Do not silently convert a backlog into spawned workers. The launch ladder makes the decision visible and auditable.

Launch `dynamic-workflow-backlog` when `automode` returns `create-backlog` or `plan-only`, or when the request has any hard trigger:

| Condition | Launch decision |
|---|---|
| User explicitly says dynamic workflow, workflow backlog, many-agent, multi-agent, subagents, spawn agents, swarm, resumable, or adversarial verification | Launch |
| Tier 2 or Tier 3 task with 3+ independent workstreams | Launch |
| Large repo-wide audit, migration, redesign, benchmark sweep, or security review | Launch |
| Task needs durable state because it may span turns, interruptions, or multiple workers | Launch |
| Task needs independent refutation before final synthesis | Launch |
| Small single-file edit, quick explanation, typo fix, or one-off answer | Do not launch |
| Parallel workers would touch the same mutable files without clear ownership | Do not launch; use normal PhaseLoop |
| Destructive, production, secret, or security-sensitive execution is possible | Create plan-only backlog and stop for approval before execution |

Default model route:

1. Run `workflow-audit-router` for ambiguous tasks.
2. Run `automode --task "<task>"` when the task might require dynamic orchestration.
3. If `action: "skip"`, continue with `agent-phase-ratchet`.
4. If `action: "plan-only"`, create the backlog and stop for approval before worker export/execution.
5. If `action: "create-backlog"`, work from the backlog in the main session or export worker plans after dry-run review.
6. If the user explicitly requested parallel agents, run `run-workers --dry-run`, preflight write-heavy execution, and choose native subagents for read/review lanes or tmux/worktree or Codex app worktrees for write-heavy lanes.

## Mapping From Claude Dynamic Workflows To Codex

| Claude Dynamic Workflows | Codex/ECC simulation |
|---|---|
| Workflow script | `dynamic-workflow-backlog.js` plus `.dynamic-workflows/<run>/workflow.json` |
| Script variables hold intermediate state | JSON/JSONL backlog, results, claims, and review files |
| Subagents | Codex worker prompts, optional tmux/worktree workers, or manual fresh-context subtasks |
| `/workflows` progress view | `status`, `watch`, `dashboard`, and worker wave coordination files |
| Resumability | Re-run `status` or `next`; completed tasks remain recorded |
| Adversarial verification | Add review tasks with `add-review` before final synthesis |
| Save as command | Use `slash-workflow-pack` after a run proves useful |

## Workflow

1. Start with `agent-phase-ratchet` and classify the task.
2. Use this skill only for Tier 2 or Tier 3 work, or for an explicit dynamic workflow request.
3. Run the launch classifier:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js automode --task "Audit all API routes for missing auth checks"
   ```

4. Create a durable workflow plan automatically:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js plan \
     --name "repo-auth-audit" \
     --task "Audit all API routes for missing auth checks with adversarial verification"
   ```

   Use manual `init` only when you already know the exact task graph:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js init \
     --name "repo-auth-audit" \
     --goal "Audit all API routes for missing auth checks" \
     --task "map|mapper|Map route surface|List routes and auth middleware evidence" \
     --task "audit|auditor|Find auth gaps|Inspect mapped routes for missing checks" \
     --task "verify|adversary|Refute findings|Try to disprove each claimed gap"
   ```

5. Work from the backlog:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js next --run .dynamic-workflows/repo-auth-audit
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js claim --run .dynamic-workflows/repo-auth-audit --task T001 --agent codex-main
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js complete --run .dynamic-workflows/repo-auth-audit --task T001 --status pass --summary "Mapped 17 routes" --evidence "rg route output"
   ```

6. Explicitly preview and launch Codex worker waves when parallel execution is worth the overhead:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js run-workers \
     --run .dynamic-workflows/repo-auth-audit \
     --dry-run
   ```

   The dry-run prints the wave plan and selected runnable tasks without mutating task state. Launch workers only when execution is explicit:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js run-workers \
     --run .dynamic-workflows/repo-auth-audit \
     --execute \
     --adapter tmux-worktree
   ```

   Worker execution preflights `codex`, `git`, `tmux`, the worker launcher, the repo root, and writable run directory before materializing the wave or marking tasks running. If preflight fails, the command returns a structured `launched: false` response and leaves task state unchanged.

   Worker execution uses the installed ECC tmux/worktree launcher and captures status/handoff files under `waves/<wave-id>/`. Collect completed worker evidence back into the backlog:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js collect-workers \
     --run .dynamic-workflows/repo-auth-audit \
     --wave <wave-id>
   ```

   Worker configuration can be passed per wave. Pass model/profile only when you intentionally want to override the current Codex runtime:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js run-workers \
     --run .dynamic-workflows/repo-auth-audit \
     --execute \
     --model <model> \
     --profile <profile> \
     --sandbox workspace-write \
     --timeout-seconds 3600
   ```

7. Use progress controls while a run is active:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js watch --run .dynamic-workflows/repo-auth-audit
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js dashboard --run .dynamic-workflows/repo-auth-audit --port 8765
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js pause --run .dynamic-workflows/repo-auth-audit
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js resume --run .dynamic-workflows/repo-auth-audit
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js retry --run .dynamic-workflows/repo-auth-audit --task T002
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js cancel --run .dynamic-workflows/repo-auth-audit --task T003
   ```

   `plan-only` workflows must be approved before execution:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js resume \
     --run .dynamic-workflows/repo-auth-audit \
     --approve-execution
   ```

8. Shard large target lists when work can be split safely:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js shard \
     --run .dynamic-workflows/repo-auth-audit \
     --path "src/api/users.ts" \
     --path "src/api/admin.ts" \
     --prompt-template "Audit {target} for missing auth checks and cite file evidence."
   ```

9. Add adversarial checks before final synthesis:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js add-reviews \
     --run .dynamic-workflows/repo-auth-audit
   ```

   Use one-off `add-review` when a specific result needs deeper challenge.

10. Gate the final answer through synthesis:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js synthesize \
     --run .dynamic-workflows/repo-auth-audit
   ```

11. Export an optional tmux/worktree plan only when you need a standalone plan file instead of `run-workers`:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js export-worktree-plan \
     --run .dynamic-workflows/repo-auth-audit \
     --out .orchestration/repo-auth-audit.json
   ```

   Then review the dry-run before standalone execution:

   ```bash
   node scripts/orchestrate-worktrees.js .orchestration/repo-auth-audit.json
   ```

## Safety Rules

- Default to backlog and dry-run. `automode` never spawns Codex workers by itself.
- `run-workers` also defaults to preview behavior unless `--execute` is explicit.
- `plan-only` workflows refuse worker execution until `resume --approve-execution` records approval.
- Native Codex subagents are for read/review/research lanes unless the user gives a narrow write scope in the same checkout.
- Use tmux/worktree workers for write-heavy lanes because they start in isolated worktrees.
- Every worker prompt must isolate itself from the parent goal and must not create, resume, update, or complete Codex goals.
- Use `--max-concurrency` no higher than 16 and `--max-agents` no higher than 1000.
- Do not use this for small one-file tasks.
- Keep destructive changes outside worker tasks unless the user explicitly approves them.
- Workers must have disjoint ownership when they edit files.
- `cancel` records cancellation state only; it does not kill active worker panes unless a future explicit kill implementation is added.
- Treat the final synthesis as unproven until `synthesize` reports `ready: true`.
- Treat medium/high token warnings as a reason to start scoped before exporting worker plans.

## Output Contract

Return:
- run path
- task counts by status
- next runnable tasks
- verification/adversarial tasks
- exported plan path when created
- synthesis readiness and blockers
- token warning
- proof commands run
- residual risks
