#!/usr/bin/env python3
"""Render a launch-specific progress digest for an ECC dynamic workflow run."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


LANES = [
    {
        "key": "repo_map",
        "label": "Repo Map",
        "weight": 10,
        "roles": {"repo-profiler", "repo-mapper"},
        "phases": {"map"},
    },
    {
        "key": "security",
        "label": "Security",
        "weight": 15,
        "roles": {"security-auditor"},
        "phases": {"audit"},
    },
    {
        "key": "readiness",
        "label": "Readiness",
        "weight": 15,
        "roles": {"readiness-verifier"},
        "phases": {"verify"},
    },
    {
        "key": "sellability",
        "label": "Sellability",
        "weight": 15,
        "roles": {"sellability-analyst"},
        "phases": {"market"},
    },
    {
        "key": "market_pain",
        "label": "Market Pain Research",
        "weight": 20,
        "roles": {"market-researcher"},
        "phases": {"research"},
    },
    {
        "key": "target_outreach",
        "label": "Target Customers + Outreach",
        "weight": 10,
        "roles": {"market-researcher"},
        "phases": {"research"},
    },
    {
        "key": "safe_fix",
        "label": "Safe Fix Lane",
        "weight": 10,
        "roles": {"fix-implementer"},
        "phases": {"execute"},
    },
    {
        "key": "synthesis",
        "label": "Synthesis + Validation",
        "weight": 5,
        "roles": {"reporter"},
        "phases": {"synthesize"},
    },
]

PHASE_ORDER = ["map", "audit", "verify", "market", "research", "execute", "synthesize"]
STATUS_SCORE = {
    "pass": 100,
    "running": 45,
    "fail": 35,
    "pending": 0,
    "cancelled": 0,
}


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


def iso_now(value: Optional[str]) -> datetime:
    parsed = parse_time(value) if value else None
    return parsed or datetime.now(timezone.utc)


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            rows.append(value)
    return rows


def read_text(path_text: Any) -> str:
    if not isinstance(path_text, str) or not path_text:
        return ""
    path = Path(path_text)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_worker_status(content: str) -> Dict[str, str]:
    status: Dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line.startswith("- ") or ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        status[key.strip().lower().replace(" ", "_")] = value.strip().strip("`")
    return status


def load_waves(run_dir: Path) -> List[Dict[str, Any]]:
    waves_dir = run_dir / "waves"
    if not waves_dir.exists():
        return []
    waves: List[Dict[str, Any]] = []
    for wave_file in sorted(waves_dir.glob("*/wave.json")):
        wave = read_json(wave_file, {})
        if isinstance(wave, dict):
            wave["_path"] = str(wave_file)
            waves.append(wave)
    return waves


def lane_for_task(task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if task.get("reviewOf"):
        return None
    for lane in LANES:
        if task_matches_lane(task, lane):
            return lane
    return None


def task_matches_lane(task: Dict[str, Any], lane: Dict[str, Any]) -> bool:
    if task.get("reviewOf"):
        return False
    role = str(task.get("role", ""))
    phase = str(task.get("phase", ""))
    return role in lane["roles"] or phase in lane["phases"]


def status_score(task: Dict[str, Any]) -> int:
    return STATUS_SCORE.get(str(task.get("status", "pending")), 0)


def confidence_for(percent: float, evidence_count: int, has_fail: bool) -> int:
    if has_fail:
        return 2
    if percent >= 100 and evidence_count > 0:
        return 5
    if percent >= 100:
        return 4
    if percent >= 45:
        return 3
    if percent > 0:
        return 2
    return 1


def lane_matrix(tasks: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result_by_task = {str(item.get("taskId") or item.get("task") or ""): item for item in results}
    rows: List[Dict[str, Any]] = []
    for lane in LANES:
        lane_tasks = [task for task in tasks if task_matches_lane(task, lane)]
        if lane_tasks:
            percent = sum(status_score(task) for task in lane_tasks) / len(lane_tasks)
            statuses = sorted({str(task.get("status", "pending")) for task in lane_tasks})
        else:
            percent = 0.0
            statuses = ["not_scheduled"]
        evidence: List[str] = []
        has_fail = False
        for task in lane_tasks:
            if task.get("status") == "fail":
                has_fail = True
            summary = str(task.get("summary") or task.get("evidence") or task.get("lastError") or "").strip()
            if summary:
                evidence.append(f"{task.get('id')}: {summary}")
            result = result_by_task.get(str(task.get("id")))
            if result:
                result_summary = str(result.get("summary") or result.get("evidence") or "").strip()
                if result_summary:
                    evidence.append(f"{task.get('id')} result: {result_summary}")
        rows.append(
            {
                "lane": lane["label"],
                "target_percent": lane["weight"],
                "current_percent": round(percent, 1),
                "status": ", ".join(statuses),
                "evidence": evidence[:3],
                "confidence": confidence_for(percent, len(evidence), has_fail),
            }
        )
    return rows


def task_age_minutes(task: Dict[str, Any], now_value: datetime) -> float:
    updated = parse_time(task.get("updatedAt")) or parse_time(task.get("createdAt")) or now_value
    return max(0.0, (now_value - updated).total_seconds() / 60.0)


def run_age_hours(workflow: Dict[str, Any], now_value: datetime) -> float:
    created = parse_time(workflow.get("createdAt")) or now_value
    return max(0.0, (now_value - created).total_seconds() / 3600.0)


def current_phase(tasks: List[Dict[str, Any]]) -> str:
    running = [task for task in tasks if task.get("status") == "running"]
    candidates = running or [task for task in tasks if task.get("status") == "pending"] or [task for task in tasks if task.get("status") == "fail"]
    if candidates:
        return str(candidates[0].get("phase", "unknown"))
    return "complete"


def next_phase_name(phase: str) -> str:
    if phase not in PHASE_ORDER:
        return "none"
    index = PHASE_ORDER.index(phase)
    return PHASE_ORDER[index + 1] if index + 1 < len(PHASE_ORDER) else "none"


def count_open_in_phase(tasks: List[Dict[str, Any]], phase: str) -> int:
    return sum(1 for task in tasks if task.get("phase") == phase and task.get("status") != "pass")


def infer_root_cause(task: Optional[Dict[str, Any]], age_minutes: float, threshold_minutes: int) -> str:
    if not task:
        return "evidence gap"
    role = str(task.get("role", ""))
    title = str(task.get("title", "")).lower()
    prompt = str(task.get("prompt", ""))
    status = str(task.get("status", "pending"))
    last_error = str(task.get("lastError") or "").lower()
    if status == "fail":
        if any(word in last_error for word in ["test", "lint", "build", "typecheck"]):
            return "testing loop"
        return "worker failure"
    if age_minutes >= threshold_minutes and status == "running":
        return "tool/execution delay"
    if role == "market-researcher":
        return "search/exploration"
    if "approve" in title or "decision" in title:
        return "decision paralysis"
    if len(prompt) > 2500:
        return "context overload"
    if status == "pending" and task.get("dependsOn"):
        return "dependency issue"
    return "evidence gap"


def unblock_options(root_cause: str) -> List[Dict[str, str]]:
    options = {
        "context overload": [
            ("Split current lane into one artifact-only subtask", "More coordination overhead", "1-3 hours", "May miss cross-lane links"),
            ("Write a compact repo/source ledger before continuing", "Slower immediate progress", "2-4 hours", "Ledger can become stale"),
            ("Pause non-critical lanes and finish one proof bucket", "Less parallelism", "2-6 hours", "Lower breadth"),
        ],
        "ambiguous requirements": [
            ("Freeze launch mode as pilot-only until evidence improves", "Conservative decision", "2-4 hours", "May understate upside"),
            ("Convert ambiguity into explicit assumptions and gaps", "More caveats", "1-2 hours", "Requires later validation"),
            ("Ask for owner approval only on high-impact ambiguity", "Interrupts run", "Variable", "May block automation"),
        ],
        "dependency issue": [
            ("Run dependency blocker task first", "Delays dependent lanes", "1-3 hours", "May reveal larger scope"),
            ("Mark blocked proof bucket and continue independent lanes", "Leaves gap unresolved", "1-2 hours", "Final decision may be lower"),
            ("Create a small approval-gated fix plan", "No immediate fix", "1 hour", "Needs owner action"),
        ],
        "testing loop": [
            ("Reduce to the narrowest failing command", "Less broad coverage", "1-2 hours", "Can miss adjacent regressions"),
            ("Separate deterministic failures from environment failures", "More reporting work", "1-3 hours", "May still need secrets"),
            ("Pause fixes and report exact failing gate", "Stops implementation", "Immediate", "Launch remains caveated"),
        ],
        "search/exploration": [
            ("Limit research to top 5 sources per pain point", "Less exhaustive", "2-4 hours", "May miss niche buyers"),
            ("Use narrow ICP segments instead of named accounts", "Less account-specific", "1-2 hours", "Outreach needs later refinement"),
            ("Create clearly labeled synthetic hypotheses for missing feedback", "Not launch proof", "1 hour", "Cannot support commercial-ready"),
        ],
        "decision paralysis": [
            ("Choose the safest launch decision supported by proof", "Conservative", "Immediate", "May defer sales push"),
            ("Score each decision against P0/P1 and evidence gates", "More analysis", "1 hour", "Still judgment-based"),
            ("Escalate only irreversible choices", "Requires user input", "Variable", "May delay completion"),
        ],
        "tool/execution delay": [
            ("Collect worker status and handoffs, then retry failed/stale task", "May duplicate work", "1-2 hours", "Token cost"),
            ("Pause the stale task and run remaining independent tasks", "Leaves blocker", "Immediate", "Synthesis may not be ready"),
            ("Reduce concurrency and isolate the slow lane", "Slower throughput", "2-4 hours", "Less parallelism"),
        ],
        "worker failure": [
            ("Read handoff/status and retry with a narrower prompt", "More attempts", "1-3 hours", "May repeat failure"),
            ("Convert failure into explicit gap and continue", "No fix", "Immediate", "Lower launch decision"),
            ("Run focused local command to reproduce the failure", "Manual effort", "1-2 hours", "May require environment setup"),
        ],
        "evidence gap": [
            ("Gather the minimum proof for the current claim", "Narrows scope", "1-2 hours", "May not cover all claims"),
            ("Downgrade claim to repo artifact/candidate/roadmap", "Weaker launch language", "Immediate", "Less sellable"),
            ("Create a follow-up validation task", "Defers proof", "Immediate", "Cannot support commercial-ready"),
        ],
    }
    return [
        {
            "action": action,
            "tradeoff": tradeoff,
            "expected_time_saved": saved,
            "risk": risk,
        }
        for action, tradeoff, saved, risk in options[root_cause][:3]
    ]


def choose_bottleneck(tasks: List[Dict[str, Any]], now_value: datetime, threshold_minutes: int) -> Dict[str, Any]:
    candidates = [task for task in tasks if task.get("status") in {"running", "fail", "pending"}]
    if not candidates:
        return {
            "task_id": "none",
            "title": "No active bottleneck",
            "phase": "complete",
            "lane": "none",
            "status": "complete",
            "elapsed_minutes_since_update": 0,
            "last_update": "",
            "root_cause": "evidence gap",
            "stalled": False,
            "top_unblock_options": unblock_options("evidence gap"),
        }
    candidates.sort(
        key=lambda task: (
            0 if task.get("status") == "running" else 1 if task.get("status") == "fail" else 2,
            -task_age_minutes(task, now_value),
        )
    )
    task = candidates[0]
    age = task_age_minutes(task, now_value)
    lane = lane_for_task(task)
    root_cause = infer_root_cause(task, age, threshold_minutes)
    return {
        "task_id": task.get("id", ""),
        "title": task.get("title", ""),
        "phase": task.get("phase", ""),
        "lane": lane["label"] if lane else "Adversarial Review" if task.get("reviewOf") else "unknown",
        "status": task.get("status", "pending"),
        "elapsed_minutes_since_update": round(age, 1),
        "last_update": task.get("updatedAt") or task.get("createdAt") or "",
        "root_cause": root_cause,
        "stalled": age >= threshold_minutes and task.get("status") in {"running", "pending"},
        "top_unblock_options": unblock_options(root_cause),
    }


def completed_summaries(tasks: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> List[str]:
    summaries: List[str] = []
    for task in tasks:
        if task.get("status") != "pass":
            continue
        text = str(task.get("summary") or task.get("evidence") or "").strip()
        summaries.append(f"{task.get('id')} {task.get('phase')}/{task.get('role')}: {task.get('title')}{' - ' + text if text else ''}")
    for result in results:
        summary = str(result.get("summary") or result.get("evidence") or "").strip()
        if summary:
            summaries.append(f"result {result.get('taskId') or result.get('task')}: {summary}")
    return summaries[:10]


def worker_statuses(waves: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    statuses: List[Dict[str, Any]] = []
    for wave in waves:
        for worker in wave.get("tasks", []):
            if not isinstance(worker, dict):
                continue
            content = read_text(worker.get("statusFilePath"))
            parsed = parse_worker_status(content)
            statuses.append(
                {
                    "wave_id": wave.get("waveId"),
                    "task_id": worker.get("taskId"),
                    "status_file": worker.get("statusFilePath"),
                    "handoff_file": worker.get("handoffFilePath"),
                    "state": parsed.get("state") or "unknown",
                    "updated": parsed.get("updated") or "",
                }
            )
    return statuses


def build_digest(args: argparse.Namespace) -> Dict[str, Any]:
    run_dir = Path(args.run).expanduser().resolve()
    workflow = read_json(run_dir / "workflow.json", {})
    tasks = read_jsonl(run_dir / "backlog.jsonl")
    results = read_jsonl(run_dir / "results.jsonl")
    waves = load_waves(run_dir)
    now_value = iso_now(args.now)
    phase = args.phase or current_phase(tasks)
    next_phase = next_phase_name(phase)
    matrix = lane_matrix(tasks, results)
    bottleneck = choose_bottleneck(tasks, now_value, args.stall_threshold_minutes)
    pending = [task for task in tasks if task.get("status") != "pass"]
    run_hours = run_age_hours(workflow, now_value)
    total_weighted = round(
        sum((row["target_percent"] * row["current_percent"] / 100.0) for row in matrix),
        1,
    )
    return {
        "schema_version": 1,
        "generated_at": now_value.isoformat(),
        "run_dir": str(run_dir),
        "repo": args.repo or workflow.get("repoRoot") or "",
        "run": {
            "name": workflow.get("name", run_dir.name),
            "goal": workflow.get("goal", ""),
            "age_hours": round(run_hours, 2),
            "twenty_hour_digest_required": run_hours >= 20,
        },
        "accomplished": completed_summaries(tasks, results),
        "target_matrix": matrix,
        "overall_weighted_percent": total_weighted,
        "pending": [
            {
                "id": task.get("id"),
                "phase": task.get("phase"),
                "role": task.get("role"),
                "title": task.get("title"),
                "status": task.get("status"),
                "updated_at": task.get("updatedAt"),
            }
            for task in pending[:20]
        ],
        "activities_remaining": {
            "total": len(pending),
            "current_phase": phase,
            "current_phase_remaining": count_open_in_phase(tasks, phase),
            "next_phase": next_phase,
            "next_phase_remaining": count_open_in_phase(tasks, next_phase) if next_phase != "none" else 0,
        },
        "current_bottleneck": bottleneck,
        "waves": [
            {
                "wave_id": wave.get("waveId"),
                "status": wave.get("status"),
                "created_at": wave.get("createdAt"),
                "task_count": len(wave.get("tasks", [])) if isinstance(wave.get("tasks"), list) else 0,
            }
            for wave in waves
        ],
        "worker_statuses": worker_statuses(waves),
        "market_synthetic_data": {
            "allowed": True,
            "rule": "Use only clearly labeled hypotheses when real feedback/source evidence is unavailable; synthetic-only evidence cannot support commercial-ready.",
        },
    }


def render_markdown(digest: Dict[str, Any]) -> str:
    lines = [
        "# Commercial Launch Progress Digest",
        "",
        f"- Run: `{digest['run']['name']}`",
        f"- Run age: {digest['run']['age_hours']} hours",
        f"- Overall weighted progress: {digest['overall_weighted_percent']}%",
        f"- 20h bottleneck digest required: `{digest['run']['twenty_hour_digest_required']}`",
        "",
        "## Accomplished",
    ]
    if digest["accomplished"]:
        lines.extend(f"- {item}" for item in digest["accomplished"])
    else:
        lines.append("- None recorded yet.")

    lines.extend(
        [
            "",
            "## Target Accomplishment Matrix",
            "",
            "| Lane | Target % | Current % | Status | Evidence | Confidence |",
            "|---|---:|---:|---|---|---:|",
        ]
    )
    for row in digest["target_matrix"]:
        evidence = "; ".join(row["evidence"]) if row["evidence"] else "No evidence yet"
        lines.append(
            f"| {row['lane']} | {row['target_percent']} | {row['current_percent']} | "
            f"{row['status']} | {evidence.replace('|', '/')} | {row['confidence']} |"
        )

    lines.extend(["", "## Pending"])
    if digest["pending"]:
        for task in digest["pending"]:
            lines.append(f"- {task['id']} {task['phase']}/{task['role']}: {task['title']} ({task['status']})")
    else:
        lines.append("- None.")

    activities = digest["activities_remaining"]
    lines.extend(
        [
            "",
            "## Activities Remaining",
            "",
            f"- Total: {activities['total']}",
            f"- Current phase `{activities['current_phase']}`: {activities['current_phase_remaining']}",
            f"- Next phase `{activities['next_phase']}`: {activities['next_phase_remaining']}",
        ]
    )

    bottleneck = digest["current_bottleneck"]
    lines.extend(
        [
            "",
            "## Current Bottleneck",
            "",
            f"- Task: `{bottleneck['task_id']}` {bottleneck['title']}",
            f"- Lane: {bottleneck['lane']}",
            f"- Status: {bottleneck['status']}",
            f"- Last update: {bottleneck['last_update'] or 'unknown'}",
            f"- Minutes since update: {bottleneck['elapsed_minutes_since_update']}",
            f"- Stalled: `{bottleneck['stalled']}`",
            f"- Root cause: `{bottleneck['root_cause']}`",
            "",
            "## Top 3 Unblock Options",
            "",
            "| Action | Tradeoff | Expected Time Saved | Risk |",
            "|---|---|---|---|",
        ]
    )
    for option in bottleneck["top_unblock_options"]:
        lines.append(
            f"| {option['action']} | {option['tradeoff']} | {option['expected_time_saved']} | {option['risk']} |"
        )

    lines.extend(
        [
            "",
            "## Market Synthetic Data Rule",
            "",
            digest["market_synthetic_data"]["rule"],
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a launch-specific progress digest for an ECC run.")
    parser.add_argument("--run", required=True, help="Dynamic workflow run directory.")
    parser.add_argument("--repo", help="Repository path, used for display when workflow metadata is absent.")
    parser.add_argument("--phase", help="Override current phase for the activities-remaining section.")
    parser.add_argument("--stall-threshold-minutes", type=int, default=120)
    parser.add_argument("--now", help="Override current timestamp for deterministic tests.")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args(argv)
    if args.stall_threshold_minutes < 1:
        raise SystemExit("--stall-threshold-minutes must be at least 1")
    return args


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    try:
        digest = build_digest(args)
    except Exception as exc:  # noqa: BLE001 - CLI should report digest failures plainly.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.output == "json":
        print(json.dumps(digest, indent=2))
    else:
        print(render_markdown(digest), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
