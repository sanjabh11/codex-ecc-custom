#!/usr/bin/env python3
"""Scenario: State file permissions and versioning.

Tests that advisor_state.json is written with 0600 permissions
and includes the version field.
"""

import json
import os
import stat
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fable.advisor_cli import reset_state, save_state, load_state, ADVISOR_STATE, STATE_VERSION


def main():
    reset_state()

    # Test 1: State file has version field
    state = load_state()
    assert state.get("version") == STATE_VERSION, \
        f"State should have version={STATE_VERSION}, got {state.get('version')}"

    # Test 2: State file permissions are 0600 (owner read/write only)
    file_stat = ADVISOR_STATE.stat()
    file_mode = stat.S_IMODE(file_stat.st_mode)
    assert file_mode == 0o600, \
        f"State file should have 0600 permissions, got {oct(file_mode)}"

    # Test 3: Save state preserves version
    state["call_count"] = 1
    state["history"] = [{"call": 1, "context_preview": "test", "response_preview": "resp", "timestamp": "2024-01-01T00:00:00Z"}]
    save_state(state)
    loaded = load_state()
    assert loaded.get("version") == STATE_VERSION, \
        f"Version should persist after save, got {loaded.get('version')}"

    # Test 4: Re-check permissions after save
    file_stat = ADVISOR_STATE.stat()
    file_mode = stat.S_IMODE(file_stat.st_mode)
    assert file_mode == 0o600, \
        f"State file should still have 0600 after save, got {oct(file_mode)}"

    reset_state()
    print("PASS: state_permissions_versioning — 0600 perms + version field verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
