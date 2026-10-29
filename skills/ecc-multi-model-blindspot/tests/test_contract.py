#!/usr/bin/env python3
"""Regression checks for the blindspot workflow's proof boundary."""

import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[3] / "skills" / "ecc-multi-model-blindspot" / "SKILL.md"


class BlindspotContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf-8")

    def test_workflow_phases_and_templates_exist(self):
        for marker in (
            "Phase 1: Dispatch",
            "Phase 2: Cross-Review",
            "Phase 3: Synthesize",
            "Phase 4: Deliver",
            "Dispatch Prompt Template",
            "Cross-Review Prompt Template",
        ):
            self.assertIn(marker, self.text)

    def test_degraded_paths_are_explicit(self):
        self.assertIn("Single-Model Fallback", self.text)
        self.assertIn("No models available", self.text)
        self.assertIn("label the result `unverified`", self.text)
        self.assertIn("no embedded model runner", self.text)
        self.assertIn("Actual dispatch depends on host integrations", self.text)

    def test_consensus_requires_evidence(self):
        self.assertIn("model roster", self.text)
        self.assertIn("independent responses", self.text)
        self.assertIn("agreement count", self.text)
        self.assertIn("Do NOT claim consensus or majority confidence", self.text)


if __name__ == "__main__":
    unittest.main()
