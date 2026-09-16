#!/usr/bin/env python3
"""Validate skill-optimizer evidence JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set


VALID_RESULTS = {"pass", "fail", "not_run"}
VALID_STRICTNESS = {
    "supportive",
    "neutral",
    "competing",
    "adversarial",
    "regression",
    "custom",
}
PLACEHOLDER_EVIDENCE = {
    "add command output, transcript, artifact, or reviewer note",
    "todo",
    "tbd",
    "placeholder",
    "evidence not collected yet; replace this before validation.",
}


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("top-level JSON must be an object")
    return value


def is_blank(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def parse_csv(values: Optional[str]) -> Set[str]:
    if not values:
        return set()
    return {item.strip() for item in values.split(",") if item.strip()}


def evidence_is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered in PLACEHOLDER_EVIDENCE or lowered.startswith("add command output")


def require_string_list(
    errors: List[str],
    scenario_id: str,
    field: str,
    value: Any,
    *,
    allow_empty: bool = False,
) -> List[str]:
    if not isinstance(value, list):
        errors.append(f"{scenario_id} {field} must be a list")
        return []
    if not allow_empty and not value:
        errors.append(f"{scenario_id} {field} must be a non-empty list")
    normalized: List[str] = []
    for index, item in enumerate(value, start=1):
        if is_blank(item):
            errors.append(f"{scenario_id} {field}[{index}] must be a non-empty string")
        else:
            normalized.append(str(item).strip())
    return normalized


def count_results(scenarios: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"pass": 0, "fail": 0, "not_run": 0}
    for scenario in scenarios:
        result = scenario.get("result")
        if result in counts:
            counts[result] += 1
    return counts


def validate(
    data: Dict[str, Any],
    require_results: bool,
    require_all_pass: bool,
    *,
    allow_missing_target: bool = False,
    require_coverage_tags: bool = False,
    require_strictness: Optional[Set[str]] = None,
    require_artifacts_exist: bool = False,
) -> List[str]:
    errors: List[str] = []
    if data.get("schema_version") != "skill-optimizer.v1":
        errors.append("schema_version must be skill-optimizer.v1")
    if not data.get("skill_name"):
        errors.append("skill_name is required")
    target_path = data.get("target_path")
    if not target_path:
        errors.append("target_path is required")
    elif not str(target_path).startswith("/"):
        errors.append("target_path must be absolute")
    elif not allow_missing_target and not Path(str(target_path)).exists():
        errors.append(f"target_path does not exist: {target_path}")

    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("scenarios must be a non-empty list")
        scenarios = []

    seen = set()
    strictness_seen: Set[str] = set()
    for index, scenario in enumerate(scenarios, start=1):
        if not isinstance(scenario, dict):
            errors.append(f"scenario {index} must be an object")
            continue
        scenario_id = scenario.get("id")
        if not scenario_id:
            errors.append(f"scenario {index} is missing id")
        elif scenario_id in seen:
            errors.append(f"scenario id is duplicated: {scenario_id}")
        else:
            seen.add(scenario_id)
        for field in ["title", "prompt", "strictness", "grader", "expected", "result", "evidence"]:
            if field not in scenario:
                errors.append(f"{scenario_id or index} missing {field}")
        scenario_label = str(scenario_id or index)
        strictness = scenario.get("strictness")
        if is_blank(strictness):
            errors.append(f"{scenario_label} strictness must be a non-empty string")
        elif strictness not in VALID_STRICTNESS:
            errors.append(
                f"{scenario_label} strictness must be one of {', '.join(sorted(VALID_STRICTNESS))}"
            )
        else:
            strictness_seen.add(str(strictness))
        result = scenario.get("result")
        if result not in VALID_RESULTS:
            errors.append(f"{scenario_label} result must be pass, fail, or not_run")
        elif result == "not_run" and is_blank(scenario.get("not_run_reason")):
            errors.append(f"{scenario_label} not_run requires not_run_reason")

        require_string_list(errors, scenario_label, "expected", scenario.get("expected"))
        evidence = require_string_list(errors, scenario_label, "evidence", scenario.get("evidence"))
        for item in evidence:
            if evidence_is_placeholder(item):
                errors.append(f"{scenario_label} evidence contains placeholder text")

        coverage_tags = scenario.get("coverage_tags", [])
        if require_coverage_tags or "coverage_tags" in scenario:
            require_string_list(errors, scenario_label, "coverage_tags", coverage_tags)

        artifact_paths = scenario.get("artifact_paths", [])
        if "artifact_paths" in scenario:
            paths = require_string_list(
                errors, scenario_label, "artifact_paths", artifact_paths, allow_empty=True
            )
            if require_artifacts_exist:
                for item in paths:
                    path = Path(item)
                    if not path.is_absolute():
                        errors.append(f"{scenario_label} artifact_paths must be absolute: {item}")
                    elif not path.exists():
                        errors.append(f"{scenario_label} artifact path does not exist: {item}")

    summary = data.get("summary")
    counts = count_results([scenario for scenario in scenarios if isinstance(scenario, dict)])
    passed = counts["pass"]
    failed = counts["fail"]
    not_run = counts["not_run"]
    if not isinstance(summary, dict):
        errors.append("summary must be an object")
    else:
        expected_counts = {
            "passed": passed,
            "failed": failed,
            "not_run": not_run,
            "total": len(scenarios),
        }
        for field, expected in expected_counts.items():
            value = summary.get(field)
            if value is not None and value != expected:
                errors.append(f"summary.{field} must be {expected}")
        score = summary.get("score")
        if score is not None:
            if not (isinstance(score, (int, float)) and 0 <= score <= 1):
                errors.append("summary.score must be null or a number from 0 to 1")
            elif scenarios:
                expected_score = passed / len(scenarios)
                if abs(float(score) - expected_score) > 0.0001:
                    errors.append(
                        f"summary.score must match pass ratio {expected_score:.4f}"
                    )

    required_strictness = require_strictness or set()
    missing_strictness = sorted(required_strictness - strictness_seen)
    if missing_strictness:
        errors.append(f"missing required strictness coverage: {', '.join(missing_strictness)}")

    if require_results and not_run:
        errors.append(f"{not_run} scenarios are not_run")
    if require_all_pass and (failed or not_run):
        errors.append(f"all-pass gate failed: {passed} pass, {failed} fail, {not_run} not_run")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", help="Evidence JSON path")
    parser.add_argument("--require-results", action="store_true")
    parser.add_argument("--require-all-pass", action="store_true")
    parser.add_argument("--allow-missing-target", action="store_true")
    parser.add_argument("--require-coverage-tags", action="store_true")
    parser.add_argument(
        "--require-strictness",
        help="Comma-separated strictness values that must be represented.",
    )
    parser.add_argument("--require-artifacts-exist", action="store_true")
    args = parser.parse_args()

    try:
        data = load_json(Path(args.evidence))
        errors = validate(
            data,
            args.require_results,
            args.require_all_pass,
            allow_missing_target=args.allow_missing_target,
            require_coverage_tags=args.require_coverage_tags,
            require_strictness=parse_csv(args.require_strictness),
            require_artifacts_exist=args.require_artifacts_exist,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should report validation failures plainly.
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2

    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 2

    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
