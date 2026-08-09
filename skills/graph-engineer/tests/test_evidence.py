import json
import subprocess
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
REPO_ROOT = SKILL_DIR.parents[1]
GRAPH = TESTS_DIR / "test_valid_graph.json"
RECORDER = SKILL_DIR / "scripts" / "record_evidence.py"


class TestEvidenceRecorder(unittest.TestCase):
    def run_recorder(self, root, run_id, event_type, *extra):
        output = root / "run.jsonl"
        command = [
            "python3",
            str(RECORDER),
            "--graph", str(GRAPH),
            "--run-id", run_id,
            "--event-type", event_type,
            "--output", str(output),
            "--evidence-root", str(root),
            "--runtime-root", str(REPO_ROOT),
        ]
        command.extend(extra)
        return subprocess.run(command, capture_output=True, text=True)

    def test_lifecycle_node_binding_and_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            started = self.run_recorder(root, "run-1", "run_started")
            self.assertEqual(started.returncode, 0, started.stderr)
            attempt = self.run_recorder(root, "run-1", "node_attempt", "--node", "worker-a", "--status", "pass", "--note", "api_key=do-not-store")
            self.assertEqual(attempt.returncode, 0, attempt.stderr)
            finished = self.run_recorder(root, "run-1", "run_finished")
            self.assertEqual(finished.returncode, 0, finished.stderr)
            records = [json.loads(line) for line in (root / "run.jsonl").read_text().splitlines()]
            self.assertEqual([record["event_type"] for record in records], ["run_started", "node_attempt", "run_finished"])
            self.assertIn("[REDACTED]", records[1]["note"])
            self.assertNotIn("do-not-store", (root / "run.jsonl").read_text())
            self.assertTrue((root / "run.jsonl.lock").exists())

    def test_unknown_node_and_invalid_lifecycle_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unknown = self.run_recorder(root, "run-2", "node_attempt", "--node", "not-a-node", "--status", "pass")
            self.assertNotEqual(unknown.returncode, 0)
            self.assertIn("not declared", unknown.stderr)
            self.assertEqual(self.run_recorder(root, "run-2", "run_started").returncode, 0)
            unknown_after_start = self.run_recorder(root, "run-2", "node_attempt", "--node", "not-a-node", "--status", "pass")
            self.assertNotEqual(unknown_after_start.returncode, 0)
            self.assertIn("not declared", unknown_after_start.stderr)

    def test_gate_requires_a_strict_approval_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            started = self.run_recorder(root, "run-3", "run_started")
            self.assertEqual(started.returncode, 0)
            missing = self.run_recorder(root, "run-3", "gate_decision", "--node", "human-gate-publish", "--status", "pass")
            self.assertNotEqual(missing.returncode, 0)
            binding = json.dumps({
                "run_id": "run-3",
                "graph_sha256": json.loads(started.stdout)["graph_sha256"],
                "artifact_digest": "sha256:artifact",
                "action": "publish",
                "target": "human-gate-publish",
                "approver": "test",
                "decision": "approved",
                "approved_at": "2026-08-09T00:00:00Z",
                "expires_at": "2026-08-10T00:00:00Z",
            })
            accepted = self.run_recorder(root, "run-3", "gate_decision", "--node", "human-gate-publish", "--status", "pass", "--artifact-digest", "sha256:artifact", "--approval-binding", binding)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)

    def test_negative_measurements_and_path_escape_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.run_recorder(root, "run-4", "run_started").returncode, 0)
            negative = self.run_recorder(root, "run-4", "node_attempt", "--node", "worker-a", "--status", "pass", "--tokens", "-1")
            self.assertNotEqual(negative.returncode, 0)
            outside = root.parent / "outside.jsonl"
            escaped = subprocess.run([
                "python3", str(RECORDER), "--graph", str(GRAPH), "--run-id", "run-5",
                "--event-type", "run_started", "--output", str(outside), "--evidence-root", str(root),
                "--runtime-root", str(REPO_ROOT),
            ], capture_output=True, text=True)
            self.assertNotEqual(escaped.returncode, 0)
            self.assertIn("inside", escaped.stderr)


if __name__ == "__main__":
    unittest.main()
