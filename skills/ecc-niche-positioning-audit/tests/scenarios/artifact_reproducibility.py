#!/usr/bin/env python3
"""Scenario 6: canonical artifact hashing and safe supersede behavior."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from generate_artifact import (  # noqa: E402
    atomic_write_json,
    check_artifact,
    compute_state_hash,
    generate_artifact,
    supersede_and_regenerate,
)


def run() -> int:
    tmpdir = Path(tempfile.mkdtemp(prefix="artifact_repro_"))
    state_path = tmpdir / "state.json"
    state = {
        "audit_id": "AUD-ARTIFACT-006",
        "product_context": "Evidence-backed positioning tool",
        "scope": "standard",
        "started_at": "2026-07-16T10:00:00Z",
        "current_phase": "VALIDATION_PENDING",
        "current_gate": "GO",
        "evidence_limited_mode": True,
        "evidence_types_present": ["product_promise"],
        "evidence_limitations": ["No first-party buyer evidence"],
        "phases_completed": ["phase-0", "phase-1", "phase-2", "phase-3", "phase-4", "phase-5"],
        "gates_passed": [{"gate": "gate-1", "decision": "CONDITIONAL_GO"}],
        "experiments_executed": 0,
        "experiments_designed": 1,
        "market_validation_status": "validation_pending",
        "last_updated": "2026-07-16T10:00:00Z",
        "schema_version": "v8",
        "decision_confidence": {
            "composite": 40,
            "quality": 12,
            "coverage": 10,
            "consistency": 10,
            "counter": 8,
            "validation": 0,
        },
        "evidence_limitations": ["No first-party buyer evidence"],
    }
    atomic_write_json(state_path, state)
    state_hash = compute_state_hash(state_path)
    artifact_path = tmpdir / "artifact.json"
    atomic_write_json(artifact_path, generate_artifact(state, state_hash))

    first_check = check_artifact(artifact_path, state_path)
    assert first_check["match"], first_check

    inconsistent = json.loads(artifact_path.read_text())
    inconsistent["confidence"]["composite"] = 99
    atomic_write_json(artifact_path, inconsistent)
    assert not check_artifact(artifact_path, state_path)["match"], "Confidence arithmetic drift must fail artifact checks"
    atomic_write_json(artifact_path, generate_artifact(state, state_hash))

    # Reformat and reorder the same semantic JSON; canonical hashing must remain stable.
    state_path.write_text(json.dumps({"decision_confidence": state["decision_confidence"], **{k: v for k, v in state.items() if k != "decision_confidence"}}, indent=4))
    assert check_artifact(artifact_path, state_path)["match"], "Formatting changes must not create artifact drift"

    result = supersede_and_regenerate(artifact_path, state_path)
    superseded = json.loads(artifact_path.read_text())
    assert superseded["superseded"] is True, superseded
    replacement = Path(result["new_artifact"])
    assert replacement.exists(), replacement
    assert check_artifact(replacement, state_path)["match"], "Replacement must match current canonical state"
    assert not check_artifact(artifact_path, state_path)["match"], "Superseded artifacts must not pass current-artifact checks"

    legacy_path = tmpdir / "legacy-v7-artifact.json"
    legacy = generate_artifact(state, state_hash)
    legacy.pop("schema_version")
    atomic_write_json(legacy_path, legacy)
    legacy_result = supersede_and_regenerate(legacy_path, state_path)
    assert json.loads(legacy_path.read_text())["superseded"] is True
    assert check_artifact(Path(legacy_result["new_artifact"]), state_path)["match"]

    cli = SKILL_DIR / "scripts" / "generate_artifact.py"
    cli_artifact = tmpdir / "cli-artifact.json"
    generated = subprocess.run([sys.executable, str(cli), "--state", str(state_path), "--generate", "--output", str(cli_artifact)], capture_output=True, text=True)
    assert generated.returncode == 0, generated.stderr
    checked = subprocess.run([sys.executable, str(cli), "--state", str(state_path), "--artifact", str(cli_artifact), "--check"], capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr
    superseded = subprocess.run([sys.executable, str(cli), "--state", str(state_path), "--artifact", str(cli_artifact), "--supersede", "--output", str(tmpdir / "cli-replacement.json")], capture_output=True, text=True)
    assert superseded.returncode == 0, superseded.stderr
    assert (tmpdir / "cli-replacement.json").exists()

    print("PASS: artifact_reproducibility — canonical hash, schema validation, atomic supersede")
    return 0


if __name__ == "__main__":
    sys.exit(run())
