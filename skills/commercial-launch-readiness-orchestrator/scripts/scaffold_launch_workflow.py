#!/usr/bin/env python3
"""Emit ECC dynamic workflow commands for a one-repo launch audit.

This script is intentionally non-mutating: it prints the commands, task graph,
review graph, and optional report template for a commercial launch readiness
run, but it never executes them.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Dict, List, Tuple


DEFAULT_RUNNER = Path(
    "/Users/sanjayb/.codex/plugins/cache/local-codex-marketplace/"
    "everything-claude-code/1.9.0/skills/dynamic-workflow-backlog/scripts/"
    "dynamic-workflow-backlog.js"
)

SKILL_DIR = Path(__file__).resolve().parents[1]

PROFILES = ["auto", "saas", "ai-app", "data-app", "devtool", "marketplace", "internal-tool"]
PROGRESS_POLICIES = ["phase", "interval", "both", "off"]
OPTIMIZATION_POLICIES = ["off", "safe", "strict", "measured"]
BUDGET_CONCURRENCY = {"conservative": 2, "standard": 4, "aggressive": 8}

PROOF_CONTRACT = (
    "Evidence contract: separate hosted/live, local, repo artifact, candidate/shadow, "
    "and roadmap proof. Cite exact files, commands, runtime outputs, or URLs. Do not "
    "claim completion, safety, market demand, or commercial readiness without evidence. "
    "Stop before production deploys, credential changes, payment changes, destructive "
    "migrations, live outreach, data deletion, or secret-dependent actions."
)

CODE_OPTIMIZATION_CONTRACT = {
    "off": "",
    "safe": (
        "Code optimization gate: when proposing or changing repo code, compare the "
        "available no-code, config-only, test/doc-only, minimal-code, and refactor "
        "options. Choose the smallest safe variant that satisfies the acceptance check, "
        "reuse repo patterns, and record verification."
    ),
    "strict": (
        "Code optimization gate: before any repo-side code decision, define the "
        "acceptance check, compare no-code/defer, config-only, test/doc-only, minimal "
        "code patch, and broader refactor variants where relevant, choose the smallest "
        "safe verified variant, reject unnecessary files/dependencies/abstractions, run "
        "focused verification, and record implementation_decisions, rejected_variants, "
        "and code_optimization_reviews when files are changed."
    ),
    "measured": (
        "Code optimization gate: use the strict gate, and when the gap involves latency, "
        "throughput, memory, bundle size, cost, query time, or build/test duration, add a "
        "measured baseline, correctness gate, one-variable variants, repeated or explained "
        "delta, and rollback path before promoting the implementation."
    ),
}

PROFILE_EMPHASIS = {
    "auto": (
        "During the audit, determine the best profile among saas, ai-app, data-app, "
        "devtool, marketplace, and internal-tool. Do not assume the profile before "
        "repo evidence is collected."
    ),
    "saas": (
        "Emphasize auth, tenant isolation, billing readiness, onboarding, retention "
        "signals, admin operations, security review proof, and support readiness."
    ),
    "ai-app": (
        "Emphasize prompt/tool safety, data leakage, evals, model boundaries, cost "
        "controls, unsafe automation, human review, and AI trust claims."
    ),
    "data-app": (
        "Emphasize data ingestion, lineage, freshness, metric definitions, privacy, "
        "exports, observability, and decision-quality proof."
    ),
    "devtool": (
        "Emphasize install friction, CLI/API ergonomics, docs, CI integration, versioning, "
        "developer trust, and time-to-value proof."
    ),
    "marketplace": (
        "Emphasize two-sided trust, listing quality, payments, disputes, fraud, supply "
        "liquidity, demand capture, and transaction safety."
    ),
    "internal-tool": (
        "Emphasize role permissions, auditability, admin workflows, data governance, "
        "training burden, and operational reliability."
    ),
}

RESEARCH_DEPTH_PROMPTS = {
    "light": "Use only essential current sources needed to verify obvious claims and major buyer assumptions.",
    "standard": "Use current sources for security practice, competitors, buyer pain, and target segments.",
    "deep": "Use broad current sources for security practice, competitors, substitutes, buyer pain, willingness-to-pay signals, target accounts, and outreach claims.",
}


def shell_join(parts: List[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def slugify(value: str, fallback: str = "launch-readiness") -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or fallback


def validate_repo(raw_repo: str) -> Path:
    repo = Path(raw_repo).expanduser().resolve()
    if not repo.exists():
        raise SystemExit(f"repo does not exist: {repo}")
    if not repo.is_dir():
        raise SystemExit(f"repo is not a directory: {repo}")
    return repo


def resolved_concurrency(args: argparse.Namespace) -> int:
    if args.max_concurrency is not None:
        value = args.max_concurrency
    else:
        value = BUDGET_CONCURRENCY[args.budget]
    if value < 1 or value > 16:
        raise SystemExit("--max-concurrency must be between 1 and 16")
    return value


def validate_progress_options(args: argparse.Namespace) -> None:
    if args.progress_interval_minutes < 1:
        raise SystemExit("--progress-interval-minutes must be at least 1")
    if args.stall_threshold_minutes < 1:
        raise SystemExit("--stall-threshold-minutes must be at least 1")


def build_goal(
    repo: Path,
    mode: str,
    profile: str,
    budget: str,
    research_depth: str,
    optimization_policy: str,
) -> str:
    return (
        "Commercial launch readiness audit for one repository at "
        f"{repo}. Mode: {mode}. Profile: {profile}. Budget: {budget}. "
        f"Research depth: {research_depth}. Optimization policy: {optimization_policy}. Repo-first security, readiness, "
        "sellability, market pain-point research, top-customer targeting, outreach "
        "planning, safe P0/P1 fix lane, lane-specific adversarial review, structured "
        "evidence manifest, and proof-bucketed synthesis."
    )


def add_contract(prompt: str, profile: str, research_depth: str, optimization_policy: str) -> str:
    parts = [
        prompt,
        PROFILE_EMPHASIS[profile],
        RESEARCH_DEPTH_PROMPTS[research_depth],
        PROOF_CONTRACT,
    ]
    optimization_contract = CODE_OPTIMIZATION_CONTRACT[optimization_policy]
    if optimization_contract:
        parts.append(optimization_contract)
    return " ".join(parts)


def safe_fix_prompt(mode: str) -> str:
    prompts = {
        "audit-only": (
            "Do not edit files. Identify deterministic P0/P1 fixes only and return "
            "a fix plan with approval gates, expected files, and verification commands."
        ),
        "fix-safe": (
            "Implement only deterministic P0/P1 repo-side fixes that need no secrets, "
            "deploys, payments, destructive migrations, or external account actions. "
            "Run focused verification and report changed files."
        ),
        "full": (
            "Implement safe bounded fixes where proof is strong. Stop before production, "
            "credential, payment, destructive, or live-outreach actions."
        ),
    }
    return prompts[mode]


def task_specs(
    repo: Path,
    mode: str,
    profile: str,
    research_depth: str,
    optimization_policy: str,
) -> List[Dict[str, str]]:
    tasks: List[Dict[str, str]] = []
    if profile == "auto":
        tasks.append(
            {
                "phase": "map",
                "role": "repo-profiler",
                "title": "Decide repo profile",
                "lane": "profile",
                "prompt": add_contract(
                    f"Inspect {repo} only enough to classify the repo as saas, ai-app, data-app, devtool, marketplace, or internal-tool. Record the evidence for the chosen profile and the profiles rejected.",
                    profile,
                    research_depth,
                    optimization_policy,
                ),
            }
        )

    tasks.extend(
        [
            {
                "phase": "map",
                "role": "repo-mapper",
                "title": "Map repo product and runtime surface",
                "lane": "repo-map",
                "prompt": add_contract(
                    f"Inspect {repo}. Identify stack, app entry points, routes/pages, auth/session model, APIs, DB/RLS, background jobs, env files, CI, deploy targets, docs, tests, analytics/observability, and existing proof artifacts. Produce a source-file proof ledger and unknowns.",
                    profile,
                    research_depth,
                    optimization_policy,
                ),
            },
            {
                "phase": "audit",
                "role": "security-auditor",
                "title": "Audit security and trust boundaries",
                "lane": "security",
                "prompt": add_contract(
                    "Map repo evidence to OWASP Top 10 2025, OWASP API Top 10 2023, OWASP GenAI where relevant, OWASP ASVS, NIST SSDF, CISA Secure by Design, and NIST AI RMF. Score P0-P3 with exact evidence.",
                    profile,
                    research_depth,
                    optimization_policy,
                ),
            },
            {
                "phase": "verify",
                "role": "readiness-verifier",
                "title": "Verify build tests deploy proof",
                "lane": "readiness",
                "prompt": add_contract(
                    "Run safe repo-native checks where possible: build, tests, lint, typecheck, API or browser smoke. Separate hosted/live, local, repo artifact, candidate/shadow, and roadmap proof buckets.",
                    profile,
                    research_depth,
                    optimization_policy,
                ),
            },
            {
                "phase": "market",
                "role": "sellability-analyst",
                "title": "Score sellability and proof",
                "lane": "sellability",
                "prompt": add_contract(
                    "Assess buyer-visible value, weak claims, onboarding gaps, pricing or pilot readiness, demo narrative, proof pack, support readiness, and commercial caveats. Score out of 5 with evidence.",
                    profile,
                    research_depth,
                    optimization_policy,
                ),
            },
            {
                "phase": "research",
                "role": "market-researcher",
                "title": "Research pains customers competitors",
                "lane": "market",
                "prompt": add_contract(
                    "Use current web research after repo mapping. Identify top 10 buyer pain points, willingness-to-pay signals, competitors, substitutes, and top 10 target accounts or segments. Cite credible URLs.",
                    profile,
                    research_depth,
                    optimization_policy,
                ),
            },
            {
                "phase": "execute",
                "role": "fix-implementer",
                "title": "Handle safe P0 P1 fixes",
                "lane": "safe-fix",
                "prompt": add_contract(safe_fix_prompt(mode), profile, research_depth, optimization_policy),
            },
            {
                "phase": "synthesize",
                "role": "reporter",
                "title": "Produce launch decision report",
                "lane": "synthesis",
                "prompt": add_contract(
                    "Produce the required tables and a launch evidence JSON matching references/launch-evidence-schema.md: launch score, gap analysis, top 10 pain points, top 10 target customers, outreach plan, fix report, adversarial review summary, and ECC ledger. Assign blocked, pilot-only, sellable-with-caveats, or commercial-ready.",
                    profile,
                    research_depth,
                    optimization_policy,
                ),
            },
        ]
    )
    return tasks


def review_specs(
    tasks: List[Dict[str, str]],
    profile: str,
    research_depth: str,
    optimization_policy: str,
) -> List[Dict[str, str]]:
    lane_labels = {
        "repo-map": "repo map",
        "security": "security",
        "readiness": "readiness",
        "sellability": "sellability",
        "market": "market and customer targeting",
        "safe-fix": "safe fix",
        "synthesis": "synthesis",
    }
    reviews: List[Dict[str, str]] = []
    for index, task in enumerate(tasks, start=1):
        lane = task.get("lane", "")
        if lane not in lane_labels:
            continue
        target_id = f"T{index:03d}"
        lane_label = lane_labels[lane]
        reviews.append(
            {
                "target": target_id,
                "phase": "verify",
                "role": f"{slugify(lane_label)}-adversary",
                "title": f"Challenge {lane_label} lane",
                "prompt": add_contract(
                    f"Try to refute task {target_id} ({task['title']}). Find unsupported claims, missing evidence, false positives, unsafe launch language, buyer-risk gaps, and any violation of the proof buckets or stop gates.",
                    profile,
                    research_depth,
                    optimization_policy,
                ),
            }
        )
        if lane == "safe-fix" and optimization_policy != "off":
            reviews.append(
                {
                    "target": target_id,
                    "phase": "verify",
                    "role": "code-optimization-reviewer",
                    "title": "Challenge code minimality and proof",
                    "prompt": add_contract(
                        (
                            f"Review task {target_id} ({task['title']}) for the Code Optimization Gate. "
                            "Find unnecessary code, avoidable dependencies, overbroad refactors, missing simpler "
                            "config/doc/test/no-code alternatives, missing acceptance checks, missing tests, weak "
                            "rollback, and proof-bucket violations. Approve only the smallest safe verified "
                            "implementation, or require a retry with rejected variants documented."
                        ),
                        profile,
                        research_depth,
                        optimization_policy,
                    ),
                }
            )
    return reviews


def encode_task(task: Dict[str, str]) -> str:
    return "|".join([task["phase"], task["role"], task["title"], task["prompt"]])


def build_add_review_command(runner: Path, run_dir: Path, review: Dict[str, str]) -> str:
    return shell_join(
        [
            "node",
            str(runner),
            "add-review",
            "--run",
            str(run_dir),
            "--target",
            review["target"],
            "--role",
            review["role"],
            "--title",
            review["title"],
            "--prompt",
            review["prompt"],
        ]
    )


def report_template_text() -> str:
    path = SKILL_DIR / "references" / "final-report-template.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def build_commands(
    runner: Path,
    repo: Path,
    run_name: str,
    mode: str,
    profile: str,
    budget: str,
    research_depth: str,
    worker_mode: str,
    max_concurrency: int,
    include_reviews: bool,
    progress_policy: str,
    progress_interval_minutes: int,
    stall_threshold_minutes: int,
    optimization_policy: str,
) -> Tuple[Dict[str, object], List[Dict[str, str]], List[Dict[str, str]]]:
    goal = build_goal(repo, mode, profile, budget, research_depth, optimization_policy)
    run_dir = repo / ".dynamic-workflows" / run_name
    runner_text = str(runner)
    tasks = task_specs(repo, mode, profile, research_depth, optimization_policy)
    reviews = review_specs(tasks, profile, research_depth, optimization_policy) if include_reviews else []

    init_parts = [
        "node",
        runner_text,
        "init",
        "--run",
        str(run_dir),
        "--name",
        run_name,
        "--goal",
        goal,
        "--repo",
        str(repo),
        "--mode",
        "manual",
        "--max-concurrency",
        str(max_concurrency),
    ]
    for task in tasks:
        init_parts.extend(["--task", encode_task(task)])

    run_workers_parts = [
        "node",
        runner_text,
        "run-workers",
        "--run",
        str(run_dir),
        "--dry-run" if worker_mode == "dry-run" else "--execute",
    ]
    if worker_mode == "execute":
        run_workers_parts.extend(["--adapter", "tmux-worktree"])

    review_commands = [build_add_review_command(runner, run_dir, review) for review in reviews]

    commands: Dict[str, object] = {
        "automode_dry_run": shell_join(
            ["node", runner_text, "automode", "--dry-run", "--task", goal]
        ),
        "init_backlog": shell_join(init_parts),
        "add_lane_reviews": review_commands,
        "run_workers": shell_join(run_workers_parts),
        "watch": shell_join(["node", runner_text, "watch", "--run", str(run_dir)]),
        "dashboard": shell_join(
            ["node", runner_text, "dashboard", "--run", str(run_dir), "--port", "8765"]
        ),
        "dashboard_print_html": shell_join(
            ["node", runner_text, "dashboard", "--run", str(run_dir), "--print-html"]
        ),
        "synthesize": shell_join(["node", runner_text, "synthesize", "--run", str(run_dir)]),
        "validate_evidence": shell_join(
            [
                "python3",
                str(SKILL_DIR / "scripts" / "validate_launch_evidence.py"),
                str(run_dir / "launch-evidence.json"),
                "--require-repo-exists",
            ]
        ),
    }
    if progress_policy != "off":
        commands["progress_digest"] = shell_join(
            [
                "python3",
                str(SKILL_DIR / "scripts" / "render_progress_digest.py"),
                "--run",
                str(run_dir),
                "--repo",
                str(repo),
                "--stall-threshold-minutes",
                str(stall_threshold_minutes),
            ]
        )
        commands["progress_digest_json"] = shell_join(
            [
                "python3",
                str(SKILL_DIR / "scripts" / "render_progress_digest.py"),
                "--run",
                str(run_dir),
                "--repo",
                str(repo),
                "--stall-threshold-minutes",
                str(stall_threshold_minutes),
                "--output",
                "json",
            ]
        )
    sequence: List[Dict[str, str]] = [
        {"step": "1", "name": "automode_dry_run", "command": str(commands["automode_dry_run"])},
        {"step": "2", "name": "init_backlog", "command": str(commands["init_backlog"])},
    ]
    for index, command in enumerate(review_commands, start=1):
        sequence.append({"step": f"2.{index}", "name": "add_lane_review", "command": command})
    sequence.extend(
        [
            {"step": "3", "name": "run_workers", "command": str(commands["run_workers"])},
            {"step": "4", "name": "watch", "command": str(commands["watch"])},
        ]
    )
    if progress_policy != "off":
        sequence.append({"step": "4.1", "name": "progress_digest", "command": str(commands["progress_digest"])})
    sequence.extend(
        [
            {"step": "5", "name": "synthesize", "command": str(commands["synthesize"])},
            {"step": "6", "name": "validate_evidence", "command": str(commands["validate_evidence"])},
        ]
    )
    commands["ordered_sequence"] = sequence
    return commands, tasks, reviews


def build_manifest(args: argparse.Namespace) -> Dict[str, object]:
    repo = validate_repo(args.repo)
    validate_progress_options(args)
    run_name = slugify(args.name or f"{repo.name}-commercial-launch")
    runner = Path(args.runner).expanduser().resolve()
    max_concurrency = resolved_concurrency(args)
    commands, tasks, reviews = build_commands(
        runner=runner,
        repo=repo,
        run_name=run_name,
        mode=args.mode,
        profile=args.profile,
        budget=args.budget,
        research_depth=args.research_depth,
        worker_mode=args.worker_mode,
        max_concurrency=max_concurrency,
        include_reviews=args.include_reviews,
        progress_policy=args.progress_policy,
        progress_interval_minutes=args.progress_interval_minutes,
        stall_threshold_minutes=args.stall_threshold_minutes,
        optimization_policy=args.optimization_policy,
    )
    references = [
        str(SKILL_DIR / "references" / "security-readiness-framework.md"),
        str(SKILL_DIR / "references" / "market-outreach-framework.md"),
        str(SKILL_DIR / "references" / "workflow-equivalence-and-gaps.md"),
        str(SKILL_DIR / "references" / "launch-evidence-schema.md"),
        str(SKILL_DIR / "references" / "final-report-template.md"),
        str(SKILL_DIR / "references" / "one-repo-run-prompt.md"),
        str(SKILL_DIR / "references" / "ecc-skill-suite-contract.md"),
    ]
    expected_outputs = [
        "launch score table",
        "gap analysis table",
        "top 10 pain points",
        "top 10 target customers or segments",
        "30/60/90 outreach plan",
        "fix report",
        "launch evidence JSON",
        "launch evidence validator pass",
        "ECC ledger",
    ]
    if args.progress_policy != "off":
        references.insert(4, str(SKILL_DIR / "references" / "progress-reporting-contract.md"))
        expected_outputs.insert(7, "phase-wise progress digest")
        expected_outputs.insert(8, "bottleneck log for long-running runs")
    if args.optimization_policy != "off":
        references.insert(5, str(SKILL_DIR / "references" / "code-optimization-contract.md"))
        expected_outputs.insert(9, "code optimization decision ledger")

    manifest: Dict[str, object] = {
        "skill": "commercial-launch-readiness-orchestrator",
        "non_mutating": True,
        "repo": str(repo),
        "run_name": run_name,
        "run_dir": str(repo / ".dynamic-workflows" / run_name),
        "mode": args.mode,
        "profile": args.profile,
        "budget": args.budget,
        "research_depth": args.research_depth,
        "worker_mode": args.worker_mode,
        "progress_policy": {
            "mode": args.progress_policy,
            "interval_minutes": args.progress_interval_minutes,
            "stall_threshold_minutes": args.stall_threshold_minutes,
            "twenty_hour_digest_required": args.progress_policy != "off",
        },
        "optimization_policy": {
            "mode": args.optimization_policy,
            "requires_review": args.optimization_policy != "off",
            "requires_measurement": args.optimization_policy == "measured",
        },
        "max_concurrency": max_concurrency,
        "include_reviews": args.include_reviews,
        "runner": str(runner),
        "runner_exists": runner.exists(),
        "references": references,
        "ordered_sequence": commands.get("ordered_sequence", []),
        "tasks": tasks,
        "review_tasks": reviews,
        "commands": commands,
        "stop_gates": [
            "production deploy",
            "credential or secret changes",
            "payment changes",
            "destructive migrations or data deletion",
            "live outreach",
            "secret-dependent tests",
            "worker execution without explicit approval",
        ],
        "expected_outputs": expected_outputs,
    }
    if args.emit_report_template:
        manifest["report_template"] = report_template_text()
    return manifest


def render_command_block(name: str, value: object) -> List[str]:
    lines = [f"### {name}", ""]
    if name == "ordered_sequence" and isinstance(value, list):
        lines.extend(["| Step | Name | Command |", "|---|---|---|"])
        for item in value:
            if isinstance(item, dict):
                command = str(item.get("command", "")).replace("|", "\\|")
                lines.append(f"| {item.get('step', '')} | {item.get('name', '')} | `{command}` |")
        lines.append("")
        return lines
    if isinstance(value, list):
        if value:
            lines.extend(["```bash", "\n".join(str(command) for command in value), "```", ""])
        else:
            lines.extend(["No commands generated.", ""])
        return lines
    lines.extend(["```bash", str(value), "```", ""])
    return lines


def render_task_table(title: str, tasks: List[Dict[str, str]], review: bool = False) -> List[str]:
    if review:
        lines = [f"## {title}", "", "| Target | Phase | Role | Title | Prompt |", "|---|---|---|---|---|"]
        for task in tasks:
            prompt = str(task["prompt"]).replace("|", "\\|")
            lines.append(
                f"| {task['target']} | {task['phase']} | {task['role']} | {task['title']} | {prompt} |"
            )
        return lines

    lines = [f"## {title}", "", "| Lane | Phase | Role | Title | Prompt |", "|---|---|---|---|---|"]
    for task in tasks:
        prompt = str(task["prompt"]).replace("|", "\\|")
        lines.append(
            f"| {task.get('lane', '')} | {task['phase']} | {task['role']} | {task['title']} | {prompt} |"
        )
    return lines


def render_markdown(manifest: Dict[str, object]) -> str:
    commands = manifest["commands"]
    tasks = manifest["tasks"]
    reviews = manifest["review_tasks"]
    assert isinstance(commands, dict)
    assert isinstance(tasks, list)
    assert isinstance(reviews, list)

    lines = [
        "# Commercial Launch Readiness Workflow Scaffold",
        "",
        f"- Repo: `{manifest['repo']}`",
        f"- Run dir: `{manifest['run_dir']}`",
        f"- Mode: `{manifest['mode']}`",
        f"- Profile: `{manifest['profile']}`",
        f"- Budget: `{manifest['budget']}`",
        f"- Research depth: `{manifest['research_depth']}`",
        f"- Worker mode: `{manifest['worker_mode']}`",
        f"- Progress policy: `{manifest['progress_policy']}`",
        f"- Optimization policy: `{manifest['optimization_policy']}`",
        f"- Max concurrency: `{manifest['max_concurrency']}`",
        f"- Reviews included: `{manifest['include_reviews']}`",
        f"- Runner exists: `{manifest['runner_exists']}`",
        f"- Non-mutating scaffold: `{manifest['non_mutating']}`",
        "",
        "## Commands",
        "",
    ]
    for name, command in commands.items():
        lines.extend(render_command_block(name, command))

    lines.extend(render_task_table("Task Graph", tasks))
    lines.append("")
    lines.extend(render_task_table("Lane-Specific Review Tasks", reviews, review=True))

    lines.extend(["", "## Stop Gates", ""])
    for gate in manifest["stop_gates"]:
        lines.append(f"- {gate}")

    lines.extend(["", "## Final Synthesis Checklist", ""])
    for output in manifest["expected_outputs"]:
        lines.append(f"- {output}")

    template = manifest.get("report_template")
    if isinstance(template, str) and template.strip():
        lines.extend(["", "## Report Template", "", template.rstrip()])

    return "\n".join(lines) + "\n"


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit ECC dynamic workflow commands for one-repo commercial launch readiness."
    )
    parser.add_argument("--repo", required=True, help="Repository path to audit.")
    parser.add_argument("--name", default="", help="Run name. Defaults to repo-name-commercial-launch.")
    parser.add_argument(
        "--mode",
        choices=["audit-only", "fix-safe", "full"],
        default="audit-only",
        help="Audit/fix mode.",
    )
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        default="auto",
        help="Commercial audit profile. auto emits a repo-profiler task.",
    )
    parser.add_argument(
        "--budget",
        choices=["conservative", "standard", "aggressive"],
        default="standard",
        help="Budget profile used for generated max concurrency unless explicitly overridden.",
    )
    parser.add_argument(
        "--research-depth",
        choices=["light", "standard", "deep"],
        default="deep",
        help="External research depth for generated prompts.",
    )
    parser.add_argument(
        "--worker-mode",
        choices=["dry-run", "execute"],
        default="dry-run",
        help="Generated worker command mode. The scaffold still only prints commands.",
    )
    parser.add_argument(
        "--progress-policy",
        choices=PROGRESS_POLICIES,
        default="both",
        help="Progress reporting policy for generated long-running workflow commands.",
    )
    parser.add_argument(
        "--progress-interval-minutes",
        type=int,
        default=45,
        help="Default proactive progress update interval.",
    )
    parser.add_argument(
        "--stall-threshold-minutes",
        type=int,
        default=120,
        help="Minutes without meaningful status change before a bottleneck digest is required.",
    )
    parser.add_argument(
        "--optimization-policy",
        choices=OPTIMIZATION_POLICIES,
        default="strict",
        help="Code optimization gate policy for generated implementation and review tasks.",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=None,
        help="Override generated ECC worker concurrency.",
    )
    parser.add_argument(
        "--include-reviews",
        dest="include_reviews",
        action="store_true",
        default=True,
        help="Generate lane-specific add-review commands.",
    )
    parser.add_argument(
        "--no-include-reviews",
        dest="include_reviews",
        action="store_false",
        help="Skip lane-specific review task commands.",
    )
    parser.add_argument(
        "--emit-report-template",
        action="store_true",
        help="Include the final Markdown report template in scaffold output.",
    )
    parser.add_argument("--runner", default=str(DEFAULT_RUNNER), help="Dynamic workflow runner path.")
    parser.add_argument(
        "--output",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format.",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    manifest = build_manifest(args)
    if args.output == "json":
        print(json.dumps(manifest, indent=2))
    else:
        print(render_markdown(manifest), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
