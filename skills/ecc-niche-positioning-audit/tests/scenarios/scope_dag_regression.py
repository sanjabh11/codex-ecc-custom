#!/usr/bin/env python3
"""Scenario 8: scope-DAG validation rejects reordered or incomplete paths."""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from validate_skill import SKILL_FILE, check_scope_dag  # noqa: E402


def run() -> int:
    body = SKILL_FILE.read_text().split("---", 2)[-1]
    assert check_scope_dag(body)["valid"], "canonical scope DAG must pass"

    malformed = body.replace(
        "P0 → P1 → P2 → P3-lite → P4-lite → TERMINAL",
        "P0 → P1 → P2 → P4-lite → P3-lite → TERMINAL",
    )
    result = check_scope_dag(malformed)
    assert not result["valid"], "reordered quick path must fail"
    assert any("Quick Mode Path" in error for error in result["errors"]), result

    print("PASS: scope_dag_regression — reordered path is rejected")
    return 0


if __name__ == "__main__":
    sys.exit(run())
