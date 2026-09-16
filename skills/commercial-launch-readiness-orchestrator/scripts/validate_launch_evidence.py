#!/usr/bin/env python3
"""Validate commercial launch readiness evidence JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse


PROFILES = {"saas", "ai-app", "data-app", "devtool", "marketplace", "internal-tool", "unknown"}
MODES = {"audit-only", "fix-safe", "full"}
RESEARCH_DEPTHS = {"light", "standard", "deep"}
WORKER_MODES = {"dry-run", "execute"}
DECISIONS = {"blocked", "pilot-only", "sellable-with-caveats", "commercial-ready"}
SEVERITIES = {"P0", "P1", "P2", "P3"}
PROOF_BUCKETS = {"hosted_live", "local", "repo_artifact", "candidate_shadow", "roadmap"}
RESOLVED_STATUSES = {"fixed", "resolved", "closed", "done", "accepted", "mitigated"}
SCORE_FIELDS = {"security", "readiness", "sellability", "evidence", "overall"}
MARKET_EVIDENCE_MODES = {"real", "mixed", "synthetic-only", "unknown"}
OPTIMIZATION_POLICIES = {"safe", "strict", "measured"}
OPTIMIZATION_VERDICTS = {"pass", "fail", "needs-retry"}
BOTTLENECK_ROOT_CAUSES = {
    "context overload",
    "ambiguous requirements",
    "dependency issue",
    "testing loop",
    "search/exploration",
    "decision paralysis",
    "tool/execution delay",
    "worker failure",
    "evidence gap",
}


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON must be an object")
    return data


def is_blank(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def require_object(errors: List[str], data: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be an object")
        return {}
    return value


def require_list(errors: List[str], data: Dict[str, Any], key: str) -> List[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        errors.append(f"{key} must be a list")
        return []
    return value


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def list_has_items(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def parse_time(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def run_duration_hours(run: Dict[str, Any]) -> Optional[float]:
    for key, divisor in [
        ("duration_hours", 1),
        ("elapsed_hours", 1),
        ("duration_minutes", 60),
        ("elapsed_minutes", 60),
        ("duration_seconds", 3600),
        ("elapsed_seconds", 3600),
    ]:
        value = run.get(key)
        if isinstance(value, (int, float)):
            return float(value) / divisor
    started = parse_time(run.get("started_at") or run.get("created_at"))
    completed = parse_time(run.get("completed_at") or run.get("generated_at"))
    if started and completed:
        return max(0.0, (completed - started).total_seconds() / 3600)
    return None


def unresolved_gaps(gaps: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"P0": 0, "P1": 0}
    for gap in gaps:
        severity = str(gap.get("severity", "")).upper()
        status = str(gap.get("status", "open")).strip().lower()
        if severity in counts and status not in RESOLVED_STATUSES:
            counts[severity] += 1
    return counts


def validate_gap(errors: List[str], gap: Any, index: int) -> Dict[str, Any]:
    if not isinstance(gap, dict):
        errors.append(f"gaps[{index}] must be an object")
        return {}
    for field in ["gap", "severity", "evidence", "framework_mapping", "buyer_impact", "fix", "status"]:
        if field not in gap:
            errors.append(f"gaps[{index}] missing {field}")
    severity = str(gap.get("severity", "")).upper()
    if severity not in SEVERITIES:
        errors.append(f"gaps[{index}].severity must be P0, P1, P2, or P3")
    if is_blank(gap.get("gap")):
        errors.append(f"gaps[{index}].gap must be non-empty")
    if is_blank(gap.get("evidence")):
        errors.append(f"gaps[{index}].evidence must be non-empty")
    if not list_has_items(gap.get("framework_mapping")):
        errors.append(f"gaps[{index}].framework_mapping must be a non-empty list")
    if is_blank(gap.get("buyer_impact")):
        errors.append(f"gaps[{index}].buyer_impact must be non-empty")
    if is_blank(gap.get("fix")):
        errors.append(f"gaps[{index}].fix must be non-empty")
    if is_blank(gap.get("status")):
        errors.append(f"gaps[{index}].status must be non-empty")
    return gap


def validate_pain_point(errors: List[str], item: Any, index: int, *, require_sources: bool) -> None:
    if not isinstance(item, dict):
        errors.append(f"pain_points[{index}] must be an object")
        return
    for field in [
        "rank",
        "pain_point",
        "affected_buyer",
        "source_evidence",
        "willingness_to_pay_signal",
        "repo_proof_fit",
        "confidence",
    ]:
        if field not in item:
            errors.append(f"pain_points[{index}] missing {field}")
    if not isinstance(item.get("rank"), int) or item.get("rank", 0) < 1:
        errors.append(f"pain_points[{index}].rank must be a positive integer")
    if not isinstance(item.get("confidence"), int) or not 1 <= item.get("confidence", 0) <= 5:
        errors.append(f"pain_points[{index}].confidence must be an integer from 1 to 5")
    sources = item.get("source_evidence")
    if not list_has_items(sources):
        errors.append(f"pain_points[{index}].source_evidence must be a non-empty list")
    elif require_sources:
        for source_index, source in enumerate(sources, start=1):
            if not isinstance(source, str) or not is_url(source):
                errors.append(f"pain_points[{index}].source_evidence[{source_index}] must be an http(s) URL")


def validate_target_customer(errors: List[str], item: Any, index: int) -> None:
    if not isinstance(item, dict):
        errors.append(f"target_customers[{index}] must be an object")
        return
    for field in [
        "rank",
        "account_or_segment",
        "pain",
        "trigger",
        "decision_maker",
        "outreach_angle",
        "proof_to_show",
        "confidence",
    ]:
        if field not in item:
            errors.append(f"target_customers[{index}] missing {field}")
    if not isinstance(item.get("rank"), int) or item.get("rank", 0) < 1:
        errors.append(f"target_customers[{index}].rank must be a positive integer")
    if not isinstance(item.get("confidence"), int) or not 1 <= item.get("confidence", 0) <= 5:
        errors.append(f"target_customers[{index}].confidence must be an integer from 1 to 5")
    if is_blank(item.get("proof_to_show")):
        errors.append(f"target_customers[{index}].proof_to_show must be non-empty")


def validate_progress_update(errors: List[str], item: Any, index: int) -> None:
    if not isinstance(item, dict):
        errors.append(f"progress_updates[{index}] must be an object")
        return
    for field in ["phase", "accomplished", "target_matrix", "pending", "bottleneck", "created_at"]:
        if field not in item:
            errors.append(f"progress_updates[{index}] missing {field}")
    if is_blank(item.get("phase")):
        errors.append(f"progress_updates[{index}].phase must be non-empty")
    if not isinstance(item.get("target_matrix"), list):
        errors.append(f"progress_updates[{index}].target_matrix must be a list")


def validate_bottleneck(errors: List[str], item: Any, index: int) -> None:
    if not isinstance(item, dict):
        errors.append(f"bottleneck_log[{index}] must be an object")
        return
    for field in ["phase", "task_or_subtask", "elapsed_minutes", "last_update", "root_cause", "top_unblock_options"]:
        if field not in item:
            errors.append(f"bottleneck_log[{index}] missing {field}")
    if item.get("root_cause") not in BOTTLENECK_ROOT_CAUSES:
        errors.append(
            f"bottleneck_log[{index}].root_cause must be one of {', '.join(sorted(BOTTLENECK_ROOT_CAUSES))}"
        )
    if not isinstance(item.get("top_unblock_options"), list) or len(item.get("top_unblock_options", [])) < 3:
        errors.append(f"bottleneck_log[{index}].top_unblock_options must include at least three options")


def validate_synthetic_data(errors: List[str], item: Any, index: int) -> None:
    if not isinstance(item, dict):
        errors.append(f"synthetic_data_points[{index}] must be an object")
        return
    for field in ["hypothesis", "reason", "validation_source_needed"]:
        if field not in item or is_blank(item.get(field)):
            errors.append(f"synthetic_data_points[{index}].{field} must be non-empty")


def validate_implementation_decision(errors: List[str], item: Any, index: int) -> None:
    if not isinstance(item, dict):
        errors.append(f"implementation_decisions[{index}] must be an object")
        return
    for field in [
        "decision",
        "acceptance_check",
        "chosen_variant",
        "files_changed",
        "tests_run",
        "proof",
        "reason",
    ]:
        if field not in item:
            errors.append(f"implementation_decisions[{index}] missing {field}")
    for field in ["decision", "acceptance_check", "chosen_variant", "proof", "reason"]:
        if is_blank(item.get(field)):
            errors.append(f"implementation_decisions[{index}].{field} must be non-empty")
    if not isinstance(item.get("files_changed"), list):
        errors.append(f"implementation_decisions[{index}].files_changed must be a list")
    if not isinstance(item.get("tests_run"), list):
        errors.append(f"implementation_decisions[{index}].tests_run must be a list")


def validate_rejected_variant(errors: List[str], item: Any, index: int) -> None:
    if not isinstance(item, dict):
        errors.append(f"rejected_variants[{index}] must be an object")
        return
    for field in ["variant", "reason_rejected", "tradeoff", "evidence"]:
        if field not in item or is_blank(item.get(field)):
            errors.append(f"rejected_variants[{index}].{field} must be non-empty")


def validate_optimization_review(errors: List[str], item: Any, index: int) -> None:
    if not isinstance(item, dict):
        errors.append(f"code_optimization_reviews[{index}] must be an object")
        return
    for field in ["target_task", "policy", "verdict", "minimality_score", "evidence", "tests_or_checks"]:
        if field not in item:
            errors.append(f"code_optimization_reviews[{index}] missing {field}")
    if item.get("policy") not in OPTIMIZATION_POLICIES:
        errors.append(
            f"code_optimization_reviews[{index}].policy must be one of {', '.join(sorted(OPTIMIZATION_POLICIES))}"
        )
    if item.get("verdict") not in OPTIMIZATION_VERDICTS:
        errors.append(
            f"code_optimization_reviews[{index}].verdict must be one of {', '.join(sorted(OPTIMIZATION_VERDICTS))}"
        )
    if not isinstance(item.get("minimality_score"), int) or not 1 <= item.get("minimality_score", 0) <= 5:
        errors.append(f"code_optimization_reviews[{index}].minimality_score must be an integer from 1 to 5")
    if is_blank(item.get("evidence")):
        errors.append(f"code_optimization_reviews[{index}].evidence must be non-empty")
    if not isinstance(item.get("tests_or_checks"), list):
        errors.append(f"code_optimization_reviews[{index}].tests_or_checks must be a list")


def non_empty_list_field(container: Dict[str, Any], key: str) -> bool:
    value = container.get(key)
    return isinstance(value, list) and bool(value)


def validate(
    data: Dict[str, Any],
    *,
    allow_partial: bool = False,
    allow_missing_sources: bool = False,
    require_repo_exists: bool = False,
) -> List[str]:
    errors: List[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    for key in [
        "repo",
        "run",
        "launch_decision",
        "scores",
        "proof_buckets",
        "gaps",
        "pain_points",
        "target_customers",
        "outreach_plan",
        "fix_report",
        "implementation_decisions",
        "rejected_variants",
        "code_optimization_reviews",
        "adversarial_reviews",
        "progress_updates",
        "bottleneck_log",
        "market_evidence_mode",
        "synthetic_data_points",
        "ecc_ledger",
    ]:
        if key not in data:
            errors.append(f"missing top-level key: {key}")

    repo = require_object(errors, data, "repo")
    repo_path = repo.get("path")
    if is_blank(repo.get("name")):
        errors.append("repo.name is required")
    if is_blank(repo_path):
        errors.append("repo.path is required")
    elif not str(repo_path).startswith("/"):
        errors.append("repo.path must be absolute")
    elif require_repo_exists and not Path(str(repo_path)).exists():
        errors.append(f"repo.path does not exist: {repo_path}")
    if repo.get("profile") not in PROFILES:
        errors.append(f"repo.profile must be one of {', '.join(sorted(PROFILES))}")

    run = require_object(errors, data, "run")
    if is_blank(run.get("name")):
        errors.append("run.name is required")
    if run.get("mode") not in MODES:
        errors.append(f"run.mode must be one of {', '.join(sorted(MODES))}")
    if run.get("research_depth") not in RESEARCH_DEPTHS:
        errors.append(f"run.research_depth must be one of {', '.join(sorted(RESEARCH_DEPTHS))}")
    if run.get("worker_mode") not in WORKER_MODES:
        errors.append(f"run.worker_mode must be one of {', '.join(sorted(WORKER_MODES))}")
    duration = run_duration_hours(run)

    decision = data.get("launch_decision")
    if decision not in DECISIONS:
        errors.append(f"launch_decision must be one of {', '.join(sorted(DECISIONS))}")

    scores = require_object(errors, data, "scores")
    for field in sorted(SCORE_FIELDS):
        value = scores.get(field)
        if not isinstance(value, int) or not 1 <= value <= 5:
            errors.append(f"scores.{field} must be an integer from 1 to 5")

    proof_buckets = require_object(errors, data, "proof_buckets")
    for bucket in sorted(PROOF_BUCKETS):
        value = proof_buckets.get(bucket)
        if not isinstance(value, list):
            errors.append(f"proof_buckets.{bucket} must be a list")

    gap_items = [
        validate_gap(errors, gap, index)
        for index, gap in enumerate(require_list(errors, data, "gaps"), start=1)
    ]
    blockers = unresolved_gaps([gap for gap in gap_items if gap])
    if blockers["P0"] > 0 and decision != "blocked":
        errors.append("unresolved P0 gaps require launch_decision blocked")
    if blockers["P1"] > 0 and decision == "commercial-ready":
        errors.append("commercial-ready is not allowed with unresolved P1 gaps")

    pain_points = require_list(errors, data, "pain_points")
    target_customers = require_list(errors, data, "target_customers")
    if not allow_partial:
        if len(pain_points) < 10:
            errors.append("completed evidence must include at least 10 pain_points")
        if len(target_customers) < 10:
            errors.append("completed evidence must include at least 10 target_customers")
    for index, item in enumerate(pain_points, start=1):
        validate_pain_point(errors, item, index, require_sources=not allow_missing_sources)
    for index, item in enumerate(target_customers, start=1):
        validate_target_customer(errors, item, index)

    for key in ["outreach_plan", "ecc_ledger"]:
        require_object(errors, data, key)
    fix_report = require_object(errors, data, "fix_report")
    implementation_decisions = require_list(errors, data, "implementation_decisions")
    rejected_variants = require_list(errors, data, "rejected_variants")
    optimization_reviews = require_list(errors, data, "code_optimization_reviews")
    require_list(errors, data, "adversarial_reviews")
    progress_updates = require_list(errors, data, "progress_updates")
    bottleneck_log = require_list(errors, data, "bottleneck_log")
    synthetic_data_points = require_list(errors, data, "synthetic_data_points")
    for index, item in enumerate(implementation_decisions, start=1):
        validate_implementation_decision(errors, item, index)
    for index, item in enumerate(rejected_variants, start=1):
        validate_rejected_variant(errors, item, index)
    for index, item in enumerate(optimization_reviews, start=1):
        validate_optimization_review(errors, item, index)
    for index, item in enumerate(progress_updates, start=1):
        validate_progress_update(errors, item, index)
    for index, item in enumerate(bottleneck_log, start=1):
        validate_bottleneck(errors, item, index)
    for index, item in enumerate(synthetic_data_points, start=1):
        validate_synthetic_data(errors, item, index)

    market_mode = data.get("market_evidence_mode")
    if market_mode not in MARKET_EVIDENCE_MODES:
        errors.append(f"market_evidence_mode must be one of {', '.join(sorted(MARKET_EVIDENCE_MODES))}")
    if decision == "commercial-ready" and market_mode == "synthetic-only":
        errors.append("commercial-ready cannot depend on synthetic-only market evidence")
    if duration is not None and duration >= 20 and not bottleneck_log:
        errors.append("runs of 20 hours or more require at least one bottleneck_log entry")

    code_changed = non_empty_list_field(fix_report, "files_changed")
    fix_tests_present = non_empty_list_field(fix_report, "tests_run")
    decision_tests_present = any(
        isinstance(item, dict) and non_empty_list_field(item, "tests_run")
        for item in implementation_decisions
    )
    passing_optimization_review = any(
        isinstance(item, dict) and item.get("verdict") == "pass"
        for item in optimization_reviews
    )
    if code_changed:
        if not implementation_decisions:
            errors.append("code changes require at least one implementation_decisions item")
        if not optimization_reviews:
            errors.append("code changes require at least one code_optimization_reviews item")
        if not (fix_tests_present or decision_tests_present):
            errors.append("code changes require at least one test/check in fix_report.tests_run or implementation_decisions.tests_run")
        if optimization_reviews and not passing_optimization_review:
            errors.append("code changes require at least one passing code optimization review")

    if decision == "commercial-ready":
        if scores.get("security", 0) < 4 or scores.get("readiness", 0) < 4:
            errors.append("commercial-ready requires security and readiness scores of at least 4")
        if scores.get("sellability", 0) < 4 or scores.get("evidence", 0) < 4:
            errors.append("commercial-ready requires sellability and evidence scores of at least 4")
        if not proof_buckets.get("hosted_live"):
            errors.append("commercial-ready requires at least one hosted/live proof item")

    return errors


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate commercial launch evidence JSON.")
    parser.add_argument("evidence", help="Launch evidence JSON path.")
    parser.add_argument("--allow-partial", action="store_true", help="Allow fewer than 10 pain points or target customers.")
    parser.add_argument("--allow-missing-sources", action="store_true", help="Do not require pain point source URLs.")
    parser.add_argument("--require-repo-exists", action="store_true", help="Require repo.path to exist locally.")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    try:
        data = load_json(Path(args.evidence))
        errors = validate(
            data,
            allow_partial=args.allow_partial,
            allow_missing_sources=args.allow_missing_sources,
            require_repo_exists=args.require_repo_exists,
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
    raise SystemExit(main(sys.argv[1:]))
