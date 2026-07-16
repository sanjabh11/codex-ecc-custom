#!/usr/bin/env python3
"""Generate, verify, and safely supersede positioning-audit artifacts.

The state hash is computed from canonical JSON, so formatting and key order do
not create false drift. Writes are atomic. A supersede operation preserves the
old artifact as ``superseded: true`` and writes a distinct replacement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = SKILL_DIR / "schemas" / "artifact.schema.json"
STATE_SCHEMA_PATH = SKILL_DIR / "schemas" / "state.schema.json"
VALID_PHASES = {f"phase-{index}" for index in range(8)}


def canonical_json(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON for hashing and artifact comparisons."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read valid JSON from {path}: {error}") from error


def compute_state_hash(state_path: Path) -> str:
    """Compute SHA-256 over canonical parsed state JSON, not raw file bytes."""
    state = load_json(state_path)
    validate_state_instance(state)
    return hashlib.sha256(canonical_json(state)).hexdigest()


def atomic_write_json(path: Path, value: Any) -> None:
    """Write JSON atomically in the destination directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def validate_artifact_instance(artifact: dict, *, strict_semantics: bool = True) -> None:
    """Validate generated output against the checked-in artifact schema."""
    try:
        import jsonschema
    except ImportError as error:
        raise RuntimeError("jsonschema is required to validate generated artifacts") from error

    schema = load_json(SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(artifact), key=lambda item: list(item.path))
    if errors:
        details = "; ".join(error.message for error in errors[:5])
        raise ValueError(f"generated artifact does not conform to schema: {details}")
    if strict_semantics:
        subscores = artifact["confidence"]["subscores"]
        expected = sum(subscores.values())
        if abs(artifact["confidence"]["composite"] - expected) > 1e-9:
            raise ValueError(f"artifact confidence composite {artifact['confidence']['composite']} != subscore sum {expected}")
        if artifact.get("evidence_limited") and artifact["gate_decision"]["decision"] == "GO":
            raise ValueError("evidence-limited artifacts cannot carry a GO decision")


def validate_state_instance(state: dict) -> None:
    """Require artifact generation to consume a schema-valid v8 state."""
    try:
        import jsonschema
    except ImportError as error:
        raise RuntimeError("jsonschema is required to validate source state") from error

    schema = load_json(STATE_SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(state), key=lambda item: list(item.path))
    if errors:
        details = "; ".join(error.message for error in errors[:5])
        raise ValueError(f"source state does not conform to schema: {details}")


def normalize_phase(state: dict, phase: str | None) -> str:
    candidate = phase or state.get("current_phase")
    if candidate in VALID_PHASES:
        return candidate
    if candidate == "VALIDATION_PENDING":
        return "phase-5"
    if candidate == "completed":
        return "phase-7"
    return "phase-0"


def infer_gate(state: dict) -> str:
    if state.get("evidence_limited_mode"):
        return "CONDITIONAL_GO"
    if state.get("market_validation_status") == "validated":
        return "GO"
    if state.get("market_validation_status") == "invalidated":
        return "STOP"
    return "CONDITIONAL_GO"


def normalize_gate(state: dict) -> str:
    decision = state.get("current_gate") or infer_gate(state)
    if decision == "GO" and state.get("evidence_limited_mode"):
        return "CONDITIONAL_GO"
    if decision == "GO" and state.get("experiments_executed", 0) == 0:
        return "CONDITIONAL_GO"
    return decision if decision in {"GO", "CONDITIONAL_GO", "RECYCLE", "STOP"} else infer_gate(state)


def generate_artifact(state: dict, state_hash: str, phase: str | None = None) -> dict:
    """Generate a schema-valid artifact from audit state."""
    validate_state_instance(state)
    confidence = state.get("decision_confidence", {})
    artifact = {
        "artifact_id": f"ART-{state.get('audit_id', 'UNKNOWN')}-{phase or state.get('current_phase', 'current')}",
        "phase": normalize_phase(state, phase),
        "scope": state.get("scope"),
        "evidence_limited": bool(state.get("evidence_limited_mode", False)),
        "confidence": {
            "composite": confidence.get("composite", 0),
            "subscores": {
                "evidence_quality": confidence.get("quality", 0),
                "source_coverage": confidence.get("coverage", 0),
                "internal_consistency": confidence.get("consistency", 0),
                "counter_evidence_survival": confidence.get("counter", 0),
                "validation_evidence": confidence.get("validation", 0),
            },
            "iterations": 1,
            "improvements_made": "",
        },
        "findings": [],
        "gap_analysis": [],
        "adversarial_review": {},
        "adversarial_reviews": [],
        "gate_decision": {
            "decision": normalize_gate(state),
            "conditions": state.get("evidence_limitations", []),
        },
        "research_question_tree_update": {},
        "next_phase_skill_selection": "",
        "generated_from_state_hash": state_hash,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "superseded": False,
        "schema_version": "v8",
    }
    validate_artifact_instance(artifact)
    return artifact


def check_artifact(artifact_path: Path, state_path: Path) -> dict:
    """Verify schema, current-state hash, and non-superseded status."""
    current_hash = compute_state_hash(state_path)
    try:
        artifact = load_json(artifact_path)
        validate_artifact_instance(artifact)
        schema_valid = True
        schema_error = None
    except (ValueError, RuntimeError) as error:
        artifact = {}
        schema_valid = False
        schema_error = str(error)

    artifact_hash = artifact.get("generated_from_state_hash")
    superseded = bool(artifact.get("superseded", False))
    match = schema_valid and artifact_hash == current_hash and not superseded
    return {
        "match": match,
        "schema_valid": schema_valid,
        "schema_error": schema_error,
        "current_hash": current_hash,
        "artifact_hash": artifact_hash,
        "superseded": superseded,
        "artifact_id": artifact.get("artifact_id", "unknown"),
    }


def supersede_and_regenerate(artifact_path: Path, state_path: Path, output_path: Path | None = None) -> dict:
    """Preserve the old artifact as superseded and write a distinct replacement."""
    old_artifact = load_json(artifact_path)
    try:
        validate_artifact_instance(old_artifact)
    except ValueError:
        # v5-v7 artifacts used the same core shape but did not always carry a
        # top-level schema_version. They may be superseded, never treated as
        # current v8 artifacts, after this narrow compatibility normalization.
        if old_artifact.get("schema_version") is not None:
            raise
        old_artifact["schema_version"] = "v8"
        old_artifact.setdefault("generated_from_state_hash", None)
        old_artifact.setdefault("generated_at", None)
        old_artifact.setdefault("superseded", False)
        validate_artifact_instance(old_artifact, strict_semantics=False)
    state = load_json(state_path)
    state_hash = compute_state_hash(state_path)

    old_artifact["superseded"] = True
    atomic_write_json(artifact_path, old_artifact)

    if output_path is None or output_path.resolve() == artifact_path.resolve():
        output_path = artifact_path.with_name(f"{artifact_path.stem}.regenerated{artifact_path.suffix}")

    new_artifact = generate_artifact(state, state_hash)
    atomic_write_json(output_path, new_artifact)
    return {
        "superseded_artifact": str(artifact_path),
        "new_artifact": str(output_path),
        "state_hash": state_hash,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Artifact reproducibility for positioning audit v8")
    parser.add_argument("--state", required=True, help="Path to state.json")
    parser.add_argument("--artifact", help="Path to existing artifact (for --check or --supersede)")
    parser.add_argument("--output", help="Output path for generated or superseded artifact")
    parser.add_argument("--generate", action="store_true", help="Generate new artifact from state")
    parser.add_argument("--check", action="store_true", help="Check artifact against state")
    parser.add_argument("--supersede", action="store_true", help="Supersede old artifact and generate a replacement")
    args = parser.parse_args()
    state_path = Path(args.state)

    try:
        if args.check:
            if not args.artifact:
                raise ValueError("--check requires --artifact")
            result = check_artifact(Path(args.artifact), state_path)
            if not result["match"]:
                raise ValueError(
                    f"artifact check failed: schema_valid={result['schema_valid']}, "
                    f"superseded={result['superseded']}, hash_match={result['artifact_hash'] == result['current_hash']}"
                    + (f" ({result['schema_error']})" if result["schema_error"] else "")
                )
            print(f"OK: {result['artifact_id']} matches canonical state hash {result['current_hash'][:16]}...")
            return

        if args.supersede:
            if not args.artifact:
                raise ValueError("--supersede requires --artifact")
            result = supersede_and_regenerate(Path(args.artifact), state_path, Path(args.output) if args.output else None)
            print(f"Superseded: {result['superseded_artifact']}")
            print(f"Replacement: {result['new_artifact']}")
            print(f"State hash: {result['state_hash'][:16]}...")
            return

        if args.generate:
            state = load_json(state_path)
            state_hash = compute_state_hash(state_path)
            artifact = generate_artifact(state, state_hash)
            output = Path(args.output) if args.output else state_path.parent / "artifact.json"
            atomic_write_json(output, artifact)
            print(f"Generated artifact: {output}")
            print(f"State hash: {state_hash[:16]}...")
            return

        raise ValueError("specify --generate, --check, or --supersede")
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
