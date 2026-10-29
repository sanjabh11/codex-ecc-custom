#!/usr/bin/env python3
"""route_tool_call — judge a single tool/command call through the tool-route pack.

Pipeline per the JEV loop: deterministic gate first (exec_gate.py), then the
``tool-route`` verdict pack (Choice/Score/Noul questions), then code enforces
the band and appends a ``pack-decision`` trace record to the phase ledger.

Exit codes mirror exec_gate: 0 allow, 2 ask, 1 deny.

Usage:
  python3 route_tool_call.py --tool Bash --command "git push --force" \
      --context "user asked to fix history" [--simulate] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

JEV_DIR = Path(os.environ.get("JEV_DIR", Path.home() / "jev-starter"))
JEV_PYTHON = JEV_DIR / ".venv" / "bin" / "python"
DEFAULT_LEDGER = (
    Path.home() / "codex-ecc-custom" / ".phase-loop" / "phase-ledger.jsonl"
)
ARTIFACT_DIR = JEV_DIR / "artifacts" / "pack-runs" / "tool-route"
BAND_EXIT = {"allow": 0, "ask": 2, "deny": 1}


@dataclass(frozen=True)
class RouteResult:
    band: str
    score: float
    gate_verdict: str
    gate_reasons: list[str]
    simulated: bool
    item_id: str


def _jev_python() -> str:
    return str(JEV_PYTHON) if JEV_PYTHON.is_file() else sys.executable


def run_exec_gate(command: str) -> tuple[str, list[str]]:
    """Deterministic first pass; 'unknown' when the gate cannot answer."""
    try:
        proc = subprocess.run(
            [_jev_python(), "exec_gate.py", command, "--json"],
            capture_output=True, text=True, timeout=10, cwd=JEV_DIR,
        )
        data = json.loads(proc.stdout)
        if isinstance(data, dict) and "verdict" in data:
            reasons = data.get("reasons", [])
            if isinstance(reasons, str):
                reasons = [r.strip() for r in reasons.split(";") if r.strip()]
            return str(data["verdict"]), [str(r) for r in reasons]
    except Exception:  # gate broken -> keep judging, mark unknown
        pass
    return "unknown", ["exec_gate unavailable"]


def run_pack(row: dict, simulate: bool, out_dir: Path) -> RouteResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(json.dumps(row) + "\n")
        rows_path = handle.name
    cmd = [
        _jev_python(), "packs.py", "--pack", "tool-route",
        "--input", rows_path, "--out-dir", str(out_dir),
    ]
    if simulate:
        # keep simulated answers out of the shared cache
        cmd += ["--simulate", "--cache-dir",
                tempfile.mkdtemp(prefix="sim-cache-")]
    else:
        cmd += ["--cache-dir", str(out_dir / "live-cache")]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=JEV_DIR)
    if proc.returncode != 0:
        raise RuntimeError(f"packs.py failed: {proc.stderr.strip()[:300]}")

    item_id = str(row["id"])
    decision, score = "ask", 0.0
    for artifact in out_dir.glob("*.jsonl"):
        for line in artifact.read_text(encoding="utf-8").splitlines():
            record = json.loads(line) if line.strip() else {}
            if str(record.get("id")) == item_id:
                decision = str(record.get("decision", "ask"))
                score = float(record.get("score") or 0.0)
    state = row["state"]
    return RouteResult(
        band=decision, score=score,
        gate_verdict=str(state["gate_verdict"]),
        gate_reasons=list(state["gate_reasons"]),
        simulated=simulate, item_id=item_id,
    )


def append_ledger(result: RouteResult, context: str, ledger: Path) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "type": "pack-decision",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pack": "tool-route",
        "item_id": result.item_id,
        "decision": result.band,
        "score": result.score,
        "gate_verdict": result.gate_verdict,
        "simulated": result.simulated,
        "context": context[:200],
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", default="Bash")
    parser.add_argument("--command", required=True)
    parser.add_argument("--context", default="")
    parser.add_argument("--simulate", action="store_true",
                        help="no JEV spend; deterministic mock answers")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--out-dir", type=Path, default=ARTIFACT_DIR)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    gate_verdict, gate_reasons = run_exec_gate(args.command)
    row = {
        "id": f"route-{uuid.uuid4().hex[:12]}",
        "state": {
            "tool": args.tool,
            "command": args.command,
            "gate_verdict": gate_verdict,
            "gate_reasons": gate_reasons[:3],
            "context": args.context,
        },
    }
    try:
        result = run_pack(row, args.simulate, args.out_dir)
    except Exception as error:
        # pack broke -> escalate, never allow
        result = RouteResult(
            band="ask", score=0.0, gate_verdict=gate_verdict,
            gate_reasons=gate_reasons + [f"pack error: {str(error)[:120]}"],
            simulated=args.simulate, item_id=str(row["id"]),
        )
    append_ledger(result, args.command, args.ledger)

    payload = {
        "band": result.band,
        "score": result.score,
        "pack": "tool-route",
        "command": args.command,
        "gate_verdict": result.gate_verdict,
        "gate_reasons": result.gate_reasons,
        "simulated": result.simulated,
        "item_id": result.item_id,
    }
    if args.json:
        print(json.dumps(payload))
    else:
        note = " (simulated)" if result.simulated else ""
        print(f"band={result.band}{note} score={result.score:.0f} "
              f"gate={result.gate_verdict}")
    return BAND_EXIT.get(result.band, 2)


if __name__ == "__main__":
    raise SystemExit(main())
