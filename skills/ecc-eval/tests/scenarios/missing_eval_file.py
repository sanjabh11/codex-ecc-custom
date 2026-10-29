#!/usr/bin/env python3
"""Scenario: Missing eval file — runner handles nonexistent eval file gracefully."""

import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
RUNNER = SKILL_DIR / "scripts" / "run_eval.sh"

def main():
    # With --prompt and nonexistent --eval, runner should still work
    # (eval file is optional when prompt is provided)
    result = subprocess.run(
        ["bash", str(RUNNER), "--backend", "fallback",
         "--eval", "/nonexistent/file.md",
         "--prompt", "test eval prompt"],
        capture_output=True, text=True, timeout=10
    )
    # Fallback exits 1 but should not crash
    assert result.returncode == 1, f"Expected exit 1, got {result.returncode}"
    assert "No non-interactive runner" in result.stderr

    # Without --prompt and nonexistent --eval, runner should error
    result2 = subprocess.run(
        ["bash", str(RUNNER), "--backend", "fallback",
         "--eval", "/nonexistent/file.md"],
        capture_output=True, text=True, timeout=10
    )
    assert result2.returncode == 1, f"Expected exit 1, got {result2.returncode}"

    print("PASS: missing_eval_file — handles nonexistent eval file gracefully")
    sys.exit(0)


if __name__ == "__main__":
    main()
