# Gauntlet Loop — Source Notes

Distilled from Matt Shumer's published material. The SKILL.md is
self-contained; this file preserves the primary-source detail behind it.

## Sources

- "How to Run a Gauntlet Loop" — somethingbig.ai/gauntlet-loop (Jul 27, 2026).
- `mshumer/Claude-of-Duty` repository — the shipped output and `prompt.md`
  (see `canonical-prompt.md`).
- "How I Prompt Fable" — workbench.md/pub/IbaCrTjLJT — same doctrine stated
  generally: goal not steps, house rules, a bar the agent can check itself
  against, builder never grades its own work, live workbench doc, ultracode
  reserved for foundations.

## Details worth keeping that did not fit the SKILL.md

- Origin: the Call-of-Duty-style build by Claude Opus 5 — one prompt, many
  hours, ~55,000 LOC, every texture/mesh/animation/sound generated in code.
  Skeptics re-ran the prompt and got working games; the prompt is the method.
- Harness guidance from the article: a normal chat surface cannot run this —
  the agent must open files, run code, render, inspect screenshots, spawn
  other agents. Claude Code sub-agents were the example of clean critic
  contexts; Codex was noted as strong for backend work and decent at
  criticizing visuals, weaker at creating them.
- Bar examples by domain:
  - Games/visual: screenshots of the real category leader.
  - Websites: the best real sites in the category.
  - Writing: paragraphs at the target clarity/compression (e.g., Paul
    Graham's) — for the critic to ask "is every paragraph at least this
    clear?", not to copy voice.
  - Backend: test suite, latency target, failure-recovery test, security
    review, reference implementation.
- "A hard bar does not need to be realistically reachable. My game did not
  become better than Call of Duty. I stopped the run while it was still
  improving."
- The critic as A/B tester: show both artifacts without saying which is ours;
  it picks the better one; when ours loses it names the largest meaningful
  gap. The builder fixes exactly that gap — then the piece goes through the
  gauntlet again.
- Decomposition examples: a game → gun, hands, trees, bushes, lighting,
  movement, enemy behavior, sound, individual effects; an article → argument,
  opening, examples, sections, paragraphs, transitions. The lead agent decides
  granularity, grouping, and parallelism — do not pre-decide.
- Stopping criteria he names: when you like the result, when improvements are
  too small to matter, or when the compute budget is spent.
- Smoothing pass: after a wave of parallel improvements, one fresh agent makes
  the pieces "feel like one thing rather than a collection of separately
  improved parts" — fixes conflicts and seams, does not redesign.
- Follow-on applications he points to: a skills-folder upgrade loop, the
  prompt generator at somethingbig.ai/gauntlet-loop/generator, and the loop
  applied to Blender/Three.js/Unreal world-building.
