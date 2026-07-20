#!/usr/bin/env python3
"""Scenario: JSON output mode produces valid structured response.

Tests that --json flag produces a response matching advisor-response.schema.json.
"""

import json
import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


def main():
    # Run the CLI with --dry-run --json to get a structured response without API call
    cli_path = PROJECT_ROOT / "fable" / "advisor_cli.py"
    result = subprocess.run(
        [sys.executable, str(cli_path), "--json", "--dry-run", "test context for json mode"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT),
    )

    assert result.returncode == 0, f"CLI exited with {result.returncode}: {result.stderr}"

    response = json.loads(result.stdout)

    # Verify required fields from advisor-response.schema.json
    assert "status" in response, "Missing 'status' field"
    assert "advice" in response, "Missing 'advice' field"
    assert "call_count" in response, "Missing 'call_count' field"
    assert "calls_remaining" in response, "Missing 'calls_remaining' field"
    assert "backend" in response, "Missing 'backend' field"

    # Verify status is dry_run
    assert response["status"] == "dry_run", f"Expected status 'dry_run', got '{response['status']}'"

    # Verify backend is a valid enum value
    assert response["backend"] in ("grok_cli", "claude_native", "codex_orchestration", "fallback"), \
        f"Invalid backend value: {response['backend']}"

    # Verify calls_remaining is non-negative
    assert response["calls_remaining"] >= 0, f"calls_remaining should be >= 0, got {response['calls_remaining']}"

    print("PASS: json_output — structured JSON response matches schema")
    sys.exit(0)


if __name__ == "__main__":
    main()
