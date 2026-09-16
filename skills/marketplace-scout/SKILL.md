---
name: marketplace-scout
description: "Scout Claude/Codex/agent plugin marketplaces and rank candidates against ECC inventory, safety, implementation cost, and user workflow fit."
origin: ECC
---

# Marketplace Scout

Use this skill to research plugin marketplaces, GitHub repos, skill catalogs, or agent workflow packs and decide what is worth adapting into ECC.

## Activation

Use when the user asks to:
- explore plugin marketplaces or lists
- compare top plugins or skills
- borrow ideas from external agent ecosystems
- find the best additions for `everything-claude-code`
- periodically monitor marketplaces for useful updates

## Research Rules

- Browse current sources when the marketplace, repo, or ranking may have changed.
- Prefer primary sources: official plugin repo, marketplace listing, package manifest, docs, and commit history.
- Do not recommend installation from summary pages alone.
- Route all adoption decisions through `safe-plugin-importer`.

## Evaluation Matrix

Score each candidate from 1 to 5:

| Dimension | Meaning |
|---|---|
| Workflow fit | Matches the user's recurring Codex/ECC tasks |
| ECC coverage gap | Adds capability not already covered |
| Safety | Low supply-chain, secrets, and permission risk |
| Implementation cost | Easy to rebuild or adapt safely |
| Verification path | Has clear smoke tests or evidence gates |
| Cross-platform value | Works across Codex, Windsurf, Antigravity, Cursor, or Claude-style agents |

## Workflow

1. Establish inventory:
   - current ECC skills
   - exposed plugins/connectors in the session
   - existing install modules and target platforms
2. Research candidates:
   - current marketplace pages
   - GitHub repositories
   - docs and examples
   - recent issues/security signals when relevant
3. Deduplicate:
   - mark as already covered, partial gap, or net-new
4. Rank:
   - use the evaluation matrix
   - include adoption mode: reject, document, adapt, create new skill, install with approval
5. Produce implementation plan:
   - P1/P2/P3 grouping
   - proof commands
   - runtime cache implications
   - user approval gates

## Output Template

```md
| Rank | Candidate | Source | Gap Filled | Score /5 | Adopt Mode | Why Now | Verification |
|---|---|---|---|---:|---|---|---|
```

## Pairings

| Pair with | Use |
|---|---|
| `safe-plugin-importer` | Supply-chain and manifest review |
| `workflow-audit-router` | Route candidates to minimal ECC implementation |
| `plugin-customizer` | Convert broad ideas into local skills |
| `scheduled-briefing-pack` | Repeat marketplace scouting on cadence |
