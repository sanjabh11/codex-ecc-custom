---
name: agent-phase-ratchet
description: "Automatically classify non-trivial and critical agent work, then enforce PhaseLoop_v2 with research gates, baselines, one focused lever, verification, reflection, and next-phase adjustment."
origin: ECC
---

# Agent Phase Ratchet

Use this skill automatically when a task is non-trivial or critical, even if the user does not name the skill. It prevents unchecked execution by forcing task classification, measurable evidence, reflection, and an explicit next adjustment.

## Automatic Activation

At task start, silently classify the request before choosing the workflow:
- If the task is `Tier 0`, proceed normally and skip the ledger unless the user asks for one.
- If the task is `Tier 1` or higher, activate this skill and include a compact phase ledger in the handoff.
- If the task is `Tier 2` or higher, maintain a plan or repo-native task artifact when the task will span multiple phases, turns, or agents.
- If the task is `Tier 3`, define stop-and-ask thresholds before risky execution.

The user does not need to say "Use agent-phase-ratchet" or "Use PhaseLoop_v2". Those phrases are manual override triggers, not requirements.

## Trigger Phrases

- "agent phase ratchet"
- "PhaseLoop_v2"
- "benchmark execution"
- "phase loop"
- "self-improve"
- "non-trivial task"
- "don't just keep executing"
- "ratchet"

## Scope Tiers

- `Tier 0`: trivial one-liners. Skip the ledger unless the user asks for it.
- `Tier 1`: normal non-trivial work. Emit a compact phase ledger in the final response.
- `Tier 2`: multi-phase, multi-turn, or 3+ phase work. Maintain a persistent master plan or repo-native task artifact when appropriate.
- `Tier 3`: high-risk security, deployment, destructive, production, compliance, or performance work. Persist artifacts, run explicit gates, and stop-and-ask on failed critical evidence.

## Workflow

1. Classify the tier and state the measurable objective.
2. Select the skill set and research depth:
   - `light`: inspect local files and current instructions.
   - `standard`: inspect repo, relevant docs, tests, and tool availability.
   - `deep`: add external/current research for changing APIs, security, performance, legal, medical, finance, or strategic claims.
   - `high-risk`: include explicit stop-and-ask thresholds before execution.
3. Capture the baseline before editing or executing the main lever.
4. Execute one focused lever. A lever is one acceptance dimension, not necessarily one file.
5. Verify with the narrowest reliable evidence first, then broader gates if justified.
6. Reflect from evidence only: note what changed, what failed, what was inefficient, and what should adjust next.
7. Decide: `continue`, `change-plan`, or `stop-and-ask`.

## Persistent Flywheel Artifacts

For Tier 2, Tier 3, explicitly benchmarked work, or tasks that span multiple turns, create repo-local `.phase-loop/` artifacts. Prefer the bundled helper when available:

```bash
node skills/agent-phase-ratchet/scripts/phase-loop-ledger.js init --task "<task>" --tier 2
node skills/agent-phase-ratchet/scripts/phase-loop-ledger.js classify --task "<task>" --json
node skills/agent-phase-ratchet/scripts/phase-loop-ledger.js record \
  --phase P1 \
  --objective "<one focused acceptance dimension>" \
  --baseline "<measured starting state>" \
  --research-delta "<new evidence or not needed>" \
  --check "npm run build|pass|12000" \
  --metric "build_ms=12000:lower:5" \
  --delta "<measured change>" \
  --reflection "<evidence-bound lesson>" \
  --decision continue \
  --next-adjustment "<next phase change>"
node skills/agent-phase-ratchet/scripts/phase-loop-ledger.js trace-step --phase P1 --name "<step>" --status pass --evidence "<command or artifact>"
node skills/agent-phase-ratchet/scripts/phase-loop-ledger.js health --json
node skills/agent-phase-ratchet/scripts/phase-loop-ledger.js next --json
node skills/agent-phase-ratchet/scripts/phase-loop-ledger.js audit --json
node skills/agent-phase-ratchet/scripts/phase-loop-ledger.js import-bench --file ".bench-history/latest.json" --metric-prefix "bench" --threshold-pct 5
node skills/agent-phase-ratchet/scripts/phase-loop-ledger.js map-beads --phase P1 --bead "<bead-id>"
node skills/agent-phase-ratchet/scripts/phase-loop-ledger.js pack --name "phase-p1-evidence" --json
node skills/agent-phase-ratchet/scripts/phase-loop-ledger.js status --json
```

If the helper is not installed at the target path, use the same artifact layout manually:
- `.phase-loop/master-plan.md`: living plan and phase order.
- `.phase-loop/phase-ledger.jsonl`: every phase entry with baseline, checks, delta, reflection, decision, and next adjustment.
- `.phase-loop/ratchets.json`: current non-regression baselines for tracked metrics.
- `.phase-loop/improvements.jsonl`: queued prompt/skill/process improvements that need explicit approval before global mutation.
- `.phase-loop/session-health.jsonl`: disk, memory, load, and zombie-process snapshots for long-running phases.
- `.phase-loop/trace-spans.jsonl`: span/step-level evidence, status, failure categories, and artifacts for diagnosis after a failed or inefficient phase.
- `.phase-loop/bead-map.json`: phase-to-Beads mapping when `.beads` is present.
- `.phase-loop/evidence-packs/*.json`: hashed evidence manifests for phase handoff, review, or audit.

## True Flywheel Mechanisms

- Cross-phase compounding: start each phase by reading the prior `next_adjustment`, failed checks, and queued improvements.
- Task classification: use `classify --json` when a workflow needs a durable tier/research/subskill decision instead of relying on chat-only judgment.
- Next-phase synthesis: use `next --json` to generate a continuation prompt from prior ledger state instead of relying on memory.
- Global ratchets: store comparable metrics in `.phase-loop/ratchets.json`; use `import-bench` for JSON/JSONL benchmark outputs and fail closed when metrics regress beyond threshold.
- Span-level diagnosis: use `trace-step` for meaningful tool, research, edit, verification, and failure-localization steps; this prevents outcome-only audits.
- Beads integration: when `.beads` exists, include the Beads ID in the ledger via `--bead <id>` or map it later with `map-beads`; use `beads-triage` before selecting the next phase.
- Documentation/provenance: every Tier 2+ phase should point to durable artifacts in the ledger; use `pack` to produce hashed evidence manifests; commits are provenance only after checks pass.
- Self-audit: use `audit --json` before handoff or continuation to count implemented versus remaining flywheel mechanisms from current artifacts.
- Ambition/polish rounds: after core acceptance criteria pass, optionally add `P-polish` or `P-optimize` using the same loop.
- Monitoring: run `health` at phase boundaries for Tier 3, long-running, or multi-agent work. Treat Agent Mail or other coordination tools as optional until verified in-session.

## Subskill Routing

Select subskills from the task evidence, not from user phrasing:
- Use `perf-ratchet` for before/after latency, throughput, memory, build time, bundle size, or benchmark claims.
- Use `conformance-gate` for correctness, release claims, API/design contracts, proof levels, and live/local/artifact-only boundaries.
- Use `fuzz-regression` when malformed input, adversarial examples, parser boundaries, or prior failures need durable regression coverage.
- Use `beads-triage` when `.beads` exists or the user asks for dependency-aware task selection.
- Use `cass-session-search` only after `cass health --json` is healthy; otherwise fall back to memory and repo search.
- Use `dynamic-workflow-backlog` when Tier 2 or Tier 3 work needs many-agent decomposition, durable state, resumability, adversarial verification, or broad independent workstreams. Run its `automode --task "<task>" --dry-run` command when uncertain.
- Use `eval-harness` for reusable pass/fail agent or LLM workflow evaluation.
- Use `verification-loop` after substantial implementation or before handoff.

When multiple routes apply, keep the set minimal. Example: a performance-sensitive parser bug may use `perf-ratchet`, `conformance-gate`, and `fuzz-regression`; a normal UI redesign usually needs only this skill plus `verification-loop`.

## Phase Ledger Schema

```json
{
  "phase_id": "P1",
  "objective": "Implement one focused change",
  "baseline": "Current measured state before action",
  "research_delta": "New evidence or 'not needed'",
  "checks": [
    {
      "command": "npm run build",
      "duration_ms": 12000,
      "status": "pass"
    }
  ],
  "delta": "Measured before/after result",
  "reflection": "What worked, failed, or was inefficient",
  "decision": "continue | change-plan | stop-and-ask",
  "next_adjustment": "Concrete improvement for next phase"
}
```

## Output Contract

Return:
- `Tier`: why this level was chosen.
- `Baseline`: files, runtime state, metrics, or proof boundary before action.
- `Checks`: commands, browser/runtime checks, or evidence gathered, with pass/fail/not-run status.
- `Delta`: what measurably changed.
- `Reflection`: evidence-bound critique, not vibes.
- `Next adjustment`: concrete improvement for the next phase.

## Safety Rules

- Do not claim a tool, hook, connector, MCP server, or CLI is active unless verified in the current session.
- Do not rely on CASS when `cass health --json` is unhealthy.
- Do not mutate global skills, prompts, hooks, or plugin files from reflection alone; queue improvement ideas unless the user explicitly asks to apply them.
- Do not claim performance improvement without before/after evidence and comparable commands.
- Do not claim correctness without conformance, build, test, browser, runtime, or other concrete proof.
- Stop and ask before destructive actions, production-risk changes, missing secrets, security-sensitive ambiguity, or failed critical gates.
