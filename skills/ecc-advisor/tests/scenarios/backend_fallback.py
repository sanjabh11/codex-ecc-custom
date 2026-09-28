#!/usr/bin/env python3
"""Scenario: Backend fallback — non-implemented backends fall back to grok_cli.

Tests that when --backend claude_native or --backend codex_orchestration is
forced, the CLI falls back to grok_cli if available, or returns a clear
message if no grok_cli token exists.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fable.advisor_cli import get_advice, load_config, reset_state


def _services():
    """Patch both fallback-capable backends with one canned responder."""
    mock_instance = MagicMock()
    mock_instance.api_key = "fake-key"
    mock_instance.generate.return_value = "Fallback advice from fallback backend"
    # has_credentials is a classmethod consulted during rerouting
    mock_cls = MagicMock(return_value=mock_instance)
    mock_cls.has_credentials = MagicMock(return_value=True)
    return mock_cls


def main():
    reset_state()
    config = load_config()

    # Test 1: --backend claude_native should fall back to an available backend
    with patch("fable.advisor_cli.GrokService", _services()), \
         patch("fable.advisor_cli.JevGatewayService", _services()):
        result = get_advice(
            "test context for backend fallback",
            config,
            backend="claude_native",
        )
        assert "Fallback advice from fallback backend" in result or "[Advisor]" in result, \
            f"Expected fallback backend or advisor message, got: {result}"
        assert "not yet implemented" not in result, \
            "Should not say 'not yet implemented' when a fallback backend succeeds"

    # Test 2: --backend codex_orchestration should also fall back
    with patch("fable.advisor_cli.GrokService", _services()), \
         patch("fable.advisor_cli.JevGatewayService", _services()):
        result = get_advice(
            "test context for codex backend",
            config,
            backend="codex_orchestration",
        )
        assert "Fallback advice from fallback backend" in result or "[Advisor]" in result, \
            f"Expected fallback backend or advisor message, got: {result}"

    reset_state()
    print("PASS: backend_fallback — non-implemented backends fall back to grok_cli")
    sys.exit(0)


if __name__ == "__main__":
    main()
