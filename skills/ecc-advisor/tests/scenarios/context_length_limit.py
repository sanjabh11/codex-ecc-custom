#!/usr/bin/env python3
"""Scenario: Context length limit.

Tests that excessively large context is truncated to MAX_CONTEXT_CHARS
to prevent API abuse and excessive token usage.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fable.advisor_cli import get_advice, load_config, reset_state, MAX_CONTEXT_CHARS


def main():
    reset_state()
    config = load_config()

    # Create context larger than MAX_CONTEXT_CHARS
    large_context = "A" * (MAX_CONTEXT_CHARS + 5000)

    with patch("fable.advisor_cli.GrokService") as MockGrok:
        mock_instance = MagicMock()
        mock_instance.api_key = "fake-key"
        mock_instance.generate.return_value = "Advice"
        MockGrok.return_value = mock_instance

        result = get_advice(large_context, config)

        # Check that the context was truncated before being passed to generate
        call_args = mock_instance.generate.call_args
        if call_args:
            prompt = call_args[1].get("prompt", "") or call_args[0][0]
            # The prompt includes context + wrapper text, so check it's not excessively large
            assert len(prompt) < MAX_CONTEXT_CHARS + 500, \
                f"Context should be truncated, prompt length={len(prompt)}"
            assert "[... truncated" in prompt, \
                f"Truncation marker missing in prompt"

    reset_state()
    print("PASS: context_length_limit — large context truncated to MAX_CONTEXT_CHARS")
    sys.exit(0)


if __name__ == "__main__":
    main()
