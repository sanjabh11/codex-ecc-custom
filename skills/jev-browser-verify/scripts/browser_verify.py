#!/usr/bin/env python3
"""browser_verify — judge captured browser evidence through browser-verify pack.

The agent captures evidence via the playwright MCP server (snapshot text or
screenshot description), saves it to a file, and this script packs it into a
row, runs the ``browser-verify`` verdict pack, and appends a ``pack-decision``
record to the phase ledger.

Usage:
  python3 browser_verify.py --evidence snapshot.txt \
      --expect "title visible, nav has 5 items" [--url URL] [--simulate] [--json]
Exit: 0 pass, 2 review, 1 fail or infra error.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

JEV_DIR = Path(os.environ.get("JEV_DIR", Path.home() / "jev-starter"))
JEV_PYTHON = JEV_DIR / ".venv" / "bin" / "python"
DEFAULT_LEDGER = (
    Path.home() / "codex-ecc-custom" / ".phase-loop" / "phase-ledger.jsonl"
)
OUT_DIR = JEV_DIR / "artifacts" / "pack-runs" / "browser-verify"
EVIDENCE_MAX = 8000
BAND_EXIT = {"pass": 0, "review": 2, "fail": 1}


def _jev_python() -> str:
    return str(JEV_PYTHON) if JEV_PYTHON.is_file() else sys.executable


def load_evidence(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"evidence file not found: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > EVIDENCE_MAX:
        text = text[:EVIDENCE_MAX] + f"\n[... truncated {len(text) - EVIDENCE_MAX} chars]"
    return text


def run_pack(row: dict, simulate: bool) -> tuple[str, float]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(json.dumps(row) + "\n")
        rows_path = handle.name
    cmd = [
        _jev_python(), "packs.py", "--pack", "browser-verify",
        "--input", rows_path, "--out-dir", str(OUT_DIR),
    ]
    if simulate:
        cmd += ["--simulate", "--cache-dir",
                tempfile.mkdtemp(prefix="sim-cache-")]
    else:
        cmd += ["--cache-dir", str(OUT_DIR / "live-cache")]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=JEV_DIR)
    if proc.returncode != 0:
        raise RuntimeError(f"packs.py failed: {proc.stderr.strip()[:300]}")

    item_id = str(row["id"])
    for artifact in OUT_DIR.glob("*.jsonl"):
        for line in artifact.read_text(encoding="utf-8").splitlines():
            record = json.loads(line) if line.strip() else {}
            if str(record.get("id")) == item_id:
                return str(record.get("decision", "review")), float(
                    record.get("score") or 0.0)
    return "review", 0.0


def append_ledger(item_id: str, decision: str, score: float,
                  url: str, simulate: bool, ledger: Path) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "type": "pack-decision",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pack": "browser-verify",
        "item_id": item_id,
        "decision": decision,
        "score": score,
        "gate_verdict": "verify",
        "simulated": simulate,
        "context": url[:200],
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--expect", required=True)
    parser.add_argument("--url", default="")
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        evidence = load_evidence(args.evidence)
        row = {
            "id": f"verify-{uuid.uuid4().hex[:12]}",
            "state": {
                "url": args.url,
                "expectation": args.expect,
                "evidence": evidence,
            },
        }
        decision, score = run_pack(row, args.simulate)
    except Exception as error:
        # verification infra broke -> review, never pass
        decision, score = "review", 0.0
        row = {"id": "verify-error"}
        print(f"verify error (escalating to review): {error}",
              file=sys.stderr)
    append_ledger(str(row["id"]), decision, score,
                  args.url, args.simulate, args.ledger)

    payload = {"band": decision, "score": score,
               "simulated": args.simulate, "item_id": str(row["id"])}
    if args.json:
        print(json.dumps(payload))
    else:
        note = " (simulated)" if args.simulate else ""
        print(f"band={decision}{note} score={score:.0f}")
    return BAND_EXIT.get(decision, 2)


if __name__ == "__main__":
    raise SystemExit(main())
