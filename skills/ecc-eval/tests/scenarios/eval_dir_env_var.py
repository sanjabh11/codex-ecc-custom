#!/usr/bin/env python3
"""Scenario: EVAL_DIR env var — runner resolves via EVAL_DIR."""

import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent

def main():
    env = os.environ.copy()
    env["EVAL_DIR"] = str(SKILL_DIR)

    result = subprocess.run(
        ["bash", str(SKILL_DIR / "scripts" / "run_eval.sh"), "--help"],
        capture_output=True, text=True, timeout=10,
        env=env,
    )
    assert result.returncode == 0, f"--help failed with exit {result.returncode}"
    assert "--eval" in result.stdout, "--eval flag not in help"

    print("PASS: eval_dir_env_var — EVAL_DIR env var works")
    sys.exit(0)


if __name__ == "__main__":
    main()
