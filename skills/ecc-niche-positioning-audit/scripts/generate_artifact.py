#!/usr/bin/env python3
"""Artifact reproducibility script for ecc-niche-positioning-audit v8.

Computes SHA-256 hash of canonical state.json and generates or verifies
artifacts against that hash. Supports three modes:

  --generate : Create a new artifact from state.json with state hash populated
  --check    : Verify an existing artifact's hash matches current state
  --supersede: Mark old artifacts as superseded when regenerating

Usage:
  python3 generate_artifact.py --state <path/to/state.json> --generate [--output <path>]
  python3 generate_artifact.py --state <path/to/state.json> --artifact <path> --check
  python3 generate_artifact.py --state <path/to/state.json> --artifact <path> --supersede [--output <path>]
"""
import sys
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone


def compute_state_hash(state_path: Path) -> str:
    """Compute SHA-256 hash of the canonical state.json file."""
    content = state_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def generate_artifact(state: dict, state_hash: str, phase: str = None) -> dict:
    """Generate a minimal artifact from state, with state hash populated."""
    confidence = state.get("decision_confidence", {})
    subscores = {
        "evidence_quality": confidence.get("quality", 0),
        "source_coverage": confidence.get("coverage", 0),
        "internal_consistency": confidence.get("consistency", 0),
        "counter_evidence_survival": confidence.get("counter", 0),
        "validation_evidence": confidence.get("validation", 0),
    }

    artifact = {
        "artifact_id": f"ART-{state.get('audit_id', 'UNKNOWN')}-{phase or 'current'}",
        "phase": phase or state.get("current_phase", "phase-0"),
        "scope": state.get("scope"),
        "evidence_limited": state.get("evidence_limited_mode", False),
        "confidence": {
            "composite": confidence.get("composite", 0),
            "subscores": subscores,
            "iterations": 1,
            "improvements_made": "",
        },
        "findings": [],
        "gap_analysis": [],
        "adversarial_review": {},
        "adversarial_reviews": [],
        "gate_decision": {
            "decision": state.get("current_gate") or _infer_gate(state),
            "conditions": state.get("evidence_limitations", []),
        },
        "research_question_tree_update": {},
        "next_phase_skill_selection": "",
        "generated_from_state_hash": state_hash,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "superseded": False,
    }
    return artifact


def _infer_gate(state: dict) -> str:
    """Infer gate decision from state."""
    if state.get("evidence_limited_mode"):
        return "CONDITIONAL_GO"
    if state.get("market_validation_status") == "validated":
        return "GO"
    if state.get("market_validation_status") == "invalidated":
        return "STOP"
    if state.get("experiments_executed", 0) == 0:
        return "CONDITIONAL_GO"
    return "GO"


def check_artifact(artifact_path: Path, state_path: Path) -> dict:
    """Verify an existing artifact's state hash matches current state."""
    current_hash = compute_state_hash(state_path)
    try:
        artifact = json.loads(artifact_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {"match": False, "error": str(e), "current_hash": current_hash}

    artifact_hash = artifact.get("generated_from_state_hash")
    superseded = artifact.get("superseded", False)

    return {
        "match": artifact_hash == current_hash,
        "current_hash": current_hash,
        "artifact_hash": artifact_hash,
        "superseded": superseded,
        "artifact_id": artifact.get("artifact_id", "unknown"),
    }


def supersede_and_regenerate(artifact_path: Path, state_path: Path, output_path: Path = None) -> dict:
    """Mark old artifact as superseded and generate a new one."""
    state = json.loads(state_path.read_text())
    state_hash = compute_state_hash(state_path)

    if artifact_path.exists():
        old_artifact = json.loads(artifact_path.read_text())
        old_artifact["superseded"] = True
        artifact_path.write_text(json.dumps(old_artifact, indent=2))

    new_artifact = generate_artifact(state, state_hash)
    out = output_path or artifact_path
    out.write_text(json.dumps(new_artifact, indent=2))

    return {
        "superseded_artifact": str(artifact_path),
        "new_artifact": str(out),
        "state_hash": state_hash,
    }


def main():
    parser = argparse.ArgumentParser(description="Artifact reproducibility for positioning audit v8")
    parser.add_argument("--state", required=True, help="Path to state.json")
    parser.add_argument("--artifact", help="Path to existing artifact (for --check or --supersede)")
    parser.add_argument("--output", help="Output path for generated artifact")
    parser.add_argument("--generate", action="store_true", help="Generate new artifact from state")
    parser.add_argument("--check", action="store_true", help="Check artifact hash against state")
    parser.add_argument("--supersede", action="store_true", help="Supersede old artifact and regenerate")

    args = parser.parse_args()
    state_path = Path(args.state)

    if not state_path.exists():
        print(f"ERROR: state.json not found at {state_path}")
        sys.exit(1)

    if args.check:
        if not args.artifact:
            print("ERROR: --check requires --artifact path")
            sys.exit(1)
        result = check_artifact(Path(args.artifact), state_path)
        if result["match"]:
            print(f"OK: Artifact hash matches state hash")
            print(f"  artifact_id: {result.get('artifact_id', 'unknown')}")
            print(f"  superseded: {result.get('superseded', False)}")
            print(f"  hash: {result['current_hash'][:16]}...")
            sys.exit(0)
        else:
            print(f"MISMATCH: Artifact hash does not match state hash")
            print(f"  current state hash: {result.get('current_hash', 'N/A')[:16]}...")
            if result.get('artifact_hash'):
                print(f"  artifact hash:      {result.get('artifact_hash', 'N/A')[:16]}...")
            else:
                print(f"  artifact hash:      N/A")
            if result.get("superseded"):
                print(f"  WARNING: Artifact is superseded")
            sys.exit(1)

    elif args.supersede:
        if not args.artifact:
            print("ERROR: --supersede requires --artifact path")
            sys.exit(1)
        output = Path(args.output) if args.output else None
        result = supersede_and_regenerate(Path(args.artifact), state_path, output)
        print(f"Superceded: {result['superseded_artifact']}")
        print(f"New artifact: {result['new_artifact']}")
        print(f"State hash: {result['state_hash'][:16]}...")
        sys.exit(0)

    elif args.generate:
        state = json.loads(state_path.read_text())
        state_hash = compute_state_hash(state_path)
        artifact = generate_artifact(state, state_hash)
        output = Path(args.output) if args.output else state_path.parent / "artifact.json"
        output.write_text(json.dumps(artifact, indent=2))
        print(f"Generated artifact: {output}")
        print(f"State hash: {state_hash[:16]}...")
        print(f"Generated at: {artifact['generated_at']}")
        sys.exit(0)

    else:
        print("ERROR: Specify --generate, --check, or --supersede")
        sys.exit(1)


if __name__ == "__main__":
    main()
