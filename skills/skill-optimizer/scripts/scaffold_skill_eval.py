#!/usr/bin/env python3
"""Emit a small skill-evaluation scenario and evidence template."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


BASE_SCENARIOS = [
    {
        "id": "S001",
        "title": "Direct activation",
        "prompt": "Use this skill for its most direct supported request.",
        "strictness": "supportive",
        "grader": "human",
        "coverage_tags": ["activation", "core-workflow"],
        "expected": [
            "The agent activates the skill for the target task.",
            "The agent follows the skill's required workflow.",
            "The final answer includes evidence or a not-run reason.",
        ],
    },
    {
        "id": "S002",
        "title": "Weak prompt activation",
        "prompt": "Ask for the same outcome without naming the skill.",
        "strictness": "neutral",
        "grader": "human",
        "coverage_tags": ["metadata", "auto-selection"],
        "expected": [
            "The metadata description is specific enough for auto-selection.",
            "The workflow does not depend on the user naming the skill.",
        ],
    },
    {
        "id": "S003",
        "title": "Competing scope pressure",
        "prompt": "Ask for adjacent work that could tempt the agent to over-expand.",
        "strictness": "competing",
        "grader": "human",
        "coverage_tags": ["scope-control", "adjacent-routing"],
        "expected": [
            "The agent keeps scope bounded.",
            "The agent routes to adjacent skills only when evidence supports it.",
        ],
    },
]

TARGET_KIND_EXTRAS = {
    "skill": [
        {
            "title": "Validation gate",
            "prompt": "Edit the skill and decide whether it can be promoted.",
            "strictness": "regression",
            "grader": "deterministic",
            "coverage_tags": ["quick-validate", "promotion-gate"],
            "expected": [
                "Runs or cites quick validation.",
                "Requires scenario evidence before promotion.",
                "Returns promote or hold with reasons.",
            ],
        }
    ],
    "prompt": [
        {
            "title": "Prompt ambiguity",
            "prompt": "Use the prompt under vague user intent and score whether it asks the right clarifying question.",
            "strictness": "neutral",
            "grader": "human",
            "coverage_tags": ["ambiguity", "assumptions"],
            "expected": [
                "States assumptions explicitly.",
                "Asks only necessary clarifying questions.",
                "Does not invent unavailable context.",
            ],
        }
    ],
    "agent": [
        {
            "title": "Role handoff boundary",
            "prompt": "Ask the agent to complete work that partly belongs to another role.",
            "strictness": "competing",
            "grader": "human",
            "coverage_tags": ["role-boundary", "handoff"],
            "expected": [
                "Keeps its role clear.",
                "Hands off or routes only the out-of-scope portion.",
                "Maintains evidence continuity.",
            ],
        }
    ],
    "workflow": [
        {
            "title": "Resume and evidence continuity",
            "prompt": "Resume a partially completed workflow and produce a final handoff.",
            "strictness": "regression",
            "grader": "human",
            "coverage_tags": ["resumability", "evidence-ledger"],
            "expected": [
                "Finds prior state before acting.",
                "Avoids restarting completed work.",
                "Reports evidence and remaining blockers.",
            ],
        }
    ],
    "commercial-launch": [
        {
            "title": "Launch blocker gate",
            "prompt": "Evaluate a repo with unresolved P0/P1 issues and decide launch status.",
            "strictness": "adversarial",
            "grader": "human",
            "coverage_tags": ["launch-gate", "p0-p1", "proof-buckets"],
            "expected": [
                "Does not return commercial-ready with unresolved P0/P1 blockers.",
                "Separates hosted/live, local, repo artifact, candidate/shadow, and roadmap proof.",
                "Maps gaps to buyer impact and frameworks.",
            ],
        },
        {
            "title": "Market evidence gate",
            "prompt": "Rank target customers for a repo with limited market sources.",
            "strictness": "neutral",
            "grader": "human",
            "coverage_tags": ["market-research", "source-evidence"],
            "expected": [
                "Uses current source evidence for pain points.",
                "Ranks by buyer pain, proof fit, urgency, and confidence.",
                "Marks weak claims as assumptions or gaps.",
            ],
        },
    ],
    "coding-discipline": [
        {
            "title": "Unclear bug diagnosis",
            "prompt": "Fix a bug report without a clear root cause.",
            "strictness": "adversarial",
            "grader": "human",
            "coverage_tags": ["diagnosis", "reproduction", "regression-test"],
            "expected": [
                "Reproduces or identifies closest evidence before editing.",
                "Forms a testable hypothesis.",
                "Runs a focused regression check after the fix.",
            ],
        },
        {
            "title": "Overengineering pressure",
            "prompt": "Ask for a small fix while suggesting a broad rewrite.",
            "strictness": "competing",
            "grader": "human",
            "coverage_tags": ["simplicity", "surgical-diff"],
            "expected": [
                "Chooses the smallest viable change.",
                "Avoids speculative abstractions.",
                "Preserves unrelated dirty worktree changes.",
            ],
        },
    ],
}


def build_manifest(args: argparse.Namespace) -> Dict[str, Any]:
    skill_path = Path(args.skill).expanduser().resolve()
    scenarios: List[Dict[str, Any]] = [dict(item) for item in BASE_SCENARIOS]
    for extra in TARGET_KIND_EXTRAS.get(args.target_kind, []):
        scenarios.append({"id": f"S{len(scenarios) + 1:03d}", **extra})
    for index, prompt in enumerate(args.scenario, start=len(scenarios) + 1):
        scenarios.append(
            {
                "id": f"S{index:03d}",
                "title": f"Custom scenario {index:03d}",
                "prompt": prompt,
                "strictness": "custom",
                "grader": "human",
                "coverage_tags": ["custom"],
                "expected": ["User-defined expected behavior."],
            }
        )

    return {
        "schema_version": "skill-optimizer.v1",
        "skill_name": args.name or skill_path.parent.name,
        "target_kind": args.target_kind,
        "target_path": str(skill_path),
        "run_id": args.run_id,
        "summary": {
            "score": None,
            "passed": None,
            "failed": None,
            "not_run": len(scenarios),
            "total": len(scenarios),
        },
        "scenarios": [
            {
                **scenario,
                "result": "not_run",
                "not_run_reason": "Template scaffold only; scenario evidence has not been collected yet.",
                "evidence": ["Evidence not collected yet; replace this before validation."],
                "artifact_paths": [],
            }
            for scenario in scenarios
        ],
        "rejected_edits": [],
        "notes": "Fill results after running scenarios.",
    }


def to_markdown(manifest: Dict[str, Any]) -> str:
    lines = [
        f"# Skill Evaluation: {manifest['skill_name']}",
        "",
        f"- Target: `{manifest['target_path']}`",
        f"- Target kind: `{manifest['target_kind']}`",
        f"- Run: `{manifest['run_id']}`",
        f"- Scenarios: {len(manifest['scenarios'])}",
        "",
        "| ID | Strictness | Tags | Title | Prompt |",
        "|---|---|---|---|---|",
    ]
    for scenario in manifest["scenarios"]:
        lines.append(
            f"| {scenario['id']} | {scenario['strictness']} | {', '.join(scenario.get('coverage_tags', []))} | {scenario['title']} | {scenario['prompt']} |"
        )
    lines.extend(
        [
            "",
            "## Evidence JSON",
            "",
            "```json",
            json.dumps(manifest, indent=2),
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", required=True, help="Path to target SKILL.md or prompt file")
    parser.add_argument("--name", help="Override skill/workflow name")
    parser.add_argument(
        "--target-kind",
        choices=["skill", "prompt", "agent", "workflow", "commercial-launch", "coding-discipline"],
        default="skill",
        help="Scenario profile to scaffold.",
    )
    parser.add_argument("--run-id", default="local-skill-eval")
    parser.add_argument("--scenario", action="append", default=[], help="Add a custom scenario prompt")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    manifest = build_manifest(args)
    if args.output == "json":
        print(json.dumps(manifest, indent=2))
    else:
        print(to_markdown(manifest), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
