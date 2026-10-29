# Gauntlet Loop meta-prompt

Verbatim from "How to Run a Gauntlet Loop" (somethingbig.ai/gauntlet-loop).
Paste into a strong model along with the goal; it picks the bar and writes the
final short prompt, which then runs inside an agentic harness.

```
I want to run a Gauntlet Loop for this goal:

[GOAL]

Possible references or quality bars:

[OPTIONAL REFERENCES]

Choose the strongest concrete bar that an agent can actually inspect and compare its work against. If I have not supplied one, propose a useful comp or measurement that plays the same role for this task that real Call of Duty screenshots played for Matt Shumer's Claude of Duty game (read the prompt: https://github.com/mshumer/Claude-of-Duty/blob/main/prompt.md). Explain the bar in one sentence.

Then write a short prompt for Claude Code or Codex in the style of Matt's prompt (minimal is better here, we want the agent to decide the specifics!).

Give the lead agent the goal and the bar, but let it choose the approach. Tell it to divide the goal into the smallest pieces that can be improved and judged independently. For each important piece, it should fan out a builder and a separate critic with fresh context.

Each critic must inspect the real output, compare it directly with the bar—using a blind A/B comparison when possible—identify the biggest remaining gap, and send it back for another round. Keep looping until our output wins or I stop the run.

Have the lead agent maintain a simple live progress page that shows the work evolving over time.

Have it use subagents and ultracode. Do not prescribe the architecture, exact decomposition, or a fixed number of rounds. Keep the final prompt short, just like Matt's.
```

Adaptation note for harness-agnostic use: where it says "Claude Code or
Codex", substitute the current host; where it says "ultracode", substitute the
host's highest reasoning effort; where it says "/loop", substitute the host's
repeat mechanism or explicit re-invocation. The embedded GitHub URL may be
replaced with this repo's local `references/canonical-prompt.md` to avoid
fetching live web content mid-run.
