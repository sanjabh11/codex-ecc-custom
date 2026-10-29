#!/usr/bin/env python3
"""sandbox_exec — run a command inside an E2B sandbox.

The sandbox half of the JEV narrow-decision loop: route_tool_call judges
whether code should run locally or sandboxed; this executes the sandbox
side. Missing E2B_API_KEY exits 10 with a NEEDS marker so callers can
collect the credential once, never silently fall back to local execution.

Usage:
  python3 sandbox_exec.py --command "uname -a" [--timeout 120] [--json]
  uv run --with e2b sandbox_exec.py --command "..."
Exit: 0 ran, 10 missing E2B_API_KEY, 2 e2b SDK missing, 1 sandbox error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LEDGER = (
    Path.home() / "codex-ecc-custom" / ".phase-loop" / "phase-ledger.jsonl"
)
CMD_MAX = 2000


def append_ledger(command: str, status: str, ledger: Path) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "type": "sandbox-run",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "context": command[:200],
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def run_in_sandbox(command: str, timeout: int) -> dict:
    try:
        from e2b_code_interpreter import Sandbox  # type: ignore
    except ImportError:
        try:
            from e2b import Sandbox  # type: ignore
        except ImportError:
            raise RuntimeError("e2b SDK not installed")
    sandbox = Sandbox.create(timeout=timeout)
    try:
        run = getattr(sandbox, "run_code", None) or getattr(
            sandbox, "commands", None)
        if hasattr(sandbox, "commands"):
            proc = sandbox.commands.run(command, timeout=timeout)
            return {
                "exit_code": getattr(proc, "exit_code", None),
                "stdout": str(getattr(proc, "stdout", ""))[:8000],
                "stderr": str(getattr(proc, "stderr", ""))[:4000],
            }
        result = sandbox.run_code(command)
        return {
            "exit_code": 0 if not getattr(result, "error", None) else 1,
            "stdout": str(getattr(result, "text", ""))[:8000],
            "stderr": str(getattr(result, "error", ""))[:4000],
        }
    finally:
        kill = getattr(sandbox, "kill", None) or getattr(sandbox, "close", None)
        if kill:
            kill()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if len(args.command) > CMD_MAX:
        print("command too long for sandbox submission", file=sys.stderr)
        return 1
    if not os.environ.get("E2B_API_KEY"):
        print("NEEDS_INPUT\nMISSING=E2B_API_KEY")
        append_ledger(args.command, "refused-no-key", args.ledger)
        return 10

    try:
        result = run_in_sandbox(args.command, args.timeout)
    except RuntimeError as error:
        if "not installed" in str(error):
            print("e2b SDK missing — run via `uv run --with e2b ...` "
                  "or `pip install e2b`", file=sys.stderr)
            append_ledger(args.command, "refused-no-sdk", args.ledger)
            return 2
        print(f"sandbox error: {error}", file=sys.stderr)
        append_ledger(args.command, "error", args.ledger)
        return 1
    except Exception as error:
        print(f"sandbox error: {error}", file=sys.stderr)
        append_ledger(args.command, "error", args.ledger)
        return 1

    append_ledger(args.command, "ran", args.ledger)
    if args.json:
        print(json.dumps(result))
    else:
        sys.stdout.write(result["stdout"])
        if result["stderr"]:
            sys.stderr.write(result["stderr"])
        print(f"\n[sandbox exit={result['exit_code']}]")
    return int(result["exit_code"] or 0)


if __name__ == "__main__":
    raise SystemExit(main())
