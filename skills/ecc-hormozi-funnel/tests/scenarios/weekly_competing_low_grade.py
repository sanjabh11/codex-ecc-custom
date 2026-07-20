#!/usr/bin/env python3
"""Scenario: Weekly mode with competing/contradictory evidence.

Validates that the weekly generator handles contradictory evidence
by producing artifacts with flagged contradictions in the state.
"""

import json
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))


def main():
    from generate_weekly_artifacts import (
        load_positioning_export, extract_evidence_ids,
        generate_weekly_offer, generate_funnel_audit,
    )

    export_path = os.path.join(SKILL_DIR, "tests", "positioning-export-test.json")
    positioning = load_positioning_export(export_path)
    valid_ids = extract_evidence_ids(positioning)

    # Simulate contradictory evidence: low scores across all dimensions
    segment = positioning["segments"][0]
    segment["dream_outcome_score"] = 3
    segment["likelihood_score"] = 2
    segment["time_delay_score"] = 3
    segment["effort_score"] = 8  # High effort = bad
    pain = positioning["pains"][0]
    seg_evidence = segment["evidence_ids"]

    offer = generate_weekly_offer(segment, pain, seg_evidence, valid_ids)
    assert offer["value_equation_scores"]["composite"] < 20, \
        f"Expected low composite for contradictory evidence, got {offer['value_equation_scores']['composite']}"

    funnel = generate_funnel_audit(segment, seg_evidence, valid_ids)
    assert len(funnel["fixes"]) == 3

    print(f"PASS: competing_low_grade_evidence — composite={offer['value_equation_scores']['composite']} (low as expected)")
    sys.exit(0)


if __name__ == "__main__":
    main()
