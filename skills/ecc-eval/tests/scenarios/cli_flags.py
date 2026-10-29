#!/usr/bin/env python3
"""Scenario: CLI flags — workdir, sandbox, ignore-config, ignore-rules, no-ephemeral, extra-args."""

import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
RUNNER = SKILL_DIR / "scripts" / "run_eval.sh"

def main():
    result = subprocess.run(
        ["bash", str(RUNNER), "--help"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, f"--help failed with exit {result.returncode}"

    flags = [
        "--workdir", "--sandbox", "--ignore-config", "--ignore-rules",
        "--no-ephemeral", "--extra-args", "--skip-git-check",
    ]
    for flag in flags:
        assert flag in result.stdout, f"{flag} not in --help output"

    print("PASS: cli_flags — all CLI flags present in --help")
    sys.exit(0)


if __name__ == "__main__":
    main()
