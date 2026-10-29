#!/usr/bin/env python3
"""Scenario: Runner stops with unavailable.json when no experiment registration provided.

Verifies that when Stage 3 (experiment registration) is unavailable,
the runner produces unavailable.json listing the missing component
and still completes with the artifacts from Stage 2.
"""

import json
import os
import subprocess
import sys
import tempfile

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RUNNER = os.path.join(SKILL_DIR, "ecc-weekly-marketing-flywheel", "scripts", "run_weekly_marketing_flywheel.py")
TEST_EXPORT = os.path.join(
    SKILL_DIR, "ecc-hormozi-funnel", "tests", "positioning-export-test.json"
)


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [sys.executable, RUNNER,
             "--repository", "/tmp/test-repo",
             "--objective", "unavailable stage3 test",
             "--week", "2026-07-20",
             "--mode", "dry-run",
             "--positioning-export", TEST_EXPORT],
            capture_output=True, text=True, cwd=SKILL_DIR,
        )

        if result.returncode != 0:
            print(f"FAIL: Runner exited with {result.returncode}: {result.stderr}")
            sys.exit(1)

        assert "COMPLETE_WITH_UNAVAILABLE" in result.stdout, "Runner should report unavailable items"

        output_dir = None
        for line in result.stdout.split("\n"):
            if "Output directory:" in line:
                output_dir = line.split("Output directory:")[1].strip()
                break

        if not output_dir:
            print("FAIL: Could not find output directory")
            sys.exit(1)

        unavailable_path = os.path.join(output_dir, "unavailable.json")
        if not os.path.exists(unavailable_path):
            print("FAIL: unavailable.json not produced")
            sys.exit(1)

        with open(unavailable_path) as f:
            unavailable = json.load(f)

        assert "items" in unavailable, "unavailable.json missing 'items'"
        assert len(unavailable["items"]) > 0, "unavailable.json has no items"
        assert unavailable["items"][0]["stage"] == "stage3_experiment", "First unavailable item should be stage3"

        # Verify artifacts still produced despite unavailable stage 3
        for artifact in ["offer.json", "hooks.json", "content-calendar.json", "funnel-audit.json", "proof-library.json"]:
            if not os.path.exists(os.path.join(output_dir, artifact)):
                print(f"FAIL: {artifact} not produced despite Stage 2 success")
                sys.exit(1)

        print(f"PASS: unavailable.json lists {len(unavailable['items'])} missing item(s), artifacts still produced")
        sys.exit(0)


if __name__ == "__main__":
    main()
