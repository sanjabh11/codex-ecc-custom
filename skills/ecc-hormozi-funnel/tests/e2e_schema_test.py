#!/usr/bin/env python3
"""Red contract test — validates weekly artifacts against weekly-v1 schemas.

Phase 3: Originally proved 4/5 artifacts failed v8 schema validation.
Phase 4: Now validates against weekly-v1 schemas — all 5 should PASS.

Run: python3 skills/ecc-hormozi-funnel/tests/e2e_schema_test.py
"""

import json
import os
import subprocess
import sys
import tempfile

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SKILL_DIR))
SCHEMA_DIR = os.path.join(SKILL_DIR, "schemas", "weekly-v1")
TEST_EXPORT = os.path.join(SKILL_DIR, "tests", "positioning-export-test.json")
GENERATOR = os.path.join(SKILL_DIR, "scripts", "generate_weekly_artifacts.py")

def main():
    try:
        import jsonschema
    except ImportError:
        print("SKIP: jsonschema not installed")
        sys.exit(0)

    # Run generator in temp dir
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [sys.executable, GENERATOR, TEST_EXPORT, tmpdir, "2026-07-20"],
            capture_output=True, text=True, cwd=PROJECT_ROOT,
        )
        if result.returncode != 0:
            print(f"FAIL: generator exited with {result.returncode}: {result.stderr}")
            sys.exit(1)

        # Map artifacts to weekly-v1 schemas
        artifact_schema_map = {
            "offer.json": "weekly-offer.schema.json",
            "content-calendar.json": "weekly-content-calendar.schema.json",
            "funnel-audit.json": "weekly-funnel-audit.schema.json",
            "proof-library.json": "weekly-proof-library.schema.json",
        }

        failures = []
        passes = []

        for artifact_file, schema_file in artifact_schema_map.items():
            artifact_path = os.path.join(tmpdir, artifact_file)
            schema_path = os.path.join(SCHEMA_DIR, schema_file)

            if not os.path.exists(artifact_path):
                failures.append(f"{artifact_file}: file not generated")
                continue
            if not os.path.exists(schema_path):
                failures.append(f"{schema_file}: schema not found")
                continue

            with open(artifact_path) as f:
                artifact = json.load(f)
            with open(schema_path) as f:
                schema = json.load(f)

            try:
                jsonschema.validate(instance=artifact, schema=schema)
                passes.append(f"{artifact_file}: PASS")
            except jsonschema.ValidationError as e:
                failures.append(f"{artifact_file}: FAIL — {e.message}")

        # hooks.json is an array; weekly-hooks.schema.json expects an array
        hooks_path = os.path.join(tmpdir, "hooks.json")
        hooks_schema_path = os.path.join(SCHEMA_DIR, "weekly-hooks.schema.json")
        if os.path.exists(hooks_path) and os.path.exists(hooks_schema_path):
            with open(hooks_path) as f:
                hooks = json.load(f)
            with open(hooks_schema_path) as f:
                hooks_schema = json.load(f)

            try:
                jsonschema.validate(instance=hooks, schema=hooks_schema)
                passes.append("hooks.json: PASS (array validates against weekly-hooks schema)")
            except jsonschema.ValidationError as e:
                failures.append(f"hooks.json: FAIL — {e.message}")

        print("=== Weekly-v1 Schema Validation Results ===")
        for p in passes:
            print(f"  [PASS] {p}")
        for f in failures:
            print(f"  [FAIL] {f}")

        if len(failures) == 0:
            print(f"\nGREEN: All {len(passes)} weekly artifacts validate against weekly-v1 schemas")
            sys.exit(0)
        else:
            print(f"\nRED: {len(failures)} artifact(s) still failing")
            sys.exit(1)


if __name__ == "__main__":
    main()
