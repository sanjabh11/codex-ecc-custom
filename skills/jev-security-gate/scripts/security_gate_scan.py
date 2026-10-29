#!/usr/bin/env python3
"""security_gate_scan — semgrep findings judged by the security-findings pack.

Pipeline: semgrep --json -> findings rows -> security-findings verdict pack
-> block/fix/accept bands -> pack-decision trace records in the phase ledger.

Usage:
  python3 security_gate_scan.py --path skills/ [--rules-config auto]
      [--simulate] [--ledger PATH] [--json]
Exit: 0 no blocking findings, 1 scan/pack failure, 2 >=1 blocking finding.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

JEV_DIR = Path(os.environ.get("JEV_DIR", Path.home() / "jev-starter"))
JEV_PYTHON = JEV_DIR / ".venv" / "bin" / "python"
DEFAULT_LEDGER = (
    Path.home() / "codex-ecc-custom" / ".phase-loop" / "phase-ledger.jsonl"
)
OUT_DIR = JEV_DIR / "artifacts" / "pack-runs" / "security-findings"
SNIPPET_MAX = 200
FINDINGS_MAX = 50


def _jev_python() -> str:
    return str(JEV_PYTHON) if JEV_PYTHON.is_file() else sys.executable


def run_semgrep(path: Path, rules_config: str,
                context: str = "repository code under review") -> list[dict]:
    if shutil.which("semgrep") is None:
        raise RuntimeError(
            "semgrep not found on PATH — install with `uv tool install semgrep`"
        )
    proc = subprocess.run(
        ["semgrep", "--config", rules_config, "--json",
         "--quiet", "--no-git-ignore", str(path)],
        capture_output=True, text=True, timeout=600,
    )
    if proc.returncode not in (0, 1):  # 1 = findings present on some versions
        raise RuntimeError(f"semgrep failed: {proc.stderr.strip()[:300]}")
    data = json.loads(proc.stdout or "{}")
    rows = []
    for finding in (data.get("results") or [])[:FINDINGS_MAX]:
        check = str(finding.get("check_id", "?"))
        path_str = str(finding.get("path", "?"))
        extra = finding.get("extra") or {}
        rows.append({
            "id": f"{path_str}:{finding.get('start', {}).get('line', '?')}",
            "state": {
                "rule": check.split(".")[-1],
                "severity": str(extra.get("severity", "?")),
                "message": str(extra.get("message", ""))[:200],
                "path": path_str,
                "snippet": str(extra.get("lines", ""))[:SNIPPET_MAX],
                "context": context,
            },
        })
    return rows


def run_pack(rows: list[dict], simulate: bool) -> dict[str, dict]:
    if not rows:
        return {}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
        rows_path = handle.name
    cmd = [
        _jev_python(), "packs.py", "--pack", "security-findings",
        "--input", rows_path, "--out-dir", str(OUT_DIR),
    ]
    if simulate:
        # simulated answers must never enter the shared cache — a later live
        # scan would otherwise serve them as real verdicts
        cmd += ["--simulate", "--cache-dir",
                tempfile.mkdtemp(prefix="sim-cache-")]
    else:
        cmd += ["--cache-dir", str(OUT_DIR / "live-cache")]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=JEV_DIR)
    if proc.returncode != 0:
        raise RuntimeError(f"packs.py failed: {proc.stderr.strip()[:300]}")

    verdicts: dict[str, dict] = {}
    for artifact in OUT_DIR.glob("*.jsonl"):
        for line in artifact.read_text(encoding="utf-8").splitlines():
            record = json.loads(line) if line.strip() else {}
            if record.get("id"):
                verdicts[str(record["id"])] = {
                    "decision": str(record.get("decision", "fix")),
                    "score": float(record.get("score") or 0.0),
                }
    return verdicts


def append_ledger(rows: list[dict], verdicts: dict[str, dict],
                  simulate: bool, ledger: Path) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        for row in rows:
            verdict = verdicts.get(str(row["id"]), {})
            record = {
                "type": "pack-decision",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pack": "security-findings",
                "item_id": str(row["id"]),
                "decision": verdict.get("decision", "unknown"),
                "score": verdict.get("score", 0.0),
                "gate_verdict": "scan",
                "simulated": simulate,
                "context": f"{row['state']['rule']} @ {row['state']['path']}",
            }
            handle.write(json.dumps(record) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--rules-config", default="auto")
    parser.add_argument("--context", default="repository code under review",
                        help="what the scanned code is — sharper state means "
                             "fewer clarity-floored reviews")
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    rows = run_semgrep(args.path, args.rules_config, args.context)
    verdicts = run_pack(rows, args.simulate)
    append_ledger(rows, verdicts, args.simulate, args.ledger)

    bands: dict[str, int] = {}
    for verdict in verdicts.values():
        bands[verdict["decision"]] = bands.get(verdict["decision"], 0) + 1
    payload = {
        "findings": len(rows),
        "bands": bands,
        "blocking": bands.get("block", 0),
        "simulated": args.simulate,
    }
    if args.json:
        print(json.dumps(payload))
    else:
        note = " (simulated)" if args.simulate else ""
        print(f"findings={len(rows)} bands={bands}{note}")
    return 2 if bands.get("block") else 0


if __name__ == "__main__":
    raise SystemExit(main())
