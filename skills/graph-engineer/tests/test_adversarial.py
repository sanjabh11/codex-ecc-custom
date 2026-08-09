import json
import os
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
REPO_ROOT = SKILL_DIR.parents[1]
GRAPH = TESTS_DIR / "test_valid_graph.json"
V11_GRAPH = TESTS_DIR / "test_valid_v11_graph.json"
VALIDATOR = SKILL_DIR / "scripts" / "validate_graph.py"
RUNTIME = SKILL_DIR / "scripts" / "check_runtime.py"
RECORDER = SKILL_DIR / "scripts" / "record_evidence.py"


class TestGraphEngineerAdversarial(unittest.TestCase):
    def validator(self, graph_path, *extra):
        return subprocess.run(
            ["python3", str(VALIDATOR), "--runtime-root", str(REPO_ROOT), *extra, str(graph_path)],
            capture_output=True,
            text=True,
        )

    def test_duplicate_ids_and_unknown_fields_fail_cleanly(self):
        graph = json.loads(GRAPH.read_text())
        graph["nodes"].append(dict(graph["nodes"][0]))
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(graph, handle)
            handle.flush()
            result = self.validator(handle.name)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        graph = json.loads(GRAPH.read_text())
        graph["nodes"][0]["unexpected"] = "field"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(graph, handle)
            handle.flush()
            result = self.validator(handle.name)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Additional properties", result.stdout)

    def test_graph_size_limit_fails_before_semantic_processing(self):
        graph = json.loads(GRAPH.read_text())
        graph["description"] = "x" * (5 * 1024 * 1024)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(graph, handle)
            handle.flush()
            result = subprocess.run(["python3", str(VALIDATOR), handle.name], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("safety limit", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_runtime_symlink_escape_is_not_hashable(self):
        from importlib.util import module_from_spec, spec_from_file_location

        spec = spec_from_file_location("graph_engineer_runtime_adversarial", SKILL_DIR / "scripts" / "check_runtime.py")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "skills" / "graph-engineer"
            package.mkdir(parents=True)
            outside = root / "outside.txt"
            outside.write_text("outside")
            (package / "SKILL.md").symlink_to(outside)
            # G8: runtime_hash now returns None for unsafe symlinks (fail closed)
            self.assertIsNone(module.runtime_hash(root))

    def recorder(self, root, run_id, event_type, *extra):
        return subprocess.run([
            "python3", str(RECORDER), "--graph", str(GRAPH), "--run-id", run_id,
            "--event-type", event_type, "--output", str(root / "evidence.jsonl"),
            "--evidence-root", str(root), "--runtime-root", str(REPO_ROOT), *extra,
        ], capture_output=True, text=True)

    def test_corrupt_evidence_is_rejected_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "evidence.jsonl"
            output.write_text("not-json\n")
            result = self.recorder(root, "corrupt", "run_started")
            self.assertEqual(result.returncode, 1)
            self.assertIn("invalid JSONL", result.stderr)
            self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_concurrent_runs_append_complete_json_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_ids = [f"concurrent-{index}" for index in range(4)]
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda run_id: self.recorder(root, run_id, "run_started"), run_ids))
            self.assertTrue(all(result.returncode == 0 for result in results), [result.stderr for result in results])
            lines = (root / "evidence.jsonl").read_text().splitlines()
            self.assertEqual(len(lines), len(run_ids))
            records = [json.loads(line) for line in lines]
            self.assertEqual({record["run_id"] for record in records}, set(run_ids))
            self.assertTrue(all(len(record["graph_sha256"]) == 64 for record in records))

    def test_no_absolute_user_paths_in_distributable_package(self):
        forbidden = ("/" + "Users/", "/" + "home/")
        for path in SKILL_DIR.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if path.name == "evidence.jsonl":
                continue
            data = path.read_bytes()
            with self.subTest(path=path.relative_to(SKILL_DIR)):
                self.assertFalse(any(marker.encode() in data for marker in forbidden))

    # === Sixth Audit Gap Tests ===

    def test_g8_missing_runtime_root_returns_none_not_sentinel(self):
        """G8: runtime_hash(None) must return None, not a sentinel hash."""
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location("ge_runtime_g8", SKILL_DIR / "scripts" / "check_runtime.py")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIsNone(module.runtime_hash(None))
        self.assertIsNone(module.runtime_hash(""))

    def test_g8_missing_package_returns_none_not_sentinel(self):
        """G8: runtime_hash with missing package dir must return None."""
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location("ge_runtime_g8b", SKILL_DIR / "scripts" / "check_runtime.py")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            # Directory exists but no skills/graph-engineer package
            self.assertIsNone(module.runtime_hash(directory))

    def test_g9_unknown_tool_blocked_by_default(self):
        """G9: Unknown tools not in policy taxonomy must be blocked."""
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location("ge_runtime_g9", SKILL_DIR / "scripts" / "check_runtime.py")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        graph = {"nodes": [{"id": "n1", "type": "worker", "tools": ["totally-unknown-tool-xyz"]}]}
        checks, blocked, degraded = module.check_tools(graph)
        self.assertTrue(any("unknown tool" in b.get("reason", "") for b in blocked),
                        f"Expected unknown tool to be blocked, got blocked={blocked}")

    def test_g10_invalid_utf8_graph_rejected_without_traceback(self):
        """G10: Invalid UTF-8 in graph file must be rejected cleanly."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
            handle.write(b'{\n  "name": "\xff\xfe invalid utf8\n}')
            path = handle.name
        try:
            result = subprocess.run(["python3", str(VALIDATOR), path], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stdout + result.stderr)
        finally:
            os.unlink(path)

    def test_g10_invalid_utf8_evidence_rejected(self):
        """G10: Invalid UTF-8 in evidence file must be rejected."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "evidence.jsonl"
            output.write_bytes(b'\xff\xfe invalid utf8\n')
            result = self.recorder(root, "utf8-bad", "run_started")
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_g11_review_on_non_reviewer_node_rejected(self):
        """G11: review events on non-reviewer nodes must be rejected."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.recorder(root, "g11-1", "run_started").returncode, 0)
            # worker-a is a worker node, not a reviewer — review must fail
            result = self.recorder(root, "g11-1", "review", "--node", "worker-a", "--status", "pass")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reviewer", result.stderr.lower())

    def test_g11_node_attempt_on_human_gate_rejected(self):
        """G11: node_attempt events on human-gate nodes must be rejected."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.recorder(root, "g11-2", "run_started").returncode, 0)
            # human-gate-publish is a human-gate, not a worker — node_attempt must fail
            result = self.recorder(root, "g11-2", "node_attempt", "--node", "human-gate-publish", "--status", "pass")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("executable", result.stderr.lower())

    def test_g12_run_finished_without_node_attempt_rejected(self):
        """G12: run_finished without any node_attempt must be rejected."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.recorder(root, "g12-1", "run_started").returncode, 0)
            # No node_attempt before run_finished
            result = self.recorder(root, "g12-1", "run_finished")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("node_attempt", result.stderr.lower())

    def test_g12_review_without_prior_attempt_rejected(self):
        """G12: review without prior node_attempt on same node must be rejected."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.recorder(root, "g12-2", "run_started").returncode, 0)
            # review on reviewer-a without any prior node_attempt on reviewer-a
            result = self.recorder(root, "g12-2", "review", "--node", "reviewer-a", "--status", "pass")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("node_attempt", result.stderr.lower())

    def test_g14_malformed_policy_raises_value_error(self):
        """G14: load_tool_policy must raise ValueError on malformed policy, not fall back."""
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location("ge_policy_g14", SKILL_DIR / "scripts" / "runtime_policy.py")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as handle:
            handle.write("{ invalid json")
            path = handle.name
        try:
            with self.assertRaises(ValueError):
                module.load_tool_policy(path)
        finally:
            os.unlink(path)

    def test_g14_missing_policy_raises_value_error(self):
        """G14: load_tool_policy must raise ValueError on missing policy file."""
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location("ge_policy_g14b", SKILL_DIR / "scripts" / "runtime_policy.py")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(ValueError):
            module.load_tool_policy("/nonexistent/path/to/policy.json")

    def test_g15_runtime_identity_has_interpreter_path_and_hostname(self):
        """G15: runtime_identity must include interpreter_path and hostname."""
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location("ge_runtime_g15", SKILL_DIR / "scripts" / "check_runtime.py")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        identity = module.runtime_identity()
        self.assertIn("interpreter_path", identity)
        self.assertIn("hostname", identity)
        self.assertTrue(identity["interpreter_path"])
        self.assertTrue(identity["hostname"])

    def test_g16_malformed_policy_blocks_without_traceback(self):
        """A malformed shared policy must fail closed at both API and CLI boundaries."""
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location("ge_runtime_g16", SKILL_DIR / "scripts" / "check_runtime.py")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        graph = {"nodes": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            handle.write("[]")
            handle.flush()
            checks, blocked, degraded = module.check_tools(graph, rules_path=handle.name)
        self.assertEqual(checks, [])
        self.assertTrue(blocked)
        self.assertEqual(degraded, [])

    def test_g17_invalid_review_timestamp_fails_cleanly(self):
        """FormatChecker must reject invalid review timestamps without a traceback."""
        report = {
            "reviewer_id": "reviewer-a",
            "reviewed_node_id": "worker-a",
            "question": "Is the output factually correct?",
            "result": "pass",
            "feedback": "accepted",
            "timestamp": "not-a-date",
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(report, handle)
            handle.flush()
            result = self.validator(GRAPH, "--review-report", handle.name)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertIn("review_report_0_schema_valid", result.stdout)

    def test_g18_v11_required_fields_are_enforced(self):
        """A v1.1 marker cannot bypass objective, criteria, budget, or evidence policy."""
        graph = json.loads(V11_GRAPH.read_text())
        graph.pop("objective")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(graph, handle)
            handle.flush()
            result = self.validator(handle.name)
        self.assertEqual(result.returncode, 1)
        self.assertIn("objective", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_g19_standalone_node_schema_is_resolvable(self):
        """The node schema is independently usable, not only a dangling relative ref."""
        import jsonschema
        node = json.loads(GRAPH.read_text())["nodes"][0]
        schema = json.loads((SKILL_DIR / "schemas" / "node-definition.schema.json").read_text())
        jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker()).validate(node)

    def test_g20_lifecycle_events_cannot_be_bound_to_nodes(self):
        """Run lifecycle records are run-scoped and cannot smuggle a node binding."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.recorder(
                root,
                "g20-1",
                "run_started",
                "--node",
                "worker-a",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not be bound", result.stderr)
            self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
