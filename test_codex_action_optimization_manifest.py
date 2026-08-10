#!/usr/bin/env python3
"""Regression tests for the typed Codex action optimization manifest."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_codex_action_optimization_manifest import generate
from scripts.validate_codex_action_optimization_manifest import validate_manifest


ROOT = Path(__file__).resolve().parent


class CodexActionOptimizationManifestTests(unittest.TestCase):
    def test_generated_manifest_binds_all_observed_top_level_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "actions.json"
            generate(ROOT / "docs/audits/skill-usage-audit-frozen-summary.json", output)
            result = validate_manifest(
                output,
                schema_path=ROOT / "schemas/codex-action-optimization-manifest.schema.json",
                check_sources=True,
            )
            self.assertEqual(result["status"], "valid", result)
            self.assertEqual(result["actions"], 12)

    def test_source_count_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "actions.json"
            generate(ROOT / "docs/audits/skill-usage-audit-frozen-summary.json", output)
            payload = json.loads(output.read_text(encoding="utf-8"))
            payload["actions"][0]["observed_count"] += 1
            output.write_text(json.dumps(payload), encoding="utf-8")
            result = validate_manifest(
                output,
                schema_path=ROOT / "schemas/codex-action-optimization-manifest.schema.json",
                check_sources=True,
            )
            self.assertEqual(result["status"], "invalid")
            self.assertTrue(any("observed_count" in error for error in result["errors"]))

    def test_missing_result_contract_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "actions.json"
            generate(ROOT / "docs/audits/skill-usage-audit-frozen-summary.json", output)
            payload = json.loads(output.read_text(encoding="utf-8"))
            del payload["actions"][0]["result_contract"]["required_fields"]
            output.write_text(json.dumps(payload), encoding="utf-8")
            result = validate_manifest(
                output,
                schema_path=ROOT / "schemas/codex-action-optimization-manifest.schema.json",
                check_sources=False,
            )
            self.assertEqual(result["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
