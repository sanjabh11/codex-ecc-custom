---
name: ecc-advisor
description: >-
  Client-side advisor pattern pairing the harness's native model (executor)
  with Grok 4.5 (advisor) for cost-optimized multi-model orchestration.
  The executor runs the task end-to-end; Grok 4.5 is consulted at decision
  points via a CLI helper script. No API keys needed — uses Super Grok CLI token.
  TRIGGER when: "advisor", "two-model", "cascade", "escalation",
  "consult stronger model", "cost optimization model", "Grok advisor",
  "second opinion", or when following the advisor pattern from the Claude API docs.
  DO NOT TRIGGER when: task is trivially one-line, or no Grok CLI token exists.
---

# ecc-advisor

## When to Use

- Non-trivial coding tasks where a second opinion at decision points improves quality
- Tasks where the executor model might miss edge cases or architectural decisions
- Long-horizon workflows where having an excellent initial plan prevents expensive backtracking
- Any task where you want near-frontier intelligence at the harness model's cost

## How It Works

You (the harness model) are the **executor**. Grok 4.5 is your **advisor**.

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

- Max 3 advisor calls per session (configurable in `fable/advisor_config.json`)
- Check status: `python3 fable/advisor_cli.py --status`
- Reset counter: `python3 fable/advisor_cli.py --reset`
- Advisor output capped at 2048 tokens per call

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

- Requires Grok CLI token at `~/.grok/auth.json` (verified working with Super Grok)
- Requires Python3 + requests library (already installed)
- No API keys needed for either model
- If no token is available, the advisor returns a graceful fallback message and you proceed without it

## Platform Compatibility

Works across all harnesses — the executor is always the harness's native model (free, no API key):

- **Cascade** → Claude as executor, Grok 4.5 as advisor
- **Codex** → GPT-5.6 as executor, Grok 4.5 as advisor
- **Anti-Gravity** → Gemini 3.5 as executor, Grok 4.5 as advisor

The advisor is always Grok 4.5 via Super Grok CLI token (free, no API key).

## Backing Skills

- `ecc-fable-loop` — for iterative loop-based workflows
- `ecc-model-route` — for model routing decisions

## References

- [Claude API Advisor Tool docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)
- [The Advisor Strategy blog post](https://claude.com/blog/the-advisor-strategy)
- [advisor-middleware (fallback mode pattern)](https://github.com/emanueleielo/advisor-middleware)
