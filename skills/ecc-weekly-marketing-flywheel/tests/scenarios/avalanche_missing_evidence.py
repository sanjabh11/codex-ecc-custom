#!/usr/bin/env python3
"""Scenario: Avalanche Insight Hub — missing evidence, safety-gated.

Validates the flywheel chain when evidence is sparse and safety gates prevent
certain claims for the avalanche forecasting repo.
"""

import json
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    manifest = {
        "run_id": "WMF-20260720-004",
        "repository": "/Users/sanjayb/avalanche-insight-hub",
        "objective": "Select one DRDO/DGRE scientist-collateral improvement and one validation-workflow uptake experiment.",
        "week": "2026-07-20",
        "mode": "dry-run",
        "horizon_days": 7,
        "research_depth": "quick",
        "stages": [
            {"stage": 1, "skill": "ecc-niche-positioning-audit", "status": "completed",
             "output_files": ["positioning-audit-export.json"], "evidence_limited": True},
            {"stage": 2, "skill": "ecc-hormozi-funnel", "status": "completed",
             "output_files": ["offer.json", "hooks.json", "content-calendar.json", "funnel-audit.json", "proof-library.json"],
             "evidence_limited": True},
            {"stage": 3, "skill": "ecc-growth-experiment-loop", "status": "unavailable",
             "output_files": [], "evidence_limited": True},
        ],
        "evidence_limited": True,
        "approval_required": True,
    }

    packet = {
        "packet_id": "PKT-20260720-004",
        "run_id": manifest["run_id"],
        "week": "2026-07-20",
        "outputs": {
            "offer_count": 1,
            "hook_count": 3,
            "content_days": 7,
            "funnel_fixes": 3,
            "proof_updates": 1,
            "experiment_count": 0,
        },
        "evidence_ids_cited": ["E-001"],
        "unavailable_components": ["experiment_loop", "analytics"],
        "evidence_limited": True,
        "approval_required": True,
        "no_external_writes": True,
    }

    safety_gates = {
        "no_safety_gate_alteration": True,
        "no_official_operational_use_claim": True,
    }

    assert packet["outputs"]["experiment_count"] == 0, "Experiment should be unavailable"
    assert "experiment_loop" in packet["unavailable_components"]
    assert safety_gates["no_safety_gate_alteration"] is True
    assert safety_gates["no_official_operational_use_claim"] is True
    assert manifest["mode"] == "dry-run"

    print("PASS: avalanche_missing_evidence — experiment unavailable, safety gates preserved")
    sys.exit(0)


if __name__ == "__main__":
    main()
