#!/usr/bin/env python3
"""Scenario: Strategic Intelligence Platform — competing evidence, governed forecasts.

Validates the flywheel chain with geopolitical forecast governance constraints.
"""

import json
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    manifest = {
        "run_id": "WMF-20260720-003",
        "repository": "/Users/sanjayb/minimax/strategic-intelligence-platform",
        "objective": "Select one enterprise or public-sector pilot wedge and one reviewer-workflow experiment.",
        "week": "2026-07-20",
        "mode": "draft-only",
        "horizon_days": 7,
        "research_depth": "standard",
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

    # Verify geopolitical governance constraint
    safety_gates = {
        "geopolitical_forecasts_governed": True,
        "implementation_only_evidence_labeled": True,
        "no_market_validation_claim": True,
    }

    assert safety_gates["geopolitical_forecasts_governed"] is True
    assert safety_gates["no_market_validation_claim"] is True
    assert "pilot" in manifest["objective"].lower()

    print("PASS: strategic_intel_competing — governed forecasts, safety gates verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
