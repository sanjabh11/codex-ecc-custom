#!/usr/bin/env python3
"""Regression tests for deterministic Graphify health discovery."""

import json
import subprocess
from pathlib import Path
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
HEALTH = SKILL_DIR / "scripts" / "graphify-health.sh"


class GraphifyHealthTests(unittest.TestCase):
    def test_health_is_local_and_bounded(self):
        content = HEALTH.read_text(encoding="utf-8")
        self.assertNotIn("uv tool run --from", content)
        result = subprocess.run(
            ["bash", str(HEALTH), "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["healthy"])
        self.assertTrue(payload["binary"].endswith("/graphify"))
        self.assertTrue(payload["version"])


if __name__ == "__main__":
    unittest.main()
