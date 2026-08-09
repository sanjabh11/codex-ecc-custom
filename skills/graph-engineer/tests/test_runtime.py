import datetime as dt
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
REPO_ROOT = SKILL_DIR.parents[1]
GRAPH = TESTS_DIR / "test_valid_graph.json"
RUNTIME = SKILL_DIR / "scripts" / "check_runtime.py"


def iso(offset_seconds):
    value = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=offset_seconds)
    return value.isoformat().replace("+00:00", "Z")


def load_runtime_module():
    spec = importlib.util.spec_from_file_location("graph_engineer_runtime", RUNTIME)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def manifest_for(module, graph, run_id="run-test", artifact_digest="sha256:test-artifact"):
    graph_value = json.loads(Path(graph).read_text())
    graph_sha = module.graph_hash(graph_value)
    runtime_sha = module.runtime_hash(REPO_ROOT)
    return {
        "manifest_version": "v1",
        "graph_sha256": graph_sha,
        "runtime_sha256": runtime_sha,
        "issued_at": iso(-60),
        "expires_at": iso(3600),
        "revoked": False,
        "runtime_profile": "unittest",
        "runtime_identity": module.runtime_identity(),
        "tool_snapshot": {},
        "approval_binding": {
            "run_id": run_id,
            "graph_sha256": graph_sha,
            "artifact_digest": artifact_digest,
            "action": "publish",
            "target": "human-gate-publish",
            "approver": "unittest",
            "decision": "approved",
            "approved_at": iso(-30),
            "expires_at": iso(1800),
        },
    }


class TestRuntimeGate(unittest.TestCase):
    def run_gate(self, manifest, graph=GRAPH, run_id="run-test", artifact_digest="sha256:test-artifact"):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(manifest, handle)
            handle.flush()
            return subprocess.run(
                [
                    "python3",
                    str(RUNTIME),
                    "--graph",
                    str(graph),
                    "--runtime-root",
                    str(REPO_ROOT),
                    "--manifest",
                    handle.name,
                    "--run-id",
                    run_id,
                    "--artifact-digest",
                    artifact_digest,
                ],
                capture_output=True,
                text=True,
            )

    def test_valid_manifest_is_available(self):
        module = load_runtime_module()
        result = self.run_gate(manifest_for(module, GRAPH))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["decision"], "available")

    def test_missing_manifest_is_rejected_by_cli(self):
        result = subprocess.run(
            ["python3", str(RUNTIME), "--graph", str(GRAPH)],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_revoked_manifest_is_not_available(self):
        module = load_runtime_module()
        manifest = manifest_for(module, GRAPH)
        manifest["revoked"] = True
        manifest["revocation_reason"] = "test revocation"
        result = self.run_gate(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["decision"], "revoked")

    def test_runtime_hash_mismatch_is_blocked(self):
        module = load_runtime_module()
        manifest = manifest_for(module, GRAPH)
        manifest["runtime_sha256"] = "0" * 64
        result = self.run_gate(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["decision"], "blocked")

    def test_invalid_graph_never_receives_available(self):
        module = load_runtime_module()
        manifest = manifest_for(module, GRAPH)
        result = self.run_gate(manifest, graph=TESTS_DIR / "test_no_diagram.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["decision"], "blocked")

    def test_invalid_expiry_and_identity_are_blocked(self):
        module = load_runtime_module()
        manifest = manifest_for(module, GRAPH)
        manifest["expires_at"] = "not-an-iso-time"
        result = self.run_gate(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["decision"], "blocked")
        manifest = manifest_for(module, GRAPH)
        manifest["runtime_identity"]["platform"] = "tampered"
        result = self.run_gate(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["decision"], "blocked")

    def test_runtime_hash_is_content_bound(self):
        module = load_runtime_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "skills" / "graph-engineer"
            package.mkdir(parents=True)
            (package / "SKILL.md").write_text("one")
            first = module.runtime_hash(root)
            (package / "SKILL.md").write_text("two")
            second = module.runtime_hash(root)
            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
