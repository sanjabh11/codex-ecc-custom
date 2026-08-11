from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_skill_optimization_roi import validate


ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "schemas/skill-optimization-roi-pilot.schema.json"
TEMPLATE = ROOT / "docs/audits/skill-optimization-roi-pilot-template.json"


class SkillOptimizationRoiTests(unittest.TestCase):
    def test_not_run_template_is_valid_and_truthful(self) -> None:
        result = validate(TEMPLATE, SCHEMA)
        self.assertEqual(result["status"], "valid", result)

    def test_observed_record_requires_hashes_and_metrics(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        payload = copy.deepcopy(payload)
        record = payload["records"][0]
        record["status"] = "observed"
        record["proof_level"] = "local"
        record["outcome"]["success"] = True
        record["outcome"]["reviewer_decision"] = "pass"
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "roi.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate(path, SCHEMA)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("required for an observed result" in error for error in result["errors"]))

    def test_live_proof_requires_external_attestation(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        payload = copy.deepcopy(payload)
        record = payload["records"][0]
        record["status"] = "observed"
        record["proof_level"] = "live"
        record["input_sha256"] = "a" * 64
        record["output_sha256"] = "b" * 64
        record["artifact_sha256"] = "c" * 64
        record["metrics"] = {"latency_ms": 1, "prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2, "cost_usd": 0}
        record["outcome"] = {"success": True, "criteria": ["ok"], "reviewer_decision": "pass"}
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "roi.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate(path, SCHEMA)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("external_attestation" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
