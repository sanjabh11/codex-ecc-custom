#!/usr/bin/env python3
"""Scenario 4: Schema drift failure — state with invalid fields, expects validator FAIL.

A state file with schema-incompatible fields (wrong enum value, missing required field)
should cause the validator to fail, not silently pass.
"""
import sys
import json
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from validate_skill import validate_audit_instance


def run():
    tmpdir = Path(tempfile.mkdtemp(prefix="audit_schema_drift_"))

    # Intentionally invalid state: missing required fields, wrong enum values
    state = {
        "audit_id": "AUD-DRIFT-004",
        "product_context": "Test product",
        "scope": "invalid_scope",  # NOT in enum [quick, standard, deep]
        "started_at": "2026-07-13T10:00:00Z",
        "current_phase": "INVALID_PHASE",  # NOT in valid enum
        "decision_confidence": {
            "composite": 50,
            "quality": 15,
            "coverage": 12,
            "consistency": 10,
            "counter": 8,
            "validation": 5,
        },
        "evidence_types_present": ["user_quote"],
        "evidence_limitations": [],
        "phases_completed": ["phase-0"],
        "gates_passed": [],
        "schema_version": "v8",
        "evidence_limited_mode": False,
        "market_validation_status": "invalid_status",  # NOT in valid enum
        "experiments_designed": 0,
        "experiments_executed": 0,
        "last_updated": "2026-07-13T10:00:00Z",
    }

    experiments = {
        "audit_id": "AUD-DRIFT-004",
        "experiments": [],
        "schema_version": "v8",
    }

    (tmpdir / "state.json").write_text(json.dumps(state, indent=2))
    (tmpdir / "experiments.json").write_text(json.dumps(experiments, indent=2))

    # The validate_audit_instance function should either fail or produce failing checks
    result = validate_audit_instance(tmpdir)

    # With invalid state, the validator should not silently pass all checks
    # At minimum, the executed_count_consistency should pass (0 == 0)
    # But the design_is_not_validation check should catch the invalid market_validation_status
    checks_by_name = {c["name"]: c for c in result["checks"]}

    # The market_validation_status is "invalid_status" which is NOT "validation_pending"
    # So the design_is_not_validation check should FAIL
    if "design_is_not_validation" in checks_by_name:
        assert not checks_by_name["design_is_not_validation"]["pass"], \
            "Validator should FAIL design_is_not_validation check with invalid market_validation_status"
    assert not result["all_pass"], "Schema drift must fail the persisted-audit validator"

    print("PASS: schema_drift_failure — validator correctly detects schema drift")
    return 0


if __name__ == "__main__":
    sys.exit(run())
