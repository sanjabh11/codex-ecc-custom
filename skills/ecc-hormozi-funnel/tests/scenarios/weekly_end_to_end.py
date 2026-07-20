#!/usr/bin/env python3
"""Scenario: End-to-end positioning to funnel pipeline.

Validates the full chain: positioning export → weekly artifacts → output validation.
Runs the weekly generator as a subprocess and checks all output files.
"""

import json
import os
import subprocess
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    export_path = os.path.join(SKILL_DIR, "tests", "positioning-export-test.json")
    output_dir = os.path.join(SKILL_DIR, "tests", "generated", "e2e")
    generator = os.path.join(SKILL_DIR, "scripts", "generate_weekly_artifacts.py")

    result = subprocess.run(
        [sys.executable, generator, export_path, output_dir, "2026-07-20"],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        print(f"FAIL: Generator exited with code {result.returncode}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)

    # Verify all 5 output files exist
    expected_files = ["offer.json", "hooks.json", "content-calendar.json", "funnel-audit.json", "proof-library.json"]
    for fname in expected_files:
        fpath = os.path.join(output_dir, fname)
        assert os.path.exists(fpath), f"Missing output: {fpath}"
        with open(fpath) as f:
            data = json.load(f)
        # hooks.json is a list, others are dicts
        if isinstance(data, list):
            for item in data:
                assert item.get("schema_version") == "v8", f"{fname} item has wrong schema_version"
        else:
            assert data.get("schema_version") == "v8", f"{fname} has wrong schema_version"

    # Verify constraints
    with open(os.path.join(output_dir, "offer.json")) as f:
        offer = json.load(f)
    assert offer["weekly_mode"] is True

    with open(os.path.join(output_dir, "hooks.json")) as f:
        hooks = json.load(f)
    assert len(hooks) == 3, f"Expected 3 hooks, got {len(hooks)}"

    with open(os.path.join(output_dir, "content-calendar.json")) as f:
        cal = json.load(f)
    assert cal["horizon_days"] == 7, f"Expected 7 days, got {cal['horizon_days']}"
    assert len(cal["days"]) == 7

    with open(os.path.join(output_dir, "funnel-audit.json")) as f:
        funnel = json.load(f)
    assert len(funnel["fixes"]) == 3, f"Expected 3 fixes, got {len(funnel['fixes'])}"

    with open(os.path.join(output_dir, "proof-library.json")) as f:
        proof = json.load(f)
    assert len(proof["evidence_cited"]) >= 1

    print("PASS: end_to_end_positioning_to_funnel — 5 files, all constraints verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
