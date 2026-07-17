#!/usr/bin/env python3
"""Tests for the AI marketing skill adoption validator."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "validate_marketing_skill_adoption",
    ROOT / "scripts/validate_marketing_skill_adoption.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class MarketingSkillAdoptionTests(unittest.TestCase):
    def test_canonical_portfolio_passes(self):
        self.assertEqual([], MODULE.validate_repo(ROOT))

    def test_missing_evidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = MODULE.validate_repo(Path(tmp))
        self.assertTrue(any("missing audit report" in error for error in errors))
        self.assertTrue(any("invalid JSON" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
