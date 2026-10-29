#!/usr/bin/env python3
"""Scenario: Corrupted state file recovery.

Tests that load_state() recovers gracefully when advisor_state.json
is corrupted (invalid JSON, missing fields, etc.).
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fable.advisor_cli import load_state, reset_state, ADVISOR_STATE


def main():
    reset_state()

    # Test 1: Invalid JSON
    ADVISOR_STATE.write_text("{invalid json!!!")
    state = load_state()
    assert state["call_count"] == 0, f"Corrupted JSON should reset to defaults, got call_count={state['call_count']}"
    assert state["history"] == [], f"Corrupted JSON should reset to empty history"

    # Test 2: Missing required fields
    ADVISOR_STATE.write_text(json.dumps({"foo": "bar"}))
    state = load_state()
    assert state["call_count"] == 0, f"Missing fields should reset to defaults"
    assert state["history"] == [], f"Missing fields should reset to empty history"

    # Test 3: Valid state loads correctly
    reset_state()
    valid_state = {"call_count": 2, "history": [{"call": 1, "context_preview": "test", "response_preview": "resp", "timestamp": "2024-01-01T00:00:00Z"}], "session_id": None, "version": 1}
    ADVISOR_STATE.write_text(json.dumps(valid_state))
    state = load_state()
    assert state["call_count"] == 2, f"Valid state should load, got call_count={state['call_count']}"

    reset_state()
    print("PASS: corrupted_state_recovery — recovers from invalid JSON and missing fields")
    sys.exit(0)


if __name__ == "__main__":
    main()
