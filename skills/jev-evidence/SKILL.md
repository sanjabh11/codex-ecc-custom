---
name: jev-evidence
description: >-
  Gather evidence context before JEV decisions — pulls cm context, cass
  history search (only when healthy), and session notes into one bounded
  JSON block that can be merged into pack state. Use before any pack run
  where past sessions or memory should inform the judgment.
---

# JEV Evidence

Combos #6–#9 mapped onto the memory stack you already own: instead of
installing Meilisearch/Qdrant/Graphiti, `gather_context.py` queries the
existing retrieval layer — `cm context`, `cass search` (health-gated) —
and returns a bounded JSON block the caller merges into pack `state`.

## Sources

| Source | Status check | Budget |
|---|---|---|
| `cm context "<query>"` | `cm --version` | ~4 KB |
| `cass search "<query>" --robot` | `cass health --json` must be healthy | ~4 KB |
| callimachus MCP (thread search) | agent-side, not scriptable — the SKILL.md lane | manual |

cass is health-gated per global rules: if `cass health` is unhealthy the
source is skipped with a note, never blocks.

## Usage

```bash
python3 skills/jev-evidence/scripts/gather_context.py \
    --query "previous decisions about X" --json

# merge into a pack row's state.context before calling packs.py
```

Output JSON: `{"cm": "...", "cass": [...], "skipped": ["cass: unhealthy"]}`.
No ledger writes — evidence gathering is read-only.

## Boundaries

- Never blocks: missing CLIs are skipped, not errors (exit 0 with
  `skipped` list) — evidence improves judgment but absence of it must
  not stop the gate.
- Each source is truncated (`--max-chars`, default 4000) — evidence is
  a supplement, not a dump.
- Never embed secrets: cm/cass output is clipped; the caller decides what
  joins pack state.
