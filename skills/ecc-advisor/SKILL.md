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

| Priority | Backend | Harness | Advisor Model | How | API Key Needed | CLI Status |
|---|---|---|---|---|---|---|
| 1 | **Native Claude Advisor API** | Claude Code | Opus 4.6 or Fable 5 | `advisor_20260301` server-side tool | No (uses Claude subscription) | Detection only — CLI returns fallback; harness calls advisor directly |
| 2 | **Codex-Orchestration plugin** | Codex | Fable 5 via MCP | `codex-orchestration` plugin seats | No (uses Codex subscription) | Detection only — CLI falls back to grok_cli |
| 3 | **Jev / Vercel AI Gateway** | Cline, Codex, Devin, Antigravity | gemini-2.5-flash-lite (fallback gpt-4o) | `bash skills/ecc-advisor/scripts/call_advisor.sh` | No (`AI_GATEWAY_API_KEY`/`JEV_API_KEY` env or `cline-jev-browser.config.json` plugin config) | **Fully implemented** |
| 4 | **Grok CLI** | Any harness | Grok 4.5 | same wrapper | No (Super Grok CLI OAuth token at `~/.grok/auth.json`) | **Fully implemented** |
| 5 | **Graceful fallback** | Any | None | Proceed without advisor | N/A | Always available |

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

### Backend 3/4: CLI backends (Jev Gateway primary, Grok fallback)

Works on any harness. The executor calls a wrapper script that resolves the canonical `fable/advisor_cli.py` and sends context to the detected backend (Jev / Vercel AI Gateway when gateway credentials exist, else Grok CLI when `~/.grok/auth.json` exists):

**Path Resolution:** always invoke via `bash skills/ecc-advisor/scripts/call_advisor.sh` — never `python3 fable/advisor_cli.py` directly (that path is CWD/git-root relative and breaks outside the canonical repo). The wrapper resolves, in order: `$FABLE_DIR`, the skill's own repo sibling path, `~/codex-ecc-custom/fable/advisor_cli.py`, then the git root.

**MCP connector (Codex and other harnesses that only surface MCP tools):** `scripts/advisor_mcp.py` is a dependency-free stdio MCP server exposing `advisor`, `advisor_status`, and `advisor_probe` tools. Registered in `~/.codex/config.toml` as `[mcp_servers.ecc-advisor]`; other hosts can register the same script path — it wraps the canonical `fable/advisor_cli.py` and writes no state on status/probe calls.

1. Work on the task normally — read files, run commands, orient
2. **Before substantive work** (writing code, committing to an approach), call the advisor:
   ```bash
   bash skills/ecc-advisor/scripts/call_advisor.sh "I'm working on X. My current approach is Y. The key decision is Z. Should I proceed?"
   ```
3. Read the advisor's response and give it serious weight
4. If the advisor points out a flaw, adapt. If it confirms your approach, proceed with confidence
5. **When stuck** (errors recurring, approach not converging), call the advisor again
6. **Before declaring done**, call the advisor for a final review

### Two-stage Jev evaluation (jev_gateway backend)

When `advisor_eval_enabled` is on, each advisor call runs the eval model first and the chat model only phrases its verdict:

- **Stage 1 — eval:** a bounded Jev eval call answers `sound` / `verdict` / `unaddressed_risk`. `advisor_eval_backend` (`auto`|`typesafe`|`vercel`|`off`) picks the endpoint; `auto` prefers `api.typesafe.ai` (`TYPESAFE_API_KEY`, same engine as jev-starter packs) and falls back to the Vercel `/evaluate` route. Bounded by `eval_timeout_seconds` (default 20s).
- **Stage 2 — communicate:** the chat model receives the structured verdict and may only phrase it, never override it.
- Responses carry `[Jev eval: sound=0.92 | verdict=proceed(0.8) | …]` when eval ran, or `[eval unavailable: <reason>]` when it failed — a missing prefix now means eval was disabled, not silently dead.
- History entries record `latency_ms`, `eval_status`, `eval_latency_ms`, `fallback_used`, `backend`, `model`, `error_preview` — use `--status` to audit them.

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
- Nudge turn: config `nudge_turn` (default 2) controls when the executor is reminded to call the advisor if it hasn't yet

### Grok CLI Backend
- Max 3 advisor calls per session (configurable in `fable/advisor_config.json`)
- Check status: `bash skills/ecc-advisor/scripts/call_advisor.sh --status`
- Reset counter: `bash skills/ecc-advisor/scripts/call_advisor.sh --reset`
- Advisor output capped at 2048 tokens per call
- Timeout: 60s per request (configurable via `timeout_seconds` in config), plus a single wall-clock budget across eval + retries + fallback (`total_timeout_seconds`, default 90s)
- Retry: 1 retry on failure (configurable via `retry_attempts` in config); deterministic 4xx (non-429) errors are never retried
- Dry run: `bash skills/ecc-advisor/scripts/call_advisor.sh --dry-run "<context>"` (no call budget consumed)
- Gateway health check: `bash skills/ecc-advisor/scripts/call_advisor.sh --probe` (times every advisor endpoint — typesafe eval, gemini chat, gpt-4o fallback, vercel eval — and prints status + latency; use this first when the advisor feels slow or unavailable)
- JSON output: `bash skills/ecc-advisor/scripts/call_advisor.sh --json "<context>"` (for programmatic use)
- Context from file: `bash skills/ecc-advisor/scripts/call_advisor.sh --context-file <path> "<question>"`
- Session tagging: `bash skills/ecc-advisor/scripts/call_advisor.sh --session <id> "<context>"` (tags history entries for audit trail; call count is global)

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
bash skills/ecc-advisor/scripts/call_advisor.sh "Building a REST API for a large dataset. Considering offset pagination vs cursor-based. Dataset is 50M rows, needs real-time inserts. Which approach and why?"
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
- **Codex** → Codex-Orchestration plugin (Fable 5 advisor) — preferred, or Jev Gateway / Grok CLI fallback
- **Windsurf / Devin** → Jev Gateway or Grok CLI — cross-harness fallback
- **Autogravity (Anti-Gravity)** → Jev Gateway or Grok CLI — cross-harness fallback

**Windows note:** The CLI uses `signal.alarm()` for timeout on Unix. On Windows, the signal-based timeout is skipped and the underlying `requests` library timeout is used instead.

The advisor is always a stronger model than the executor. The specific pairing depends on which backend is available in the current harness.

## Auto-Revocation

The advisor can be remotely disabled — checked before any backend call:

- `fable/advisor_config.json` → `"revoked": true` (+ optional `revocation_reason`, `revoked_until` ISO timestamp for temporary revocation)
- `ECC_ADVISOR_REVOKED=1` env var
- A missing/corrupt config file **fails closed** — calls are treated as revoked rather than allowed.

When revoked, `get_advice` returns a `[Advisor] Revoked:` message and the executor proceeds without advisor. Use `--unrevoke` (CLI flag) to clear a manual revocation.

## Portability Note

Skill copies exist under several roots (`~/.agents/skills/` symlinked, `~/.windsurf/skills/`, this repo). Only `scripts/call_advisor.sh` is location-safe: it resolves `$FABLE_DIR`, then the skill's own repo sibling, then `~/codex-ecc-custom/fable/advisor_cli.py`, then the git root. Any copy of this skill can be invoked from any CWD; all copies share the one canonical `fable/` state file.

## Backing Skills

- `ecc-fable-loop` — for iterative loop-based workflows
- `ecc-model-route` — for model routing decisions

## References

- [Claude API Advisor Tool docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)
- [The Advisor Strategy blog post](https://claude.com/blog/the-advisor-strategy)
- [advisor-middleware (fallback mode pattern)](https://github.com/emanueleielo/advisor-middleware)
