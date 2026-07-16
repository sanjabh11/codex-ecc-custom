#!/usr/bin/env python3
"""Scenario 1: Evidence-rich supportive — expects GO gate decision.

A product with customer quotes, analytics data, and sales data should
produce a full GO decision at Gate 1, not CONDITIONAL_GO.
"""
import sys
import json
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from validate_skill import validate_audit_instance


def run():
    tmpdir = Path(tempfile.mkdtemp(prefix="audit_supportive_"))

    state = {
        "audit_id": "AUD-SUPPORTIVE-001",
        "product_context": "B2B SaaS analytics platform",
        "scope": "standard",
        "started_at": "2026-07-13T10:00:00Z",
        "current_phase": "VALIDATION_PENDING",
        "decision_confidence": {
            "composite": 72,
            "quality": 22,
            "coverage": 18,
            "consistency": 16,
            "counter": 10,
            "validation": 6,
        },
        "evidence_types_present": ["user_quote", "analytics_data", "sales_data", "product_promise"],
        "evidence_limitations": [],
        "phases_completed": ["phase-0", "phase-1", "phase-2", "phase-3", "phase-4", "phase-5"],
        "gates_passed": [
            {"gate": "gate-1", "decision": "GO"},
            {"gate": "gate-2", "decision": "GO"},
            {"gate": "gate-3", "decision": "GO"},
            {"gate": "gate-4", "decision": "GO"},
            {"gate": "gate-5", "decision": "GO"},
        ],
        "schema_version": "v8",
        "evidence_limited_mode": False,
        "market_validation_status": "in_progress",
        "experiments_designed": 3,
        "experiments_executed": 1,
    }

    experiments = {
        "audit_id": "AUD-SUPPORTIVE-001",
        "experiments": [
            {
                "experiment_id": "EXP-001",
                "hypothesis_id": "H1",
                "claim_being_tested": "Enterprise teams will pay $100/month",
                "owner": "Product Team",
                "fidelity": "medium",
                "method": "50-user survey",
                "sample_size": 50,
                "success_threshold": ">=40% WTP",
                "failure_threshold": "<20% WTP",
                "decision_rule": "If >=40%: proceed",
                "risk_check": "Survey bias",
                "instrumentation": "Typeform",
                "status": "completed",
                "result": "52% WTP",
                "hypothesis_transition": "supported",
                "evidence_produced": "pricing_signal",
            },
            {
                "experiment_id": "EXP-002",
                "hypothesis_id": "H2",
                "claim_being_tested": "Data teams are primary segment",
                "owner": "Research",
                "fidelity": "low",
                "method": "Landing page test",
                "sample_size": 200,
                "success_threshold": ">=60% data team signups",
                "failure_threshold": "<30%",
                "decision_rule": "If <30%: discard",
                "risk_check": "Traffic bias",
                "instrumentation": "GA",
                "status": "designed",
            },
            {
                "experiment_id": "EXP-003",
                "hypothesis_id": "H3",
                "claim_being_tested": "Reduces onboarding by 50%",
                "owner": "CS",
                "fidelity": "high",
                "method": "Pilot",
                "sample_size": 5,
                "success_threshold": "<4hr onboarding",
                "failure_threshold": ">6hr",
                "decision_rule": "If <4hr: validated",
                "risk_check": "Small sample",
                "instrumentation": "Product analytics",
                "status": "designed",
            },
        ],
        "schema_version": "v8",
    }

    (tmpdir / "state.json").write_text(json.dumps(state, indent=2))
    (tmpdir / "experiments.json").write_text(json.dumps(experiments, indent=2))

    result = validate_audit_instance(tmpdir)

    assert result["all_pass"], f"Expected all checks to pass, got: {result['checks']}"
    assert not state["evidence_limited_mode"], "Should NOT be in evidence-limited mode"

    customer_types = {"user_quote", "behavioral_observation", "support_ticket", "analytics_data", "sales_data"}
    has_customer = bool(set(state["evidence_types_present"]) & customer_types)
    assert has_customer, "Should have customer/commercial evidence"

    print("PASS: supportive_evidence_rich — GO gate decision with customer evidence")
    return 0


if __name__ == "__main__":
    sys.exit(run())
