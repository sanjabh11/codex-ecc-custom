#!/usr/bin/env python3
"""Generate the ranked skill optimization manifest from frozen audit inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_snapshot(root: Path, binding: str) -> dict[str, str]:
    if binding not in {"exact-head", "ancestor-commit"}:
        raise ValueError(f"unsupported Git snapshot binding: {binding}")
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.STDOUT
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=root,
            text=True,
            stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"cannot capture Git snapshot for {root}: {exc}") from exc
    if len(head) != 40:
        raise ValueError(f"unexpected Git HEAD format: {head!r}")
    dirty = bool(status.strip())
    return {
        "binding": binding,
        "scope": "working-tree" if dirty else "clean-checkout",
        "git_head": head,
        "worktree_status": "dirty" if dirty else "clean",
        "tracked_file_policy": "working-tree" if dirty else "tracked-only",
    }


ALIASES: dict[str, list[str]] = {
    "ecc-advisor": ["advisor"],
    "ecc-niche-positioning-audit": ["positioning-audit"],
    "slides": ["slide-deck"],
    "last30days": ["last-30-days"],
    "graph-engineer": ["graph-engineering"],
    "ecc-graphify": ["graphify"],
    "plan-certificates": ["plan-certificate"],
    "deterministic-simulation-testing": ["dst"],
    "ecc-a11y-audit": ["a11y-audit"],
    "ecc-buyer-pipeline": ["buyer-pipeline"],
    "ecc-conversion-audit": ["conversion-audit"],
    "spec-first-doctrine": ["spec-first"],
    "agents-md-generator": ["agents-generator"],
    "ecc-content-quality-ops": ["content-quality"],
    "ecc-cpp-review": ["cpp-review"],
}


NEXT_ACTIONS: dict[str, str] = {
    "deep-research": "External label only: bind the active host implementation and run a dated source-ledger scenario before promotion.",
    "ecc-niche-positioning-audit": "Add the shared optimization contract and claim-to-evidence output matrix after a passing before-run.",
    "ecc-advisor": "Add machine-readable advisor decision, remaining-call-budget, and completion-gate evidence after a passing before-run.",
    "prompt-optimizer": "External label only: verify the host implementation and require before/after prompt scenarios.",
    "conformance-gate": "External label only: verify the host implementation and require negative fixtures plus proof-layer labels.",
    "slides": "Add a render/open smoke artifact and final output hash; keep source-generation proof separate from visual proof.",
    "last30days": "Reconcile the UTC window and source-list contract, then run fresh/expired-cache scenarios.",
    "agent-phase-ratchet": "External label only: verify the host implementation and require baseline/check/reflection ledger evidence.",
    "second-brain-ops": "Add target-path, content-hash, reversible-write, and approval fields before any durable vault write.",
    "ecc-explain": "Add audience, evidence-level, limitations, and final-artifact fields to the output contract.",
    "ecc-ml-engineering": "Add dataset/model provenance, scope boundary, and reproducibility gates before implementation claims.",
    "ecc-multi-execute": "Add action budget, ownership map, approval gate, and rollback/stop condition before orchestration.",
    "skill-optimizer": "External label only: verify the host implementation and run supportive/neutral/competing evidence scenarios.",
    "ecc-hormozi-funnel": "Separate copy generation from buyer validation and require claim provenance before promotion.",
    "codebase-onboarding": "External label only: verify the host implementation and require HEAD/status/instruction/dependency/test baseline.",
    "ecc-fable-loop": "Add termination, budget, durable-state, and stop-condition output fields; mentions are not activation proof.",
    "ecc-model-route": "Add an auditable route decision, model/tool constraints, and explicit fallback behavior.",
    "ecc-verify": "Add standard discovery tests and a structured failure taxonomy including untested layers.",
    "ecc-prompt-optimize": "Separate the canonical package from external prompt-optimizer aliases and add namespace mapping.",
    "graph-engineer": "Keep the graph/schema validator as core and record host/MCP/runtime/human-gate proof separately.",
    "ecc-graphify": "Retain the clean-checkout core gate; keep host, remote, multimodal, and optional-export proof separate.",
    "plan-certificates": "Pilot on one provenance-heavy plan with expiry, replay, and verification output.",
    "deterministic-simulation-testing": "Pilot one boundary regression with deterministic seed, fixture, replay command, and artifact hash.",
    "ecc-a11y-audit": "Pilot one user-facing surface with tool availability, scope, and manual-review fallback recorded.",
    "ecc-buyer-pipeline": "Pilot one evidence-backed buyer hypothesis; separate draft outreach from validated buyer evidence.",
    "ecc-conversion-audit": "Pilot one funnel artifact with baseline metric source, variant boundary, and claim guard.",
    "spec-first-doctrine": "Pilot one architecture change with acceptance criteria and refusal when the spec is incomplete.",
    "agents-md-generator": "Pilot on a temporary repository with precedence, diff review, and no-broad-overwrite checks.",
    "ecc-content-quality-ops": "Pilot one customer-facing artifact with source registry, claim scan, and render/link check.",
    "ecc-cpp-review": "Activate only on a real C/C++ change after compiler/toolchain detection is proven.",
}


def _metric(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "selector_prompt_count": row.get("selector_prompt_count", 0),
        "selector_session_count": row.get("selector_session_count", 0),
        "mention_prompt_count": row.get("mention_prompt_count", 0),
        "mention_session_count": row.get("mention_session_count", 0),
        "measurement": "frozen local transcript evidence; not host activation proof",
    }


def _quality(row: dict[str, Any]) -> dict[str, Any]:
    return row.get(
        "quality_signals",
        {
            "has_frontmatter": None,
            "has_output_contract": None,
            "has_references": None,
            "has_scope_boundary": None,
            "has_scripts": None,
            "has_tests": None,
        },
    )


def _row(
    row: dict[str, Any],
    *,
    bucket: str,
    rank: int,
    root: Path,
    proof_refs: list[str],
) -> dict[str, Any]:
    name = row["name"]
    target = root / "skills" / name / "SKILL.md"
    source_kind = "canonical" if row.get("inventory_source") == "canonical" or target.is_file() else "external"
    canonical_path = str(target.relative_to(root)) if source_kind == "canonical" else f"external://{name}"
    target_hash = _sha256(target) if source_kind == "canonical" and target.is_file() else None
    owner = "external" if source_kind == "external" else ("architect" if name in {"ecc-advisor", "ecc-niche-positioning-audit"} else "glm")
    status = "defer" if source_kind == "external" else "pilot"
    scenario_ids = [f"supportive-{name}", f"neutral-{name}", f"competing-{name}"]
    return {
        "id": name,
        "rank_bucket": bucket,
        "rank": rank,
        "canonical_path": canonical_path,
        "aliases": ALIASES.get(name, []),
        "source_kind": source_kind,
        "target_sha256": target_hash,
        "status": status,
        "owner": owner,
        "proof_ref": proof_refs,
        "before_metric": _metric(row),
        "after_metric": {"status": "not_run", "measurement": "no per-skill optimization run recorded yet"},
        "next_action": NEXT_ACTIONS.get(name, "Run a bounded supportive, neutral, and competing scenario matrix."),
        "risk": "none" if source_kind == "external" else "contract-only",
        "quality_signals": _quality(row),
        "optimization": {
            "goal": "Make skill selection, scope control, output contract, and proof boundary explicit without changing unrelated behavior.",
            "control": "Run stable supportive, neutral, and competing scenarios; compare before/after evidence and reject metadata-only promotion.",
            "scenario_ids": scenario_ids,
        },
    }


def generate(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    summary_path = args.summary.resolve()
    skill_manifest_path = args.skill_manifest.resolve()
    inventory_path = args.inventory.resolve()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    proof_refs = [
        str(args.report.resolve().relative_to(root)),
        str(summary_path.relative_to(root)),
    ]
    rows.extend(
        _row(row, bucket="top20", rank=index, root=root, proof_refs=proof_refs)
        for index, row in enumerate(summary["ranked_top_skills"], 1)
    )
    rows.extend(
        _row(row, bucket="under10", rank=index, root=root, proof_refs=proof_refs)
        for index, row in enumerate(summary["underutilized_candidates"], 1)
    )
    return {
        "schema_version": "skill-optimization-manifest.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_audit": {
            "summary_path": str(summary_path.relative_to(root)),
            "summary_sha256": _sha256(summary_path),
            "skill_manifest_path": str(skill_manifest_path.relative_to(root)),
            "skill_manifest_sha256": _sha256(skill_manifest_path),
            "inventory_path": str(inventory_path.relative_to(root)),
            "inventory_sha256": _sha256(inventory_path),
            "window_start": summary["window"]["start"],
            "window_end": summary["window"]["end"],
            "snapshot": _git_snapshot(root, args.snapshot_binding),
        },
        "skills": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--summary", type=Path, default=Path("docs/audits/skill-usage-audit-frozen-summary.json"))
    parser.add_argument("--skill-manifest", type=Path, default=Path("docs/audits/skill-usage-audit-skill-manifest.json"))
    parser.add_argument("--inventory", type=Path, default=Path("docs/skill-inventory.csv"))
    parser.add_argument("--report", type=Path, default=Path("docs/skill-usage-audit-2026-08-10.md"))
    parser.add_argument(
        "--snapshot-binding",
        choices=("exact-head", "ancestor-commit"),
        default="exact-head",
        help="Bind a working-tree artifact to the exact HEAD or allow a later release commit to descend from it",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = generate(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "generated", "output": str(args.output), "skills": len(data["skills"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
