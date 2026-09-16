#!/usr/bin/env python3
"""Compare completed one-repo commercial launch evidence JSON files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from validate_launch_evidence import validate


DECISION_WEIGHT = {
    "commercial-ready": 4,
    "sellable-with-caveats": 3,
    "pilot-only": 2,
    "blocked": 1,
    "unknown": 0,
}


def load_report(path_text: str) -> Dict[str, Any]:
    path = Path(path_text).expanduser().resolve()
    if path.is_dir():
        raise SystemExit(f"refusing raw repo directory; provide launch evidence JSON: {path}")
    if not path.exists():
        raise SystemExit(f"report does not exist: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid JSON in {path}: {error}") from error
    if not isinstance(data, dict):
        raise SystemExit(f"report must be a JSON object: {path}")
    errors = validate(data)
    if errors:
        joined = "\n- ".join(errors)
        raise SystemExit(f"invalid launch evidence in {path}\n- {joined}")
    data["_source_path"] = str(path)
    return data


def as_number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def text_value(value: Any, default: str = "unknown") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def normalize_scores(data: Dict[str, Any]) -> Dict[str, float]:
    raw = data.get("scores") or data.get("launch_score") or {}
    if not isinstance(raw, dict):
        raw = {}
    return {
        "security": as_number(raw.get("security")),
        "readiness": as_number(raw.get("readiness")),
        "sellability": as_number(raw.get("sellability")),
        "evidence": as_number(raw.get("evidence")),
        "overall": as_number(raw.get("overall")),
    }


def repo_name(data: Dict[str, Any]) -> str:
    repo = data.get("repo")
    if isinstance(repo, dict):
        return text_value(repo.get("name"), Path(text_value(repo.get("path"), "repo")).name)
    return text_value(data.get("repo_name"), Path(data["_source_path"]).stem)


def repo_path(data: Dict[str, Any]) -> str:
    repo = data.get("repo")
    if isinstance(repo, dict):
        return text_value(repo.get("path"), "")
    return text_value(data.get("repo_path"), "")


def decision(data: Dict[str, Any]) -> str:
    value = data.get("launch_decision") or data.get("decision")
    if isinstance(value, dict):
        value = value.get("value") or value.get("decision")
    normalized = text_value(value).lower()
    return normalized if normalized in DECISION_WEIGHT else "unknown"


def gaps(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = data.get("gaps") or data.get("gap_analysis") or []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []


def unresolved_p0_p1(gap_items: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"P0": 0, "P1": 0}
    resolved_statuses = {"fixed", "resolved", "closed", "done", "accepted"}
    for item in gap_items:
        severity = text_value(item.get("severity"), "").upper()
        status = text_value(item.get("status"), "open").lower()
        if severity in counts and status not in resolved_statuses:
            counts[severity] += 1
    return counts


def list_len(data: Dict[str, Any], key: str) -> int:
    value = data.get(key)
    return len(value) if isinstance(value, list) else 0


def summarize_report(data: Dict[str, Any]) -> Dict[str, Any]:
    score = normalize_scores(data)
    gap_items = gaps(data)
    blockers = unresolved_p0_p1(gap_items)
    launch_decision = decision(data)
    return {
        "source_path": data["_source_path"],
        "repo_name": repo_name(data),
        "repo_path": repo_path(data),
        "profile": (data.get("repo") or {}).get("profile", "unknown") if isinstance(data.get("repo"), dict) else "unknown",
        "launch_decision": launch_decision,
        "scores": score,
        "unresolved_p0": blockers["P0"],
        "unresolved_p1": blockers["P1"],
        "gap_count": len(gap_items),
        "pain_point_count": list_len(data, "pain_points"),
        "target_customer_count": list_len(data, "target_customers"),
        "rank_score": (
            DECISION_WEIGHT[launch_decision] * 100
            + score["overall"] * 10
            + score["sellability"] * 3
            + score["evidence"] * 2
            - blockers["P0"] * 50
            - blockers["P1"] * 15
        ),
    }


def compare(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    summaries = [summarize_report(report) for report in reports]
    ordered = sorted(
        summaries,
        key=lambda item: (
            item["rank_score"],
            -item["unresolved_p0"],
            -item["unresolved_p1"],
            item["scores"]["overall"],
        ),
        reverse=True,
    )
    return {
        "schema_version": 1,
        "report_count": len(summaries),
        "reports": summaries,
        "recommended_order": [
            {
                "rank": index,
                "repo_name": item["repo_name"],
                "launch_decision": item["launch_decision"],
                "overall_score": item["scores"]["overall"],
                "unresolved_p0": item["unresolved_p0"],
                "unresolved_p1": item["unresolved_p1"],
                "reason": order_reason(item),
            }
            for index, item in enumerate(ordered, start=1)
        ],
    }


def order_reason(item: Dict[str, Any]) -> str:
    if item["unresolved_p0"] > 0:
        return "Lower priority until P0 blockers are resolved."
    if item["launch_decision"] == "commercial-ready":
        return "Strongest launch candidate by decision and score."
    if item["launch_decision"] == "sellable-with-caveats":
        return "Good sales candidate with caveats to disclose."
    if item["launch_decision"] == "pilot-only":
        return "Use for controlled pilot, not broad launch."
    if item["unresolved_p1"] > 0:
        return "Needs P1 blocker reduction before commercial push."
    return "Insufficient evidence or blocked launch state."


def render_markdown(result: Dict[str, Any]) -> str:
    lines = [
        "# Commercial Launch Portfolio Comparison",
        "",
        f"Reports compared: {result['report_count']}",
        "",
        "## Recommended Order",
        "",
        "| Rank | Repo | Decision | Overall | P0 | P1 | Reason |",
        "|---:|---|---|---:|---:|---:|---|",
    ]
    for item in result["recommended_order"]:
        lines.append(
            f"| {item['rank']} | {item['repo_name']} | {item['launch_decision']} | "
            f"{item['overall_score']:.1f} | {item['unresolved_p0']} | {item['unresolved_p1']} | {item['reason']} |"
        )

    lines.extend(
        [
            "",
            "## Report Details",
            "",
            "| Repo | Profile | Security | Readiness | Sellability | Evidence | Gaps | Pain Points | Targets | Source |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in result["reports"]:
        score = item["scores"]
        lines.append(
            f"| {item['repo_name']} | {item['profile']} | {score['security']:.1f} | "
            f"{score['readiness']:.1f} | {score['sellability']:.1f} | {score['evidence']:.1f} | "
            f"{item['gap_count']} | {item['pain_point_count']} | {item['target_customer_count']} | {item['source_path']} |"
        )
    return "\n".join(lines) + "\n"


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare completed commercial launch evidence JSON files.")
    parser.add_argument("reports", nargs="+", help="Completed launch evidence JSON files.")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if len(args.reports) < 2:
        raise SystemExit("provide at least two launch evidence JSON files")
    result = compare([load_report(path) for path in args.reports])
    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        print(render_markdown(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
