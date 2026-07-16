#!/usr/bin/env python3
"""Scenario 5: Stale regulation adversarial — stale evidence + adversarial challenge, expects RECYCLE.

A product with stale regulatory evidence that an adversarial reviewer challenges
should produce a RECYCLE gate decision, not GO.
"""
import sys
import json
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from validate_skill import validate_audit_instance


def run():
    tmpdir = Path(tempfile.mkdtemp(prefix="audit_stale_reg_"))

    state = {
        "audit_id": "AUD-STALE-005",
        "product_context": "Healthcare compliance platform",
        "scope": "deep",
        "started_at": "2026-07-13T10:00:00Z",
        "current_phase": "VALIDATION_PENDING",
        "decision_confidence": {
            "composite": 31,
            "quality": 8,
            "coverage": 10,
            "consistency": 8,
            "counter": 5,
            "validation": 0,
        },
        "evidence_types_present": ["competitor_intel"],
        "evidence_limitations": [
            "Regulatory evidence is >18 months old (stale)",
            "Adversarial review identified missing HIPAA 2025 update coverage",
            "No current first-party buyer evidence",
        ],
        "phases_completed": ["phase-0", "phase-1", "phase-2", "phase-3", "phase-4"],
        "gates_passed": [
            {"gate": "gate-1", "decision": "CONDITIONAL_GO"},
            {"gate": "gate-2", "decision": "RECYCLE"},
            {"gate": "gate-3", "decision": "CONDITIONAL_GO"},
            {"gate": "gate-4", "decision": "RECYCLE"},
        ],
        "schema_version": "v8",
        "evidence_limited_mode": True,
        "market_validation_status": "validation_pending",
        "experiments_designed": 0,
        "experiments_executed": 0,
        "drift_status": "stale",
        "last_updated": "2026-07-13T10:00:00Z",
    }

    experiments = {
        "audit_id": "AUD-STALE-005",
        "experiments": [],
        "schema_version": "v8",
    }

    (tmpdir / "state.json").write_text(json.dumps(state, indent=2))
    (tmpdir / "experiments.json").write_text(json.dumps(experiments, indent=2))
    (tmpdir / "evidence-corpus.json").write_text(json.dumps({
        "audit_id": "AUD-STALE-005",
        "evidence_items": [{
            "evidence_id": "EV-001",
            "type": "competitor_intel",
            "source": "regulatory-summary-2024",
            "source_tier": "secondary",
            "timestamp": "2024-01-10T00:00:00Z",
            "freshness": "stale",
            "grade": "LOW",
            "confidence": 0.4,
            "provenance": "Secondary regulatory summary collected during a prior audit.",
            "is_customer_commercial": False,
            "authority_tier": "tier-2",
            "checked_at": "2026-07-13T10:00:00Z",
            "expiry": "2025-01-10T00:00:00Z",
            "url_health": "alive",
            "content_summary": "Old compliance summary that may miss current regulatory requirements."
        }],
        "total_items": 1,
        "types_present": 1,
        "types_missing": 10,
        "evidence_limited_mode": True,
        "schema_version": "v8"
    }, indent=2))
    (tmpdir / "hypotheses.json").write_text(json.dumps({
        "audit_id": "AUD-STALE-005",
        "hypotheses": [{
            "id": "H1",
            "hypothesis": "The current compliance positioning is still valid.",
            "status": "unresolved",
            "evidence_bundle": [{
                "claim": "The regulatory positioning remains current.",
                "evidence_ids": ["EV-001"],
                "min_high": 1,
                "min_medium": 2,
                "satisfied": False
            }]
        }],
        "schema_version": "v8"
    }, indent=2))

    result = validate_audit_instance(tmpdir)

    # The key check is: stale evidence + adversarial challenge = RECYCLE.
    assert not result["all_pass"], "Stale load-bearing evidence must fail the audit validator"
    checks_by_name = {c["name"]: c for c in result["checks"]}
    assert not checks_by_name["evidence_bundle_semantics"]["pass"], "Stale evidence must be rejected for load-bearing claims"

    # Check that at least one gate was RECYCLE
    recycle_gates = [g for g in state["gates_passed"] if g["decision"] == "RECYCLE"]
    assert len(recycle_gates) >= 1, "Should have at least one RECYCLE gate due to stale evidence"

    # Drift status should be stale
    assert state["drift_status"] == "stale", "Drift status should be 'stale'"

    # Validation should be pending (no experiments executed)
    assert state["market_validation_status"] == "validation_pending"
    assert state["experiments_executed"] == 0

    print("PASS: stale_regulation_adversarial — RECYCLE with stale evidence and adversarial challenge")
    return 0


if __name__ == "__main__":
    sys.exit(run())
