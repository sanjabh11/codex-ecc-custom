#!/usr/bin/env python3
"""Regression tests for the shared skill optimization manifest gate."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_skill_optimization_manifest import validate_manifest
from scripts.record_skill_optimization_result import record


ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "schemas" / "skill-optimization-manifest.schema.json"
TEMPLATE = ROOT / "docs" / "audits" / "skill-optimization-manifest.template.json"
CURRENT_MANIFEST = ROOT / "docs" / "audits" / "skill-optimization-manifest.json"
SUMMARY = ROOT / "docs" / "audits" / "skill-usage-audit-frozen-summary.json"


class SkillOptimizationManifestTests(unittest.TestCase):
    def test_template_is_schema_valid_without_live_target_checks(self) -> None:
        result = validate_manifest(
            TEMPLATE,
            schema_path=SCHEMA,
            root=ROOT,
            summary_path=None,
            check_sources=False,
        )
        self.assertEqual(result["status"], "valid", result)

    def test_duplicate_aliases_are_rejected(self) -> None:
        data = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        row = data["skills"][0]
        second = copy.deepcopy(row)
        second["id"] = "second-skill"
        second["aliases"] = ["same-alias"]
        row["aliases"] = ["same-alias"]
        data["skills"].append(second)
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "manifest.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = validate_manifest(path, schema_path=SCHEMA, root=ROOT, summary_path=None, check_sources=False)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("alias collision" in error for error in result["errors"]))

    def test_missing_competing_scenario_is_rejected(self) -> None:
        data = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        data["skills"][0]["optimization"]["scenario_ids"] = ["supportive-example", "neutral-example", "other-example"]
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "manifest.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = validate_manifest(path, schema_path=SCHEMA, root=ROOT, summary_path=None, check_sources=False)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("missing competing" in error for error in result["errors"]))

    def test_snapshot_provenance_is_required(self) -> None:
        data = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        del data["source_audit"]["snapshot"]
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "manifest.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = validate_manifest(path, schema_path=SCHEMA, root=ROOT, summary_path=None, check_sources=False)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("snapshot" in error for error in result["errors"]))

    def test_snapshot_git_head_drift_is_rejected(self) -> None:
        data = json.loads(CURRENT_MANIFEST.read_text(encoding="utf-8"))
        data["source_audit"]["snapshot"]["git_head"] = "0" * 40
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "manifest.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = validate_manifest(
                path,
                schema_path=SCHEMA,
                root=ROOT,
                summary_path=SUMMARY,
                check_sources=True,
            )
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("snapshot Git HEAD drift" in error for error in result["errors"]))

    def test_record_result_updates_one_canonical_row(self) -> None:
        data = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "manifest.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            record(
                path,
                skill_id="example-skill",
                status="edit",
                after_metric={"status": "promoted", "delta": 0.25},
                proof_refs=["comparison.json"],
            )
            updated = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(updated["skills"][0]["status"], "edit")
        self.assertEqual(updated["skills"][0]["after_metric"]["status"], "promoted")
        self.assertIn("comparison.json", updated["skills"][0]["proof_ref"])


if __name__ == "__main__":
    unittest.main()
