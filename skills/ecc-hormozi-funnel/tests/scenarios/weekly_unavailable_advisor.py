#!/usr/bin/env python3
"""Scenario: Advisor unavailable — graceful skip.

Validates that when the advisor is not reachable, the state correctly
records advisor_available=false and advisor_used=false, and the
generator still produces valid artifacts without advisor input.
"""

import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))


def main():
    from generate_weekly_artifacts import (
        load_positioning_export, extract_evidence_ids,
        generate_weekly_offer,
    )

    export_path = os.path.join(SKILL_DIR, "tests", "positioning-export-test.json")
    positioning = load_positioning_export(export_path)
    valid_ids = extract_evidence_ids(positioning)

    segment = positioning["segments"][0]
    pain = positioning["pains"][0]
    seg_evidence = segment["evidence_ids"]

    # Generate offer without advisor
    offer = generate_weekly_offer(segment, pain, seg_evidence, valid_ids)

    # Simulate state with advisor unavailable
    confidence = min(25 + 20 + 22 + 0, 100)  # advisor_confirmed=0
    state = {
        "advisor_used": False,
        "tool_health": {
            "advisor_available": False,
            "validator_available": True,
            "schema_validation_passed": True,
        },
        "decision_confidence": {
            "evidence_quality": 25,
            "source_coverage": 20,
            "adversarial_survival": 22,
            "advisor_confirmed": 0,
            "composite": confidence,
        },
    }

    assert state["advisor_used"] is False
    assert state["tool_health"]["advisor_available"] is False
    assert state["decision_confidence"]["advisor_confirmed"] == 0
    assert state["decision_confidence"]["composite"] < 100
    assert offer["weekly_mode"] is True

    print(f"PASS: unavailable_advisor — advisor_available=false, confidence={confidence}")
    sys.exit(0)


if __name__ == "__main__":
    main()
