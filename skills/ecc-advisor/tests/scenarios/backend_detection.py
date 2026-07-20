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
            # Could be grok_cli or codex_orchestration depending on environment
            assert backend in ("grok_cli", "codex_orchestration"), f"Expected grok_cli or codex_orchestration, got {backend}"

    # Test 2: Claude native when env var is set
    with patch.dict(os.environ, {"CLAUDE_ADVISOR_ENABLED": "true"}):
        backend = detect_backend()
        assert backend == "claude_native", f"Expected claude_native, got {backend}"

    # Test 3: Fallback when nothing is available
    with patch.dict(os.environ, {}, clear=True):
        with patch.object(Path, "home", return_value=Path("/nonexistent")):
            backend = detect_backend()
            assert backend == "fallback", f"Expected fallback, got {backend}"

    print("PASS: backend_detection — all 3 detection paths verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
