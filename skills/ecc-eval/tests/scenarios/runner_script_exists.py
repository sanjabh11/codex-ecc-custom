#!/usr/bin/env python3
"""Scenario: Runner script exists and is executable."""

import os
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent

def main():
    runner = SKILL_DIR / "scripts" / "run_eval.sh"
    assert runner.exists(), f"run_eval.sh not found at {runner}"
    assert os.access(runner, os.X_OK), "run_eval.sh is not executable"

    content = runner.read_text()
    assert "codex exec" in content, "codex exec backend missing"
    assert "claude -p" in content, "claude -p fallback missing"
    assert "detect_backend" in content, "backend detection missing"
    assert "--ephemeral" in content, "ephemeral flag missing"
    assert "--batch" in content, "batch mode missing"

    print("PASS: runner_script_exists — runner script verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
