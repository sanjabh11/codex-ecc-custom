#!/usr/bin/env python3
"""Scenario: History pruning.

Tests that history is pruned to MAX_HISTORY_ENTRIES when it grows
too large, preventing unbounded state file growth.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fable.advisor_cli import (
    get_advice, load_config, load_state, reset_state, save_state,
    MAX_HISTORY_ENTRIES,
)


def main():
    reset_state()
    config = load_config()

    # Manually create a state with more than MAX_HISTORY_ENTRIES
    state = load_state()
    state["call_count"] = MAX_HISTORY_ENTRIES + 10
    state["history"] = [
        {"call": i + 1, "context_preview": f"ctx-{i}", "response_preview": f"resp-{i}",
         "timestamp": "2024-01-01T00:00:00Z"}
        for i in range(MAX_HISTORY_ENTRIES + 10)
    ]
    save_state(state)

    # Verify history was pruned during save
    loaded = load_state()
    assert len(loaded["history"]) <= MAX_HISTORY_ENTRIES, \
        f"History should be pruned to {MAX_HISTORY_ENTRIES}, got {len(loaded['history'])}"

    # Verify the most recent entries are kept (not the oldest)
    first_entry = loaded["history"][0]
    last_entry = loaded["history"][-1]
    assert int(first_entry["call"]) < int(last_entry["call"]), \
        "History should preserve order — oldest pruned, newest kept"

    # Verify the last entry is the most recent
    assert int(last_entry["call"]) == MAX_HISTORY_ENTRIES + 10, \
        f"Last entry should be the most recent (call {MAX_HISTORY_ENTRIES + 10}), got {last_entry['call']}"

    reset_state()
    print(f"PASS: history_pruning — pruned to {MAX_HISTORY_ENTRIES} entries, newest kept")
    sys.exit(0)


if __name__ == "__main__":
    main()
