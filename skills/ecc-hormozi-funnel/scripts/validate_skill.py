#!/usr/bin/env python3
"""Validator for ecc-hormozi-funnel skill.

Checks:
  1. SKILL.md frontmatter (name, description, triggers, anti-triggers)
  2. SKILL.md body length (<= 1200 lines)
  3. All 4 schemas exist and are valid JSON
  4. Both references exist
  5. 5 prompts present in SKILL.md
  6. Tool truth rules count (>= 16)
  7. Value Equation formula present
  8. Hook formulas present (pain, desire, proof, curiosity)
  9. Proof density threshold mentioned (>= 50%)
 10. Evidence citation requirement present
 11. Platform formatting table present
 12. Integration contract reference present
 13. Methodology provenance reference present
 14. Offer schema validates against test fixture
 15. Hook schema validates against test fixture
"""

import json
import os
import re
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


def check_body_length(content):
    lines = content.split('\n')
    check("body_lines", len(lines) <= 1200, f"{len(lines)}/1200")


def check_schemas():
    schemas = [
        "offer.schema.json",
        "hook.schema.json",
        "content-calendar.schema.json",
        "funnel-audit.schema.json",
    ]
    for s in schemas:
        path = os.path.join(SKILL_DIR, "schemas", s)
        data = read_json(path)
        check(f"schema_{s}", data is not None, "file missing or invalid JSON")


def check_references():
    refs = ["integration-contract.md", "methodology-provenance.md"]
    for r in refs:
        path = os.path.join(SKILL_DIR, "references", r)
        check(f"reference_{r}", os.path.exists(path), "file missing")


def check_prompts(content):
    prompts = [
        "Prompt 1: Content Batching",
        "Prompt 2: Value Equation",
        "Prompt 3: Hormozi Hook",
        "Prompt 4: Hormozi Authority",
        "Prompt 5: Funnel Audit",
    ]
    for p in prompts:
        check(f"prompt_{p}", p in content, "prompt section missing")


def check_tool_truth(content):
    section_match = re.search(r'## Tool Truth(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if not section_match:
        check("tool_truth_section", False, "Tool Truth section missing")
        return
    check("tool_truth_section", True)
    tt_section = section_match.group(1)
    rules = re.findall(r'^\d+\.\s', tt_section, re.MULTILINE)
    check("tool_truth_rules", len(rules) >= 16, f"{len(rules)}/16 rules found")


def check_value_equation(content):
    check("value_equation_formula", "Value = (Dream Outcome" in content, "Value Equation formula missing")
    check("value_equation_scoring", "Dream Outcome" in content and "Likelihood" in content
          and "Time Delay" in content and "Effort" in content, "4 dimensions missing")


def check_hook_formulas(content):
    formulas = ["pain", "desire", "proof", "curiosity"]
    for f in formulas:
        check(f"hook_formula_{f}", f in content, f"hook formula '{f}' missing")


def check_proof_density(content):
    check("proof_density_threshold", "50%" in content or "0.50" in content,
          "proof density threshold missing")


def check_evidence_citation(content):
    check("evidence_citation_req", "evidence id" in content.lower() or "evidence_citations" in content,
          "evidence citation requirement missing")


def check_platform_table(content):
    platforms = ["Twitter", "Instagram", "TikTok", "LinkedIn"]
    for p in platforms:
        check(f"platform_{p}", p in content, f"platform '{p}' missing")


def check_schema_instance_validation():
    offer_path = os.path.join(SKILL_DIR, "tests", "offer_test.json")
    hook_path = os.path.join(SKILL_DIR, "tests", "hook_test.json")
    offer_data = read_json(offer_path)
    hook_data = read_json(hook_path)
    check("offer_test_fixture", offer_data is not None, "offer_test.json missing or invalid")
    check("hook_test_fixture", hook_data is not None, "hook_test.json missing or invalid")

    if offer_data:
        check("offer_test_schema_version", offer_data.get("schema_version") == "v8",
              f"expected v8, got {offer_data.get('schema_version')}")
        check("offer_test_has_scores", "value_equation_scores" in offer_data,
              "value_equation_scores missing")
        scores = offer_data.get("value_equation_scores", {})
        if scores:
            check("offer_test_composite", "composite" in scores, "composite score missing")

    if hook_data:
        check("hook_test_schema_version", hook_data.get("schema_version") == "v8",
              f"expected v8, got {hook_data.get('schema_version')}")
        check("hook_test_formula_type", hook_data.get("formula_type") in
              ["pain", "desire", "proof", "curiosity"], "invalid formula_type")
        check("hook_test_ranking", "ranking_score" in hook_data, "ranking_score missing")


def main():
    print("=== ecc-hormozi-funnel Validator ===\n")

    content = read_skill_md()
    if not content:
        print("FATAL: SKILL.md not found")
        sys.exit(1)

    check_frontmatter(content)
    check_body_length(content)
    check_schemas()
    check_references()
    check_prompts(content)
    check_tool_truth(content)
    check_value_equation(content)
    check_hook_formulas(content)
    check_proof_density(content)
    check_evidence_citation(content)
    check_platform_table(content)
    check_schema_instance_validation()

    print(f"\n{'ALL CHECKS PASSED' if checks_failed == 0 else f'{checks_failed} CHECK(S) FAILED'}")
    if checks_failed > 0:
        print(f"Failures: {', '.join(failures)}")
    sys.exit(0 if checks_failed == 0 else 1)


if __name__ == "__main__":
    main()
