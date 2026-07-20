#!/usr/bin/env python3
"""Validator for ecc-advisor skill.

Checks frontmatter, schemas, references, CLI functionality, config,
state management, backend detection, and scenario coverage.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FABLE_DIR = os.path.join(PROJECT_ROOT, "fable")

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
    check("frontmatter_name", "name: ecc-advisor" in fm, "name field missing or wrong")
    check("frontmatter_description", "description:" in fm, "description field missing")
    check("frontmatter_triggers", "TRIGGER" in fm, "trigger phrases missing")
    check("frontmatter_anti_triggers", "DO NOT TRIGGER" in fm, "anti-trigger missing")
    check("frontmatter_no_implicit", "allow_implicit_invocation" not in fm,
          "allow_implicit_invocation must NOT be in SKILL.md frontmatter")


def check_quick_validate():
    quick_validate_path = os.path.expanduser(
        "~/.codex/skills/.system/skill-creator/scripts/quick_validate.py"
    )
    if not os.path.exists(quick_validate_path):
        check("quick_validate_available", False, f"quick_validate.py not found")
        return
    result = subprocess.run(
        [sys.executable, quick_validate_path, SKILL_DIR],
        capture_output=True, text=True,
    )
    check("quick_validate_pass", result.returncode == 0,
          f"quick_validate.py failed: {result.stderr.strip() or result.stdout.strip()}")


def check_schemas():
    schemas = ["advisor-config.schema.json", "advisor-state.schema.json", "advisor-response.schema.json"]
    for s in schemas:
        path = os.path.join(SKILL_DIR, "schemas", s)
        data = read_json(path)
        check(f"schema_{s}", data is not None, "file missing or invalid JSON")


def check_jsonschema_validation():
    try:
        import jsonschema
    except ImportError:
        check("jsonschema_available", False, "jsonschema not installed")
        return
    check("jsonschema_available", True)

    # Validate advisor_config.json
    config_path = os.path.join(FABLE_DIR, "advisor_config.json")
    config_schema_path = os.path.join(SKILL_DIR, "schemas", "advisor-config.schema.json")
    config = read_json(config_path)
    config_schema = read_json(config_schema_path)
    if config and config_schema:
        try:
            jsonschema.validate(instance=config, schema=config_schema)
            check("jsonschema_config", True)
        except jsonschema.ValidationError as e:
            check("jsonschema_config", False, str(e.message))

    # Validate advisor_state.json
    state_path = os.path.join(FABLE_DIR, "advisor_state.json")
    state_schema_path = os.path.join(SKILL_DIR, "schemas", "advisor-state.schema.json")
    state = read_json(state_path)
    state_schema = read_json(state_schema_path)
    if state and state_schema:
        try:
            jsonschema.validate(instance=state, schema=state_schema)
            check("jsonschema_state", True)
        except jsonschema.ValidationError as e:
            check("jsonschema_state", False, str(e.message))


def check_references():
    refs = ["backend-status.md", "cli-flags.md"]
    for r in refs:
        path = os.path.join(SKILL_DIR, "references", r)
        check(f"reference_{r}", os.path.exists(path), "file missing")


def check_agents_file():
    path = os.path.join(SKILL_DIR, "agents", "openai.yaml")
    check("agents_openai_yaml", os.path.exists(path), "agents/openai.yaml missing")
    if os.path.exists(path):
        content = read_file(path)
        check("agents_has_implicit", "allow_implicit_invocation: true" in content,
              "allow_implicit_invocation should be in agents/openai.yaml")


def check_cli_script():
    cli_path = os.path.join(FABLE_DIR, "advisor_cli.py")
    check("cli_script_exists", os.path.exists(cli_path), "advisor_cli.py missing")
    if not os.path.exists(cli_path):
        return
    content = read_file(cli_path)

    # Check for required functions
    check("cli_has_load_config", "def load_config" in content, "load_config missing")
    check("cli_has_load_state", "def load_state" in content, "load_state missing")
    check("cli_has_save_state", "def save_state" in content, "save_state missing")
    check("cli_has_reset_state", "def reset_state" in content, "reset_state missing")
    check("cli_has_get_advice", "def get_advice" in content, "get_advice missing")
    check("cli_has_detect_backend", "def detect_backend" in content, "detect_backend missing")

    # Check for required features
    check("cli_has_argparse", "import argparse" in content, "argparse not used")
    check("cli_has_json_output", "--json" in content, "--json flag missing")
    check("cli_has_context_file", "--context-file" in content, "--context-file flag missing")
    check("cli_has_dry_run", "--dry-run" in content, "--dry-run flag missing")
    check("cli_has_session", "--session" in content, "--session flag missing")
    check("cli_has_backend_flag", "--backend" in content, "--backend flag missing")
    check("cli_has_timeout", "signal.alarm" in content or "timeout" in content.lower(), "timeout handling missing")
    check("cli_has_retry", "retry_attempts" in content, "retry logic missing")


def check_config():
    config_path = os.path.join(FABLE_DIR, "advisor_config.json")
    config = read_json(config_path)
    check("config_exists", config is not None, "advisor_config.json missing")
    if not config:
        return
    check("config_model", config.get("advisor_model") == "grok-4.5", f"expected grok-4.5, got {config.get('advisor_model')}")
    check("config_max_calls", config.get("max_advisor_calls") == 3, f"expected 3, got {config.get('max_advisor_calls')}")
    check("config_max_tokens", config.get("max_tokens_advisor") == 2048, f"expected 2048, got {config.get('max_tokens_advisor')}")
    check("config_has_system_prompt", "advisor_system_prompt" in config, "system prompt missing")
    check("config_has_nudge_text", "nudge_text" in config, "nudge_text missing")
    check("config_has_executor_prompt", "executor_system_prompt_addition" in config, "executor prompt missing")
    check("config_has_timeout", "timeout_seconds" in config, "timeout_seconds missing")
    check("config_has_retry", "retry_attempts" in config, "retry_attempts missing")


def check_skill_md_content(content):
    check("skill_has_hard_rule", "Hard Rule" in content, "Hard Rule section missing")
    check("skill_has_cost_controls", "Cost Controls" in content, "Cost Controls section missing")
    check("skill_has_platform_compat", "Platform Compatibility" in content, "Platform Compatibility missing")
    check("skill_has_dependency_gating", "Dependency Gating" in content, "Dependency Gating missing")
    check("skill_has_backend_detection", "Backend Auto-Detection" in content, "Backend Auto-Detection section missing")
    check("skill_has_weekly_mode", "Weekly Mode Integration" in content, "Weekly Mode Integration missing")
    check("skill_has_decision_confidence", "Decision Confidence Integration" in content, "Decision Confidence Integration missing")
    check("skill_mention_cascade", "Cascade" in content, "Cascade not mentioned")
    check("skill_mention_codex", "Codex" in content, "Codex not mentioned")
    check("skill_mention_anti_gravity", "Anti-Gravity" in content, "Anti-Gravity not mentioned")
    check("skill_no_hardcoded_home", "$HOME/codex-ecc-custom" not in content,
          "Hardcoded $HOME/codex-ecc-custom path found — use relative paths")
    check("skill_mention_oauth", "OAuth" in content, "OAuth token not mentioned")


def check_runner_integration():
    runner_path = os.path.join(FABLE_DIR, "fable_runner.py")
    content = read_file(runner_path)
    check("runner_exists", content is not None, "fable_runner.py missing")
    if not content:
        return
    check("runner_has_advisor_arg", "--advisor" in content, "--advisor argument missing")
    check("runner_imports_get_advice", "get_advice" in content, "get_advice import missing")


def check_test_suite():
    test_path = os.path.join(FABLE_DIR, "test_advisor.py")
    check("test_suite_exists", os.path.exists(test_path), "test_advisor.py missing")
    if not os.path.exists(test_path):
        return

    # Run the test suite
    result = subprocess.run(
        [sys.executable, test_path],
        capture_output=True, text=True,
        cwd=PROJECT_ROOT,
    )
    check("test_suite_passes", result.returncode == 0,
          f"test_advisor.py failed: {result.stderr.strip()[:200]}")


def main():
    print("=== ecc-advisor Validator ===\n")

    content = read_file(os.path.join(SKILL_DIR, "SKILL.md"))
    if not content:
        print("FATAL: SKILL.md not found")
        sys.exit(1)

    check_frontmatter(content)
    check_quick_validate()
    check_schemas()
    check_jsonschema_validation()
    check_references()
    check_agents_file()
    check_cli_script()
    check_config()
    check_skill_md_content(content)
    check_runner_integration()
    check_test_suite()

    # Run scenarios
    scenario_dir = os.path.join(SKILL_DIR, "tests", "scenarios")
    if os.path.isdir(scenario_dir):
        scenarios = [f for f in os.listdir(scenario_dir) if f.endswith(".py")]
        for scenario in sorted(scenarios):
            result = subprocess.run(
                [sys.executable, os.path.join(scenario_dir, scenario)],
                capture_output=True, text=True,
                cwd=PROJECT_ROOT,
            )
            check(f"scenario_{scenario}", result.returncode == 0,
                  f"scenario failed: {result.stderr.strip()[:200]}")

    print(f"\n{'ALL CHECKS PASSED' if checks_failed == 0 else f'{checks_failed} CHECK(S) FAILED'}")
    if checks_failed > 0:
        print(f"Failures: {', '.join(failures)}")
    sys.exit(0 if checks_failed == 0 else 1)


if __name__ == "__main__":
    main()
