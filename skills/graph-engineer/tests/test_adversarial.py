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
            self.assertEqual(module.runtime_hash(root), module.hashlib.sha256(b"unsafe-runtime-symlink").hexdigest())

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


if __name__ == "__main__":
    unittest.main()
