import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import jsonschema


TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
REPO_ROOT = SKILL_DIR.parents[1]
VALIDATOR = SKILL_DIR / "scripts" / "validate_graph.py"
GRAPH = TESTS_DIR / "test_valid_graph.json"
V11_GRAPH = TESTS_DIR / "test_valid_v11_graph.json"


def run_validator(graph_path, *extra):
    return subprocess.run(
        ["python3", str(VALIDATOR), "--runtime-root", str(REPO_ROOT), *extra, str(graph_path)],
        capture_output=True,
        text=True,
    )


class TestGraphEngineerDiscoverable(unittest.TestCase):
    def test_all_positive_fixtures_pass(self):
        fixtures = sorted(TESTS_DIR.glob("hypothetical-*.json"))
        fixtures += [TESTS_DIR / "skill-library-audit.json", TESTS_DIR / "test_valid_graph.json", TESTS_DIR / "test_valid_v11_graph.json"]
        for fixture in fixtures:
            with self.subTest(fixture=fixture.name):
                result = run_validator(fixture)
                self.assertEqual(result.returncode, 0, result.stdout[-1200:])

    def test_known_negative_fixtures_fail(self):
        for name in ("test_no_diagram.json", "test_exceeded_cap.json"):
            with self.subTest(fixture=name):
                result = run_validator(TESTS_DIR / name)
                self.assertEqual(result.returncode, 1, result.stdout[-1200:])

    def test_v11_required_fields_are_enforced(self):
        graph = json.loads(GRAPH.read_text())
        graph["schema_version"] = "v1.1"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(graph, handle)
            handle.flush()
            result = run_validator(handle.name)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_v11_semantic_state_and_resource_rules_are_enforced(self):
        mutations = [
            ("reviewer ownership", lambda graph: graph["nodes"][2].update({"reviewed_node_id": "plan"}), "reviewed_node_bound"),
            ("failure condition", lambda graph: next(edge for edge in graph["edges"] if edge["type"] == "failure").pop("condition"), "condition_is_review_failed"),
            ("exhaustion condition", lambda graph: next(edge for edge in graph["edges"] if edge["type"] == "exhaustion").update({"condition": "retryable_failure"}), "condition_is_retry_exhausted"),
            ("budget lower bound", lambda graph: graph["budget"].update({"max_model_calls": 1}), "budget_max_model_calls_covers_graph"),
            ("shared writer lock", lambda graph: graph["nodes"][3]["resources"].update({"writes": ["artifact:v11/result.json"], "locks": ["final-only-lock"]}), "writers_are_serialized"),
        ]
        for label, mutate, expected in mutations:
            graph = json.loads(V11_GRAPH.read_text())
            mutate(graph)
            with self.subTest(case=label):
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
                    json.dump(graph, handle)
                    handle.flush()
                    result = run_validator(Path(handle.name))
                self.assertEqual(result.returncode, 1, result.stdout[-1600:])
                self.assertIn(expected, result.stdout)

    def test_v11_fan_in_requires_join_contract(self):
        graph = json.loads(V11_GRAPH.read_text())
        synth = next(node for node in graph["nodes"] if node["id"] == "synthesizer")
        synth["inputs"].append("worker")
        synth["input_ports"].append({"name": "worker_result", "from_node": "worker", "from_port": "result", "schema": {"type": "object"}})
        graph["edges"].append({
            "from": "worker", "to": "synthesizer", "from_port": "result", "to_port": "worker_result",
            "dependency_reason": "Join regression test", "condition": "worker_ready", "type": "data",
        })
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(graph, handle)
            handle.flush()
            result = run_validator(Path(handle.name))
        self.assertEqual(result.returncode, 1)
        self.assertIn("join_synthesizer_declared", result.stdout)

    def test_review_report_is_schema_and_graph_bound(self):
        graph = json.loads(GRAPH.read_text())
        reviewer = next(node for node in graph["nodes"] if node["id"] == "reviewer-a")
        report = {
            "reviewer_id": "reviewer-a",
            "reviewed_node_id": "worker-a",
            "question": reviewer["review_questions"][0],
            "result": "pass",
            "feedback": "The reviewed artifact satisfies the question.",
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as report_handle:
            json.dump(report, report_handle)
            report_handle.flush()
            valid = run_validator(GRAPH, "--review-report", report_handle.name)
            self.assertEqual(valid.returncode, 0, valid.stdout[-1600:])
            report["reviewed_node_id"] = "worker-b"
            report_handle.seek(0)
            report_handle.truncate()
            json.dump(report, report_handle)
            report_handle.flush()
            invalid = run_validator(GRAPH, "--review-report", report_handle.name)
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("reviewed_node_matches", invalid.stdout)

    def test_malformed_inputs_fail_without_traceback(self):
        for content in ("{", "[]"):
            with self.subTest(content=content):
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
                    handle.write(content)
                    handle.flush()
                    result = subprocess.run(
                        ["python3", str(VALIDATOR), handle.name],
                        capture_output=True,
                        text=True,
                    )
                self.assertEqual(result.returncode, 1)
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_missing_jsonschema_fails_closed(self):
        result = subprocess.run(
            ["python3", "-S", str(VALIDATOR), str(GRAPH)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("jsonschema", result.stdout.lower())
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_activation_policy_has_unique_surface_ids(self):
        policy = json.loads((SKILL_DIR / "activation-policy.json").read_text())
        schema = json.loads((SKILL_DIR / "schemas" / "activation-policy.schema.json").read_text())
        jsonschema.validate(instance=policy, schema=schema)
        ids = [surface["id"] for surface in policy["discovery_surfaces"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("Windsurf", policy["logical_host_families"])
        self.assertEqual(len(policy["logical_host_families"]), 6)
        self.assertEqual(len(policy["discovery_surfaces"]), 7)

    def test_trigger_metadata_cases(self):
        module_path = TESTS_DIR / "test_triggers.py"
        spec = importlib.util.spec_from_file_location("graph_engineer_trigger_tests", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        policy = module.load_trigger_metadata()
        self.assertTrue(module.prompt_matches_trigger("Design an agent graph for this audit", policy))
        self.assertFalse(module.prompt_matches_trigger("Review the pipeline implementation for bugs", policy))
        self.assertFalse(module.prompt_matches_trigger("Use a multi-agent workflow, but every step depends on full prior context and must run sequentially", policy))
        self.assertFalse(module.prompt_matches_trigger("Design a graph database schema for customer records", policy))
        self.assertFalse(module.prompt_matches_trigger("Not sure whether to use a multi-agent workflow", policy))


if __name__ == "__main__":
    unittest.main()
