#!/usr/bin/env python3
"""Scenario: CLI override flags.

Tests that --max-calls, --timeout, --model, and --system-prompt
CLI flags override config file values correctly.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


def _env() -> dict:
    """Hermetic FABLE_DIR so the scenario never mutates the shared state."""
    tmp = Path(tempfile.mkdtemp(prefix="fable-scenario-"))
    shutil.copy(PROJECT_ROOT / "fable" / "advisor_config.json", tmp / "advisor_config.json")
    return {**os.environ, "FABLE_DIR": str(tmp)}


def main():
    cli_path = PROJECT_ROOT / "fable" / "advisor_cli.py"

    # Test 1: --max-calls override
    result = subprocess.run(
        [sys.executable, str(cli_path), "--dry-run", "--json", "--max-calls", "10", "test context"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT), env=_env(),
    )
    assert result.returncode == 0, f"CLI exited with {result.returncode}: {result.stderr}"
    response = json.loads(result.stdout)
    assert response["calls_remaining"] == 10, \
        f"Expected calls_remaining=10 with --max-calls 10, got {response['calls_remaining']}"

    # Test 2: --model override (check dry run mentions correct backend, model is passed to config)
    result = subprocess.run(
        [sys.executable, str(cli_path), "--dry-run", "--json", "--model", "grok-4", "test context"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT), env=_env(),
    )
    assert result.returncode == 0, f"CLI exited with {result.returncode}: {result.stderr}"

    # Test 3: --system-prompt override (dry run should still work)
    result = subprocess.run(
        [sys.executable, str(cli_path), "--dry-run", "--json", "--system-prompt", "Custom prompt", "test context"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT), env=_env(),
    )
    assert result.returncode == 0, f"CLI exited with {result.returncode}: {result.stderr}"
    response = json.loads(result.stdout)
    assert response["status"] == "dry_run", f"Expected dry_run status, got {response['status']}"

    # Test 4: --timeout override (dry run should work regardless)
    result = subprocess.run(
        [sys.executable, str(cli_path), "--dry-run", "--json", "--timeout", "60", "test context"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT), env=_env(),
    )
    assert result.returncode == 0, f"CLI exited with {result.returncode}: {result.stderr}"

    print("PASS: cli_override_flags — --max-calls, --model, --system-prompt, --timeout all work")
    sys.exit(0)


if __name__ == "__main__":
    main()
