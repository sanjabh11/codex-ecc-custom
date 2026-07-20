#!/usr/bin/env python3
"""Validator for ecc-hormozi-funnel skill v8.1.

Checks frontmatter, body length, schemas, references, prompts, tool truth,
value equation, hook formulas, proof density, evidence citations, platforms,
scope modes, advisor checkpoints, adversarial review, decision confidence,
composite cap, agents file, validation-rules.json, and test fixtures.
"""

import json
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_PATH = os.path.join(SKILL_DIR, "validation-rules.json")

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


def load_rules():
    if not os.path.exists(RULES_PATH):
        return None
    with open(RULES_PATH, "r") as f:
        return json.load(f)


def read_skill_md():
    path = os.path.join(SKILL_DIR, "SKILL.md")
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
    check("frontmatter_name", "name: ecc-hormozi-funnel" in fm, "name field missing or wrong")
    check("frontmatter_description", "description:" in fm, "description field missing")
    check("frontmatter_triggers", "TRIGGER" in fm, "trigger phrases missing")
    check("frontmatter_anti_triggers", "DO NOT TRIGGER" in fm, "anti-trigger missing")
    check("frontmatter_no_implicit", "allow_implicit_invocation" not in fm, "allow_implicit_invocation must NOT be in SKILL.md frontmatter (moved to agents/openai.yaml)")


def check_body_length(content, max_lines):
    lines = content.split('\n')
    check("body_lines", len(lines) <= max_lines, f"{len(lines)}/{max_lines}")


def check_schemas(expected):
    for s in expected:
        path = os.path.join(SKILL_DIR, "schemas", s)
        data = read_json(path)
        check(f"schema_{s}", data is not None, "file missing or invalid JSON")


def check_references(expected):
    for r in expected:
        path = os.path.join(SKILL_DIR, "references", r)
        check(f"reference_{r}", os.path.exists(path), "file missing")


def check_prompts(content, expected):
    for p in expected:
        check(f"prompt_{p}", p in content, "prompt section missing")


def check_tool_truth(content, expected_count):
    section_match = re.search(r'## Tool Truth\n(.*?)(?=\n## [A-Z]|\Z)', content, re.DOTALL)
    if not section_match:
        check("tool_truth_section", False, "Tool Truth section missing")
        return
    check("tool_truth_section", True)
    tt_section = section_match.group(1)
    rules = re.findall(r'^\d+\.\s', tt_section, re.MULTILINE)
    check("tool_truth_rules", len(rules) >= expected_count, f"{len(rules)}/{expected_count} rules found")


def check_value_equation(content):
    check("value_equation_formula", "Value = (Dream Outcome" in content, "Value Equation formula missing")
    check("value_equation_scoring", all(d in content for d in
          ["Dream Outcome", "Likelihood", "Time Delay", "Effort"]), "4 dimensions missing")
    check("value_equation_cap", "capped at 100" in content.lower() or "cap at 100" in content.lower(),
          "composite cap missing")


def check_hook_formulas(content, formulas):
    for f in formulas:
        check(f"hook_formula_{f}", f in content, f"hook formula '{f}' missing")


def check_proof_density(content):
    check("proof_density_threshold", "50%" in content or "0.50" in content,
          "proof density threshold missing")


def check_evidence_citation(content):
    check("evidence_citation_req", "evidence id" in content.lower() or "evidence_citations" in content,
          "evidence citation requirement missing")


def check_platforms(content, expected):
    for p in expected:
        check(f"platform_{p}", p in content, f"platform '{p}' missing")


def check_scope_modes(content, expected):
    for m in expected:
        check(f"scope_mode_{m}", m in content, f"scope mode '{m}' missing")


def check_advisor(content):
    check("advisor_checkpoints", "ecc-advisor" in content, "advisor integration missing")
    check("advisor_offer_ranking", "offer" in content.lower() and "advisor" in content.lower(),
          "advisor at offer ranking missing")
    check("advisor_hook_rewriting", "hook" in content.lower() and "advisor" in content.lower(),
          "advisor at hook rewriting missing")
    check("advisor_funnel_audit", "funnel audit" in content.lower() and "advisor" in content.lower(),
          "advisor at funnel audit missing")


def check_adversarial(content):
    passes = ["skeptic", "missing-perspective", "contrarian"]
    for p in passes:
        check(f"adversarial_{p}", p in content.lower(), f"adversarial pass '{p}' missing")


def check_decision_confidence(content):
    check("decision_confidence_section", "Decision Confidence" in content,
          "decision confidence section missing")
    check("decision_confidence_formula", "evidence_quality" in content and "source_coverage" in content
          and "adversarial_survival" in content and "advisor_confirmed" in content,
          "4 subscores missing")


def check_backing_skills(content):
    check("backing_skills", "Backing Skills" in content, "backing skills section missing")
    check("backing_advisor", "ecc-advisor" in content, "ecc-advisor backing skill missing")


def check_platform_compat(content):
    check("platform_compat", "Platform Compatibility" in content, "platform compatibility section missing")


def check_agents_file():
    path = os.path.join(SKILL_DIR, "agents", "openai.yaml")
    check("agents_openai_yaml", os.path.exists(path), "agents/openai.yaml missing")


def check_validation_rules(rules):
    check("validation_rules_json", rules is not None, "validation-rules.json missing or invalid")
    if rules:
        check("validation_rules_version", rules.get("schema_version") == "v8",
              f"expected v8, got {rules.get('schema_version')}")
        check("validation_rules_tool_truth", rules.get("expected_tool_truth_rules", 0) >= 20,
              f"expected >= 20, got {rules.get('expected_tool_truth_rules')}")


def check_test_fixtures():
    fixtures = ["offer_test.json", "hook_test.json", "content_calendar_test.json", "funnel_audit_test.json"]
    for fx in fixtures:
        path = os.path.join(SKILL_DIR, "tests", fx)
        data = read_json(path)
        check(f"fixture_{fx}", data is not None, "file missing or invalid JSON")
        if data:
            check(f"fixture_{fx}_version", data.get("schema_version") == "v8",
                  f"expected v8, got {data.get('schema_version')}")

    cal = read_json(os.path.join(SKILL_DIR, "tests", "content_calendar_test.json"))
    if cal:
        density = cal.get("proof_density", 0)
        check("fixture_cal_proof_density", density >= 0.50, f"proof_density={density}, expected >= 0.50")
        entries = cal.get("entries", [])
        with_proof = sum(1 for e in entries if e.get("has_proof"))
        actual_density = with_proof / len(entries) if entries else 0
        check("fixture_cal_density_match", abs(actual_density - density) < 0.01,
              f"stated={density}, actual={actual_density:.2f}")

    fa = read_json(os.path.join(SKILL_DIR, "tests", "funnel_audit_test.json"))
    if fa:
        check("fixture_fa_fixes", len(fa.get("fixes", [])) >= 3, "expected >= 3 fixes")
        check("fixture_fa_evidence", len(fa.get("evidence_citations", [])) >= 1,
              "expected >= 1 evidence citation")


def check_generate_scripts():
    fixtures_path = os.path.join(SKILL_DIR, "scripts", "generate_fixtures.py")
    weekly_path = os.path.join(SKILL_DIR, "scripts", "generate_weekly_artifacts.py")
    check("generate_fixtures_exists", os.path.exists(fixtures_path), "generate_fixtures.py missing")
    check("generate_weekly_exists", os.path.exists(weekly_path), "generate_weekly_artifacts.py missing")


def check_quick_validate():
    """Run Codex quick_validate.py as a subprocess."""
    import subprocess
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


def check_jsonschema_validation():
    """Validate test fixtures against their schemas using jsonschema."""
    try:
        import jsonschema
    except ImportError:
        check("jsonschema_available", False, "jsonschema not installed")
        return
    check("jsonschema_available", True)

    schema_map = {
        "offer_test.json": "offer.schema.json",
        "hook_test.json": "hook.schema.json",
        "content_calendar_test.json": "content-calendar.schema.json",
        "funnel_audit_test.json": "funnel-audit.schema.json",
    }
    for fixture_name, schema_name in schema_map.items():
        fixture_path = os.path.join(SKILL_DIR, "tests", fixture_name)
        schema_path = os.path.join(SKILL_DIR, "schemas", schema_name)
        if not os.path.exists(fixture_path) or not os.path.exists(schema_path):
            check(f"jsonschema_{fixture_name}", False, "fixture or schema missing")
            continue
        fixture = read_json(fixture_path)
        schema = read_json(schema_path)
        if not fixture or not schema:
            check(f"jsonschema_{fixture_name}", False, "invalid JSON")
            continue
        try:
            jsonschema.validate(instance=fixture, schema=schema)
            check(f"jsonschema_{fixture_name}", True)
        except jsonschema.ValidationError as e:
            check(f"jsonschema_{fixture_name}", False, str(e.message))


def check_weekly_mode(content, rules):
    """Verify weekly mode is present and output constraints are defined."""
    check("weekly_mode_in_content", "weekly" in content.lower(), "weekly mode not mentioned in SKILL.md")
    if rules:
        weekly_outputs = rules.get("weekly_mode_outputs")
        check("weekly_mode_outputs_defined", weekly_outputs is not None, "weekly_mode_outputs not in validation-rules.json")
        if weekly_outputs:
            check("weekly_offer_count", weekly_outputs.get("offer") == 1, f"expected 1 offer, got {weekly_outputs.get('offer')}")
            check("weekly_hook_count", weekly_outputs.get("hooks") == 3, f"expected 3 hooks, got {weekly_outputs.get('hooks')}")
            check("weekly_content_days", weekly_outputs.get("content_days") == 7, f"expected 7 days, got {weekly_outputs.get('content_days')}")
        check("reject_synthetic_claims", rules.get("reject_synthetic_economic_claims") is True,
              "reject_synthetic_economic_claims not set to true")


def main():
    print("=== ecc-hormozi-funnel Validator v8.1 ===\n")

    rules = load_rules()
    content = read_skill_md()
    if not content:
        print("FATAL: SKILL.md not found")
        sys.exit(1)

    max_lines = rules.get("max_body_lines", 1200) if rules else 1200
    expected_schemas = rules.get("expected_schemas", []) if rules else []
    expected_refs = rules.get("expected_references", []) if rules else []
    expected_prompts = rules.get("expected_prompts", []) if rules else []
    expected_formulas = rules.get("expected_hook_formulas", []) if rules else []
    expected_platforms = rules.get("expected_platforms", []) if rules else []
    expected_modes = rules.get("expected_scope_modes", []) if rules else []
    expected_tt_rules = rules.get("expected_tool_truth_rules", 20) if rules else 20

    check_frontmatter(content)
    check_body_length(content, max_lines)
    check_schemas(expected_schemas)
    check_references(expected_refs)
    check_prompts(content, expected_prompts)
    check_tool_truth(content, expected_tt_rules)
    check_value_equation(content)
    check_hook_formulas(content, expected_formulas)
    check_proof_density(content)
    check_evidence_citation(content)
    check_platforms(content, expected_platforms)
    check_scope_modes(content, expected_modes)
    check_advisor(content)
    check_adversarial(content)
    check_decision_confidence(content)
    check_backing_skills(content)
    check_platform_compat(content)
    check_agents_file()
    check_validation_rules(rules)
    check_test_fixtures()
    check_generate_scripts()
    check_quick_validate()
    check_jsonschema_validation()
    check_weekly_mode(content, rules)

    print(f"\n{'ALL CHECKS PASSED' if checks_failed == 0 else f'{checks_failed} CHECK(S) FAILED'}")
    if checks_failed > 0:
        print(f"Failures: {', '.join(failures)}")
    sys.exit(0 if checks_failed == 0 else 1)


if __name__ == "__main__":
    main()
