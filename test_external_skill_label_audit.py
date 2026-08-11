from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts/audit_external_skill_labels.py"
SCHEMA = ROOT / "schemas/external-skill-label-audit.schema.json"


class ExternalSkillLabelAuditTests(unittest.TestCase):
    def test_discovery_is_hash_bound_and_never_loader_proof(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            host_root = Path(raw) / "skills"
            target = Path(raw) / "canonical" / "deep-research"
            target.mkdir(parents=True)
            (target / "SKILL.md").write_text("---\nname: deep-research\n---\n", encoding="utf-8")
            host_root.mkdir()
            (host_root / "deep-research").symlink_to(target, target_is_directory=True)
            result = subprocess.run(
                ["python3", str(SCRIPT), "--label", "deep-research", "--host-root", str(host_root)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "discovery-only")
        self.assertFalse(payload["authenticated_loader_proof"])
        candidate = payload["labels"][0]["candidates"][0]
        self.assertEqual(candidate["status"], "present")
        self.assertEqual(candidate["projection_kind"], "symlink")
        self.assertEqual(len(candidate["content_sha256"]), 64)

        import jsonschema

        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(payload)

    def test_schema_rejects_loader_claim(self) -> None:
        import jsonschema

        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        invalid = {"schema_version": "external-skill-label-audit.v1", "status": "loaded", "authenticated_loader_proof": True, "labels": []}
        self.assertTrue(list(jsonschema.Draft202012Validator(schema).iter_errors(invalid)))


if __name__ == "__main__":
    unittest.main()
