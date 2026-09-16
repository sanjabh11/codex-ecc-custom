#!/usr/bin/env python3
"""Compare two skill-optimizer evidence runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from validate_skill_evidence import validate


def load(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("schema_version") != "skill-optimizer.v1":
        raise SystemExit(f"{path}: schema_version must be skill-optimizer.v1")
    errors = validate(data, require_results=True, require_all_pass=False)
    if errors:
        joined = "\n- ".join(errors)
        raise SystemExit(f"{path}: invalid evidence\n- {joined}")
    return data


def score(data: Dict[str, Any]) -> float:
    summary_score = data.get("summary", {}).get("score")
    if isinstance(summary_score, (int, float)):
        return float(summary_score)
    scenarios = data.get("scenarios", [])
    if not scenarios:
        return 0.0
    passed = sum(1 for item in scenarios if item.get("result") == "pass")
    return passed / len(scenarios)


def result_map(data: Dict[str, Any]) -> Dict[str, str]:
    return {item["id"]: item.get("result", "not_run") for item in data.get("scenarios", []) if "id" in item}


def count_map(data: Dict[str, Any]) -> Dict[str, int]:
    results = result_map(data)
    return {
        "pass": sum(1 for value in results.values() if value == "pass"),
        "fail": sum(1 for value in results.values() if value == "fail"),
        "not_run": sum(1 for value in results.values() if value == "not_run"),
        "total": len(results),
    }


def compare(
    before: Dict[str, Any],
    after: Dict[str, Any],
    mode: str,
    *,
    allow_target_mismatch: bool = False,
) -> Dict[str, Any]:
    before_score = score(before)
    after_score = score(after)
    before_results = result_map(before)
    after_results = result_map(after)
    before_ids = set(before_results)
    after_ids = set(after_results)
    missing_baseline = sorted(before_ids - after_ids)
    added_scenarios = sorted(after_ids - before_ids)

    regressed: List[str] = []
    newly_passing: List[str] = []
    for scenario_id, before_result in before_results.items():
        if scenario_id not in after_results:
            continue
        after_result = after_results[scenario_id]
        if before_result == "pass" and after_result != "pass":
            regressed.append(scenario_id)
        if before_result != "pass" and after_result == "pass":
            newly_passing.append(scenario_id)

    blocking_reasons: List[str] = []
    if missing_baseline:
        blocking_reasons.append("candidate removed baseline scenarios")
    if regressed:
        blocking_reasons.append("candidate regressed previously passing scenarios")
    if not allow_target_mismatch:
        for field in ["skill_name", "target_path"]:
            if before.get(field) != after.get(field):
                blocking_reasons.append(f"{field} differs between before and after")

    if mode == "strict-improve":
        if after_score <= before_score:
            blocking_reasons.append("candidate did not strictly improve score")
        decision = "promote" if not blocking_reasons else "hold"
    else:
        if after_score < before_score:
            blocking_reasons.append("candidate score is lower than baseline")
        decision = "promote" if not blocking_reasons else "hold"

    return {
        "mode": mode,
        "skill_name": after.get("skill_name", before.get("skill_name", "")),
        "target_path": after.get("target_path", before.get("target_path", "")),
        "before_score": before_score,
        "after_score": after_score,
        "delta": after_score - before_score,
        "before_counts": count_map(before),
        "after_counts": count_map(after),
        "missing_baseline": missing_baseline,
        "added_scenarios": added_scenarios,
        "regressed": regressed,
        "newly_passing": newly_passing,
        "blocking_reasons": sorted(set(blocking_reasons)),
        "decision": decision,
    }


def markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# Skill Run Comparison",
        "",
        f"- Mode: `{report['mode']}`",
        f"- Skill: `{report['skill_name']}`",
        f"- Target: `{report['target_path']}`",
        f"- Before score: {report['before_score']:.3f}",
        f"- After score: {report['after_score']:.3f}",
        f"- Delta: {report['delta']:.3f}",
        f"- Decision: `{report['decision']}`",
        f"- Blocking reasons: {', '.join(report['blocking_reasons']) or 'None'}",
        "",
        "| Run | Pass | Fail | Not run | Total |",
        "|---|---:|---:|---:|---:|",
        (
            f"| Before | {report['before_counts']['pass']} | {report['before_counts']['fail']} | "
            f"{report['before_counts']['not_run']} | {report['before_counts']['total']} |"
        ),
        (
            f"| After | {report['after_counts']['pass']} | {report['after_counts']['fail']} | "
            f"{report['after_counts']['not_run']} | {report['after_counts']['total']} |"
        ),
        "",
        "| Type | Scenario IDs |",
        "|---|---|",
        f"| Missing baseline | {', '.join(report['missing_baseline']) or 'None'} |",
        f"| Added scenarios | {', '.join(report['added_scenarios']) or 'None'} |",
        f"| Regressed | {', '.join(report['regressed']) or 'None'} |",
        f"| Newly passing | {', '.join(report['newly_passing']) or 'None'} |",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--mode", choices=["strict-improve", "no-regression"], default="strict-improve")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--allow-target-mismatch", action="store_true")
    args = parser.parse_args()

    report = compare(
        load(Path(args.before)),
        load(Path(args.after)),
        args.mode,
        allow_target_mismatch=args.allow_target_mismatch,
    )
    if args.output == "json":
        print(json.dumps(report, indent=2))
    else:
        print(markdown(report), end="")
    return 0 if report["decision"] == "promote" else 1


if __name__ == "__main__":
    raise SystemExit(main())
