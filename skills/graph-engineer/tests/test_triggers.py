#!/usr/bin/env python3
"""Metadata-only trigger and discovery regression tests."""

import json
import os
import sys

try:
    import jsonschema
except ImportError:  # pragma: no cover - fail closed in the CLI
    jsonschema = None

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY_FILE = os.path.join(SKILL_DIR, "activation-policy.json")


def load_trigger_metadata():
    with open(POLICY_FILE, encoding="utf-8") as handle:
        policy = json.load(handle)
    if jsonschema is None:
        raise RuntimeError("jsonschema is required to validate activation metadata")
    schema_file = os.path.join(SKILL_DIR, "schemas", "activation-policy.schema.json")
    with open(schema_file, encoding="utf-8") as handle:
        schema = json.load(handle)
    jsonschema.validate(instance=policy, schema=schema)
    if len(policy["logical_host_families"]) != policy["logical_host_family_count"]:
        raise ValueError("logical host-family count does not match activation metadata")
    if len(policy["discovery_surfaces"]) != policy["physical_discovery_path_count"]:
        raise ValueError("physical discovery-path count does not match activation metadata")
    return policy


def prompt_matches_trigger(prompt, trigger_policy):
    """Conservative approximation; this does not claim to be a host engine."""
    prompt_lower = prompt.lower()
    for phrase in trigger_policy.get("clarification_phrases", []):
        if phrase in prompt_lower:
            return False
    for anti in trigger_policy.get("anti_trigger_phrases", []):
        if anti in prompt_lower:
            return False
    if "full prior context" in prompt_lower and "sequential" in prompt_lower:
        return False
    if "review" in prompt_lower and "pipeline" in prompt_lower and not any(
        signal in prompt_lower
        for signal in ("agent graph", "multi-agent", "diamond", "parallel", "fan-out")
    ):
        return False
    for phrase in trigger_policy.get("trigger_phrases", []):
        if phrase in prompt_lower:
            return True
    keywords = ["graph", "diamond", "parallel", "review", "pipeline", "multi-agent"]
    return sum(1 for keyword in keywords if keyword in prompt_lower) >= 2


def main():
    print("graph-engineer trigger regression tests (metadata-only)\n")
    try:
        trigger_policy = load_trigger_metadata()
    except (OSError, ValueError) as exc:
        print(f"  [FAIL] Could not load activation policy: {exc}")
        sys.exit(1)

    passed = 0
    failed = 0

    positive_prompts = [
        "Design an agent graph for my content pipeline",
        "I need a multi-agent workflow with parallel reviewers",
        "Build a reliable agent pipeline with diamond pattern",
        "Help with graph validation for my agent pipeline",
        "Set up job-based nodes for my research workflow",
    ]
    print("Positive trigger tests (should trigger):")
    for prompt in positive_prompts:
        triggered = prompt_matches_trigger(prompt, trigger_policy)
        status = "PASS" if triggered else "FAIL"
        print(f"  [{status}] '{prompt[:60]}...'")
        passed += int(triggered)
        failed += int(not triggered)

    negative_prompts = [
        "Write a single Python function to sort a list",
        "Fix this one-line typo in my config file",
        "What is the capital of France?",
        "Run a simple linear chain with no parallelism or review gates",
        "Just write the code directly, no planning needed",
        "Single-agent prompt with no graph structure needed",
        "Use a multi-agent workflow, but every step depends on full prior context and must run sequentially",
        "Review the pipeline implementation for bugs",
        "Design a graph database schema for customer records",
        "Not sure whether to use a multi-agent workflow",
    ]
    print("\nNegative trigger tests (should NOT trigger):")
    for prompt in negative_prompts:
        triggered = prompt_matches_trigger(prompt, trigger_policy)
        status = "PASS" if not triggered else "FAIL"
        print(f"  [{status}] '{prompt[:60]}...'")
        passed += int(not triggered)
        failed += int(triggered)

    strict_platforms = os.environ.get("GRAPH_ENGINEER_STRICT_PLATFORMS") == "1"
    skipped = 0
    print("\nPlatform discovery tests (physical surfaces, not loader proof):")
    for surface in trigger_policy.get("discovery_surfaces", []):
        path = surface["path"]
        name = surface["id"]
        expanded = os.path.expanduser(path)
        exists = os.path.exists(expanded)
        is_symlink = os.path.islink(expanded)
        target_has_skill = exists and os.path.isfile(os.path.join(os.path.realpath(expanded), "SKILL.md"))
        if exists and is_symlink and target_has_skill:
            print(f"  [PASS] {name}: symlink to a readable skill")
            passed += 1
        elif not strict_platforms and not exists:
            print(f"  [SKIP] {name}: host surface is not installed in this environment")
            skipped += 1
        else:
            print(f"  [FAIL] {name}: missing, stale, or not a symlink")
            failed += 1

    print(f"\n{'─' * 40}")
    print(f"Tests passed: {passed}/{passed + failed + skipped}")
    print(f"Tests failed: {failed}/{passed + failed + skipped}")
    print(f"Tests skipped: {skipped}")
    if failed:
        print("\nRESULT: FAIL")
        sys.exit(1)
    print("\nRESULT: ALL TESTS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
