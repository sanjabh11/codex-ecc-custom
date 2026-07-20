#!/usr/bin/env python3
"""Scenario: Fabricated claim rejection.

Validates that the weekly generator rejects synthetic economic claims:
  - Hardcoded price without evidence
  - is_real: true without evidence citation
  - Forbidden guarantee terms
"""

import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))


def main():
    from generate_weekly_artifacts import reject_synthetic_claims

    rejections = 0

    # Test 1: Reject hardcoded price without evidence
    bad_offer_1 = {"price": 2500, "evidence_citations": []}
    try:
        reject_synthetic_claims(bad_offer_1, "offer")
        print("FAIL: Should have rejected hardcoded price without evidence")
        sys.exit(1)
    except SystemExit:
        rejections += 1

    # Test 2: Reject is_real=true without evidence
    bad_offer_2 = {"scarcity_urgency": {"is_real": True}, "evidence_citations": []}
    try:
        reject_synthetic_claims(bad_offer_2, "offer")
        print("FAIL: Should have rejected is_real=true without evidence")
        sys.exit(1)
    except SystemExit:
        rejections += 1

    # Test 3: Reject forbidden guarantee terms
    bad_offer_3 = {
        "guarantee": {"terms": "Complete the program or get a full refund"},
        "evidence_citations": ["E-001"],
    }
    try:
        reject_synthetic_claims(bad_offer_3, "offer")
        print("FAIL: Should have rejected forbidden guarantee term")
        sys.exit(1)
    except SystemExit:
        rejections += 1

    assert rejections == 3, f"Expected 3 rejections, got {rejections}"

    # Test 4: Accept evidence-backed price
    good_offer = {
        "price": 2500,
        "evidence_citations": ["E-001"],
        "scarcity_urgency": {"is_real": False},
        "guarantee": {"terms": "See pilot agreement"},
    }
    reject_synthetic_claims(good_offer, "offer")  # Should not raise

    print(f"PASS: fabricated_claim_rejection — {rejections} synthetic claims rejected, 1 evidence-backed accepted")
    sys.exit(0)


if __name__ == "__main__":
    main()
