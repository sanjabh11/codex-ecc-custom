#!/usr/bin/env python3
"""Validator for ecc-weekly-marketing-flywheel composite skill.

Checks frontmatter, schemas, references, repo profiles, evidence contract,
chain architecture, behavioral rules, and scenario coverage.
"""

import json
import os
import re
import subprocess
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

checks_passed = 0
checks_failed = 0
failures = []


def check(name, condition, detail=""):
    global checks_passed, checks_failed
    if condition:
        print(f"  [PASS] {name}")
        checks_passed += 1
    else:
        print(f"  [FAIL] {name} — {detail}")
        checks_failed += 1
        failures.append(name)


def read_file(path):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return f.read()


def read_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def check_frontmatter(content):
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        check("frontmatter_exists", False, "No frontmatter found")
        return
    fm = fm_match.group(1)
    check("frontmatter_name", "name: ecc-weekly-marketing-flywheel" in fm, "name field missing or wrong")
    check("frontmatter_description", "description:" in fm, "description field missing")
    check("frontmatter_triggers", "TRIGGER" in fm, "trigger phrases missing")
    check("frontmatter_anti_triggers", "DO NOT TRIGGER" in fm, "anti-trigger missing")
    check("frontmatter_no_implicit", "allow_implicit_invocation" not in fm,
          "allow_implicit_invocation must NOT be in SKILL.md frontmatter")


def check_quick_validate():
    """Run Codex quick_validate.py as a subprocess."""
    quick_validate_path = os.path.expanduser(
        "~/.codex/skills/.system/skill-creator/scripts/quick_validate.py"
    )
    if not os.path.exists(quick_validate_path):
        check("quick_validate_available", False, f"quick_validate.py not found at {quick_validate_path}")
        return
    result = subprocess.run(
        [sys.executable, quick_validate_path, SKILL_DIR],
        capture_output=True, text=True,
    )
    check("quick_validate_pass", result.returncode == 0,
          f"quick_validate.py failed: {result.stderr.strip() or result.stdout.strip()}")


def check_schemas():
    schemas = ["run-manifest.schema.json", "weekly-packet.schema.json"]
    for s in schemas:
        path = os.path.join(SKILL_DIR, "schemas", s)
        data = read_json(path)
        check(f"schema_{s}", data is not None, "file missing or invalid JSON")


def check_references():
    refs = ["repo-profiles.md", "evidence-contract.md"]
    for r in refs:
        path = os.path.join(SKILL_DIR, "references", r)
        check(f"reference_{r}", os.path.exists(path), "file missing")


def check_chain_architecture(content):
    check("chain_stage1", "ecc-niche-positioning-audit" in content, "Stage 1 skill missing")
    check("chain_stage2", "ecc-hormozi-funnel" in content, "Stage 2 skill missing")
    check("chain_stage3", "ecc-growth-experiment-loop" in content, "Stage 3 skill missing")
    check("chain_closed_loop_excluded", "following-week" in content.lower() or "NOT in" in content,
          "ecc-closed-loop-analytics exclusion not documented")


def check_behavioral_rules(content):
    check("rule_draft_only", "draft-only" in content, "draft-only mode not mentioned")
    check("rule_no_external_writes", "no external writes" in content.lower() or "No external writes" in content,
          "no external writes rule missing")
    check("rule_no_fabricated", "fabricated" in content.lower(), "no fabricated claims rule missing")
    check("rule_unavailable", "unavailable" in content.lower(), "unavailable handling not mentioned")
    check("rule_evidence_traceability", "evidence" in content.lower(), "evidence traceability not mentioned")


def check_repo_profiles(content):
    # Check in the references file, not just SKILL.md
    repo_profiles_path = os.path.join(SKILL_DIR, "references", "repo-profiles.md")
    profiles_content = read_file(repo_profiles_path) or ""
    combined = content + "\n" + profiles_content
    repos = ["Career", "Canada Energy", "codex-ecc-custom", "Strategic Intelligence", "Avalanche"]
    for repo in repos:
        check(f"repo_profile_{repo}", repo in combined, f"repo profile for {repo} missing")


def check_agents_file():
    path = os.path.join(SKILL_DIR, "agents", "openai.yaml")
    check("agents_openai_yaml", os.path.exists(path), "agents/openai.yaml missing")


def check_output_constraints(content):
    check("output_1_offer", "1 offer" in content or "offer_count" in content, "1 offer constraint missing")
    check("output_3_hooks", "3 hooks" in content or "hook_count" in content, "3 hooks constraint missing")
    check("output_7_days", "7-day" in content or "7 days" in content or "content_days" in content,
          "7-day content constraint missing")
    check("output_3_fixes", "3 funnel fixes" in content or "funnel_fixes" in content,
          "3 funnel fixes constraint missing")
    check("output_1_experiment", "1 experiment" in content or "experiment_count" in content,
          "1 experiment constraint missing")


def check_runner():
    """Verify the deterministic runner exists and produces valid output in dry-run mode."""
    import tempfile
    runner = os.path.join(SKILL_DIR, "scripts", "run_weekly_marketing_flywheel.py")
    check("runner_exists", os.path.exists(runner), "run_weekly_marketing_flywheel.py not found")

    if not os.path.exists(runner):
        return

    # Run in dry-run mode with the test positioning export
    hormozi_test_export = os.path.join(
        os.path.dirname(SKILL_DIR), "ecc-hormozi-funnel", "tests", "positioning-export-test.json"
    )
    result = subprocess.run(
        [sys.executable, runner,
         "--repository", "/tmp/test-repo",
         "--objective", "validator test",
         "--week", "2026-07-20",
         "--mode", "dry-run",
         "--positioning-export", hormozi_test_export],
        capture_output=True, text=True, cwd=os.path.dirname(SKILL_DIR),
    )
    check("runner_dry_run_exit", result.returncode == 0,
          f"Runner failed: {result.stderr.strip()[:200]}")

    # Find output directory from stdout
    output_dir = None
    for line in result.stdout.split("\n"):
        if "Output directory:" in line:
            output_dir = line.split("Output directory:")[1].strip()
            break

    if output_dir and os.path.isdir(output_dir):
        # Check for required output files
        required_files = [
            "run-manifest.json", "offer.json", "hooks.json",
            "content-calendar.json", "funnel-audit.json", "proof-library.json",
            "evidence-ledger.json", "approval-required.md", "hashes.json",
        ]
        for f in required_files:
            check(f"runner_output_{f}", os.path.exists(os.path.join(output_dir, f)),
                  f"{f} not produced by runner")

        # Validate manifest against schema
        try:
            import jsonschema
            manifest_path = os.path.join(output_dir, "run-manifest.json")
            schema_path = os.path.join(SKILL_DIR, "schemas", "run-manifest.schema.json")
            if os.path.exists(manifest_path) and os.path.exists(schema_path):
                with open(manifest_path) as fh:
                    manifest = json.load(fh)
                with open(schema_path) as fh:
                    schema = json.load(fh)
                try:
                    jsonschema.validate(instance=manifest, schema=schema)
                    check("runner_manifest_schema", True)
                except jsonschema.ValidationError as e:
                    check("runner_manifest_schema", False, e.message)
        except ImportError:
            check("runner_manifest_schema", False, "jsonschema not installed")
    else:
        check("runner_output_dir", False, "Could not find output directory")


def check_runner_stops_without_input():
    """Verify the runner stops explicitly when no positioning export is provided."""
    runner = os.path.join(SKILL_DIR, "scripts", "run_weekly_marketing_flywheel.py")
    if not os.path.exists(runner):
        return

    result = subprocess.run(
        [sys.executable, runner,
         "--repository", "/tmp/test-repo",
         "--objective", "stop test",
         "--week", "2026-07-20",
         "--mode", "dry-run"],
        capture_output=True, text=True, cwd=os.path.dirname(SKILL_DIR),
    )
    check("runner_stops_without_input", "STOPPED" in result.stdout,
          "Runner should stop when Stage 1 is unavailable")


def main():
    print("=== ecc-weekly-marketing-flywheel Validator ===\n")

    content = read_file(os.path.join(SKILL_DIR, "SKILL.md"))
    if not content:
        print("FATAL: SKILL.md not found")
        sys.exit(1)

    check_frontmatter(content)
    check_quick_validate()
    check_schemas()
    check_references()
    check_chain_architecture(content)
    check_behavioral_rules(content)
    check_repo_profiles(content)
    check_agents_file()
    check_output_constraints(content)
    check_runner()
    check_runner_stops_without_input()

    # Run scenarios
    scenario_dir = os.path.join(SKILL_DIR, "tests", "scenarios")
    if os.path.isdir(scenario_dir):
        scenarios = [f for f in os.listdir(scenario_dir) if f.endswith(".py")]
        for scenario in sorted(scenarios):
            result = subprocess.run(
                [sys.executable, os.path.join(scenario_dir, scenario)],
                capture_output=True, text=True,
            )
            check(f"scenario_{scenario}", result.returncode == 0,
                  f"scenario failed: {result.stderr.strip()[:200]}")

    print(f"\n{'ALL CHECKS PASSED' if checks_failed == 0 else f'{checks_failed} CHECK(S) FAILED'}")
    if checks_failed > 0:
        print(f"Failures: {', '.join(failures)}")
    sys.exit(0 if checks_failed == 0 else 1)


if __name__ == "__main__":
    main()
