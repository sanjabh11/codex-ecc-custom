# Manager Loop — Source Notes

Distilled from Matt Shumer's published material. The SKILL.md is
self-contained; this file preserves the primary-source detail behind it.

## Sources

- "My GPT-6 Astra Review" — somethingbig.ai/astra-review (Sep 3, 2026).
  The Manager Loop section describes: coordinator interviews the human until
  the goal is agreed → turns it into a checklist of to-dos → starts an
  implementer in a separate Codex session ("a completely separate agent, not a
  sub-agent") → coordinator gives it a phase, uses goal mode to keep it working
  toward the phase's finish line → moves it to the next phase when done.
- Implementation document circulated with the pattern (phase-wise plan,
  exit gates, failure modes) — reproduced in the SKILL.md workflow.
- X posts by @mattshumer_ demonstrating the setup (Sept 2026).

## Details worth keeping that did not fit the SKILL.md

- Shumer's hardware notes: raised Codex sub-agent limits from 4 to 16 on one
  machine and 96 on the machine running the civilization / New York builds.
  "Obscene overkill and incredibly expensive" — treat as an upper bound demo,
  not a recommendation. Raising the limit alone does not increase delegation;
  sometimes explicit encouragement is needed even at max reasoning effort.
- He generates a web page showing the checklist plus a graph of items
  completed over time, and built a way to visualize sub-agents working on the
  project. The live visualization is part of why he trusts the setup.
- On briefing the Manager: for a specific vision, invest in the alignment
  conversation (mockups for interfaces before building the real thing). When
  leaving decisions to the model, give inspiration — links to products,
  designs, or ideas — rather than exhaustive description.
- On prompt-writing: when asking the Manager to write prompts for other
  agents, tell it to keep them as minimal as possible while preserving intent.
- "You don't need this for ordinary work. This is what I've been using when I
  want to ask for something absurd."
- Reported plateau problem the pattern solves: single agents reach a point
  where progress slows — they keep working, get absorbed in details, and stop
  improving the overall project. The Manager's whole job is the thing the human
  was doing: keeping work moving through the larger plan.
- Cost: his large experiments "consumed enormous amounts of tokens." The
  pattern is meant for absurdly ambitious goals; monitor spend.
- Untested extensions he suggested: a fresh Implementer per phase with written
  handoffs; letting the Implementer propose plan changes that the Manager
  accepts or rejects.

## Phase exit gates (from the implementation doc)

- Phase 0 exit: written, approved phased checklist both agents can reference.
- Phase 1 exit: two independent sessions running, able to communicate,
  Implementer holds the checklist.
- Phase 2 exit: Manager actively assigning; phase one underway; progress page
  visible.
- Phase 3 exit: all phases complete + final evidence reviewed, or human stop.
