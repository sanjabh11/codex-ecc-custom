from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_skill_optimization_comparison import validate


ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "schemas/skill-optimization-comparison.schema.json"
COMPARISONS = ROOT / "docs/audits/skill-optimization-evidence/comparisons"


class SkillOptimizationComparisonTests(unittest.TestCase):
    def test_existing_contract_comparisons_are_valid(self) -> None:
        for path in sorted(COMPARISONS.glob("*.json")):
            with self.subTest(path=path.name):
                self.assertEqual(validate(path, SCHEMA)["status"], "valid")

    def test_count_mismatch_is_rejected(self) -> None:
        payload = json.loads((COMPARISONS / "ecc-advisor.json").read_text(encoding="utf-8"))
        payload = copy.deepcopy(payload)
        payload["after_counts"]["total"] += 1
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "comparison.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate(path, SCHEMA)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("total" in error for error in result["errors"]))

    def test_promote_with_not_run_scenario_is_rejected(self) -> None:
        payload = json.loads((COMPARISONS / "ecc-advisor.json").read_text(encoding="utf-8"))
        payload = copy.deepcopy(payload)
        payload["after_counts"] = {"pass": 3, "fail": 0, "not_run": 1, "total": 4}
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "comparison.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate(path, SCHEMA)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("all after scenarios" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
