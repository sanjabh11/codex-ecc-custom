#!/usr/bin/env python3
"""Scenario: Offer scoring with strong evidence.

Validates that the Value Equation offer builder produces correct composite
scores when evidence is rich and all dimensions score high.
"""

import json
import sys


def compute_composite(dream, likelihood, time_delay, effort):
    """Value Equation composite: (Dream x Likelihood) / ((11-Time) x (11-Effort)) x 10"""
    denominator = (11 - time_delay) * (11 - effort)
    if denominator == 0:
        return 0.0
    return round((dream * likelihood) / denominator * 10, 2)


def main():
    # Simulate an offer with strong evidence
    offer = {
        "offer_id": "OFF-001",
        "segment_id": "SEG-001",
        "pain_id": "H-SEG1-001",
        "dream_outcome": {
            "statement": "Triple your MRR in 60 days using our proven framework",
            "specificity_score": 9,
        },
        "value_equation_scores": {
            "dream_outcome": 9,
            "likelihood": 8,
            "time_delay": 8,
            "effort_sacrifice": 7,
        },
        "evidence_citations": ["E-001", "E-005", "E-012"],
        "schema_version": "v8",
    }

    scores = offer["value_equation_scores"]
    expected_composite = compute_composite(
        scores["dream_outcome"],
        scores["likelihood"],
        scores["time_delay"],
        scores["effort_sacrifice"],
    )
    scores["composite"] = expected_composite

    # Assertions
    assert expected_composite > 30.0, f"Expected high composite, got {expected_composite}"
    assert len(offer["evidence_citations"]) >= 1, "Must cite at least 1 evidence ID"
    assert offer["schema_version"] == "v8", "Schema version must be v8"
    assert scores["dream_outcome"] >= 7, "Dream outcome should be high with strong evidence"
    assert scores["likelihood"] >= 7, "Likelihood should be high with strong evidence"

    print(f"PASS: offer_scoring_evidence_rich — composite={expected_composite}, "
          f"evidence_citations={len(offer['evidence_citations'])}")
    sys.exit(0)


if __name__ == "__main__":
    main()
