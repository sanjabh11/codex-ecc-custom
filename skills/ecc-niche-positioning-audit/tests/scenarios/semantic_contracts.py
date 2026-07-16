#!/usr/bin/env python3
"""Scenario 9: persisted semantic contracts reject false evidence and arithmetic."""

import json
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from validate_skill import validate_audit_instance  # noqa: E402


def _state() -> dict:
    return {
        "audit_id": "AUD-SEMANTIC-009",
        "product_context": "Evidence-backed positioning tool",
        "scope": "standard",
        "started_at": "2026-07-16T10:00:00Z",
        "current_phase": "VALIDATION_PENDING",
        "decision_confidence": {"composite": 40, "quality": 12, "coverage": 10, "consistency": 10, "counter": 8, "validation": 0},
        "evidence_types_present": ["product_promise"],
        "evidence_limitations": ["No first-party buyer evidence"],
        "phases_completed": ["phase-0", "phase-1", "phase-2", "phase-3", "phase-4", "phase-5"],
        "gates_passed": [{"gate": "gate-1", "decision": "CONDITIONAL_GO"}],
        "schema_version": "v8",
        "evidence_limited_mode": True,
        "market_validation_status": "validation_pending",
        "experiments_designed": 0,
        "experiments_executed": 0,
        "last_updated": "2026-07-16T10:00:00Z",
    }


def _experiments() -> dict:
    return {"audit_id": "AUD-SEMANTIC-009", "experiments": [], "schema_version": "v8"}


def _corpus() -> dict:
    return {
        "audit_id": "AUD-SEMANTIC-009",
        "evidence_items": [{
            "evidence_id": "EV-001",
            "type": "product_promise",
            "source": "product-brief",
            "source_tier": "secondary",
            "timestamp": "2026-07-16T09:00:00Z",
            "freshness": "fresh",
            "grade": "HIGH",
            "confidence": 0.9,
            "provenance": "Current product brief reviewed during audit framing.",
            "is_customer_commercial": False,
            "authority_tier": "tier-2",
            "checked_at": "2026-07-16T09:30:00Z",
            "expiry": "2027-01-16T00:00:00Z",
            "url_health": "not_applicable",
            "content_summary": "The product promises evidence-backed positioning decisions."
        }],
        "total_items": 1,
        "types_present": 1,
        "types_missing": 10,
        "evidence_limited_mode": True,
        "schema_version": "v8",
    }


def _hypotheses() -> dict:
    return {
        "audit_id": "AUD-SEMANTIC-009",
        "hypotheses": [{
            "id": "H1",
            "hypothesis": "The product brief is sufficient proof for buyer adoption.",
            "status": "unresolved",
            "evidence_bundle": [{
                "claim": "Buyer adoption will follow from the product promise.",
                "evidence_ids": ["EV-001"],
                "min_high": 0,
                "min_medium": 2,
                "satisfied": True,
            }],
        }],
        "schema_version": "v8",
    }


def run() -> int:
    tmpdir = Path(tempfile.mkdtemp(prefix="audit_semantic_contracts_"))
    (tmpdir / "state.json").write_text(json.dumps(_state(), indent=2))
    (tmpdir / "experiments.json").write_text(json.dumps(_experiments(), indent=2))
    (tmpdir / "evidence-corpus.json").write_text(json.dumps(_corpus(), indent=2))
    (tmpdir / "hypotheses.json").write_text(json.dumps(_hypotheses(), indent=2))

    result = validate_audit_instance(tmpdir)
    checks = {check["name"]: check for check in result["checks"]}
    assert not result["all_pass"], "zero-threshold evidence bundle must not pass"
    assert not checks["evidence_bundle_semantics"]["pass"], checks

    experiments = _experiments()
    experiments["audit_id"] = "AUD-WRONG-ID"
    (tmpdir / "experiments.json").write_text(json.dumps(experiments, indent=2))
    result = validate_audit_instance(tmpdir)
    checks = {check["name"]: check for check in result["checks"]}
    assert not checks["audit_id_consistency"]["pass"], checks
    (tmpdir / "experiments.json").write_text(json.dumps(_experiments(), indent=2))

    state = _state()
    state["decision_confidence"]["composite"] = 99
    (tmpdir / "state.json").write_text(json.dumps(state, indent=2))
    result = validate_audit_instance(tmpdir)
    checks = {check["name"]: check for check in result["checks"]}
    assert not checks["confidence_arithmetic"]["pass"], checks

    state["decision_confidence"]["composite"] = 40
    state["schema_version"] = "v7"
    (tmpdir / "state.json").write_text(json.dumps(state, indent=2))
    result = validate_audit_instance(tmpdir)
    checks = {check["name"]: check for check in result["checks"]}
    assert not checks["state_schema"]["pass"], checks

    print("PASS: semantic_contracts — evidence thresholds, arithmetic, and v8 versioning are enforced")
    return 0


if __name__ == "__main__":
    sys.exit(run())
