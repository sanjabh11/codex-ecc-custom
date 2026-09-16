---
name: commercial-launch-readiness-orchestrator
description: Orchestrate one-repository commercial launch audits using ECC dynamic workflow backlog and worker runner. Use when evaluating a repo for security, launch readiness, sellability, market pain points, target customers, outreach planning, proof-backed launch decisions, or safe P0/P1 commercial-readiness fixes.
---

# Commercial Launch Readiness Orchestrator

## Purpose

Use this skill to audit exactly one repository at a time for commercial launch. The workflow is repo-first, evidence-bound, current-research-backed, and compatible with Everything Claude Code (ECC) dynamic workflow backlog runs.

Default outcome: a launch decision, gap analysis, market pain map, target customer ranking, outreach plan, safe fix report, structured evidence manifest, and ECC ledger.

This skill is a Codex/ECC workflow harness, not Claude native `/workflows`. It recreates the useful pattern with explicit backlog files, worker dry-runs, tmux/worktree execution when approved, evidence collection, dashboard/watch status, and synthesis gating.

## Hard Rules

- Require one absolute repository path per run. Do not audit three repos in one pass; run this skill three times, then compare the three completed evidence reports.
- Inspect repository truth before internet research: stack, routes, auth, APIs, DB/RLS, envs, CI, deployment targets, docs, user flows, tests, and existing proof artifacts.
- Use internet research for current security practice, competitor/substitute analysis, buyer pain, target accounts, and outreach claims. Cite source links in final deliverables.
- Separate proof buckets: hosted/live, local, repo artifact, candidate/shadow, roadmap.
- Run `dynamic-workflow-backlog automode --dry-run` before creating the backlog.
- Always run `run-workers --dry-run` before any worker execution.
- Use `run-workers --execute` only after explicit user approval and only when tasks are independent, bounded, and safe to run.
- Generate lane-specific adversarial review tasks by default; final claims should pass review before synthesis.
- Do not perform production deploys, credential rotation, payment changes, live outreach, destructive actions, data deletion, or secret-dependent tests without explicit approval.
- Safe fixes are limited to deterministic P0/P1 repo-side changes that do not need secrets, production access, payments, destructive migrations, or external account actions.
- Any repo-side code decision must pass the Code Optimization Gate before implementation: compare the smallest safe options, reject unnecessary code, avoid new dependencies or abstractions without evidence, and verify the chosen change.

## Quick Start

Generate a one-repo workflow scaffold:

```bash
python3 /Users/sanjayb/.codex/skills/commercial-launch-readiness-orchestrator/scripts/scaffold_launch_workflow.py \
  --repo /absolute/path/to/repo \
  --name launch-readiness-audit \
  --mode audit-only \
  --profile auto \
  --budget standard \
  --research-depth deep \
  --optimization-policy strict \
  --worker-mode dry-run
```

The scaffold prints exact ECC dynamic workflow commands. It does not execute them.

Useful options:

- `--profile auto|saas|ai-app|data-app|devtool|marketplace|internal-tool`
- `--budget conservative|standard|aggressive`
- `--research-depth light|standard|deep`
- `--progress-policy phase|interval|both|off`
- `--progress-interval-minutes 45`
- `--stall-threshold-minutes 120`
- `--optimization-policy off|safe|strict|measured`
- `--emit-report-template`
- `--include-reviews` or `--no-include-reviews`

## Workflow

1. Validate inputs
   - Confirm the repo path is absolute, exists, and is the only repo in scope.
   - Check git status before editing. Never revert unrelated user changes.
   - Verify the installed ECC runner path:
     `/Users/sanjayb/.codex/plugins/cache/local-codex-marketplace/everything-claude-code/1.9.0/skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js`

2. Select profile and budget
   - Use `--profile auto` when the repo type is unknown. The scaffold does not inspect the repo; it emits a repo-profiler task that decides the profile during the real audit.
   - Use explicit profiles when known: `saas`, `ai-app`, `data-app`, `devtool`, `marketplace`, or `internal-tool`.
   - Budget controls generated concurrency: conservative `2`, standard `4`, aggressive `8`, unless `--max-concurrency` is explicit.

3. Repo map
   - Identify stack, package managers, app entry points, routes/pages, auth/session model, APIs, database/RLS, background jobs, env files, CI, deploy targets, docs, tests, and analytics/observability.
   - Create an initial proof ledger with source file paths, commands run, and unknowns.

4. Dynamic backlog gate
   - Run:
     ```bash
     node /Users/sanjayb/.codex/plugins/cache/local-codex-marketplace/everything-claude-code/1.9.0/skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js automode --dry-run --task "<commercial launch audit goal>"
     ```
   - If automode recommends `skip`, continue with a normal focused audit.
   - If automode recommends `create-backlog`, create the backlog and preview workers.
   - If automode recommends `plan-only`, create the safe backlog but do not execute workers until the approval gate is cleared.

5. Audit lanes
   - Security: map findings to OWASP, NIST SSDF, CISA Secure by Design, and NIST AI RMF where relevant.
   - Readiness: verify build/test/lint/browser smoke where safe; distinguish live proof from local proof.
   - Sellability: score buyer-visible value, proof-backed benefits, onboarding, pricing/pilot readiness, demo narrative, and weak claims.
   - Market research: discover top 10 pain points with current sources and willingness-to-pay signals.
   - Target customers: rank top 10 accounts or segments by buyer pain, proof fit, urgency, trigger events, access path, and confidence.
   - Safe fix lane: implement only bounded P0/P1 repo-side fixes when mode allows it, and only after the Code Optimization Gate selects the smallest safe verified variant.
   - Adversarial review: refute each major lane before final synthesis.

6. Worker runner flow
   - Create or use a run directory under the repo, usually `.dynamic-workflows/<run-name>`.
   - Add lane-specific review tasks after backlog init when review generation is enabled.
   - Preview:
     ```bash
     node <runner> run-workers --run <run-dir> --dry-run
     ```
   - Execute only after approval:
     ```bash
     node <runner> run-workers --run <run-dir> --execute --adapter tmux-worktree
     ```
   - Collect evidence:
     ```bash
     node <runner> collect-workers --run <run-dir> --wave <wave-id>
     ```
   - Review progress:
     ```bash
     node <runner> watch --run <run-dir>
     node <runner> dashboard --run <run-dir> --port 8765
     python3 /Users/sanjayb/.codex/skills/commercial-launch-readiness-orchestrator/scripts/render_progress_digest.py --run <run-dir> --repo <repo-path>
     ```
   - Gate final answer:
     ```bash
     node <runner> synthesize --run <run-dir>
     ```

## Long-Running Progress Updates

This skill must proactively report progress for long-running jobs. This is an agent reporting contract plus generated digest commands; it is not a hidden daemon or automatic background monitor.

Default reporting rules:

- Emit a progress digest after each phase completion.
- Emit a progress digest after every worker wave is launched or collected.
- Emit a progress digest every 45 minutes while the run is active.
- If no meaningful task, worker, or evidence status changes for 120 minutes, emit a bottleneck digest before continuing.
- For any run active for 20 hours or more, emit an immediate bottleneck digest before doing more research, fixes, or synthesis.

Every progress digest must include:

- accomplished work: completed lanes, evidence collected, files/reports/checks produced
- target accomplishment matrix: lane, target weight, current percent, status, evidence, confidence
- pending work: remaining tasks, missing evidence, unresolved blockers
- activities remaining: current phase and next phase action counts
- current bottleneck: exact task/subtask, elapsed time, last update, affected lane
- root cause: context overload, ambiguous requirements, dependency issue, test loop, search/exploration, decision paralysis, tool delay, worker failure, or evidence gap
- top three unblock options with tradeoff, expected time saved, and risk
- synthetic market/customer data only when clearly labeled as hypotheses and never as proof for `commercial-ready`

## Code Optimization Gate

Use this gate for every coding decision, code patch, fix plan, or implementation variant in the safe-fix lane. This is a bounded proof gate, not a claim of global optimality.

Default policy: `strict`.

Policy modes:

- `off`: do not add optimization review tasks; still follow normal `coding-judgment` safety.
- `safe`: require a smallest-safe-change check before implementation.
- `strict`: require a variant comparison, rejected-variant ledger, focused verification, and code-optimization review for any repo-side code change.
- `measured`: use `strict`, and add benchmark or performance measurements when the gap involves latency, throughput, memory, bundle size, cost, or build/test duration.

Before implementing any code change:

- Define the acceptance check and proof bucket.
- Compare at least these variants when relevant: no-code/defer, config-only, test/doc-only, minimal code patch, and broader refactor.
- Choose the smallest variant that satisfies the acceptance check and preserves repo patterns.
- Reject new files, dependencies, abstractions, architecture changes, broad rewrites, or generated code unless evidence shows they are necessary.
- Run focused verification after the change and record commands, outputs, failures, or not-run reasons.
- Record `implementation_decisions`, `rejected_variants`, and `code_optimization_reviews` in the launch evidence JSON when code changes are made.

For running jobs that were launched before this gate existed, do not restart the whole workflow. Add a `code-optimization-reviewer` review task to any active or completed safe-fix task, then retry only stale or failed code-changing tasks if needed.

7. Final synthesis
   - Do not present a commercial-ready claim unless the repo, runtime checks, market sources, structured evidence, and adversarial review support it.
   - Assign one launch decision: `blocked`, `pilot-only`, `sellable-with-caveats`, or `commercial-ready`.
   - Include unresolved approval gates and owner-side dependencies.
   - Emit a launch evidence JSON if a portfolio comparison will be needed later.
   - Validate the evidence JSON before portfolio comparison:
     ```bash
     python3 /Users/sanjayb/.codex/skills/commercial-launch-readiness-orchestrator/scripts/validate_launch_evidence.py <launch-evidence.json>
     ```

## Portfolio Rollup

Use `scripts/compare_launch_reports.py` only after separate one-repo runs have produced completed launch evidence JSON files. The helper refuses raw repo directories; it compares evidence reports, not source repositories.

The helper validates each input against `scripts/validate_launch_evidence.py` before ranking.

## Cross-Skill Use

- Use `coding-judgment` for the safe fix lane and any repo-side implementation decisions.
- Use `skill-optimizer` before changing this skill, its prompts, report templates, or ECC routing.
- Use ECC `benchmark-optimization-loop` only when the code decision has a measurable performance target or regression risk; otherwise prefer the Code Optimization Gate above.
- Use the dynamic workflow runner only after `automode --dry-run`; worker execution remains explicit.

## Required References

Load only the reference files needed for the run:

- `references/security-readiness-framework.md` for security, readiness, proof buckets, and launch decision criteria.
- `references/market-outreach-framework.md` for pain-point research, customer ranking, outreach scripts, and CRM/export schema.
- `references/workflow-equivalence-and-gaps.md` for Claude Dynamic Workflows versus Codex/ECC mapping.
- `references/launch-evidence-schema.md` for structured evidence JSON.
- `references/progress-reporting-contract.md` for long-running status, target matrix, bottleneck, and synthetic-data rules.
- `references/code-optimization-contract.md` for minimal-code decisions, variant comparison, verification, and optimization review.
- `references/final-report-template.md` for the required Markdown report format.
- `references/one-repo-run-prompt.md` when the user wants a paste-ready prompt for another Codex thread or repo.
- `references/ecc-skill-suite-contract.md` when this skill is edited with `skill-optimizer` or `coding-judgment`.

## Required Output Tables

Every completed run must include:

- Launch score: security, readiness, sellability, evidence, and overall scores out of 5.
- Gap analysis: gap, severity, evidence, framework mapping, buyer impact, fix, status.
- Pain points: top 10 buyer pain points with source evidence and willingness-to-pay signal.
- Target customers: top 10 accounts or segments with pain, trigger, decision maker, outreach angle, and confidence.
- Outreach plan: 30/60/90 plan, email script, LinkedIn script, demo narrative, objection handling.
- Fix report: files changed, tests run, unresolved blockers, and approval gates.
- Code optimization report: implementation decisions, rejected variants, optimization reviews, and verification evidence for any code changes.
- Structured evidence manifest matching `references/launch-evidence-schema.md`.
- Progress updates and bottleneck log for long-running jobs.
- `validate_launch_evidence.py` pass or a clear list of validation failures.
- ECC ledger: route, tier, mode, skills/tools, baseline, checks, delta, decision, next adjustment.

## Stop Gates

Stop and ask before:

- Any production deploy, migration, data deletion, account deletion, live payment change, or secret rotation.
- Any worker execution that could spend substantial tokens or touch overlapping files.
- Any claim that requires unavailable secrets, external account access, paid tooling, legal advice, medical advice, financial advice, or customer contact.
- Any launch decision that would depend on unverified hosted/live behavior.
