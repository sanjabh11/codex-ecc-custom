# Workflow Equivalence And Gaps

This skill is a Codex/ECC harness inspired by Claude Dynamic Workflows, not a native Claude `/workflows` runtime.

## Source Baseline

- Claude Dynamic Workflows announcement: https://claude.com/blog/introducing-dynamic-workflows-in-claude-code
- Claude workflow harness article: https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code
- Claude subagents docs: https://code.claude.com/docs/en/sub-agents
- Claude worktrees docs: https://code.claude.com/docs/en/worktrees

## Equivalence Map

| Claude Dynamic Workflow Concept | Codex/ECC Equivalent | Boundary |
|---|---|---|
| Dynamic workflow trigger | `dynamic-workflow-backlog automode --dry-run` | Explicit and file-backed, not automatic native `/workflows`. |
| Generated orchestration harness | `scaffold_launch_workflow.py` plus ECC Node runner | Scaffold is deterministic; it prints commands and task graph. |
| Parallel subagents | `run-workers --execute --adapter tmux-worktree` | Requires explicit approval and local Codex worker runtime. |
| Worktree isolation | ECC `tmux-worktree` adapter | Worktree merge/review remains operator-managed. |
| Progress UI | `watch`, `dashboard`, `dashboard --print-html` | Generic ECC dashboard, not a native Claude workflow panel. |
| Resumability | `.dynamic-workflows/<run>` files | Worker transcript continuation is weaker than native subagent resume. |
| Evidence collection | worker handoffs, `results.jsonl`, `claims.jsonl` | Evidence quality depends on prompts and review gates. |
| Adversarial convergence | lane-specific review tasks and `synthesize` | Reviews must be added explicitly by scaffold commands. |
| Token risk warning | ECC token warning estimates and budget option | No exact model-token accounting unless worker output exposes it. |
| First-run confirmation | dry-run-first and execute-only-after-approval rule | This is stricter and safer for commercial launch work. |

## Practical Boundary

Use this skill when the objective is a high-value commercial launch audit that benefits from durable state, evidence review, and safe worker execution. Do not describe it as Claude native `/workflows`; describe it as a Codex-native workflow harness around ECC backlog and runner primitives.

## Current Gaps

- The scaffold can tailor prompts by profile, but it does not generate a new JavaScript harness per task.
- The ECC dashboard is status-focused; launch scoring still lives in the final report and evidence JSON.
- Worker execution requires operator approval and local runtime health.
- Portfolio comparison only works after completed one-repo evidence JSON files exist.
