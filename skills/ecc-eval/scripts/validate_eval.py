#!/usr/bin/env python3
"""Validator for ecc-eval skill.

Checks frontmatter, schemas, references, runner script, CLI features,
SKILL.md content, agents file, claude-plugin, and validation rules.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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
    check("frontmatter_name", "name: ecc-eval" in fm, "name field missing or wrong")
    check("frontmatter_description", "description:" in fm, "description field missing")
    check("frontmatter_triggers", "TRIGGER" in fm, "trigger phrases missing")
    check("frontmatter_anti_triggers", "DO NOT TRIGGER" in fm, "anti-trigger missing")
    check("frontmatter_no_implicit", "no_implicit" not in fm.lower(), "no_implicit should not be in frontmatter")


def check_schemas():
    schemas = ["eval-definition.schema.json", "eval-result.schema.json"]
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

    # Validate eval-definition schema is valid JSON Schema
    schema_path = os.path.join(SKILL_DIR, "schemas", "eval-definition.schema.json")
    schema = read_json(schema_path)
    if schema:
        try:
            jsonschema.Draft202012Validator.check_schema(schema)
            check("jsonschema_eval_definition_valid", True)
        except Exception as e:
            check("jsonschema_eval_definition_valid", False, str(e))

    # Validate eval-result schema is valid JSON Schema
    schema_path = os.path.join(SKILL_DIR, "schemas", "eval-result.schema.json")
    schema = read_json(schema_path)
    if schema:
        try:
            jsonschema.Draft202012Validator.check_schema(schema)
            check("jsonschema_eval_result_valid", True)
        except Exception as e:
            check("jsonschema_eval_result_valid", False, str(e))


def check_references():
    refs = ["eval-templates.md", "ci-examples.md", "cli-flags.md"]
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
        check("agents_has_invocation", "invocation:" in content,
              "invocation block missing from openai.yaml")
        check("agents_has_runner", "run_eval.sh" in content,
              "run_eval.sh reference missing from openai.yaml")


def check_claude_plugin():
    plugin_path = os.path.join(SKILL_DIR, ".claude-plugin", "plugin.json")
    marketplace_path = os.path.join(SKILL_DIR, ".claude-plugin", "marketplace.json")
    check("claude_plugin_exists", os.path.exists(plugin_path), ".claude-plugin/plugin.json missing")
    check("claude_marketplace_exists", os.path.exists(marketplace_path), ".claude-plugin/marketplace.json missing")
    if os.path.exists(plugin_path):
        data = read_json(plugin_path)
        check("claude_plugin_valid_json", data is not None, "plugin.json is invalid JSON")
        if data:
            check("claude_plugin_name", data.get("name") == "ecc-eval", f"plugin name mismatch: {data.get('name')}")
    if os.path.exists(marketplace_path):
        data = read_json(marketplace_path)
        check("claude_marketplace_valid_json", data is not None, "marketplace.json is invalid JSON")


def check_validation_rules():
    rules_path = os.path.join(SKILL_DIR, "validation-rules.json")
    check("validation_rules_exists", os.path.exists(rules_path), "validation-rules.json missing")
    if os.path.exists(rules_path):
        data = read_json(rules_path)
        check("validation_rules_valid_json", data is not None, "validation-rules.json is invalid JSON")
        if data:
            rules = data.get("rules", {})
            check("validation_rules_has_schema_version", "schema_version" in data, "schema_version missing")
            check("validation_rules_has_required_schemas", "required_schemas" in rules, "required_schemas missing")
            check("validation_rules_has_platform_mentions", "required_platform_mentions" in rules, "required_platform_mentions missing")
            check("validation_rules_includes_autogravity", "Autogravity" in rules.get("required_platform_mentions", []), "Autogravity not in required_platform_mentions")


def check_no_hardcoded_paths():
    """Check all skill files for hardcoded /Users/sanjayb paths and $(git root) anti-pattern."""
    files_to_check = [
        os.path.join(SKILL_DIR, "SKILL.md"),
        os.path.join(SKILL_DIR, "agents", "openai.yaml"),
        os.path.join(SKILL_DIR, "references", "ci-examples.md"),
        os.path.join(SKILL_DIR, "references", "cli-flags.md"),
        os.path.join(SKILL_DIR, "references", "eval-templates.md"),
    ]
    for fpath in files_to_check:
        content = read_file(fpath)
        if content is None:
            continue
        rel_path = os.path.relpath(fpath, SKILL_DIR)
        check(f"no_hardcoded_home_{rel_path}", "/Users/sanjayb/" not in content,
              f"Hardcoded /Users/sanjayb/ path found in {rel_path}")
        # Allow $(git root) when preceded by "No " (checking for the anti-pattern, not using it)
        import re as re_mod
        git_root_uses = [m for m in re_mod.finditer(r'\$\(git root\)', content)
                         if not content[max(0, m.start()-3):m.start()].strip().lower().endswith("no")]
        check(f"no_git_root_{rel_path}", len(git_root_uses) == 0,
              f"$(git root) anti-pattern found in {rel_path}")


def check_runner_script():
    runner_path = os.path.join(SKILL_DIR, "scripts", "run_eval.sh")
    check("runner_script_exists", os.path.exists(runner_path), "scripts/run_eval.sh missing")
    if not os.path.exists(runner_path):
        return
    content = read_file(runner_path)

    check("runner_has_codex_exec", "codex exec" in content, "codex exec backend missing")
    check("runner_has_claude_fallback", "claude -p" in content, "claude -p fallback missing")
    check("runner_has_ephemeral", "--ephemeral" in content, "ephemeral flag missing")
    check("runner_has_sandbox", "--sandbox" in content or "-s " in content, "sandbox flag missing")
    check("runner_has_json", "--json" in content, "json flag missing")
    check("runner_has_batch", "--batch" in content, "batch mode missing")
    check("runner_has_model", "--model" in content, "model flag missing")
    check("runner_has_output", "--output" in content or "-o " in content, "output flag missing")
    check("runner_has_backend", "--backend" in content, "backend flag missing")
    check("runner_has_eval_dir", "EVAL_DIR" in content, "EVAL_DIR env var support missing")
    check("runner_has_ignore_config", "--ignore-config" in content, "ignore-config flag missing")
    check("runner_has_ignore_rules", "--ignore-rules" in content, "ignore-rules flag missing")
    check("runner_has_skip_git", "--skip-git-check" in content, "skip-git-check flag missing")
    check("runner_has_workdir", "--workdir" in content, "workdir flag missing")
    check("runner_has_no_ephemeral", "--no-ephemeral" in content, "no-ephemeral flag missing")
    check("runner_has_extra_args", "--extra-args" in content, "extra-args flag missing")
    check("runner_has_help", "--help" in content, "help flag missing")
    check("runner_is_executable", os.access(runner_path, os.X_OK), "run_eval.sh is not executable")
    check("runner_has_backend_detection", "detect_backend" in content, "backend detection function missing")
    check("runner_has_batch_mode", "run_batch" in content, "batch mode function missing")
    check("runner_has_single_mode", "run_single" in content, "single mode function missing")


def check_skill_md_content(content):
    check("skill_has_when_to_use", "## When to Use" in content, "When to Use section missing")
    check("skill_has_how_it_works", "## How It Works" in content, "How It Works section missing")
    check("skill_has_eval_types", "## Eval Types" in content, "Eval Types section missing")
    check("skill_has_metrics", "## Metrics" in content, "Metrics section missing")
    check("skill_has_eval_workflow", "## Eval Workflow" in content, "Eval Workflow section missing")
    check("skill_has_ci_integration", "## CI Integration" in content, "CI Integration section missing")
    check("skill_has_dependency_gating", "## Dependency Gating" in content, "Dependency Gating section missing")
    check("skill_has_auto_revocation", "## Auto-Revocation" in content, "Auto-Revocation section missing")
    check("skill_has_backend_detection", "## Backend Auto-Detection" in content, "Backend Auto-Detection section missing")
    check("skill_has_platform_compat", "## Platform Compatibility" in content, "Platform Compatibility missing")
    check("skill_has_path_resolution", "## Path Resolution" in content, "Path Resolution section missing")
    check("skill_has_portability_note", "## Portability Note" in content, "Portability Note section missing")
    check("skill_has_top10", "## Top 10 Use Cases" in content, "Top 10 Use Cases section missing")
    check("skill_mention_codex", "Codex" in content, "Codex not mentioned")
    check("skill_mention_claude", "Claude Code" in content, "Claude Code not mentioned")
    check("skill_mention_windsurf", "Windsurf" in content, "Windsurf not mentioned")
    check("skill_mention_devin", "Devin" in content, "Devin not mentioned")
    check("skill_mention_autogravity", "Autogravity" in content, "Autogravity not mentioned")
    check("skill_mention_pass_at_k", "pass@k" in content or "pass@k" in content, "pass@k metrics missing")
    check("skill_mention_codex_exec", "codex exec" in content, "codex exec not mentioned")
    check("skill_mention_claude_p", "claude -p" in content, "claude -p not mentioned")
    check("skill_no_hardcoded_home", "/Users/sanjayb/" not in content,
          "Hardcoded /Users/sanjayb/ path found in SKILL.md")
    check("skill_no_git_root", "$(git root)" not in content,
          "$(git root) anti-pattern found in SKILL.md")


def check_scenarios():
    """Run all test scenarios in tests/scenarios/."""
    scenarios_dir = os.path.join(SKILL_DIR, "tests", "scenarios")
    if not os.path.isdir(scenarios_dir):
        check("scenarios_dir_exists", False, "tests/scenarios/ directory missing")
        return
    scenarios = sorted([f for f in os.listdir(scenarios_dir) if f.endswith(".py")])
    check("scenarios_found", len(scenarios) > 0, "No .py scenario files found")
    for scenario in scenarios:
        path = os.path.join(scenarios_dir, scenario)
        try:
            result = subprocess.run(
                [sys.executable, path],
                capture_output=True, text=True, timeout=30,
                cwd=PROJECT_ROOT,
            )
            check(f"scenario_{scenario.replace('.py', '')}",
                  result.returncode == 0,
                  result.stderr[:100] if result.returncode else "")
        except subprocess.TimeoutExpired:
            check(f"scenario_{scenario.replace('.py', '')}", False, "timed out")
        except Exception as e:
            check(f"scenario_{scenario.replace('.py', '')}", False, str(e))


def main():
    print("=== ecc-eval Validator ===\n")

    content = read_file(os.path.join(SKILL_DIR, "SKILL.md"))
    if not content:
        print("FATAL: SKILL.md not found")
        sys.exit(1)

    check_frontmatter(content)
    check_schemas()
    check_jsonschema_validation()
    check_references()
    check_agents_file()
    check_claude_plugin()
    check_validation_rules()
    check_runner_script()
    check_skill_md_content(content)
    check_no_hardcoded_paths()
    check_scenarios()

    print(f"\n{'ALL CHECKS PASSED' if checks_failed == 0 else f'{checks_failed} CHECK(S) FAILED'}")
    if checks_failed > 0:
        print(f"Failures: {', '.join(failures)}")
    sys.exit(0 if checks_failed == 0 else 1)


if __name__ == "__main__":
    main()
