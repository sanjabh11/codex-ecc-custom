#!/usr/bin/env python3
"""Scenario: Fallback mode — no runner available, prints manual instructions."""

import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
RUNNER = SKILL_DIR / "scripts" / "run_eval.sh"

def main():
    # Force fallback backend with a simple eval prompt
    result = subprocess.run(
        ["bash", str(RUNNER), "--backend", "fallback", "--prompt", "test eval", "--eval", "/dev/null"],
        capture_output=True, text=True, timeout=10
    )
    # Fallback should exit 1 and print manual instructions
    assert result.returncode == 1, f"Expected exit 1 for fallback, got {result.returncode}"
    assert "No non-interactive runner available" in result.stderr, "Fallback message missing"

    print("PASS: fallback_mode — fallback exits 1 with manual instructions")
    sys.exit(0)


if __name__ == "__main__":
    main()
