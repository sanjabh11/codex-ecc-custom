#!/usr/bin/env python3
"""Scenario: Runner produces approval-required.md with human approval boundary.

Verifies that the runner output includes an approval-required.md file
that explicitly lists the human approval boundary before external writes.
"""

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
             "--objective", "approval boundary test",
             "--week", "2026-07-20",
             "--mode", "dry-run",
             "--positioning-export", TEST_EXPORT],
            capture_output=True, text=True, cwd=SKILL_DIR,
        )

        if result.returncode != 0:
            print(f"FAIL: Runner exited with {result.returncode}: {result.stderr}")
            sys.exit(1)

        output_dir = None
        for line in result.stdout.split("\n"):
            if "Output directory:" in line:
                output_dir = line.split("Output directory:")[1].strip()
                break

        if not output_dir:
            print("FAIL: Could not find output directory")
            sys.exit(1)

        approval_path = os.path.join(output_dir, "approval-required.md")
        if not os.path.exists(approval_path):
            print("FAIL: approval-required.md not produced")
            sys.exit(1)

        with open(approval_path) as f:
            content = f.read()

        assert "Approval Required" in content, "approval-required.md missing title"
        assert "human" in content.lower() or "Human" in content, "approval-required.md missing human approval mention"
        assert "external" in content.lower() or "writes" in content.lower(), "approval-required.md missing external writes mention"

        print("PASS: approval-required.md contains human approval boundary")
        sys.exit(0)


if __name__ == "__main__":
    main()
