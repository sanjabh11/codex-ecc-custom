#!/usr/bin/env python3
"""docling_ingest — documents to markdown + pack-ready JSONL rows.

Converts a document via Docling, writes <name>.md plus <name>.rows.jsonl
(one row per bounded chunk, shaped for `packs.py --input`).

Usage:
  python3 docling_ingest.py --input deck.pdf --out-dir /tmp/ingest
  uv run --with docling docling_ingest.py --input deck.pdf
Exit: 0 converted, 2 docling missing, 1 conversion failure.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LEDGER = (
    Path.home() / "codex-ecc-custom" / ".phase-loop" / "phase-ledger.jsonl"
)
INSTALL_HINT = (
    "docling not found — install with `uv tool install docling` "
    "(~2 GB models on first run) or run via `uv run --with docling`"
)


def find_docling() -> str | None:
    from shutil import which
    return which("docling")


def convert(source: Path, out_dir: Path) -> Path:
    binary = find_docling()
    if binary is None:
        # allow running inside a uv --with docling env where the CLI exists
        # only as a python entry point
        try:
            import docling  # noqa: F401
        except ImportError:
            raise RuntimeError(INSTALL_HINT)
        proc = subprocess.run(
            [sys.executable, "-m", "docling", str(source),
             "--to", "md", "--output", str(out_dir)],
            capture_output=True, text=True, timeout=1800)
    else:
        proc = subprocess.run(
            [binary, str(source), "--to", "md", "--output", str(out_dir)],
            capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0:
        raise RuntimeError(f"docling failed: {proc.stderr.strip()[:300]}")
    md = out_dir / f"{source.stem}.md"
    if not md.is_file():
        candidates = sorted(out_dir.glob("*.md"),
                            key=lambda p: p.stat().st_mtime,
                            reverse=True)
        if not candidates:
            raise RuntimeError("docling produced no markdown output")
        md = candidates[0]
    return md


def chunk_markdown(md_path: Path, max_chars: int, max_rows: int,
                   source: Path) -> Path:
    text = md_path.read_text(encoding="utf-8", errors="replace")
    rows_path = md_path.with_suffix(".rows.jsonl")
    # split on headings/double-newlines into bounded chunks
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    chunks, current = [], ""
    for block in blocks:
        if len(current) + len(block) + 2 > max_chars and current:
            chunks.append(current)
            current = block
        else:
            current = f"{current}\n\n{block}".strip()
    if current:
        chunks.append(current)
    with rows_path.open("w", encoding="utf-8") as handle:
        for index, chunk in enumerate(chunks[:max_rows]):
            row = {
                "id": f"{source.stem}-{index:03d}",
                "state": {
                    "path": str(source),
                    "chunk": index,
                    "text": chunk,
                },
            }
            handle.write(json.dumps(row) + "\n")
    return rows_path


def append_ledger(source: Path, md: Path, rows: int,
                  ledger: Path) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "type": "doc-ingest",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "markdown": str(md),
        "rows": rows,
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--max-chars", type=int, default=3000)
    parser.add_argument("--max-rows", type=int, default=50)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 1
    args.out_dir.mkdir(parents=True, exist_ok=True)

    try:
        md = convert(args.input, args.out_dir)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 2 if "install" in str(error) else 1
    rows_path = chunk_markdown(md, args.max_chars, args.max_rows, args.input)
    row_count = sum(1 for _ in rows_path.open(encoding="utf-8"))
    append_ledger(args.input, md, row_count, args.ledger)

    payload = {"markdown": str(md), "rows": str(rows_path),
               "row_count": row_count}
    if args.json:
        print(json.dumps(payload))
    else:
        print(f"markdown: {md}\nrows: {rows_path} ({row_count} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
