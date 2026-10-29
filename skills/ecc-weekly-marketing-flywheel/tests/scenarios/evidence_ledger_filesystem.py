#!/usr/bin/env python3
"""Scenario: Runner produces evidence-ledger.json with claim-to-evidence mapping.

Verifies that the runner output includes an evidence-ledger.json file that
maps each artifact's claims to their evidence IDs, and that the ledger
structure is correct.
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
             "--objective", "evidence ledger test",
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

        ledger_path = os.path.join(output_dir, "evidence-ledger.json")
        if not os.path.exists(ledger_path):
            print("FAIL: evidence-ledger.json not produced")
            sys.exit(1)

        with open(ledger_path) as f:
            ledger = json.load(f)

        assert "claims" in ledger, "Ledger missing 'claims' field"
        assert "evidence_ids_used" in ledger, "Ledger missing 'evidence_ids_used'"
        assert "evidence_ids_available" in ledger, "Ledger missing 'evidence_ids_available'"
        assert len(ledger["claims"]) > 0, "Ledger has no claims"
        assert len(ledger["evidence_ids_used"]) > 0, "Ledger has no evidence IDs used"

        for claim in ledger["claims"]:
            assert "claim_id" in claim, f"Claim missing claim_id: {claim}"
            assert "artifact" in claim, f"Claim missing artifact: {claim}"
            assert "evidence_id" in claim, f"Claim missing evidence_id: {claim}"
            assert "status" in claim, f"Claim missing status: {claim}"

        print(f"PASS: Evidence ledger has {len(ledger['claims'])} claims, {len(ledger['evidence_ids_used'])} evidence IDs")
        sys.exit(0)


if __name__ == "__main__":
    main()
