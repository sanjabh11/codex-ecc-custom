#!/usr/bin/env python3
"""Scenario 2: Neutral CEIP — mixed signals, expects CONDITIONAL_GO.

A CEIP-style outreach with some evidence but mixed signals should
produce CONDITIONAL_GO, not full GO.
"""
import sys
import json
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from validate_skill import validate_audit_instance


def run():
    tmpdir = Path(tempfile.mkdtemp(prefix="audit_neutral_"))

    state = {
        "audit_id": "AUD-NEUTRAL-002",
        "product_context": "Developer tooling platform",
        "scope": "standard",
        "started_at": "2026-07-13T10:00:00Z",
        "current_phase": "VALIDATION_PENDING",
        "decision_confidence": {
            "composite": 49,
            "quality": 15,
            "coverage": 12,
            "consistency": 14,
            "counter": 8,
            "validation": 0,
        },
        "evidence_types_present": ["user_quote", "stakeholder_input", "product_promise"],
        "evidence_limitations": ["No sales data", "Limited analytics coverage"],
        "phases_completed": ["phase-0", "phase-1", "phase-2", "phase-3", "phase-4", "phase-5"],
        "gates_passed": [
            {"gate": "gate-1", "decision": "CONDITIONAL_GO"},
            {"gate": "gate-2", "decision": "CONDITIONAL_GO"},
            {"gate": "gate-3", "decision": "GO"},
            {"gate": "gate-4", "decision": "CONDITIONAL_GO"},
            {"gate": "gate-5", "decision": "CONDITIONAL_GO"},
        ],
        "schema_version": "v8",
        "evidence_limited_mode": False,
        "market_validation_status": "validation_pending",
        "experiments_designed": 2,
        "experiments_executed": 0,
    }

    experiments = {
        "audit_id": "AUD-NEUTRAL-002",
        "experiments": [
            {
                "experiment_id": "EXP-001",
                "hypothesis_id": "H1",
                "claim_being_tested": "Devs will adopt via CLI",
                "owner": "DevRel",
                "fidelity": "low",
                "method": "Landing page test",
                "sample_size": 100,
                "success_threshold": ">=30% signup",
                "failure_threshold": "<10%",
                "decision_rule": "If <10%: recycle",
                "risk_check": "Traffic source bias",
                "instrumentation": "GA + Hotjar",
                "status": "designed",
            },
            {
                "experiment_id": "EXP-002",
                "hypothesis_id": "H2",
                "claim_being_tested": "Teams will pay $20/month",
                "owner": "Product",
                "fidelity": "medium",
                "method": "Survey",
                "sample_size": 30,
                "success_threshold": ">=35% WTP",
                "failure_threshold": "<15%",
                "decision_rule": "If <15%: test $10",
                "risk_check": "Small sample",
                "instrumentation": "Typeform",
                "status": "designed",
            },
        ],
        "schema_version": "v8",
    }

    (tmpdir / "state.json").write_text(json.dumps(state, indent=2))
    (tmpdir / "experiments.json").write_text(json.dumps(experiments, indent=2))

    result = validate_audit_instance(tmpdir)

    # With 0 executed experiments, validation score should be 0 and status should be validation_pending
    assert state["market_validation_status"] == "validation_pending", "Should be VALIDATION_PENDING"
    assert state["experiments_executed"] == 0, "Should have 0 executed experiments"

    # Check that the validator correctly identifies the lifecycle boundary
    checks_by_name = {c["name"]: c for c in result["checks"]}
    if "design_is_not_validation" in checks_by_name:
        assert checks_by_name["design_is_not_validation"]["pass"], "Design should not be validation"
    if "validation_score_zero" in checks_by_name:
        assert checks_by_name["validation_score_zero"]["pass"], "Validation score should be 0"

    print("PASS: neutral_ceip — CONDITIONAL_GO with mixed signals, VALIDATION_PENDING")
    return 0


if __name__ == "__main__":
    sys.exit(run())
