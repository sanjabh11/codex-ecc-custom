#!/usr/bin/env python3
"""gather_context — collect bounded evidence from local memory tools.

Queries `cm context` and `cass search` (health-gated) for a query string
and returns one JSON block suitable for merging into a pack row's state.
Missing/unhealthy tools are skipped, never fatal — evidence is advisory.

Usage:
  python3 gather_context.py --query "pack routing decisions" [--json]
Exit: 0 always (sources skipped individually on failure).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

MAX_CHARS = 4000
TIMEOUT = 20


def _clip(text: str, limit: int = MAX_CHARS) -> str:
    return text if len(text) <= limit else text[:limit] + "…"


def cm_context(query: str, max_chars: int) -> str | None:
    if shutil.which("cm") is None:
        return None
    proc = subprocess.run(
        ["cm", "context", query, "--json"],
        capture_output=True, text=True, timeout=TIMEOUT,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    return _clip(proc.stdout.strip(), max_chars)


def cass_healthy() -> bool:
    if shutil.which("cass") is None:
        return False
    proc = subprocess.run(
        ["cass", "health", "--json"],
        capture_output=True, text=True, timeout=TIMEOUT,
    )
    try:
        return proc.returncode == 0 and bool(
            json.loads(proc.stdout).get("healthy"))
    except (json.JSONDecodeError, AttributeError):
        return False


def cass_search(query: str, max_chars: int) -> list | None:
    proc = subprocess.run(
        ["cass", "search", query, "--robot", "--limit", "5",
         "--fields", "minimal"],
        capture_output=True, text=True, timeout=TIMEOUT,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        results = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return [{"raw": _clip(proc.stdout, max_chars)}]
    if isinstance(results, list):
        return results[:5]
    return [results]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--max-chars", type=int, default=MAX_CHARS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    evidence: dict = {"skipped": []}

    cm = cm_context(args.query, args.max_chars)
    if cm is not None:
        evidence["cm"] = cm
    else:
        evidence["skipped"].append("cm: missing or no context")

    if cass_healthy():
        hits = cass_search(args.query, args.max_chars)
        if hits:
            evidence["cass"] = hits
        else:
            evidence["skipped"].append("cass: no results")
    else:
        evidence["skipped"].append("cass: unhealthy or missing")

    if args.json:
        print(json.dumps(evidence))
    else:
        for key, value in evidence.items():
            print(f"--- {key} ---")
            print(value if isinstance(value, str)
                  else json.dumps(value, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
