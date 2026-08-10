#!/usr/bin/env python3
"""Regression tests for metadata-only skill optimization scenarios."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.run_skill_optimization_scenarios import audit_row


class SkillOptimizationRunnerTests(unittest.TestCase):
    def test_canonical_target_emits_three_strictness_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / "skills" / "demo" / "SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text(
                "---\nname: demo\n---\n\n## When to Use\nTRIGGER for demo.\n\n## Do Not Trigger\nOut of scope.\n\n## Output Contract\nEvidence and limitations.\n",
                encoding="utf-8",
            )
            row = {
                "id": "demo",
                "source_kind": "canonical",
                "canonical_path": "skills/demo/SKILL.md",
            }
            evidence = audit_row(
                row,
                root=root,
                evidence_path=root / "evidence.json",
                manifest_path=root / "manifest.json",
                report_path=root / "report.md",
            )
        self.assertEqual(evidence["summary"]["passed"], 4)
        self.assertEqual(evidence["summary"]["total"], 4)
        self.assertEqual({scenario["strictness"] for scenario in evidence["scenarios"]}, {"supportive", "neutral", "competing"})

    def test_external_label_is_not_run(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            row = {"id": "external-skill", "source_kind": "external", "canonical_path": "external://external-skill"}
            evidence = audit_row(
                row,
                root=root,
                evidence_path=root / "evidence.json",
                manifest_path=root / "manifest.json",
                report_path=root / "report.md",
            )
        self.assertEqual(evidence["summary"]["not_run"], 3)
        self.assertTrue(all(scenario["result"] == "not_run" for scenario in evidence["scenarios"]))


if __name__ == "__main__":
    unittest.main()
