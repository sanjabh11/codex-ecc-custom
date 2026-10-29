#!/usr/bin/env python3
"""pack_eval — regression-test a verdict pack against gold-labeled cases.

Reads an eval YAML (pack + labeled rows), runs the pack once via packs.py,
joins artifact decisions to gold bands, and reports hit-rate plus a
confusion matrix. Simulated runs only verify plumbing — neutral answers
produce mid-band decisions by design.

Usage:
  python3 pack_eval.py --eval evals/tool-route.eval.yaml [--simulate]
      [--min-accuracy 0.8] [--ledger PATH] [--json]
Exit: 0 accuracy ok, 2 below threshold, 1 failure.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

JEV_DIR = Path(os.environ.get("JEV_DIR", Path.home() / "jev-starter"))
JEV_PYTHON = JEV_DIR / ".venv" / "bin" / "python"
DEFAULT_LEDGER = (
    Path.home() / "codex-ecc-custom" / ".phase-loop" / "phase-ledger.jsonl"
)


def _jev_python() -> str:
    return str(JEV_PYTHON) if JEV_PYTHON.is_file() else sys.executable


def load_eval(path: Path) -> tuple[str, list[dict]]:
    try:
        import yaml  # type: ignore
    except ImportError:
        yaml = None
    raw = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(raw)
    else:
        # fall back to the engine venv's yaml
        proc = subprocess.run(
            [_jev_python(), "-c",
             "import yaml,sys,json; print(json.dumps(yaml.safe_load(sys.stdin.read())))"],
            input=raw, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError("pyyaml unavailable in system and venv python")
        data = json.loads(proc.stdout)
    pack = str(data.get("pack") or "")
    cases = data.get("cases") or []
    if not pack or not cases:
        raise RuntimeError(f"{path}: needs 'pack' and non-empty 'cases'")
    return pack, [
        {"id": str(c["id"]), "gold": str(c["gold"]), "state": c["state"]}
        for c in cases
    ]


def run_pack(pack: str, cases: list[dict], simulate: bool,
             out_dir: Path) -> dict[str, dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as handle:
        for case in cases:
            handle.write(json.dumps({"id": case["id"],
                                     "state": case["state"]}) + "\n")
        rows_path = handle.name
    cmd = [
        _jev_python(), "packs.py", "--pack", pack,
        "--input", rows_path, "--out-dir", str(out_dir),
        # evals must never serve cached verdicts — fresh cache dir per run
        "--cache-dir", tempfile.mkdtemp(prefix="eval-cache-"),
    ]
    if simulate:
        cmd.append("--simulate")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=JEV_DIR)
    if proc.returncode != 0:
        raise RuntimeError(f"packs.py failed: {proc.stderr.strip()[:300]}")

    decisions: dict[str, dict] = {}
    for artifact in out_dir.glob("*.jsonl"):
        for line in artifact.read_text(encoding="utf-8").splitlines():
            record = json.loads(line) if line.strip() else {}
            if record.get("id"):
                decisions[str(record["id"])] = {
                    "decision": str(record.get("decision", "unknown")),
                    "score": float(record.get("score") or 0.0),
                }
    return decisions


def append_ledger(pack: str, eval_name: str, accuracy: float,
                  cases: int, simulate: bool, ledger: Path) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "type": "pack-eval",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pack": pack,
        "eval": eval_name,
        "accuracy": accuracy,
        "cases": cases,
        "simulated": simulate,
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", dest="eval_path", type=Path, required=True)
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--min-accuracy", type=float, default=0.8)
    parser.add_argument("--out-dir", type=Path,
                        default=JEV_DIR / "artifacts" / "pack-runs" / "evals")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    pack, cases = load_eval(args.eval_path)
    decisions = run_pack(pack, cases, args.simulate, args.out_dir)

    hits, misses, confusion = 0, [], Counter()
    for case in cases:
        predicted = decisions.get(case["id"], {}).get("decision", "unknown")
        confusion[f"{case['gold']}->{predicted}"] += 1
        if predicted == case["gold"]:
            hits += 1
        else:
            misses.append({"id": case["id"], "gold": case["gold"],
                           "predicted": predicted})
    accuracy = hits / len(cases) if cases else 0.0
    append_ledger(pack, args.eval_path.name, accuracy,
                  len(cases), args.simulate, args.ledger)

    payload = {
        "pack": pack, "cases": len(cases), "hits": hits,
        "accuracy": round(accuracy, 3), "min_accuracy": args.min_accuracy,
        "misses": misses, "confusion": dict(confusion),
        "simulated": args.simulate,
    }
    if args.json:
        print(json.dumps(payload))
    else:
        note = " (simulated — plumbing only)" if args.simulate else ""
        print(f"pack={pack} accuracy={accuracy:.0%} "
              f"({hits}/{len(cases)}){note}")
        for miss in misses:
            print(f"  miss {miss['id']}: gold={miss['gold']} "
                  f"got={miss['predicted']}")
    return 0 if accuracy >= args.min_accuracy else 2


if __name__ == "__main__":
    raise SystemExit(main())
