#!/usr/bin/env python3
"""Test runner for graph-engineer skill validation.

Runs validate_graph.py against all test fixtures and verifies exit codes.

Usage:
    python3 tests/test_validate.py
"""

import copy
import json
import os
import subprocess
import sys
import tempfile

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALIDATOR = os.path.join(SKILL_DIR, "scripts", "validate_graph.py")
TESTS_DIR = os.path.join(SKILL_DIR, "tests")

# Test cases: (fixture_file, expected_exit_code, description)
TEST_CASES = [
    ("test_valid_graph.json", 0, "Valid graph should pass"),
    ("test_no_diagram.json", 1, "Graph without diagram should fail"),
    ("test_exceeded_cap.json", 1, "Graph with exceeded loop cap should fail"),
    ("skill-library-audit.json", 0, "Canonical skill-library audit should pass"),
    ("test_valid_v11_graph.json", 0, "Strict v1.1 typed graph should pass"),
]


def run_test(fixture, expected_exit, description):
    fixture_path = os.path.join(TESTS_DIR, fixture)
    if not os.path.exists(fixture_path):
        print(f"  [FAIL] {fixture} — file not found")
        return False

    command = [sys.executable, VALIDATOR, "--runtime-root", os.path.dirname(os.path.dirname(SKILL_DIR)), fixture_path]
    result = subprocess.run(command, capture_output=True, text=True)

    passed = result.returncode == expected_exit
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {description}")
    print(f"         Expected exit {expected_exit}, got exit {result.returncode}")

    if not passed:
        # Show last few lines of output for debugging
        lines = result.stdout.strip().split("\n")
        for line in lines[-5:]:
            print(f"         > {line}")
        if result.stderr:
            print(f"         STDERR: {result.stderr.strip()[:200]}")

    return passed


def run_mutation(name, mutate, expected_text, include_runtime_root=True):
    """Run a negative semantic case against a temporary graph definition."""
    fixture_path = os.path.join(TESTS_DIR, "test_valid_graph.json")
    with open(fixture_path, encoding="utf-8") as handle:
        graph = json.load(handle)
    mutate(graph)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump(graph, handle)
        temp_path = handle.name
    try:
        command = [sys.executable, VALIDATOR]
        if include_runtime_root:
            command.extend(["--runtime-root", os.path.dirname(os.path.dirname(SKILL_DIR))])
        command.append(temp_path)
        result = subprocess.run(command, capture_output=True, text=True)
        passed = result.returncode == 1 and expected_text in result.stdout
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            print(f"         Expected exit 1 and output containing: {expected_text}")
            print(f"         Got exit {result.returncode}: {result.stdout[-500:]}")
        return passed
    finally:
        os.unlink(temp_path)


def run_semantic_negative_tests():
    cases = [
        ("Unknown edge reference fails", lambda graph: graph["edges"][0].update({"to": "missing-node"}), "references unknown target", True),
        ("Missing input edge fails", lambda graph: graph["edges"].pop(0), "declares input 'planner' but no data/control edge supplies it", True),
        ("Unreachable node fails", lambda graph: graph["nodes"].append({"id": "orphan", "type": "worker", "responsibility": "Execute an isolated task", "inputs": [], "outputs": ["orphan.json"], "loop_cap": 1}), "Unreachable nodes", True),
        ("Data/control cycle fails", lambda graph: graph["edges"].append({"from": "worker-a", "to": "planner", "dependency_reason": "Cycle test edge", "type": "data"}), "contain a cycle", True),
        ("Multiple reviewer questions fail", lambda graph: graph["nodes"][3]["review_questions"].append("Is the output safe?"), "must ask exactly one", True),
        ("Zero reviewer questions fail", lambda graph: graph["nodes"][3].update({"review_questions": []}), "must ask exactly one", True),
        ("Worker without reviewer fails", lambda graph: graph["edges"].remove(next(edge for edge in graph["edges"] if edge["from"] == "worker-a" and edge["to"] == "reviewer-a")), "has no reviewer", True),
        ("Unknown runtime skill fails", lambda graph: graph.update({"runtime_refs": ["skill-does-not-exist"]}), "not found at", True),
        ("Runtime path escape fails", lambda graph: graph.update({"runtime_refs": ["../outside"]}), "JSON Schema violation", True),
        ("Runtime refs require root", lambda graph: graph.update({"runtime_refs": ["ecc-eval"]}), "runtime_refs require --runtime-root", False),
        ("Human gate must be connected", lambda graph: graph["nodes"].append({"id": "orphan-gate", "type": "human-gate", "responsibility": "Approve deployment", "inputs": [], "outputs": ["approval.json"], "human_gate_action": "deploy"}), "must follow a data/control predecessor", True),
        # v1.1 false-green regression tests
        ("Empty outputs fail", lambda graph: graph["nodes"][0].update({"outputs": []}), "outputs", True),
        ("Malformed tools fail", lambda graph: graph["nodes"][1].update({"tools": "not-a-list"}), "tools", True),
        ("Wrong-worker failure edge fails", lambda graph: [e.update({"to": "worker-b"}) for e in graph["edges"] if e["from"] == "reviewer-a" and e["type"] == "failure"], "targets_reviewed_worker", True),
        ("Unknown schema property fails", lambda graph: graph.update({"unknown_field": "bad"}), "Additional properties", True),
        ("Duplicate edge fails", lambda graph: graph["edges"].append(dict(graph["edges"][0])), "duplicate", True),
        ("Reviewer no fail route fails", lambda graph: graph["edges"].remove(next(e for e in graph["edges"] if e["from"] == "reviewer-a" and e["type"] == "failure")), "has no fail route", True),
        ("Reviewer no review report fails", lambda graph: graph["nodes"][3].update({"outputs": ["something.json"]}), "review/report/feedback", True),
    ]
    return sum(run_mutation(name, mutate, expected, include_runtime_root) for name, mutate, expected, include_runtime_root in cases), len(cases)


def main():
    print("graph-engineer test suite\n")
    print(f"Validator: {VALIDATOR}")
    print(f"Tests dir: {TESTS_DIR}\n")

    passed_count = 0
    failed_count = 0

    for fixture, expected_exit, description in TEST_CASES:
        if run_test(fixture, expected_exit, description):
            passed_count += 1
        else:
            failed_count += 1

    print("\nSemantic negative tests")
    semantic_passed, semantic_total = run_semantic_negative_tests()
    passed_count += semantic_passed
    failed_count += semantic_total - semantic_passed

    print(f"\n{'─' * 40}")
    print(f"Tests passed: {passed_count}/{len(TEST_CASES) + semantic_total}")
    print(f"Tests failed: {failed_count}/{len(TEST_CASES) + semantic_total}")

    if failed_count > 0:
        print("\nRESULT: FAIL")
        sys.exit(1)
    else:
        print("\nRESULT: ALL TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
