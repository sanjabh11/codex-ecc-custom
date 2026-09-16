---
name: universal-ecc-goal-attachment
description: "Attach ECC-first autonomous routing to Codex goals so task tiering, skill selection, dynamic-workflow gating, and evidence ledgers happen automatically."
origin: ECC
---

# Universal ECC Goal Attachment

Use this skill for Codex goal creation, goal-backed execution, goal refinement, and any request to force Everything Claude Code routing across a goal.

## Core Contract

For every Codex goal or non-trivial goal-backed task:

1. Use the `@everything-claude-code` plugin first whenever it is exposed in the current Codex session.
2. Do not ask the user to manually choose the mode or skill set.
3. Autonomously classify the goal, choose the smallest effective ECC workflow, select relevant skills for each phase, and verify outcomes with evidence.
4. Treat tool truth as evidence-bound: distinguish exposed in session, installed on disk, healthy/usable now, and planned but unavailable.
5. Never claim Claude-only slash commands, hooks, native Dynamic Workflows, or MCP servers exist inside Codex unless verified in the current session.

## Routing Sequence

1. Start with the single best ECC role or skill.
2. Inspect the real repo, files, runtime, browser target, config, or artifact before planning or editing.
3. Classify the task tier:
   - `Tier 0`: trivial one-liner; ledger optional.
   - `Tier 1`: normal non-trivial task; use `agent-phase-ratchet`.
   - `Tier 2`: multi-phase, multi-turn, broad repo, 3+ phases, or resumable task; use persistent planning or task artifacts.
   - `Tier 3`: security, deployment, destructive, production, compliance, secrets, performance-critical, or high-risk task; require explicit gates and stop-and-ask thresholds.
4. Use `workflow-audit-router` for ambiguous, plugin/workflow-related, automation-related, or multi-skill tasks.
5. If the task may need many-agent decomposition, durable state, adversarial verification, or resumability, run the launch gate:

```bash
node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js automode --dry-run --task "<goal>"
```

When running from an installed Codex cache rather than the plugin root, use the user-home runtime path:

```bash
node ~/.codex/plugins/cache/local-codex-marketplace/everything-claude-code/1.9.0/skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js automode --dry-run --task "<goal>"
```

## Automode Decisions

- `skip`: continue with normal `agent-phase-ratchet`.
- `create-backlog`: create or use a durable dynamic backlog, but do not spawn workers automatically.
- `plan-only`: create the safe backlog and stop for approval before worker export or risky execution.
- `forced-backlog`: only use when the user explicitly forced dynamic backlog behavior.

## Subskill Routing

- Use `agent-phase-ratchet` for all Tier 1+ work.
- Use `verification-loop` after substantial implementation or before handoff.
- Use `perf-ratchet` for performance, latency, throughput, memory, build-time, bundle-size, or benchmark claims.
- Use `conformance-gate` for correctness, release readiness, API/design contracts, proof boundaries, and live/local/artifact distinctions.
- Use `fuzz-regression` for malformed input, adversarial input, parser boundaries, fuzz cases, and edge-case regressions.
- Use `beads-triage` when `.beads` exists.
- Use `cass-session-search` only after `cass health --json` is healthy; otherwise use memory and repo search.
- Use `browser-qa` and `e2e-testing` for browser, UI, and critical flow verification when browser tooling is exposed.
- Use security review skills and explicit stop gates for security, privacy, compliance, secrets, and production-risk work.
- Use `eval-harness` for reusable agent or LLM workflow evaluation.
- Use `skill-optimizer` when improving, validating, comparing, regress-testing, or evolving skills, prompts, agents, commands, or reusable workflows.
- Use `coding-judgment` for code, fix, debug, refactor, review, simplification, approach-selection, and unclear bug or regression work.
- Use `commercial-launch-readiness-orchestrator` for one-repo commercial launch readiness, sellability, market pain, target-customer ranking, outreach planning, and proof-backed launch decisions.

Keep the set minimal. Skill routing must follow evidence and acceptance criteria, not keyword inflation.

## Goal Attachment Line

When a tool or prompt needs a compact attachment, append:

```text
Execution protocol: Apply Universal ECC Goal Attachment; use Everything Claude Code when exposed, auto-classify tier and mode, route through the smallest relevant ECC skills, run dynamic-workflow automode for broad/resumable/adversarial work, and require evidence before completion claims.
```

## Final Response Contract

For Tier 1+ goal work, include:

| Field | Required content |
|---|---|
| ECC route | Primary role or skill and why |
| Tier | 0/1/2/3 with reason |
| Mode | normal PhaseLoop, persistent PhaseLoop, dynamic backlog, or plan-only |
| Skills used | Minimal ECC skills actually used |
| Baseline | Starting proof, state, or metric |
| Checks | Commands/browser/runtime checks with pass/fail/not-run |
| Delta | What changed or what was proven |
| Reflection | Evidence-bound lesson or inefficiency |
| Decision | continue, change-plan, stop-and-ask, or complete |
| Next adjustment | Concrete next improvement |
