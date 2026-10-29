#!/usr/bin/env python3
"""Scenario: No args — runner errors when no prompt or eval file provided."""

import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
RUNNER = SKILL_DIR / "scripts" / "run_eval.sh"

def main():
    result = subprocess.run(
        ["bash", str(RUNNER), "--backend", "fallback"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 1, f"Expected exit 1, got {result.returncode}"
    assert "No prompt or eval file provided" in result.stderr, f"Expected error, got: {result.stderr[:100]}"

    print("PASS: no_args — errors when no prompt or eval file provided")
    sys.exit(0)


if __name__ == "__main__":
    main()
