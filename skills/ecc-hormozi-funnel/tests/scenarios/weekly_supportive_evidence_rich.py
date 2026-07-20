#!/usr/bin/env python3
"""Scenario: Weekly mode with supportive evidence — full pipeline.

Validates that the weekly generator produces exactly:
  1 offer, 3 hooks, 7-day calendar, 3 funnel fixes, 1 proof update
when evidence is rich and advisor is available.
"""

import json
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))


def main():
    from generate_weekly_artifacts import (
        load_positioning_export, extract_evidence_ids,
        generate_weekly_offer, generate_weekly_hook,
        generate_content_calendar, generate_funnel_audit,
        generate_proof_library_update,
    )

    export_path = os.path.join(SKILL_DIR, "tests", "positioning-export-test.json")
    positioning = load_positioning_export(export_path)
    valid_ids = extract_evidence_ids(positioning)

    assert len(valid_ids) >= 5, f"Expected >=5 evidence IDs, got {len(valid_ids)}"

    segment = positioning["segments"][0]
    pain = positioning["pains"][0]
    seg_evidence = segment["evidence_ids"]

    # 1 offer
    offer = generate_weekly_offer(segment, pain, seg_evidence, valid_ids)
    assert offer["weekly_mode"] is True
    assert offer["value_equation_scores"]["composite"] <= 100

    # 3 hooks
    hooks = []
    for i in range(3):
        h = segment["hooks"][i]
        hook = generate_weekly_hook(
            h["formula_type"], pain, segment,
            h["text"], h["clarity"], h["curiosity"], h["pull"],
            h["evidence_id"], valid_ids, rank=i + 1,
        )
        hooks.append(hook)
    assert len(hooks) == 3

    # 7-day calendar
    calendar = generate_content_calendar(segment, hooks, "2026-07-20", seg_evidence, valid_ids)
    assert calendar["horizon_days"] == 7
    assert len(calendar["days"]) == 7

    # 3 funnel fixes
    funnel = generate_funnel_audit(segment, seg_evidence, valid_ids)
    assert len(funnel["fixes"]) == 3

    # 1 proof update
    proof = generate_proof_library_update(seg_evidence, valid_ids)
    assert len(proof["evidence_cited"]) >= 1

    print("PASS: supportive_evidence_rich — 1 offer, 3 hooks, 7 days, 3 fixes, 1 proof update")
    sys.exit(0)


if __name__ == "__main__":
    main()
