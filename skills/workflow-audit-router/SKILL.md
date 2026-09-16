---
name: workflow-audit-router
description: "Audit a task before execution, then route it to the smallest effective ECC skill, connector, and verification stack. Use for ambiguous, multi-step, plugin-selection, automation, or high-risk work."
origin: ECC
---

# Workflow Audit Router

Use this skill before building or installing new workflows, when the user asks which plugin/skill/connector to use, or when a task could sprawl across multiple tools.

## When to Activate

- User asks to "audit my workflow", "which skills should I use", "route this task", or "build a plugin/workflow".
- The task mentions plugins, connectors, automations, scheduled tasks, marketplace imports, or reusable workflows.
- The task is non-trivial and could trigger multiple ECC skills.
- Before adding a new ECC skill, command, hook, or global rule.

## Core Rule

Do not add workflow machinery until the current task is classified, routed, and proof requirements are explicit.

## Workflow

1. Classify the task with `agent-phase-ratchet` or the helper when available:

   ```bash
   node skills/agent-phase-ratchet/scripts/phase-loop-ledger.js classify --task "<task>" --json
   ```

   If the task may need many-agent decomposition, durable state, adversarial verification, or resumability, also run automode:

   ```bash
   node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js automode --task "<task>" --dry-run
   ```

2. Inspect the real repo/runtime first:
   - Current worktree and touched files.
   - Existing ECC skills that already cover the request.
   - Available connectors, MCP tools, browser/runtime surfaces, and installed plugin cache.
   - Project-local rules that override global defaults.

   Auto-select:
   - `skill-optimizer` when the task asks to improve, optimize, validate, regress-test, compare, or evolve a `SKILL.md`, prompt, agent, command, or reusable workflow.
   - `coding-judgment` when the task asks to code, fix, debug, refactor, review, simplify, choose an implementation approach, or diagnose unclear bugs and regressions.
   - `commercial-launch-readiness-orchestrator` when the task asks whether one repository is secure, launch-ready, sellable, commercially ready, targetable, or ready for outreach.
   - `dynamic-workflow-backlog` only when broad independent lanes, durable state, adversarial review, or resumability are actually needed; preview with `automode --dry-run` and require explicit approval before worker execution.

3. Produce a compact route card:
   - `Tier`: 0-3, with reason.
   - `Primary skill`: exactly one orchestrator.
   - `Subskills`: only those needed for the acceptance criteria.
   - `Connectors/tools`: installed, healthy, exposed, or unavailable.
   - `Evidence plan`: commands, browser checks, artifacts, or not-run reasons.
   - `Stop gates`: destructive, production, secret, security, or failed critical checks.
   - `Dynamic workflow`: launch, plan-only, or not needed.

4. Execute only the routed plan unless the user asks to expand scope.

## Output Contract

```markdown
| Field | Decision |
|---|---|
| Tier | ... |
| Primary skill | ... |
| Subskills | ... |
| Connectors/tools | ... |
| Evidence required | ... |
| Stop gates | ... |
| Dynamic workflow | ... |
| Next action | ... |
```

## Usage Examples

```text
Use workflow-audit-router before implementing this dashboard redesign.
Route this plugin idea through ECC and tell me which skills/connectors to use.
Audit whether this should be a new skill, automation, or just a one-off command.
```

## Related Skills

- `agent-phase-ratchet` for tiering, ledgers, and phase gates.
- `connector-skill-composer` for packaging routed workflows.
- `safe-plugin-importer` for external plugin intake.
- `skill-optimizer` for scenario-backed skill, prompt, agent, and reusable workflow improvement.
- `coding-judgment` for repo-first coding, debugging, refactoring, and review discipline.
- `commercial-launch-readiness-orchestrator` for one-repo commercial readiness, market pain, target customers, outreach planning, and launch decision evidence.
- `dynamic-workflow-backlog` for Tier 2/Tier 3 work that needs durable many-agent orchestration, adversarial review, or resumability.
- `conformance-gate`, `perf-ratchet`, and `fuzz-regression` for proof routing.
