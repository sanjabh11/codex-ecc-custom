#!/usr/bin/env python3
"""escalate — send gated verdicts to the human via `hermes send`.

Reads a verdict JSON ({"band": ..., ...}) from stdin or --verdict-file.
If the band is in --on (default ask,deny,review) the verdict is formatted
into a bounded, secret-redacted message and sent through `hermes send`.

Usage:
  route_tool_call.py --json ... | escalate.py            # dry-run
  escalate.py --send --to telegram < verdict.json        # deliver
Exit: 0 delivered/nothing-to-do, 2 dry-run, 1 send failed.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LEDGER = (
    Path.home() / "codex-ecc-custom" / ".phase-loop" / "phase-ledger.jsonl"
)
CMD_MAX = 200
SECRET_RES = [
    re.compile(r"\b(sk|pk|api|key|token|secret|password|pass)[_-]?"
               r"[A-Za-z0-9._-]{8,}\b", re.IGNORECASE),
    re.compile(r"\b[A-Za-z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)"
               r"\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"(\b(?:api[-_ ]?key|token|secret|password|credential)"
               r"\s*(?:is\s*)?[:= ]?\s+)[A-Za-z0-9._-]{8,}", re.IGNORECASE),
]


def _redact_match(match: re.Match) -> str:
    return (match.group(1) if match.lastindex else "") + "[redacted]"


def redact(text: str) -> str:
    for pattern in SECRET_RES:
        text = pattern.sub(_redact_match, text)
    return text[:CMD_MAX]





def load_verdict(raw: str) -> dict:
    data = json.loads(raw.strip() or "{}")
    if not isinstance(data, dict) or "band" not in data:
        raise RuntimeError("verdict payload must be JSON with a 'band' key")
    return data


def format_message(verdict: dict) -> str:
    lines = [
        f"JEV gate: {verdict.get('band', '?').upper()}",
        f"pack/item: {verdict.get('pack', 'tool-route')} "
        f"{verdict.get('item_id', '')}",
    ]
    command = verdict.get("command") or verdict.get("context") or ""
    if command:
        lines.append(f"cmd: {redact(str(command))}")
    reasons = verdict.get("gate_reasons") or []
    if reasons:
        lines.append("reasons: " + redact("; ".join(map(str, reasons[:3]))))
    lines.append("reply allow or deny")
    return "\n".join(lines)


def append_ledger(verdict: dict, sent: bool, ledger: Path) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "type": "escalation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pack": verdict.get("pack", "tool-route"),
        "item_id": verdict.get("item_id", ""),
        "decision": verdict.get("band", "?"),
        "delivered": sent,
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def send_hermes(message: str, target: str, subject: str) -> bool:
    if shutil.which("hermes") is None:
        raise RuntimeError("hermes CLI not found on PATH")
    proc = subprocess.run(
        ["hermes", "send", "--to", target, "--subject", subject,
         "--quiet", message],
        capture_output=True, text=True, timeout=120,
    )
    return proc.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verdict-file", type=Path,
                        help="read verdict JSON from file instead of stdin")
    parser.add_argument("--on", default="ask,deny,review",
                        help="comma-separated bands that trigger escalation")
    parser.add_argument("--to", default="telegram")
    parser.add_argument("--subject", default="JEV escalation")
    parser.add_argument("--send", action="store_true",
                        help="actually deliver; default is dry-run")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    raw = (args.verdict_file.read_text(encoding="utf-8")
           if args.verdict_file else sys.stdin.read())
    try:
        verdict = load_verdict(raw)
    except Exception as error:
        print(f"escalate: bad verdict payload: {error}", file=sys.stderr)
        return 1

    bands = {b.strip() for b in args.on.split(",") if b.strip()}
    band = str(verdict.get("band", ""))
    if band not in bands:
        if args.json:
            print(json.dumps({"escalated": False, "band": band}))
        else:
            print(f"band={band} not in escalate set — nothing to send")
        return 0

    message = format_message(verdict)
    if not args.send:
        if args.json:
            print(json.dumps({"escalated": False, "dry_run": True,
                              "band": band, "message": message}))
        else:
            print(f"[dry-run] would send to {args.to}:\n{message}")
        append_ledger(verdict, sent=False, ledger=args.ledger)
        return 2

    try:
        sent = send_hermes(message, args.to, args.subject)
    except Exception as error:
        print(f"escalate: send failed: {error}", file=sys.stderr)
        sent = False
    append_ledger(verdict, sent=sent, ledger=args.ledger)
    if args.json:
        print(json.dumps({"escalated": sent, "band": band}))
    else:
        print("delivered" if sent else "send failed")
    return 0 if sent else 1


if __name__ == "__main__":
    raise SystemExit(main())
