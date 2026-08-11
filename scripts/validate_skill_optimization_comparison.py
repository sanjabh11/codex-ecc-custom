#!/usr/bin/env python3
"""Fail-closed validator for skill-optimizer strict-improve comparisons."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def _validate_counts(name: str, counts: dict[str, Any], errors: list[str]) -> None:
    total = counts["pass"] + counts["fail"] + counts["not_run"]
    if counts["total"] != total:
        errors.append(f"{name}.total must equal pass + fail + not_run")


def validate(path: Path, schema_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        import jsonschema

        payload = _load(path)
        schema = _load(schema_path)
        validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        errors.extend(error.message for error in validator.iter_errors(payload))
    except ImportError as exc:
        errors.append(f"jsonschema is required: {exc}")
        payload = {}
    except ValueError as exc:
        errors.append(str(exc))
        payload = {}

    if not errors and isinstance(payload, dict):
        _validate_counts("before_counts", payload["before_counts"], errors)
        _validate_counts("after_counts", payload["after_counts"], errors)
        expected_delta = payload["after_score"] - payload["before_score"]
        if not math.isclose(payload["delta"], expected_delta, abs_tol=1e-9):
            errors.append("delta must equal after_score - before_score")
        if payload["decision"] == "promote":
            after = payload["after_counts"]
            if payload["missing_baseline"] or payload["regressed"] or payload["blocking_reasons"]:
                errors.append("promote requires no missing baseline, regressions, or blocking reasons")
            if after["fail"] or after["not_run"]:
                errors.append("promote requires all after scenarios to pass")

    return {
        "status": "valid" if not errors else "invalid",
        "comparison": str(path),
        "schema_version": "skill-optimization-comparison.v1" if isinstance(payload, dict) else None,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("comparison", type=Path)
    parser.add_argument("--schema", type=Path, default=Path("schemas/skill-optimization-comparison.schema.json"))
    args = parser.parse_args()
    try:
        result = validate(args.comparison, args.schema)
    except Exception as exc:  # CLI boundary must not leak a traceback.
        result = {"status": "invalid", "comparison": str(args.comparison), "errors": [f"internal validator error: {exc}"]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
