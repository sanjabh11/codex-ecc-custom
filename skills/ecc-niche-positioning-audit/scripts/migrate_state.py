#!/usr/bin/env python3
"""Migrate legacy positioning-audit state to the v8 state contract.

Migration is explicit and non-destructive: an output path is required. The
input file is never overwritten by this script.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from generate_artifact import atomic_write_json


SKILL_DIR = Path(__file__).resolve().parent.parent
STATE_SCHEMA = SKILL_DIR / "schemas" / "state.schema.json"
CUSTOMER_TYPES = {
    "customer_outcome",
    "user_quote",
    "behavioral_observation",
    "support_ticket",
    "analytics_data",
    "sales_data",
}
DECISIONS = ("CONDITIONAL_GO", "RECYCLE", "STOP", "GO")


def _phase(value):
    if isinstance(value, int):
        return "completed" if value >= 8 else f"phase-{max(0, min(value, 7))}"
    if value in {"VALIDATION_PENDING", "completed"}:
        return value
    if isinstance(value, str) and re.fullmatch(r"phase-[0-7]", value):
        return value
    return "phase-0"


def _gate(value):
    if isinstance(value, dict):
        return value
    text = str(value)
    decision = next((candidate for candidate in DECISIONS if candidate in text), "CONDITIONAL_GO")
    gate_match = re.search(r"gate[-_ ]?\d+", text, re.IGNORECASE)
    return {"gate": gate_match.group(0).lower().replace("_", "-") if gate_match else "unknown", "decision": decision}


def migrate_state(legacy: dict) -> tuple[dict, list[str]]:
    """Return a v8 state and the list of dropped unsupported legacy fields."""
    state = copy.deepcopy(legacy)
    state["current_phase"] = _phase(state.get("current_phase"))
    state["schema_version"] = "v8"
    state.setdefault("last_updated", state.get("started_at") or datetime.now(timezone.utc).isoformat())
    state.setdefault("evidence_types_present", [])
    state.setdefault("evidence_types_missing", [])
    state.setdefault("evidence_limitations", [])
    state.setdefault("phases_completed", [])
    state.setdefault("gates_passed", [])
    state["phases_completed"] = [_phase(phase) for phase in state.get("phases_completed", [])]
    state["gates_passed"] = [_gate(gate) for gate in state.get("gates_passed", [])]
    current_gate = state.get("current_gate")
    if isinstance(current_gate, dict):
        state["current_gate"] = current_gate.get("decision")
    elif current_gate not in {None, *DECISIONS}:
        state["current_gate"] = _gate(current_gate)["decision"]

    confidence = state.setdefault("decision_confidence", {})
    for key in ("composite", "quality", "coverage", "consistency", "counter", "validation"):
        confidence.setdefault(key, 0)

    experiments = state.get("experiments", [])
    state.setdefault("experiments_designed", len(experiments))
    state.setdefault("experiments_executed", sum(1 for experiment in experiments if experiment.get("status") in {"completed", "failed", "inconclusive"}))
    state.setdefault("evidence_limited_mode", not bool(set(state.get("evidence_types_present", [])) & CUSTOMER_TYPES))
    default_validation_status = "validation_pending" if state["experiments_executed"] == 0 and state["current_phase"] in {"phase-5", "phase-6", "phase-7", "VALIDATION_PENDING", "completed"} else "not_started"
    if state.get("market_validation_status") not in {"not_started", "validation_pending", "in_progress", "validated", "invalidated"}:
        state["market_validation_status"] = default_validation_status
    else:
        state.setdefault("market_validation_status", default_validation_status)
    default_analysis_status = "complete" if state["current_phase"] in {"phase-5", "phase-6", "phase-7", "VALIDATION_PENDING", "completed"} else "in_progress"
    if state.get("analysis_status") not in {"in_progress", "complete"}:
        state["analysis_status"] = default_analysis_status
    else:
        state.setdefault("analysis_status", default_analysis_status)
    state.setdefault("implementation_hardening_status", None)
    state.setdefault("research_log", [])
    state.setdefault("tool_health", {})
    state.setdefault("drift_status", "not_assessed")

    schema = json.loads(STATE_SCHEMA.read_text())
    allowed = set(schema["properties"])
    dropped = sorted(key for key in state if key not in allowed)
    migrated = {key: value for key, value in state.items() if key in allowed}
    return migrated, dropped


def validate_state(state: dict) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema is required for migration validation"]
    schema = json.loads(STATE_SCHEMA.read_text())
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    return [error.message for error in sorted(validator.iter_errors(state), key=lambda item: list(item.path))]


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate positioning-audit state to v8 without overwriting input")
    parser.add_argument("--input", required=True, help="Legacy state.json")
    parser.add_argument("--output", required=True, help="New v8 state.json")
    args = parser.parse_args()

    try:
        legacy = json.loads(Path(args.input).read_text())
        migrated, dropped = migrate_state(legacy)
        errors = validate_state(migrated)
        if errors:
            raise ValueError("migrated state is invalid: " + "; ".join(errors[:5]))
        atomic_write_json(Path(args.output), migrated)
        print(f"Migrated state: {args.output}")
        print("schema_version: v8")
        if dropped:
            print("dropped_legacy_fields: " + ", ".join(dropped))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
