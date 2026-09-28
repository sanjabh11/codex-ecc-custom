#!/usr/bin/env python3
"""Scenario: Cost control — call cap and dry-run don't consume budget.

Tests that the call cap works correctly and dry-run doesn't increment
the counter.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent

# Hermetic FABLE_DIR — advisor_cli resolves state/config paths at import time.
_FABLE = Path(tempfile.mkdtemp(prefix="fable-scenario-"))
shutil.copy(PROJECT_ROOT / "fable" / "advisor_config.json", _FABLE / "advisor_config.json")
os.environ["FABLE_DIR"] = str(_FABLE)

sys.path.insert(0, str(PROJECT_ROOT))

from fable.advisor_cli import get_advice, load_config, reset_state, load_state


def main():
    reset_state()
    config = load_config()

    # Test 1: Dry run doesn't consume budget
    result = get_advice("test context", config, dry_run=True)
    assert "Dry run" in result, f"Expected dry run message, got: {result[:80]}"
    state = load_state()
    assert state["call_count"] == 0, f"Dry run should not increment counter, got {state['call_count']}"

    # Test 2: Cap reached returns fallback
    max_calls = config.get("max_advisor_calls", 30)
    state["call_count"] = max_calls
    from fable.advisor_cli import save_state
    save_state(state)

    result = get_advice("test context", config)
    assert "Call cap reached" in result, f"Expected cap message, got: {result[:80]}"
    state = load_state()
    assert state["call_count"] == max_calls, f"Cap should not increment counter, got {state['call_count']}"

    # Test 3: Dry run works even at cap
    result = get_advice("test context", config, dry_run=True)
    assert "Dry run" in result, f"Dry run should work at cap, got: {result[:80]}"

    reset_state()
    print("PASS: cost_control_dry_run — cap and dry-run budget verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
