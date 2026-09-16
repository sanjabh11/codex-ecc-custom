# One-Repo Commercial Launch Run Prompt

Copy this prompt into a new Codex thread when you want to run the orchestrator on a single repository.

```text
@commercial-launch-readiness-orchestrator
@everything-claude-code
@Browser

Audit this one repository for commercial launch readiness:

Repo path:
<ABSOLUTE_REPO_PATH>

Mode:
audit-only

Profile:
auto

Budget:
standard

Research depth:
deep

Worker mode:
dry-run first. Do not execute workers until I explicitly approve.

Progress policy:
Use progress policy `both`: report after each phase/wave and every 45 minutes. If no meaningful status changes for 120 minutes, produce a bottleneck digest before continuing. If the run reaches 20 hours, produce an immediate bottleneck digest before more research, fixes, or synthesis.

Optimization policy:
Use optimization policy `strict`: before any repo-side code decision, compare no-code/defer, config-only, test/doc-only, minimal-code, and broader-refactor variants when relevant. Implement only the smallest safe verified variant. Record implementation decisions, rejected variants, tests/checks, and code-optimization review evidence for every code change.

Goal:
Undertake systematic, ultra-focused repo-first research on this complete codebase. Map the real implementation, routes, auth, APIs, DB/RLS, envs, CI, deploy targets, docs, user flows, tests, proof artifacts, and runtime gaps before using internet research. Then use current internet research to verify security best practices, buyer pain points, competitors/substitutes, target customers, and outreach strategy.

Use the installed ECC dynamic-workflow-backlog runner when appropriate:
1. Run automode dry-run.
2. Create a repo-specific backlog under .dynamic-workflows/<run-name> if automode recommends it.
3. Add lane-specific adversarial review tasks.
4. Run run-workers --dry-run first.
5. Execute workers only if tasks are independent, safe, and I approve.
6. Collect worker evidence.
7. Review progress with watch or dashboard.
8. Render a launch-specific progress digest with `render_progress_digest.py`.
9. Add or verify a `code-optimization-reviewer` review task for the safe-fix lane before accepting code changes.
10. Gate final response through synthesize.

Required phases:
1. Repo Map
2. Security Audit
3. Readiness Audit
4. Sellability Audit
5. Market Research
6. Target Customer Ranking
7. Safe Fix Lane
8. Adversarial Review

Required final outputs:
- Launch decision table with security, readiness, sellability, evidence, and overall scores out of 5.
- Gap analysis table: gap, severity, evidence, framework mapping, buyer impact, fix, status.
- Top 10 pain points table with source evidence and willingness-to-pay signal.
- Top 10 target customers/accounts/segments table with pain, trigger, decision maker, outreach angle, confidence.
- Outreach plan with 30/60/90 plan, email script, LinkedIn script, demo narrative, and objection handling.
- Fix report with files changed, tests run, unresolved blockers, and approval gates.
- Code optimization gate report with chosen variants, rejected variants, tests/checks, and optimization review verdicts for code changes.
- Phase-wise progress digest with target accomplishment matrix and bottleneck log.
- Launch evidence JSON matching references/launch-evidence-schema.md.
- ECC ledger: route, tier, mode, skills/tools, baseline, checks, delta, decision, next adjustment.

Safety:
Do not perform production deploys, payment changes, credential changes, destructive migrations, live outreach, data deletion, or secret-dependent actions without explicit approval. Keep proof buckets separate: hosted/live, local, repo artifact, candidate/shadow, roadmap.
```

Optional scaffold command:

```bash
python3 /Users/sanjayb/.codex/skills/commercial-launch-readiness-orchestrator/scripts/scaffold_launch_workflow.py \
  --repo <ABSOLUTE_REPO_PATH> \
  --name <RUN_NAME> \
  --mode audit-only \
  --profile auto \
  --budget standard \
  --research-depth deep \
  --worker-mode dry-run \
  --progress-policy both \
  --progress-interval-minutes 45 \
  --stall-threshold-minutes 120 \
  --optimization-policy strict \
  --emit-report-template
```
