#!/usr/bin/env python3
"""Scenario: Runner produces hashes.json with SHA-256 for all output files.

Verifies that the runner output includes a hashes.json file containing
file-level SHA-256 hashes and a tree hash, and that the hashes match
the actual files on disk.
"""

import hashlib
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


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [sys.executable, RUNNER,
             "--repository", "/tmp/test-repo",
             "--objective", "hash verification test",
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

        hashes_path = os.path.join(output_dir, "hashes.json")
        if not os.path.exists(hashes_path):
            print("FAIL: hashes.json not produced")
            sys.exit(1)

        with open(hashes_path) as f:
            hashes = json.load(f)

        assert "files" in hashes, "hashes.json missing 'files'"
        assert "tree" in hashes, "hashes.json missing 'tree'"
        assert len(hashes["files"]) > 0, "hashes.json has no file hashes"

        # Verify each hash matches actual file
        for filename, expected_hash in hashes["files"].items():
            filepath = os.path.join(output_dir, filename)
            if not os.path.exists(filepath):
                print(f"FAIL: {filename} listed in hashes but not on disk")
                sys.exit(1)
            actual_hash = sha256_file(filepath)
            if actual_hash != expected_hash:
                print(f"FAIL: {filename} hash mismatch: expected {expected_hash[:12]}, got {actual_hash[:12]}")
                sys.exit(1)

        print(f"PASS: hashes.json has {len(hashes['files'])} verified file hashes + tree hash")
        sys.exit(0)


if __name__ == "__main__":
    main()
