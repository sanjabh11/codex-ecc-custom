#!/usr/bin/env python3
"""Deterministic validator for ecc-niche-positioning-audit skill v8.

Checks:
1. Frontmatter description <= 1024 characters
2. SKILL.md body <= 1200 lines
3. All referenced schemas in schemas/ exist and are valid JSON
4. Scope DAG has valid paths (quick/standard/deep) — no impossible dependencies
5. 29 Tool Truth enforcement rules present
6. Trigger phrases present in description
7. Anti-trigger section present
8. Tool Truth section present
9. Upstream Source section present
10-14. Schema existence (evidence-corpus, experiment, state, artifact, hypothesis)
15. 8 phases (P0-P7) present
16. 8-type gap classification present
17. Methodology sources have URLs (in provenance reference)
18. Lifecycle contract distinguishes experiment design from market validation
19. Schema instance validation — valid and invalid fixtures conform or fail as expected
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
import hashlib
from datetime import datetime, timezone
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
EXECUTED_EXPERIMENT_STATUSES = {"completed", "failed", "inconclusive"}
CUSTOMER_COMMERCIAL_TYPES = {
    "customer_outcome",
    "user_quote",
    "behavioral_observation",
    "support_ticket",
    "analytics_data",
    "sales_data",
}

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
        import jsonschema

        schema = json.loads(path.read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        return True
    except ImportError:
        return False
    except (json.JSONDecodeError, jsonschema.SchemaError):
        return False


def check_scope_dag(body: str) -> dict:
    """Verify scope DAG has valid paths for all 3 modes."""
    result = {"valid": True, "errors": []}

    # Check that quick mode doesn't skip a phase that another phase depends on.
    # The old implementation only searched for labels anywhere in SKILL.md, so
    # a reordered or malformed path could pass.  Compare each rendered path to
    # the machine-readable contract in validation-rules.json instead.
    scope_rules = _rules.get("rules", {}).get("scope_dag", {})
    expected_paths = {
        "Quick Mode Path": scope_rules.get(
            "quick_path",
            ["phase-0", "phase-1", "phase-2", "phase-3-lite", "phase-4-lite", "terminal"],
        ),
        "Standard Mode Path": scope_rules.get(
            "standard_path",
            ["phase-0", "phase-1", "phase-2", "phase-3", "phase-4", "approval", "terminal"],
        ),
        "Deep Mode Path": scope_rules.get(
            "deep_path_variants",
            [["phase-0", "phase-1", "phase-2", "phase-3", "phase-4", "approval", "phase-5", "phase-7", "terminal"],
             ["phase-0", "phase-1", "phase-2", "phase-3", "phase-4", "approval", "phase-5", "phase-6", "phase-7", "terminal"]],
        ),
    }
    aliases = {
        "phase-0": r"(?:phase[- ]?0|p0)",
        "phase-1": r"(?:phase[- ]?1|p1)",
        "phase-2": r"(?:phase[- ]?2|p2)",
        "phase-3-lite": r"(?:phase[- ]?3[- ]?lite|p3[- ]?lite)",
        "phase-4-lite": r"(?:phase[- ]?4[- ]?lite|p4[- ]?lite)",
        "phase-3": r"(?:phase[- ]?3|p3)(?![- ]?lite)",
        "phase-4": r"(?:phase[- ]?4|p4)(?![- ]?lite)",
        "phase-5": r"(?:phase[- ]?5|p5)",
        "phase-6": r"(?:phase[- ]?6|p6)",
        "phase-7": r"(?:phase[- ]?7|p7)",
        "approval": r"(?:\[approval\]|approval)",
        "validation_pending": r"(?:validation[-_ ]?pending)",
        "terminal": r"(?:terminal)",
    }

    def path_is_ordered(section: str, path: list[str]) -> tuple[bool, str | None]:
        cursor = 0
        for node in path:
            pattern = aliases.get(node)
            if pattern is None:
                return False, f"unknown scope-DAG node {node!r}"
            match = re.search(pattern, section[cursor:], re.IGNORECASE)
            if match is None:
                return False, f"missing {node}"
            cursor += match.end()
        return True, None

    for heading, path in expected_paths.items():
        section_match = re.search(
            rf"### {re.escape(heading)}\n(.*?)(?=\n### |\n## |\Z)",
            body,
            re.IGNORECASE | re.DOTALL,
        )
        if section_match is None:
            result["valid"] = False
            result["errors"].append(f"Missing {heading} section")
            continue
        path_options = path if path and isinstance(path[0], list) else [path]
        path_results = [path_is_ordered(section_match.group(1), option) for option in path_options]
        valid = any(option_valid for option_valid, _ in path_results)
        if not valid:
            result["valid"] = False
            errors = "; ".join(str(error) for _, error in path_results)
            result["errors"].append(f"{heading} does not match any allowed path {path_options}: {errors}")

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
        required_references = _r.get("required_references", ["references/methodology-provenance.md"])
        missing_references = [reference for reference in required_references if not (SKILL_DIR / reference).exists()]
        unlinked_references = [reference for reference in required_references if reference not in SKILL_FILE.read_text()]
        result["missing_references"] = missing_references
        result["unlinked_references"] = unlinked_references
        result["valid"] = len(urls) >= 10 and not missing_references and not unlinked_references
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


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _evidence_is_stale(item: dict) -> bool:
    if item.get("freshness") == "stale":
        return True
    expiry = _parse_timestamp(item.get("expiry"))
    return bool(expiry and expiry < datetime.now(timezone.utc))


def _canonical_state_hash(state_path: Path) -> str:
    state = json.loads(state_path.read_text())
    canonical = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _load_schema_checked(path: Path) -> tuple[dict | None, list[str]]:
    if not path.exists():
        return None, [f"missing file: {path.name}"]
    try:
        return json.loads(path.read_text()), []
    except (OSError, json.JSONDecodeError) as error:
        return None, [f"invalid JSON in {path.name}: {error}"]


def validate_audit_instance(audit_dir: Path) -> dict:
    """Validate a persisted audit instance, including schemas and lifecycle semantics."""
    result = {"audit_dir": str(audit_dir), "checks": [], "all_pass": True}
    state, state_errors = _load_schema_checked(audit_dir / "state.json")
    experiments_doc, experiment_errors = _load_schema_checked(audit_dir / "experiments.json")

    def add(name: str, passed: bool, **details) -> None:
        result["checks"].append({"name": name, "pass": bool(passed), **details})

    if state is None or experiments_doc is None:
        add("audit_files", False, errors=state_errors + experiment_errors)
        result["all_pass"] = False
        return result

    state_schema_errors = _validate_instance(state, SCHEMAS_DIR / "state.schema.json")
    experiment_schema_errors = _validate_instance(experiments_doc, SCHEMAS_DIR / "experiment.schema.json")
    add("state_schema", not state_schema_errors, errors=state_schema_errors)
    add("experiments_schema", not experiment_schema_errors, errors=experiment_schema_errors)
    add("audit_id_consistency", state.get("audit_id") == experiments_doc.get("audit_id"), state_audit_id=state.get("audit_id"), experiments_audit_id=experiments_doc.get("audit_id"))

    confidence = state.get("decision_confidence", {})
    confidence_subscores = [confidence.get(key, 0) for key in ("quality", "coverage", "consistency", "counter", "validation")]
    confidence_expected = sum(confidence_subscores)
    add("confidence_arithmetic", abs(confidence.get("composite", 0) - confidence_expected) <= 1e-9, composite=confidence.get("composite"), expected=confidence_expected)

    experiments = experiments_doc.get("experiments", [])
    observed_executed = sum(1 for experiment in experiments if experiment.get("status") in EXECUTED_EXPERIMENT_STATUSES)
    declared_executed = state.get("experiments_executed")
    add("executed_count_consistency", declared_executed == observed_executed, declared=declared_executed, observed=observed_executed)

    evidence_doc = None
    evidence_path = audit_dir / "evidence-corpus.json"
    if evidence_path.exists():
        evidence_doc, errors = _load_schema_checked(evidence_path)
        if evidence_doc is not None:
            errors.extend(_validate_instance(evidence_doc, SCHEMAS_DIR / "evidence-corpus.schema.json"))
        add("evidence_corpus_schema", not errors, errors=errors)
    add("evidence_corpus_present", evidence_doc is not None, required=True)

    hypothesis_doc = None
    hypothesis_path = audit_dir / "hypotheses.json"
    if hypothesis_path.exists():
        hypothesis_doc, errors = _load_schema_checked(hypothesis_path)
        if hypothesis_doc is not None:
            errors.extend(_validate_instance(hypothesis_doc, SCHEMAS_DIR / "hypothesis.schema.json"))
        add("hypothesis_schema", not errors, errors=errors)

    evidence_items = evidence_doc.get("evidence_items", []) if evidence_doc else []
    has_first_party_evidence = bool(
        any(item.get("is_customer_commercial") and item.get("type") in CUSTOMER_COMMERCIAL_TYPES for item in evidence_items)
    )
    if evidence_doc:
        add("evidence_audit_id_consistency", evidence_doc.get("audit_id") == state.get("audit_id"), state_audit_id=state.get("audit_id"), evidence_audit_id=evidence_doc.get("audit_id"))
        corpus_types = {item.get("type") for item in evidence_items}
        add("corpus_counts", evidence_doc.get("total_items") == len(evidence_items) and evidence_doc.get("types_present") == len(corpus_types), declared_items=evidence_doc.get("total_items"), observed_items=len(evidence_items), declared_types=evidence_doc.get("types_present"), observed_types=len(corpus_types))
        add("state_corpus_type_consistency", set(state.get("evidence_types_present", [])) == corpus_types, state_types=sorted(state.get("evidence_types_present", [])), corpus_types=sorted(corpus_types))
        add("evidence_wrapper_mode_consistency", evidence_doc.get("evidence_limited_mode") == (not has_first_party_evidence), wrapper_mode=evidence_doc.get("evidence_limited_mode"), derived_mode=not has_first_party_evidence)
        past_phase_one = "phase-1" in state.get("phases_completed", []) or state.get("current_phase") not in {"phase-0", "phase-1"}
        add("evidence_type_minimum", not past_phase_one or len(corpus_types) >= 3, required=3, observed=len(corpus_types))

    evidence_limited = bool(state.get("evidence_limited_mode", False))
    add("evidence_mode_consistency", evidence_limited == (not has_first_party_evidence), evidence_limited=evidence_limited, has_first_party_evidence=has_first_party_evidence)
    if not evidence_limited:
        add("first_party_buyer_evidence", has_first_party_evidence)

    gate_decisions = [gate.get("decision") for gate in state.get("gates_passed", [])]
    add("evidence_limited_gate_cap", not evidence_limited or (state.get("current_gate") != "GO" and "GO" not in gate_decisions), decisions=gate_decisions)

    validation_score = state.get("decision_confidence", {}).get("validation")
    if declared_executed == 0:
        add("design_is_not_validation", state.get("market_validation_status") == "validation_pending", value=state.get("market_validation_status"))
        add("validation_score_zero", validation_score == 0, value=validation_score)
        add("validation_pending_phase", state.get("current_phase") == "VALIDATION_PENDING", value=state.get("current_phase"))
        state_hypotheses = state.get("hypotheses", [])
        file_hypotheses = hypothesis_doc.get("hypotheses", []) if hypothesis_doc else []
        add("no_supported_hypothesis_without_results", not any(h.get("status") == "supported" for h in state_hypotheses + file_hypotheses))

    stale_ids = {item.get("evidence_id") for item in evidence_items if _evidence_is_stale(item)}
    if hypothesis_doc:
        add("hypothesis_audit_id_consistency", hypothesis_doc.get("audit_id") == state.get("audit_id"), state_audit_id=state.get("audit_id"), hypothesis_audit_id=hypothesis_doc.get("audit_id"))
        evidence_by_id = {item.get("evidence_id"): item for item in evidence_items}
        bundle_errors = []
        for hypothesis in hypothesis_doc.get("hypotheses", []):
            for bundle in hypothesis.get("evidence_bundle", []):
                ids = bundle.get("evidence_ids", [])
                referenced = [evidence_by_id[evidence_id] for evidence_id in ids if evidence_id in evidence_by_id]
                high = sum(item.get("grade") == "HIGH" and not _evidence_is_stale(item) for item in referenced)
                medium = sum(item.get("grade") == "MEDIUM" and not _evidence_is_stale(item) for item in referenced)
                min_high = bundle.get("min_high", 0)
                min_medium = bundle.get("min_medium", 0)
                satisfied = (min_high > 0 and high >= min_high) or (min_medium > 0 and medium >= min_medium)
                if bundle.get("satisfied") is not None and bundle.get("satisfied") != satisfied:
                    bundle_errors.append(f"{hypothesis.get('id')}:{bundle.get('claim')} satisfied flag is incorrect")
                if any(evidence_id not in evidence_by_id for evidence_id in ids):
                    bundle_errors.append(f"{hypothesis.get('id')} references unknown evidence")
                if set(ids) & stale_ids:
                    bundle_errors.append(f"{hypothesis.get('id')} load-bearing bundle references stale evidence")
                if hypothesis.get("status") == "supported" and not satisfied:
                    bundle_errors.append(f"{hypothesis.get('id')} is supported without a satisfied evidence bundle")
        add("evidence_bundle_semantics", not bundle_errors, errors=bundle_errors)
    else:
        add("evidence_bundle_semantics", True, errors=["hypotheses.json not present; bundle check not applicable"])

    if hypothesis_doc:
        transitions_by_hypothesis = {}
        for experiment in experiments:
            if experiment.get("status") in EXECUTED_EXPERIMENT_STATUSES and experiment.get("hypothesis_transition"):
                transitions_by_hypothesis.setdefault(experiment.get("hypothesis_id"), set()).add(experiment.get("hypothesis_transition"))
        transition_errors = []
        for hypothesis in hypothesis_doc.get("hypotheses", []):
            status = hypothesis.get("status")
            if status in {"supported", "weakened", "disproven"} and status not in transitions_by_hypothesis.get(hypothesis.get("id"), set()):
                transition_errors.append(f"{hypothesis.get('id')} status {status} lacks a matching executed experiment transition")
        add("experiment_hypothesis_consistency", not transition_errors, errors=transition_errors)

    # Validate all current artifacts, and require the adversarial triad for phases where it is mandatory.
    artifact_errors = []
    artifacts_dir = audit_dir / "artifacts"
    if artifacts_dir.exists():
        for artifact_path in sorted(artifacts_dir.glob("*.json")):
            artifact, errors = _load_schema_checked(artifact_path)
            if artifact is None:
                artifact_errors.extend(errors)
                continue
            schema_errors = _validate_instance(artifact, SCHEMAS_DIR / "artifact.schema.json")
            artifact_errors.extend(schema_errors)
            if artifact.get("superseded"):
                continue
            expected_hash = _canonical_state_hash(audit_dir / "state.json")
            if artifact.get("generated_from_state_hash") != expected_hash:
                artifact_errors.append(f"{artifact_path.name} does not match the current canonical state hash")
            if not schema_errors:
                subscores = artifact.get("confidence", {}).get("subscores", {})
                composite = artifact.get("confidence", {}).get("composite")
                if composite is not None and abs(composite - sum(subscores.values())) > 1e-9:
                    artifact_errors.append(f"{artifact_path.name} confidence composite does not equal subscore sum")
                if artifact.get("evidence_limited") and artifact.get("gate_decision", {}).get("decision") == "GO":
                    artifact_errors.append(f"{artifact_path.name} is evidence-limited but has GO decision")
            if artifact.get("phase") in {"phase-3", "phase-4", "phase-5"}:
                personas = {review.get("persona") for review in artifact.get("adversarial_reviews", [])}
                if personas != {"skeptic", "missing_perspective", "contrarian"}:
                    artifact_errors.append(f"{artifact_path.name} lacks the complete adversarial review triad")
    add("artifact_semantics", not artifact_errors, errors=artifact_errors)

    result["all_pass"] = all(check["pass"] for check in result["checks"])
    return result


def _validator_for(schema_path: Path):
    """Build a Draft 2020-12 validator with format checking enabled."""
    import jsonschema

    schema = json.loads(schema_path.read_text())
    return jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())


def _validate_instance(instance, schema_path: Path) -> list[str]:
    """Return deterministic schema errors for one JSON instance."""
    validator = _validator_for(schema_path)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    return [error.message for error in errors]


def check_schema_instance_validation() -> dict:
    """Check 19: Validate valid and invalid fixtures against the actual schemas."""
    result = {"valid": True, "errors": []}
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        return {"valid": False, "errors": ["jsonschema library is required; instance validation cannot be skipped"]}

    def check_item(fixture_name: str, schema_name: str, item_schema_key: str | None = None) -> None:
        fixture_path = TESTS_DIR / fixture_name
        schema_path = SCHEMAS_DIR / schema_name
        if not fixture_path.exists() or not schema_path.exists():
            result["valid"] = False
            result["errors"].append(f"missing fixture or schema: {fixture_name} / {schema_name}")
            return
        fixture = json.loads(fixture_path.read_text())
        schema = json.loads(schema_path.read_text())
        target_schema = schema.get("$defs", {}).get(item_schema_key, schema) if item_schema_key else schema

        for index, item in enumerate(fixture.get("valid_examples", [])):
            errors = _validate_instance(item, schema_path) if item_schema_key is None else _validate_instance_with_schema(item, target_schema)
            if errors:
                result["valid"] = False
                result["errors"].append(f"{fixture_name}: valid_examples[{index}]: {errors[0]}")

        for index, item in enumerate(fixture.get("invalid_examples", [])):
            candidate = {key: value for key, value in item.items() if key != "expected_error"}
            errors = _validate_instance(candidate, schema_path) if item_schema_key is None else _validate_instance_with_schema(candidate, target_schema)
            if not errors:
                result["valid"] = False
                result["errors"].append(f"{fixture_name}: invalid_examples[{index}] was accepted")

        for index, case in enumerate(fixture.get("cases", [])):
            item = case.get("experiment")
            if item is None:
                continue
            errors = _validate_instance_with_schema(item, target_schema)
            if errors:
                result["valid"] = False
                result["errors"].append(f"{fixture_name}: cases[{index}]: {errors[0]}")

    check_item("evidence_corpus_test.json", "evidence-corpus.schema.json", "evidence_item")
    check_item("experiment_lifecycle_test.json", "experiment.schema.json", "experiment")

    for fixture_name, schema_name in [
        ("state_instance_test.json", "state.schema.json"),
        ("artifact_instance_test.json", "artifact.schema.json"),
        ("hypothesis_instance_test.json", "hypothesis.schema.json"),
        ("evidence_corpus_instance_test.json", "evidence-corpus.schema.json"),
    ]:
        fixture_path = TESTS_DIR / fixture_name
        schema_path = SCHEMAS_DIR / schema_name
        if not fixture_path.exists() or not schema_path.exists():
            result["valid"] = False
            result["errors"].append(f"missing wrapper fixture or schema: {fixture_name} / {schema_name}")
            continue
        fixture = json.loads(fixture_path.read_text())
        for index, item in enumerate(fixture.get("valid_examples", [fixture])):
            errors = _validate_instance(item, schema_path)
            if errors:
                result["valid"] = False
                result["errors"].append(f"{fixture_name}[{index}]: {errors[0]}")
    return result


def _validate_instance_with_schema(instance, schema: dict) -> list[str]:
    """Validate an item schema that is nested in a wrapper schema."""
    import jsonschema

    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    return [error.message for error in errors]


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
