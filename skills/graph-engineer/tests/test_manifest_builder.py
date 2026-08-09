import json
import subprocess
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
REPO_ROOT = SKILL_DIR.parents[1]
GRAPH = TESTS_DIR / "test_valid_graph.json"
BUILDER = SKILL_DIR / "scripts" / "create_manifest.py"
RUNTIME = SKILL_DIR / "scripts" / "check_runtime.py"


class TestManifestBuilder(unittest.TestCase):
    def test_builder_creates_gate_usable_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "run.manifest.json"
            result = subprocess.run([
                "python3", str(BUILDER), "--graph", str(GRAPH), "--runtime-root", str(REPO_ROOT),
                "--run-id", "builder-run", "--artifact-digest", "sha256:builder-artifact",
                "--action", "publish", "--target", "human-gate-publish", "--approver", "test-harness",
                "--decision", "approved", "--output", str(manifest),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(manifest.read_text())
            self.assertEqual(value["approval_binding"]["run_id"], "builder-run")
            gate = subprocess.run([
                "python3", str(RUNTIME), "--graph", str(GRAPH), "--runtime-root", str(REPO_ROOT),
                "--manifest", str(manifest), "--run-id", "builder-run", "--artifact-digest", "sha256:builder-artifact",
            ], capture_output=True, text=True)
            self.assertEqual(gate.returncode, 0, gate.stdout + gate.stderr)
            self.assertEqual(json.loads(gate.stdout)["decision"], "available")

    def test_builder_rejects_invalid_graph(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "run.manifest.json"
            result = subprocess.run([
                "python3", str(BUILDER), "--graph", str(TESTS_DIR / "test_no_diagram.json"),
                "--runtime-root", str(REPO_ROOT), "--run-id", "bad", "--artifact-digest", "sha256:x",
                "--action", "publish", "--target", "human-gate-publish", "--approver", "test",
                "--decision", "approved", "--output", str(manifest),
            ], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(manifest.exists())


if __name__ == "__main__":
    unittest.main()
