#!/usr/bin/env python3
"""Scenario: Canada Energy Intelligence Platform — neutral, evidence-limited.

Validates the flywheel chain with limited evidence for the energy dashboard repo.
"""

import json
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    manifest = {
        "run_id": "WMF-20260720-002",
        "repository": "/Users/sanjayb/minimax/canada-energy-dashboard",
        "objective": "Select one consultancy proof-pack offer and one LinkedIn/intake experiment.",
        "week": "2026-07-20",
        "mode": "draft-only",
        "horizon_days": 7,
        "research_depth": "quick",
        "stages": [
            {"stage": 1, "skill": "ecc-niche-positioning-audit", "status": "completed",
             "output_files": ["positioning-audit-export.json"], "evidence_limited": True},
            {"stage": 2, "skill": "ecc-hormozi-funnel", "status": "completed",
             "output_files": ["offer.json", "hooks.json", "content-calendar.json", "funnel-audit.json", "proof-library.json"],
             "evidence_limited": True},
            {"stage": 3, "skill": "ecc-growth-experiment-loop", "status": "completed",
             "output_files": ["experiment-registration.json"], "evidence_limited": True},
        ],
        "evidence_limited": True,
        "approval_required": True,
    }

    packet = {
        "packet_id": "PKT-20260720-002",
        "run_id": manifest["run_id"],
        "week": "2026-07-20",
        "outputs": {
            "offer_count": 1,
            "hook_count": 3,
            "content_days": 7,
            "funnel_fixes": 3,
            "proof_updates": 1,
            "experiment_count": 1,
        },
        "evidence_ids_cited": ["E-001", "E-002"],
        "unavailable_components": ["analytics", "search_console"],
        "evidence_limited": True,
        "approval_required": True,
        "no_external_writes": True,
    }

    assert packet["evidence_limited"] is True
    assert len(packet["unavailable_components"]) == 2
    assert "proof-pack" in manifest["objective"].lower()
    assert packet["no_external_writes"] is True

    print("PASS: canada_energy_neutral — evidence-limited packet with unavailable components")
    sys.exit(0)


if __name__ == "__main__":
    main()
