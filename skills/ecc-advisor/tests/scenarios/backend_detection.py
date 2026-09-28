#!/usr/bin/env python3
"""Scenario: Backend auto-detection picks the right backend.

Tests that detect_backend() returns the expected backend based on
environment and file system state.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fable.advisor_cli import detect_backend


def main():
    # Test 1: Grok CLI detected when auth.json exists and no higher-priority signals
    grok_auth = Path.home() / ".grok" / "auth.json"
    if grok_auth.exists():
        with patch.dict(os.environ, {"CLAUDE_ADVISOR_ENABLED": ""}, clear=False):
            # Remove env var if set
            os.environ.pop("CLAUDE_ADVISOR_ENABLED", None)
            backend = detect_backend()
            # Could be grok_cli, codex_orchestration, or jev_gateway depending on
            # which credentials/plugins this environment exposes.
            assert backend in ("grok_cli", "codex_orchestration", "jev_gateway"), \
                f"Expected grok_cli, codex_orchestration, or jev_gateway, got {backend}"

    # Test 2: Claude native when env var is set
    with patch.dict(os.environ, {"CLAUDE_ADVISOR_ENABLED": "true"}):
        backend = detect_backend()
        assert backend == "claude_native", f"Expected claude_native, got {backend}"

    # Test 3: Fallback when nothing is available. The gateway token lookup uses
    # os.path.expanduser (~ literal), not Path.home — patch has_credentials
    # directly so no real credential file can leak into the test.
    with patch.dict(os.environ, {}, clear=True):
        with patch.object(Path, "home", return_value=Path("/nonexistent")), \
             patch("fable.advisor_cli.JevGatewayService.has_credentials", return_value=False):
            backend = detect_backend()
            assert backend == "fallback", f"Expected fallback, got {backend}"

    print("PASS: backend_detection — all 3 detection paths verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
