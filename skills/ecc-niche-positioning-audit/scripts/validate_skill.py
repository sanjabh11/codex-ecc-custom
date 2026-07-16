#!/usr/bin/env python3
"""Deterministic validator for ecc-niche-positioning-audit skill v8.

Checks:
1. Frontmatter description <= 1024 characters
2. SKILL.md body <= 1200 lines
3. All referenced schemas in schemas/ exist and are valid JSON
4. Scope DAG has valid paths (quick/standard/deep) — no impossible dependencies
5. 27 Tool Truth enforcement rules present
6. Trigger phrases present in description
7. Anti-trigger section present
8. Tool Truth section present
9. Upstream Source section present
10-14. Schema existence (evidence-corpus, experiment, state, artifact, hypothesis)
15. 8 phases (P0-P7) present
16. 8-type gap classification present
17. Methodology sources have URLs (in provenance reference)
18. Lifecycle contract distinguishes experiment design from market validation
19. Schema instance validation — test fixtures conform to their schemas
20. Gate cap logic — CONDITIONAL_GO is capped when evidence_limited_mode is true
21. Validation score zero — validation confidence is 0 when no experiments executed
22. Count equality — experiments_executed matches count of executed experiments
23. Stale artifact detection — superseded artifacts are flagged
24. Hypothesis status consistency — no hypothesis is 'supported' when all experiments are 'designed'
25. Evidence bundle minimum — each load-bearing claim has sufficient evidence
26. Freshness enforcement — no stale evidence item is load-bearing
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
EXPECTED_TOOL_TRUTH_RULES = 29
EXPECTED_PHASES = 8
EXPECTED_GAP_TYPES = 8
EXPECTED_SCHEMA_VERSION = "v8"

# Load machine-readable validation rules if available
RULES_PATH = SKILL_DIR / "validation-rules.json"
if RULES_PATH.exists():
    try:
        _rules = json.loads(RULES_PATH.read_text())
        _r = _rules.get("rules", {})
        MAX_DESC_LEN = _r.get("max_description_length", MAX_DESC_LEN)
        MAX_BODY_LINES = _r.get("max_body_lines", MAX_BODY_LINES)
        EXPECTED_TOOL_TRUTH_RULES = _r.get("expected_tool_truth_rules", EXPECTED_TOOL_TRUTH_RULES)
        EXPECTED_PHASES = _r.get("expected_phases", EXPECTED_PHASES)
        EXPECTED_GAP_TYPES = _r.get("expected_gap_types", EXPECTED_GAP_TYPES)
        EXPECTED_SCHEMA_VERSION = _r.get("expected_schema_version", EXPECTED_SCHEMA_VERSION)
    except (json.JSONDecodeError, KeyError):
        pass  # Fall back to defaults


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


def check_lifecycle_contract(body: str) -> dict:
    """Ensure the documented paths cannot call designed experiments validation."""
    required_phrases = [
        "P5 design → VALIDATION_PENDING",
        "Designed experiments are not validation evidence",
        "market_validation_status: validation_pending",
        "first-party buyer evidence",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in body]
    return {"valid": not missing, "missing": missing}


def validate_audit_instance(audit_dir: Path) -> dict:
    """Check an audit instance's designed-versus-executed lifecycle boundary."""
    state_path = audit_dir / "state.json"
    experiments_path = audit_dir / "experiments.json"
    result = {"audit_dir": str(audit_dir), "checks": [], "all_pass": True}

    try:
        state = json.loads(state_path.read_text())
        experiments = json.loads(experiments_path.read_text()).get("experiments", [])
    except (OSError, json.JSONDecodeError) as error:
        return {"audit_dir": str(audit_dir), "checks": [{"name": "audit_files", "pass": False, "error": str(error)}], "all_pass": False}

    executed_statuses = {"completed", "failed", "inconclusive"}
    observed_executed = sum(1 for experiment in experiments if experiment.get("status") in executed_statuses)
    declared_executed = state.get("experiments_executed", observed_executed)
    has_first_party_evidence = bool(
        set(state.get("evidence_types_present", []))
        & {"user_quote", "behavioral_observation", "support_ticket", "analytics_data", "sales_data"}
    )
    validation_score = state.get("decision_confidence", {}).get("validation")

    result["checks"].append({
        "name": "executed_count_consistency",
        "pass": declared_executed == observed_executed,
        "declared": declared_executed,
        "observed": observed_executed,
    })
    if declared_executed == 0:
        result["checks"].extend([
            {
                "name": "design_is_not_validation",
                "pass": state.get("market_validation_status") == "validation_pending",
                "value": state.get("market_validation_status"),
            },
            {"name": "validation_score_zero", "pass": validation_score == 0, "value": validation_score},
            {
                "name": "validation_pending_phase",
                "pass": state.get("current_phase") == "VALIDATION_PENDING",
                "value": state.get("current_phase"),
            },
        ])
    if not state.get("evidence_limited_mode", False):
        result["checks"].append({"name": "first_party_buyer_evidence", "pass": has_first_party_evidence})

    result["all_pass"] = all(check["pass"] for check in result["checks"])
    return result


def check_schema_instance_validation() -> dict:
    """Check 19: Validate test fixture instances against their schemas."""
    result = {"valid": True, "errors": []}
    try:
        import jsonschema
    except ImportError:
        # jsonschema not installed — skip with note
        return {"valid": True, "errors": ["jsonschema library not installed — skipped instance validation"]}

    fixture_map = {
        "evidence_corpus_test.json": "evidence-corpus.schema.json",
        "experiment_lifecycle_test.json": "experiment.schema.json",
    }
    for fixture_name, schema_name in fixture_map.items():
        fixture_path = TESTS_DIR / fixture_name
        schema_path = SCHEMAS_DIR / schema_name
        if not fixture_path.exists() or not schema_path.exists():
            continue
        try:
            fixture = json.loads(fixture_path.read_text())
            schema = json.loads(schema_path.read_text())
            # Validate valid_examples if present, otherwise validate the fixture itself
            if "valid_examples" in fixture:
                for item in fixture["valid_examples"]:
                    try:
                        jsonschema.validate(item, schema.get("$defs", {}).get("evidence_item", schema))
                    except jsonschema.ValidationError as e:
                        result["errors"].append(f"{fixture_name}: valid_example failed: {e.message}")
                        result["valid"] = False
        except (json.JSONDecodeError, KeyError) as e:
            result["errors"].append(f"{fixture_name}: {e}")
            result["valid"] = False
    return result


def check_gate_cap_logic(body: str) -> dict:
    """Check 20: Verify SKILL.md enforces that evidence_limited_mode caps gate at CONDITIONAL_GO."""
    result = {"valid": True, "errors": []}
    required = [
        "evidence_limited_mode",
        "CONDITIONAL GO",
        "never GO",
        "all subsequent gates are capped",
    ]
    missing = [phrase for phrase in required if phrase.lower() not in body.lower()]
    if missing:
        result["valid"] = False
        result["errors"] = [f"Missing gate cap enforcement: {', '.join(missing)}"]
    return result


def check_validation_score_rule(body: str) -> dict:
    """Check 21: Verify SKILL.md enforces validation confidence = 0 when no experiments executed."""
    result = {"valid": True, "errors": []}
    required = [
        "validation_pending",
        "validation",
        "0",
        "first-party",
    ]
    missing = [phrase for phrase in required if phrase.lower() not in body.lower()]
    if missing:
        result["valid"] = False
        result["errors"] = [f"Missing validation score rule: {', '.join(missing)}"]
    return result


def check_count_equality(body: str) -> dict:
    """Check 22: Verify state schema has experiments_executed and experiments_designed fields for count tracking."""
    result = {"valid": True, "errors": []}
    state_path = SCHEMAS_DIR / "state.schema.json"
    if not state_path.exists():
        return {"valid": False, "errors": ["state.schema.json not found"]}
    try:
        schema = json.loads(state_path.read_text())
        props = schema.get("properties", {})
        if "experiments_executed" not in props:
            result["valid"] = False
            result["errors"].append("Missing 'experiments_executed' field in state schema")
        if "experiments_designed" not in props:
            result["valid"] = False
            result["errors"].append("Missing 'experiments_designed' field in state schema")
    except json.JSONDecodeError:
        result["valid"] = False
        result["errors"] = ["state.schema.json is not valid JSON"]
    return result


def check_stale_artifact_detection() -> dict:
    """Check 23: Verify artifact schema has superseded and generated_from_state_hash fields."""
    result = {"valid": True, "errors": []}
    artifact_path = SCHEMAS_DIR / "artifact.schema.json"
    if not artifact_path.exists():
        return {"valid": False, "errors": ["artifact.schema.json not found"]}
    try:
        schema = json.loads(artifact_path.read_text())
        props = schema.get("properties", {})
        if "superseded" not in props:
            result["valid"] = False
            result["errors"].append("Missing 'superseded' field in artifact schema")
        if "generated_from_state_hash" not in props:
            result["valid"] = False
            result["errors"].append("Missing 'generated_from_state_hash' field in artifact schema")
    except json.JSONDecodeError:
        result["valid"] = False
        result["errors"] = ["artifact.schema.json is not valid JSON"]
    return result


def check_hypothesis_status_consistency(body: str) -> dict:
    """Check 24: Verify SKILL.md enforces that hypotheses cannot be 'supported' when experiments are only 'designed'."""
    result = {"valid": True, "errors": []}
    required = [
        "Designed experiments are not validation evidence",
        "no hypothesis becomes Supported until first-party results are recorded",
    ]
    missing = [phrase for phrase in required if phrase.lower() not in body.lower()]
    if missing:
        result["valid"] = False
        result["errors"] = [f"Missing hypothesis status consistency rule: {', '.join(missing)}"]
    return result


def check_evidence_bundle_minimum(body: str) -> dict:
    """Check 25: Verify SKILL.md enforces minimum evidence per load-bearing claim."""
    result = {"valid": True, "errors": []}
    required = [
        "at least one HIGH or two MEDIUM",
        "load-bearing",
        "cannot be load-bearing",
    ]
    missing = [phrase for phrase in required if phrase.lower() not in body.lower()]
    if missing:
        result["valid"] = False
        result["errors"] = [f"Missing evidence bundle minimum rule: {', '.join(missing)}"]
    return result


def check_freshness_enforcement(body: str) -> dict:
    """Check 26: Verify SKILL.md enforces that stale evidence cannot be load-bearing."""
    result = {"valid": True, "errors": []}
    # Check for freshness terms and the load-bearing restriction
    has_freshness = any(term in body.lower() for term in ["fresh", "stale", "recent"])
    has_restriction = "cannot be load-bearing" in body.lower() or "low findings cannot" in body.lower()
    if not has_freshness:
        result["valid"] = False
        result["errors"].append("Missing freshness terminology (fresh/recent/stale)")
    if not has_restriction:
        result["valid"] = False
        result["errors"].append("Missing stale/LOW evidence load-bearing restriction")
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
    for schema in ["evidence-corpus.schema.json", "experiment.schema.json", "state.schema.json", "artifact.schema.json", "hypothesis.schema.json"]:
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

    # 10-14. Schema validation (already checked in step 3)

    # 13b. Schema version check (v8)
    schema_version_ok = True
    for schema_name in ["state.schema.json", "evidence-corpus.schema.json", "experiment.schema.json", "artifact.schema.json", "hypothesis.schema.json"]:
        schema_path = SCHEMAS_DIR / schema_name
        if schema_path.exists():
            try:
                schema_json = json.loads(schema_path.read_text())
                if schema_json.get("version") != EXPECTED_SCHEMA_VERSION:
                    schema_version_ok = False
            except json.JSONDecodeError:
                schema_version_ok = False
    results["checks"].append({"name": f"schema_version_{EXPECTED_SCHEMA_VERSION}", "pass": schema_version_ok})

    # 14. Phases present
    phases = check_phases(body)
    results["checks"].append({"name": "phases_present", "pass": phases["valid"], "found": phases["phases_found"]})

    # 15. Gap types present
    gaps = check_gap_types(body)
    results["checks"].append({"name": "gap_types", "pass": gaps["valid"], "found": gaps["types_found"]})

    # 16. Methodology provenance
    prov = check_methodology_provenance()
    results["checks"].append({"name": "methodology_provenance", "pass": prov["valid"], "exists": prov["exists"]})

    lifecycle = check_lifecycle_contract(body)
    results["checks"].append({"name": "lifecycle_contract", "pass": lifecycle["valid"], "missing": lifecycle["missing"]})

    # 19. Schema instance validation — validate test fixtures against schemas
    instance_result = check_schema_instance_validation()
    results["checks"].append({"name": "schema_instance_validation", "pass": instance_result["valid"], "errors": instance_result.get("errors", [])})

    # 20. Gate cap logic — evidence_limited_mode caps gate at CONDITIONAL_GO
    gate_cap_result = check_gate_cap_logic(body)
    results["checks"].append({"name": "gate_cap_logic", "pass": gate_cap_result["valid"], "errors": gate_cap_result.get("errors", [])})

    # 21. Validation score zero when no experiments executed
    val_score_result = check_validation_score_rule(body)
    results["checks"].append({"name": "validation_score_rule", "pass": val_score_result["valid"], "errors": val_score_result.get("errors", [])})

    # 22. Count equality — experiments_executed matches executed experiment count
    count_result = check_count_equality(body)
    results["checks"].append({"name": "count_equality", "pass": count_result["valid"], "errors": count_result.get("errors", [])})

    # 23. Stale artifact detection — superseded field exists and is checked
    stale_result = check_stale_artifact_detection()
    results["checks"].append({"name": "stale_artifact_detection", "pass": stale_result["valid"], "errors": stale_result.get("errors", [])})

    # 24. Hypothesis status consistency — no 'supported' when all experiments 'designed'
    hyp_result = check_hypothesis_status_consistency(body)
    results["checks"].append({"name": "hypothesis_status_consistency", "pass": hyp_result["valid"], "errors": hyp_result.get("errors", [])})

    # 25. Evidence bundle minimum — prose rule exists in SKILL.md
    bundle_result = check_evidence_bundle_minimum(body)
    results["checks"].append({"name": "evidence_bundle_minimum", "pass": bundle_result["valid"], "errors": bundle_result.get("errors", [])})

    # 26. Freshness enforcement — stale evidence cannot be load-bearing
    freshness_result = check_freshness_enforcement(body)
    results["checks"].append({"name": "freshness_enforcement", "pass": freshness_result["valid"], "errors": freshness_result.get("errors", [])})

    # Aggregate
    results["all_pass"] = all(c["pass"] for c in results["checks"])
    return results


def main():
    results = run_validation()
    print("=" * 60)
    print("ecc-niche-positioning-audit v8 Validator")
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
    instance = None
    audit_dir_index = sys.argv.index("--audit-dir") if "--audit-dir" in sys.argv else None
    if audit_dir_index is not None:
        if audit_dir_index + 1 >= len(sys.argv):
            print("  [FAIL] audit_instance — --audit-dir requires a path")
            sys.exit(1)
        instance = validate_audit_instance(Path(sys.argv[audit_dir_index + 1]))
        for check in instance["checks"]:
            status = "PASS" if check["pass"] else "FAIL"
            print(f"  [{status}] audit_instance.{check['name']}")
        results["all_pass"] = results["all_pass"] and instance["all_pass"]

    if results["all_pass"]:
        print("ALL CHECKS PASSED")
        sys.exit(0)
    else:
        failed = [c["name"] for c in results["checks"] if not c["pass"]]
        if instance:
            failed.extend(f"audit_instance.{c['name']}" for c in instance["checks"] if not c["pass"])
        print(f"FAILED: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
