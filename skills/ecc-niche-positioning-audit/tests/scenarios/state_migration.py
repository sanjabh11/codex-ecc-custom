#!/usr/bin/env python3
"""Scenario 7: legacy v7 state migrates to a schema-valid v8 state."""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from migrate_state import migrate_state, validate_state  # noqa: E402


def run() -> int:
    legacy = {
        "audit_id": "AUD-MIGRATE-007",
        "product_context": "Legacy product",
        "scope": "standard",
        "started_at": "2026-07-10T10:00:00Z",
        "current_phase": 4,
        "decision_confidence": {"composite": 42},
        "evidence_types_present": ["product_promise"],
        "evidence_limitations": ["Legacy state did not capture buyer evidence"],
        "phases_completed": [0, 1, 2, 3],
        "gates_passed": ["gate-1: CONDITIONAL_GO", "gate-2: RECYCLE"],
        "schema_version": "v7",
        "legacy_note": "must be reported as dropped",
    }
    migrated, dropped = migrate_state(legacy)
    assert migrated["current_phase"] == "phase-4"
    assert migrated["phases_completed"] == ["phase-0", "phase-1", "phase-2", "phase-3"]
    assert migrated["gates_passed"][0]["decision"] == "CONDITIONAL_GO"
    assert migrated["schema_version"] == "v8"
    assert "legacy_note" in dropped
    assert not validate_state(migrated), validate_state(migrated)
    print("PASS: state_migration — legacy state converted to schema-valid v8 without input overwrite")
    return 0


if __name__ == "__main__":
    sys.exit(run())
