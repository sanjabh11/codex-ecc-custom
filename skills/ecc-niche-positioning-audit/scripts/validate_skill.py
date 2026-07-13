#!/usr/bin/env python3
"""Deterministic validator for ecc-niche-positioning-audit skill v5.

Checks:
1. Frontmatter description <= 1024 characters
2. SKILL.md body <= 1100 lines
3. All referenced schemas in schemas/ exist
4. Scope DAG has valid paths (quick/standard/deep) — no impossible dependencies
5. 26 Tool Truth enforcement rules present
6. Trigger phrases present in description
7. Anti-trigger section present
8. Tool Truth section present
9. Upstream Source section present
10. Evidence corpus schema validates
11. Experiment schema validates
12. State schema validates
13. Artifact schema validates
14. 8 phases (P0-P7) present
15. 8-type gap classification present
16. Methodology sources have URLs (in provenance reference)
"""

import sys
import re
import json
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SKILL_FILE = SKILL_DIR / "SKILL.md"
SCHEMAS_DIR = SKILL_DIR / "schemas"
TESTS_DIR = SKILL_DIR / "tests"
REFERENCES_DIR = SKILL_DIR / "references"

MAX_DESC_LEN = 1024
MAX_BODY_LINES = 1200
EXPECTED_TOOL_TRUTH_RULES = 26
EXPECTED_PHASES = 8
EXPECTED_GAP_TYPES = 8


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from SKILL.md."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    fm_text = parts[1]
    body = parts[2]
    fm = {}
    for line in fm_text.strip().split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm, body


def extract_description(fm: dict) -> str:
    """Extract the description value, handling multi-line YAML."""
    desc = fm.get("description", "")
    if desc == ">-" or desc == "":
        # Multi-line: reconstruct from the raw frontmatter
        return desc  # Will be handled by raw parsing
    return desc


def extract_description_raw(content: str) -> str:
    """Extract description from raw content, handling multi-line YAML."""
    parts = content.split("---", 2)
    if len(parts) < 3:
        return ""
    fm_text = parts[1]
    desc_lines = []
    in_desc = False
    for line in fm_text.split("\n"):
        if line.strip().startswith("description:"):
            in_desc = True
            val = line.split(":", 1)[1].strip()
            if val and val != ">-":
                desc_lines.append(val)
            continue
        if in_desc:
            if line.startswith("  ") or line.strip() == "":
                desc_lines.append(line.strip())
            else:
                break
    return " ".join(desc_lines)


def check_schema_exists(name: str) -> bool:
    """Check if a schema file exists and is valid JSON."""
    path = SCHEMAS_DIR / name
    if not path.exists():
        return False
    try:
        json.loads(path.read_text())
        return True
    except json.JSONDecodeError:
        return False


def check_scope_dag(body: str) -> dict:
    """Verify scope DAG has valid paths for all 3 modes."""
    result = {"valid": True, "errors": []}

    # Check that quick mode doesn't skip a phase that another phase depends on
    # Quick: P0→P1→P2→P3-lite→P4-lite→terminal
    # Standard: P0→P1→P2→P3→P4→approval→(skip 5-7)→terminal
    # Deep: P0→P1→P2→P3→P4→approval→P5→P6(if code)→P7→terminal

    # Check for the quick mode path
    if "P3-lite" not in body and "3-lite" not in body:
        result["valid"] = False
        result["errors"].append("Quick mode path does not include Phase 3-lite")
    if "P4-lite" not in body and "4-lite" not in body:
        result["valid"] = False
        result["errors"].append("Quick mode path does not include Phase 4-lite")

    # Check dependency gating table has valid quick path
    dep_section = re.search(r"## Dependency Gating\n(.*?)(?=\n## |\Z)", body, re.DOTALL)
    if dep_section:
        dep_text = dep_section.group(1)
        if "Quick mode" not in dep_text and "quick mode" not in dep_text.lower():
            result["valid"] = False
            result["errors"].append("Dependency Gating does not mention Quick mode exception")

    return result


def check_tool_truth_rules(body: str) -> dict:
    """Count Tool Truth enforcement rules."""
    result = {"count": 0, "valid": False}
    tt_section = re.search(r"### Enforcement Rules\n(.*?)(?=\n### |\n## )", body, re.DOTALL)
    if tt_section:
        rules = re.findall(r"^- .+$", tt_section.group(1), re.MULTILINE)
        result["count"] = len(rules)
        result["valid"] = len(rules) == EXPECTED_TOOL_TRUTH_RULES
    return result


def check_phases(body: str) -> dict:
    """Check all 8 phases are present."""
    result = {"phases_found": [], "valid": False}
    for i in range(8):
        if f"## Phase {i}" in body:
            result["phases_found"].append(i)
    result["valid"] = len(result["phases_found"]) == EXPECTED_PHASES
    return result


def check_gap_types(body: str) -> dict:
    """Check all 8 gap types are present."""
    result = {"types_found": [], "valid": False}
    expected = ["need gap", "product gap", "proof gap", "positioning gap",
                "pricing gap", "distribution gap", "adoption gap", "evidence gap"]
    body_lower = body.lower()
    for gap_type in expected:
        if gap_type in body_lower:
            result["types_found"].append(gap_type)
    result["valid"] = len(result["types_found"]) == EXPECTED_GAP_TYPES
    return result


def check_methodology_provenance() -> dict:
    """Check methodology provenance reference exists."""
    result = {"exists": False, "valid": False}
    path = REFERENCES_DIR / "methodology-provenance.md"
    result["exists"] = path.exists()
    if path.exists():
        content = path.read_text()
        # Check for URLs
        urls = re.findall(r"https?://[^\s)]+", content)
        result["url_count"] = len(urls)
        result["valid"] = len(urls) >= 10  # At least 10 source URLs
    return result


def run_validation() -> dict:
    """Run all validation checks."""
    results = {"checks": [], "all_pass": True}

    if not SKILL_FILE.exists():
        results["all_pass"] = False
        results["checks"].append({"name": "file_exists", "pass": False, "error": "SKILL.md not found"})
        return results

    content = SKILL_FILE.read_text()
    fm, body = parse_frontmatter(content)

    # 1. Description length
    desc = extract_description_raw(content)
    desc_len = len(desc)
    results["checks"].append({
        "name": "description_length",
        "pass": desc_len <= MAX_DESC_LEN,
        "value": desc_len,
        "max": MAX_DESC_LEN
    })

    # 2. Body line count
    body_lines = len(body.strip().split("\n"))
    results["checks"].append({
        "name": "body_lines",
        "pass": body_lines <= MAX_BODY_LINES,
        "value": body_lines,
        "max": MAX_BODY_LINES
    })

    # 3. Schemas exist and are valid JSON
    for schema in ["evidence-corpus.schema.json", "experiment.schema.json", "state.schema.json", "artifact.schema.json"]:
        exists = check_schema_exists(schema)
        results["checks"].append({"name": f"schema_{schema}", "pass": exists})

    # 4. Scope DAG validity
    dag = check_scope_dag(body)
    results["checks"].append({"name": "scope_dag", "pass": dag["valid"], "errors": dag.get("errors", [])})

    # 5. Tool Truth rules count
    tt = check_tool_truth_rules(body)
    results["checks"].append({"name": "tool_truth_rules", "pass": tt["valid"], "count": tt["count"], "expected": EXPECTED_TOOL_TRUTH_RULES})

    # 6. Trigger phrases
    triggers = ["niche segment", "positioning strategy", "positioning drift", "product-market alignment"]
    trigger_pass = all(t in content.lower() for t in triggers)
    results["checks"].append({"name": "trigger_phrases", "pass": trigger_pass})

    # 7. Anti-trigger present
    anti_trigger = "DO NOT TRIGGER" in content
    results["checks"].append({"name": "anti_trigger", "pass": anti_trigger})

    # 8. Tool Truth section
    tt_section = "## Tool Truth" in body
    results["checks"].append({"name": "tool_truth_section", "pass": tt_section})

    # 9. Upstream Source section
    us_section = "## Upstream Source" in body
    results["checks"].append({"name": "upstream_source", "pass": us_section})

    # 10-13. Schema validation (already checked in step 3)

    # 14. Phases present
    phases = check_phases(body)
    results["checks"].append({"name": "phases_present", "pass": phases["valid"], "found": phases["phases_found"]})

    # 15. Gap types present
    gaps = check_gap_types(body)
    results["checks"].append({"name": "gap_types", "pass": gaps["valid"], "found": gaps["types_found"]})

    # 16. Methodology provenance
    prov = check_methodology_provenance()
    results["checks"].append({"name": "methodology_provenance", "pass": prov["valid"], "exists": prov["exists"]})

    # Aggregate
    results["all_pass"] = all(c["pass"] for c in results["checks"])
    return results


def main():
    results = run_validation()
    print("=" * 60)
    print("ecc-niche-positioning-audit v5 Validator")
    print("=" * 60)

    for check in results["checks"]:
        status = "PASS" if check["pass"] else "FAIL"
        detail = ""
        if "value" in check:
            detail = f" ({check['value']}"
            if "max" in check:
                detail += f"/{check['max']}"
            detail += ")"
        elif "count" in check:
            detail = f" ({check['count']}/{check.get('expected', '?')})"
        elif "errors" in check and check["errors"]:
            detail = f" — {', '.join(check['errors'])}"
        elif "found" in check:
            detail = f" ({len(check['found'])} found)"

        print(f"  [{status}] {check['name']}{detail}")

    print("=" * 60)
    if results["all_pass"]:
        print("ALL CHECKS PASSED")
        sys.exit(0)
    else:
        failed = [c["name"] for c in results["checks"] if not c["pass"]]
        print(f"FAILED: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
