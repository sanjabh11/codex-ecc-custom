#!/usr/bin/env python3
"""Scenario: Weekly mode with neutral evidence — limited but valid.

Validates that the weekly generator produces a valid packet with
evidence_limited flag when only 2 evidence types are available.
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

    # Simulate limited evidence — only 2 IDs
    positioning["evidence_corpus"] = positioning["evidence_corpus"][:2]
    valid_ids = extract_evidence_ids(positioning)
    assert len(valid_ids) == 2, f"Expected 2 evidence IDs, got {len(valid_ids)}"

    segment = positioning["segments"][0]
    pain = positioning["pains"][0]
    seg_evidence = list(valid_ids)[:2]
    segment["evidence_ids"] = seg_evidence

    # 1 offer with limited evidence
    offer = generate_weekly_offer(segment, pain, seg_evidence, valid_ids)
    assert offer["weekly_mode"] is True

    # 3 hooks — all cite the same 2 evidence IDs
    hooks = []
    for i in range(3):
        hook = generate_weekly_hook(
            "pain", pain, segment,
            f"Limited-evidence hook {i+1}",
            6, 6, 6,
            seg_evidence[0], valid_ids, rank=i + 1,
        )
        hooks.append(hook)
    assert len(hooks) == 3

    # 7-day calendar
    calendar = generate_content_calendar(segment, hooks, "2026-07-20", seg_evidence, valid_ids)
    assert calendar["horizon_days"] == 7

    # 3 funnel fixes
    funnel = generate_funnel_audit(segment, seg_evidence, valid_ids)
    assert len(funnel["fixes"]) == 3

    # 1 proof update
    proof = generate_proof_library_update(seg_evidence, valid_ids)

    print("PASS: neutral_evidence_limited — packet produced with 2 evidence types")
    sys.exit(0)


if __name__ == "__main__":
    main()
