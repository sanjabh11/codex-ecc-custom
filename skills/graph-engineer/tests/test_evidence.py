import hashlib
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
    def review_artifact_args(self, root, reviewer, status):
        details = {
            "reviewer-a": ("worker-a", "Is the output factually correct?"),
            "reviewer-b": ("worker-b", "Is the output complete?"),
        }
        reviewed_node, question = details[reviewer]
        report = {
            "reviewer_id": reviewer,
            "reviewed_node_id": reviewed_node,
            "question": question,
            "result": "pass" if status == "pass" else "fail",
            "feedback": "The reviewed artifact satisfies the question.",
        }
        path = root / f"{reviewer}.review.json"
        path.write_text(json.dumps(report))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return ("--artifact", str(path), "--artifact-digest", digest)

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
        if event_type == "review" and "--artifact" not in extra:
            reviewer = extra[extra.index("--node") + 1]
            status = extra[extra.index("--status") + 1]
            command.extend(self.review_artifact_args(root, reviewer, status))
        return subprocess.run(command, capture_output=True, text=True)

    def test_lifecycle_node_binding_and_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            started = self.run_recorder(root, "run-1", "run_started")
            self.assertEqual(started.returncode, 0, started.stderr)
            for node in ("planner", "worker-a", "worker-b"):
                attempt = self.run_recorder(
                    root, "run-1", "node_attempt", "--node", node,
                    "--status", "pass",
                    *(("--note", "api_key=do-not-store") if node == "worker-a" else ()),
                )
                self.assertEqual(attempt.returncode, 0, attempt.stderr)
            for reviewer in ("reviewer-a", "reviewer-b"):
                review = self.run_recorder(root, "run-1", "review", "--node", reviewer, "--status", "pass")
                self.assertEqual(review.returncode, 0, review.stderr)
            synthesizer = self.run_recorder(root, "run-1", "node_attempt", "--node", "synthesizer", "--status", "pass")
            self.assertEqual(synthesizer.returncode, 0, synthesizer.stderr)
            binding = json.dumps({
                "run_id": "run-1",
                "graph_sha256": json.loads(started.stdout)["graph_sha256"],
                "artifact_digest": "sha256:run-1",
                "action": "publish",
                "target": "human-gate-publish",
                "approver": "test",
                "decision": "approved",
                "approved_at": "2026-08-09T00:00:00Z",
                "expires_at": "2026-08-10T00:00:00Z",
            })
            gate = self.run_recorder(
                root, "run-1", "gate_decision", "--node", "human-gate-publish",
                "--status", "pass", "--artifact-digest", "sha256:run-1",
                "--approval-binding", binding,
            )
            self.assertEqual(gate.returncode, 0, gate.stderr)
            finished = self.run_recorder(root, "run-1", "run_finished")
            self.assertEqual(finished.returncode, 0, finished.stderr)
            records = [json.loads(line) for line in (root / "run.jsonl").read_text().splitlines()]
            self.assertEqual(
                [record["event_type"] for record in records],
                ["run_started", "node_attempt", "node_attempt", "node_attempt", "review", "review", "node_attempt", "gate_decision", "run_finished"],
            )
            self.assertIn("[REDACTED]", records[2]["note"])
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
            # G12: gate_decision requires prior node_attempt or review
            attempt = self.run_recorder(root, "run-3", "node_attempt", "--node", "worker-a", "--status", "pass")
            self.assertEqual(attempt.returncode, 0, attempt.stderr)
            missing = self.run_recorder(root, "run-3", "gate_decision", "--node", "human-gate-publish", "--status", "pass")
            self.assertNotEqual(missing.returncode, 0)
            synthesis = self.run_recorder(root, "run-3", "node_attempt", "--node", "synthesizer", "--status", "pass")
            self.assertEqual(synthesis.returncode, 0, synthesis.stderr)
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
