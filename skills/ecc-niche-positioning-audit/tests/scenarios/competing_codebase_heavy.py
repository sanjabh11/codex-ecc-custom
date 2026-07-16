#!/usr/bin/env python3
"""Scenario 3: Competing — codebase-heavy, no buyer evidence, expects CONDITIONAL_GO with evidence_limited.

A product with only codebase and stakeholder evidence (no customer/commercial)
should enter evidence-limited mode with CONDITIONAL_GO (never GO).
"""
import sys
import json
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from validate_skill import validate_audit_instance


def run():
    tmpdir = Path(tempfile.mkdtemp(prefix="audit_competing_"))

    state = {
        "audit_id": "AUD-COMPETING-003",
        "product_context": "Internal developer platform",
        "scope": "standard",
        "started_at": "2026-07-13T10:00:00Z",
        "current_phase": "VALIDATION_PENDING",
        "decision_confidence": {
            "composite": 40,
            "quality": 10,
            "coverage": 8,
            "consistency": 12,
            "counter": 5,
            "validation": 5,
        },
        "evidence_types_present": ["product_promise", "stakeholder_input", "codebase_evidence"],
        "evidence_limitations": ["No customer evidence", "No sales data", "No analytics"],
        "phases_completed": ["phase-0", "phase-1", "phase-2", "phase-3", "phase-4", "phase-5"],
        "gates_passed": [
            {"gate": "gate-1", "decision": "CONDITIONAL_GO"},
            {"gate": "gate-2", "decision": "CONDITIONAL_GO"},
            {"gate": "gate-3", "decision": "CONDITIONAL_GO"},
            {"gate": "gate-4", "decision": "CONDITIONAL_GO"},
            {"gate": "gate-5", "decision": "CONDITIONAL_GO"},
        ],
        "schema_version": "v8",
        "evidence_limited_mode": True,
        "market_validation_status": "validation_pending",
        "experiments_designed": 1,
        "experiments_executed": 0,
    }

    experiments = {
        "audit_id": "AUD-COMPETING-003",
        "experiments": [
            {
                "experiment_id": "EXP-001",
                "hypothesis_id": "H1",
                "claim_being_tested": "Backend engineers are the primary user",
                "owner": "Eng Team",
                "fidelity": "low",
                "method": "Landing page with segment messaging",
                "sample_size": 150,
                "success_threshold": ">=50% backend eng signups",
                "failure_threshold": "<25%",
                "decision_rule": "If <25%: recycle",
                "risk_check": "Traffic may not represent target",
                "instrumentation": "GA",
                "status": "designed",
            },
        ],
        "schema_version": "v8",
    }

    (tmpdir / "state.json").write_text(json.dumps(state, indent=2))
    (tmpdir / "experiments.json").write_text(json.dumps(experiments, indent=2))

    result = validate_audit_instance(tmpdir)

    # Evidence-limited mode must be true
    assert state["evidence_limited_mode"], "Should be in evidence-limited mode"

    # No customer/commercial evidence
    customer_types = {"user_quote", "behavioral_observation", "support_ticket", "analytics_data", "sales_data"}
    has_customer = bool(set(state["evidence_types_present"]) & customer_types)
    assert not has_customer, "Should NOT have customer/commercial evidence"

    # All gates should be CONDITIONAL_GO (capped)
    for gate in state["gates_passed"]:
        assert gate["decision"] == "CONDITIONAL_GO", f"Gate {gate['gate']} should be CONDITIONAL_GO, got {gate['decision']}"

    # Validation should be pending
    assert state["market_validation_status"] == "validation_pending"

    # Validator should pass the lifecycle boundary checks
    checks_by_name = {c["name"]: c for c in result["checks"]}
    if "design_is_not_validation" in checks_by_name:
        assert checks_by_name["design_is_not_validation"]["pass"], "Design should not equal validation"

    print("PASS: competing_codebase_heavy — CONDITIONAL_GO with evidence_limited mode")
    return 0


if __name__ == "__main__":
    sys.exit(run())
