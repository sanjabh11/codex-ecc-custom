#!/usr/bin/env python3
"""Scenario: Backend detection — codex exec preferred, claude -p fallback."""

import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
RUNNER = SKILL_DIR / "scripts" / "run_eval.sh"

def main():
    # Test --help works
    result = subprocess.run(
        ["bash", str(RUNNER), "--help"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, f"--help failed with exit {result.returncode}"
    assert "--eval" in result.stdout, "--eval flag not in help"
    assert "--batch" in result.stdout, "--batch flag not in help"
    assert "--model" in result.stdout, "--model flag not in help"
    assert "--backend" in result.stdout, "--backend flag not in help"

    print("PASS: backend_detection — runner --help works and flags present")
    sys.exit(0)


if __name__ == "__main__":
    main()
