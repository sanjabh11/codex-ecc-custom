# The canonical Gauntlet Loop prompt

Verbatim from `mshumer/Claude-of-Duty` — `prompt.md`. This ~120-word prompt
produced the original ~55,000-line game. It is the calibration example for
"minimal prompt, ambitious goal, real bar, separate critics, no final round."

```
I want you to build a first-person shooter at the level of the most recent Call of Duty games. It should be utterly perfect, visually beautiful, with every single thing done at AAA quality—from textures to physics to anything you could think of.

Fan out sub-agents and have sub-agents tackle each one individually so that the game is utterly perfect. You should /loop on each item and have a separate sub-agent check it visually to ensure it looks triple A. That separate sub-agent should be a really harsh critic, and if it doesn't look triple A, it should keep going.

Don't stop until each sub-agent is utterly wowed with the quality when compared with the actual Call of Duty game. It should literally compare them side by side blind and say which one looks better. Do this in ThreeJS. /loop until it's utterly perfect. Fan out sub-agents and ultracode.
```

Anatomy of why it works:

- Goal only, no architecture: "a first-person shooter at the level of the most
  recent Call of Duty games" — the model chose every system.
- The bar is concrete and inspectable: actual Call of Duty. Not "good" —
  *that* game.
- Work split delegated: "fan out sub-agents" — no prescribed workstreams.
- Separate critic per piece, "a really harsh critic."
- Blind side-by-side judgment: "compare them side by side blind and say which
  one looks better."
- No arbitrary end: "/loop until it's utterly perfect" — stop condition is the
  bar, not a round count.
- Max effort: "ultracode."
