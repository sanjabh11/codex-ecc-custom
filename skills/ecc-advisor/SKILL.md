---
name: ecc-advisor
description: >-
  Multi-provider advisor pattern pairing the harness's native model (executor)
  with a stronger advisor model for cost-optimized multi-model orchestration.
  Supports three advisor backends: (1) Native Claude Advisor API (advisor_20260301)
  server-side tool for Claude Code, (2) Grok 4.5 via Super Grok CLI OAuth token for
  cross-harness use, (3) Claude Fable 5 via Codex-Orchestration plugin.
  The executor runs the task end-to-end; the advisor is consulted at decision
  points. No separate API keys needed for Grok CLI path — uses Super Grok CLI
  OAuth token (refreshed automatically).
  TRIGGER when: "advisor", "two-model", "cascade", "escalation",
  "consult stronger model", "cost optimization model", "Grok advisor",
  "second opinion", "advisor tool", "advisor strategy",
  "Sonnet Opus pairing", "Fable advisor", or when following the advisor
  pattern from the Claude API docs.
  DO NOT TRIGGER when: task is trivially one-line, or no advisor backend is available.
---

# ecc-advisor

## When to Use

- Non-trivial coding tasks where a second opinion at decision points improves quality
- Tasks where the executor model might miss edge cases or architectural decisions
- Long-horizon workflows where having an excellent initial plan prevents expensive backtracking
- Any task where you want near-frontier intelligence at the harness model's cost

## How It Works

You (the harness model) are the **executor**. A stronger model is your **advisor**.

### Advisor Backend Selection (auto-detected)

The skill automatically selects the best available advisor backend:

| Priority | Backend | Harness | Advisor Model | How | API Key Needed |
|---|---|---|---|---|---|
| 1 | **Native Claude Advisor API** | Claude Code | Opus 4.6 or Fable 5 | `advisor_20260301` server-side tool | No (uses Claude subscription) |
| 2 | **Codex-Orchestration plugin** | Codex | Fable 5 via MCP | `codex-orchestration` plugin seats | No (uses Codex subscription) |
| 3 | **Grok CLI** | Any harness | Grok 4.5 | `python3 "$(git root)/fable/advisor_cli.py"` or `python3 "$ADVISOR_CLI_PATH"` | No (Super Grok CLI OAuth token) |
| 4 | **Graceful fallback** | Any | None | Proceed without advisor | N/A |

### Backend 1: Native Claude Advisor API (preferred for Claude Code)

The official advisor tool (`advisor_20260301`) runs server-side on Anthropic's infrastructure. The executor calls it like any other tool — no extra round-trips or context management.

**Supported pairings:**
- Haiku 4.5 (executor) → Opus 4.6 (advisor)
- Sonnet 4.6 (executor) → Opus 4.6 (advisor)
- Opus 4.6 (executor) → Opus 4.6 (advisor)
- Any executor → Fable 5 (advisor, when available)

**Key properties:**
- Advisor receives the executor's full transcript as context
- Advisor returns text guidance only (400-700 tokens typically)
- Advisor's thinking blocks are dropped before result returns
- Advisor never calls tools or produces user-facing output
- `max_uses` caps advisor calls per request (primary cost control)

**Usage in Claude Code:**
The advisor tool is configured in Claude Code settings. When enabled, Claude automatically decides when to call it — at decision points, when stuck, or before declaring done.

### Backend 2: Codex-Orchestration Plugin (preferred for Codex)

When the `codex-orchestration` plugin is installed, it provides explicit seat assignment:
- **Planner seat:** Creates the plan (Fable 5 or configured model)
- **Advisor seat:** Reviews the plan (Fable 5 or configured model)
- **Executor seat:** Implements the plan (harness native model)

The PLAN_APPROVED/PLAN_REVISE protocol supports up to 5 review rounds. Use truthful route states from `ecc-model-route` to report which model actually ran.

### Backend 3: Grok CLI (cross-harness fallback)

Works on any harness. The executor calls a CLI script that sends context to Grok 4.5:

1. Work on the task normally — read files, run commands, orient
2. **Before substantive work** (writing code, committing to an approach), call the advisor:
   ```bash
   python3 fable/advisor_cli.py "I'm working on X. My current approach is Y. The key decision is Z. Should I proceed?"
   ```
3. Read the advisor's response and give it serious weight
4. If the advisor points out a flaw, adapt. If it confirms your approach, proceed with confidence
5. **When stuck** (errors recurring, approach not converging), call the advisor again
6. **Before declaring done**, call the advisor for a final review

## Advisor Timing — When to Call

Call the advisor at these decision points:

- **Before substantive work** — before writing, before committing to an interpretation, before building on an assumption. Orientation (finding files, reading config) is NOT substantive work.
- **When you believe the task is complete** — BEFORE this call, make your deliverable durable: write the file, save the result. The advisor call takes time; if the session ends during it, a durable result persists.
- **When stuck** — errors recurring, approach not converging, results that don't fit.
- **When considering a change of approach.**

On tasks longer than a few steps, call advisor at least once before committing to an approach and once before declaring done.

## When NOT to Call the Advisor

- Trivial one-line answers
- Tasks where the next action is dictated by tool output you just read
- Simple factual lookups or arithmetic
- Read-only orientation commands (ls, cat, grep, find)

## Hard Rule

Your first `write_file`, `edit_file`, or state-changing `bash` call on a task must be preceded by an advisor call in the same or an earlier turn. Read-only orientation commands are not state-changing. This is a checkpoint, not a difficulty judgment. It applies to one-line edits too.

## Giving Advice Serious Weight

If you follow a step and it fails empirically, or you have primary-source evidence that contradicts a specific claim (the file says X, the advisor says Y), adapt. A passing self-test is not evidence the advice is wrong — it's evidence your test doesn't check what the advice is checking.

If you've already retrieved data pointing one way and the advisor points another: don't silently switch. Surface the conflict in one more advisor call — "I found X, you suggest Y, which constraint breaks the tie?"

## Cost Controls

### All Backends
- Advisor calls are capped per session (configurable)
- The executor decides when to call — not every turn, only at decision points
- Advisor output is concise (200-700 tokens depending on backend)

### Grok CLI Backend
- Max 3 advisor calls per session (configurable in `fable/advisor_config.json`)
- Check status: `python3 fable/advisor_cli.py --status`
- Reset counter: `python3 fable/advisor_cli.py --reset`
- Advisor output capped at 2048 tokens per call
- Timeout: 120s per call (configurable via `timeout_seconds` in config)
- Retry: 1 retry on failure (configurable via `retry_attempts` in config)
- Dry run: `python3 fable/advisor_cli.py --dry-run "<context>"` (no call budget consumed)
- JSON output: `python3 fable/advisor_cli.py --json "<context>"` (for programmatic use)
- Context from file: `python3 fable/advisor_cli.py --context-file <path> "<question>"`
- Session isolation: `python3 fable/advisor_cli.py --session <id> "<context>"`

### Native Claude Advisor API Backend
- `max_uses` parameter caps calls per API request (primary cost control)
- Advisor usage counts toward session totals shown by `/usage`
- No client-side tracking needed — server manages call counting

### Codex-Orchestration Backend
- Up to 5 plan review rounds (PLAN_APPROVED/PLAN_REVISE protocol)
- Concurrency limits per provider (configured in plugin settings)
- Model effort normalization via `ecc-model-route`

## Context to Pass the Advisor

The advisor sees ONLY what you pass in the CLI argument, so include:
- What the task is
- What you've done so far (key findings, not everything)
- The specific decision you're facing
- Any constraints or evidence you've gathered

Example:
```bash
python3 fable/advisor_cli.py "Building a REST API for a large dataset. Considering offset pagination vs cursor-based. Dataset is 50M rows, needs real-time inserts. Which approach and why?"
```

## Dependency Gating

### Native Claude Advisor API
- Requires Claude Code with advisor tool enabled (settings → advisor)
- No separate API keys needed — uses Claude subscription
- Supported pairings: Haiku/Sonnet/Opus executor → Opus/Fable 5 advisor

### Codex-Orchestration Plugin
- Requires `codex-orchestration` plugin installed (`codex plugin list`)
- No separate API keys needed — uses Codex subscription
- Requires Python 3.11+ for plugin runtime

### Grok CLI
- Requires Grok CLI OAuth token at `~/.grok/auth.json` (verified working with Super Grok)
- Requires Python3 + requests library (already installed)
- No separate API key needed — OAuth token is refreshed automatically by `grok login`
- If no token is available, the advisor returns a graceful fallback message

### Fallback
- If no backend is available, proceed without advisor — note this in the response

## Backend Auto-Detection

The CLI auto-detects the best available backend in priority order:
1. `claude_native` — if `CLAUDE_ADVISOR_ENABLED=true` env var is set
2. `codex_orchestration` — if `~/.codex/plugins/codex-orchestration/` exists
3. `grok_cli` — if `~/.grok/auth.json` exists
4. `fallback` — no backend available

Override with `--backend <name>` flag. Only `grok_cli` is fully implemented in the CLI;
other backends return an informative message and fall back.

## Weekly Mode Integration

When used as a backing skill in weekly marketing workflows (e.g., `ecc-hormozi-funnel`
weekly mode), the advisor is consulted at three checkpoints:

1. **Offer ranking** — advisor reviews the top offer candidates and confirms or reranks
2. **Hook rewriting** — advisor reviews hook variants for persuasiveness and evidence alignment
3. **Funnel audit** — advisor reviews the 3 prioritized fixes for impact and feasibility

If the advisor is unavailable, the weekly workflow proceeds with `advisor_confirmed: false`
in the decision confidence calculation. This reduces the composite confidence score
but does not block artifact generation.

## Decision Confidence Integration

The `ecc-hormozi-funnel` skill computes a composite decision confidence from four subscores:
- `evidence_quality` — strength of cited evidence
- `source_coverage` — breadth of evidence sources
- `adversarial_survival` — survival through skeptic/contrarian/missing-perspective passes
- `advisor_confirmed` — whether the advisor confirmed the decision (this skill)

When the advisor is unavailable, `advisor_confirmed` defaults to 0.5 (neutral),
reducing the composite score by up to 12.5%. The workflow labels the output
as `evidence_limited` in this case.

## Platform Compatibility

Works across all harnesses with automatic backend selection:

- **Cascade / Claude Code** → Native Advisor API (Opus/Fable 5 advisor) — preferred
- **Codex** → Codex-Orchestration plugin (Fable 5 advisor) — preferred, or Grok CLI fallback
- **Windsurf / Devin** → Grok CLI (Grok 4.5 advisor) — cross-harness fallback
- **Anti-Gravity** → Grok CLI (Grok 4.5 advisor) — cross-harness fallback

The advisor is always a stronger model than the executor. The specific pairing depends on which backend is available in the current harness.

## Backing Skills

- `ecc-fable-loop` — for iterative loop-based workflows
- `ecc-model-route` — for model routing decisions

## References

- [Claude API Advisor Tool docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)
- [The Advisor Strategy blog post](https://claude.com/blog/the-advisor-strategy)
- [advisor-middleware (fallback mode pattern)](https://github.com/emanueleielo/advisor-middleware)

## Optimization Contract v1

This contract makes the advisor result auditable without confusing advice with
execution proof.

```yaml
contract_version: skill-optimization.v1
scope: decision-point second opinion for the executing harness
inputs:
  - task_context
  - key_decision
  - constraints_and_risks
  - available_backend_status
outputs:
  - backend_used
  - decision
  - rationale
  - calls_remaining
  - unverified_assumptions
  - next_action
evidence_policy:
  advisor_text_is_guidance_not_execution_proof: true
  record_backend_and_call_budget: true
  record_fallback_or_unavailability: true
completion_gate:
  before_edits: advisor_decision_or_explicit_fallback_record
  before_done: final_advisor_review_or_explicit_fallback_record
stop_conditions:
  - missing_task_context
  - missing_required_approval
  - advisor_result_conflicts_with_primary_evidence
```

The executor must preserve this distinction in its handoff: an advisor can
recommend, rerank, or identify a risk, but only a command, test, artifact, or
human approval proves that the recommendation was executed or accepted.
