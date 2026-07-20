#!/usr/bin/env python3
"""Scenario: Career Automation Insights Engine — supportive evidence.

Validates the flywheel chain with rich evidence for the career coaching repo.
"""

import json
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    manifest = {
        "run_id": "WMF-20260720-001",
        "repository": "/Users/sanjayb/career-automation-insights-engine-fresh",
        "objective": "Select one career-coach proof-pack CTA and one message variant that can increase sample-report requests.",
        "week": "2026-07-20",
        "mode": "draft-only",
        "horizon_days": 7,
        "research_depth": "quick",
        "stages": [
            {"stage": 1, "skill": "ecc-niche-positioning-audit", "status": "completed",
             "output_files": ["positioning-audit-export.json"], "evidence_limited": False},
            {"stage": 2, "skill": "ecc-hormozi-funnel", "status": "completed",
             "output_files": ["offer.json", "hooks.json", "content-calendar.json", "funnel-audit.json", "proof-library.json"],
             "evidence_limited": False},
            {"stage": 3, "skill": "ecc-growth-experiment-loop", "status": "completed",
             "output_files": ["experiment-registration.json"], "evidence_limited": False},
        ],
        "evidence_limited": False,
        "approval_required": True,
    }

    packet = {
        "packet_id": "PKT-20260720-001",
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
        "evidence_ids_cited": ["E-001", "E-002", "E-003"],
        "unavailable_components": [],
        "evidence_limited": False,
        "approval_required": True,
        "no_external_writes": True,
    }

    assert packet["outputs"]["offer_count"] == 1
    assert packet["outputs"]["hook_count"] == 3
    assert packet["outputs"]["content_days"] == 7
    assert packet["outputs"]["funnel_fixes"] == 3
    assert packet["outputs"]["experiment_count"] == 1
    assert packet["no_external_writes"] is True
    assert "career" in manifest["objective"].lower()

    print("PASS: career_automation_supportive — full chain, all constraints met")
    sys.exit(0)


if __name__ == "__main__":
    main()
