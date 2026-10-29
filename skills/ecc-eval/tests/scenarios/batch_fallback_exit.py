#!/usr/bin/env python3
"""Scenario: Batch fallback exits 1 when 0 files evaluated."""

import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
RUNNER = SKILL_DIR / "scripts" / "run_eval.sh"

def main():
    result = subprocess.run(
        ["bash", str(RUNNER), "--backend", "fallback",
         "--batch", "skills/*/NONEXISTENT.md",
         "--prompt", "test",
         "--output-dir", "/tmp/eval-batch-test/"],
        capture_output=True, text=True, timeout=10,
        cwd=str(SKILL_DIR.parent.parent),
    )
    assert result.returncode == 1, f"Expected exit 1 for 0 files evaluated, got {result.returncode}"
    assert "No files were evaluated" in result.stderr, f"Expected error message, got: {result.stderr[:100]}"

    print("PASS: batch_fallback_exit_code — exits 1 when 0 files evaluated")
    sys.exit(0)


if __name__ == "__main__":
    main()
