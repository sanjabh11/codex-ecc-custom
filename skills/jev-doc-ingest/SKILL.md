---
name: jev-doc-ingest
description: >-
  Convert documents (PDF, DOCX, PPTX, HTML) into structured, JEV-readable
  context via Docling — output lands as markdown plus pack-ready JSONL rows
  so verdict packs can judge document content without re-parsing. Use when
  decks, PDFs, or docs must feed a JEV decision or skill pipeline.
---

# JEV Doc Ingest

Combo #8: documents → structured context for JEV. Docling converts the
document; this script emits (a) a markdown file for humans/agents and
(b) a JSONL rows file — one row per document chunk/section — ready to pipe
into `packs.py --input`.

## Prerequisites

- `docling` — heavy install (~2 GB with torch models on first run):
  `uv tool install docling` or `uv run --with docling`.
- Without docling the script exits `2` with an install hint — never
  silently produces empty rows.

## Usage

```bash
# convert a deck to markdown + rows
python3 skills/jev-doc-ingest/scripts/docling_ingest.py \
    --input ~/Downloads/deck.pdf --out-dir /tmp/ingest

# feed rows into a pack
python3 skills/jev-doc-ingest/scripts/docling_ingest.py \
    --input report.pdf --out-dir /tmp/ingest
cd ~/jev-starter && .venv/bin/python packs.py --pack content-qa \
    --input /tmp/ingest/report.rows.jsonl --out-dir artifacts/pack-runs/qa
```

Output files: `<name>.md` (markdown) and `<name>.rows.jsonl`
(`{"id": "page-N", "state": {"path": ..., "text": ...}}`).

## Boundaries

- Chunks are capped (`--max-chars`, default 3000) and rows capped
  (`--max-rows`, default 50) — documents are evidence, not dumps.
- Private documents are converted locally; content only leaves the machine
  when the rows go to JEV for judgment — trim state to what the question
  needs.
- Watch disk: docling models land in `~/.cache/huggingface` on first use.
