#!/usr/bin/env python3
"""Run a deterministic metadata/contract audit for the ranked skill set.

This is deliberately not a host trigger engine.  It checks the committed
instruction surface and emits skill-optimizer.v1 evidence.  External labels
are recorded as not_run rather than being treated as locally loaded skills.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.validate_skill_optimization_manifest import validate_manifest
except ModuleNotFoundError:  # Direct `python scripts/<runner>.py` invocation.
    from validate_skill_optimization_manifest import validate_manifest


def _has_any(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(phrase.casefold() in lowered for phrase in phrases)


def _has_frontmatter(text: str, skill_id: str) -> bool:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    return any(line.strip().casefold() == f"name: {skill_id}" for line in lines[1:40])


def _has_output_contract(text: str) -> bool:
    return _has_any(
        text,
        (
            "optimization contract v1",
            "## output contract",
            "### output contract",
        ),
    )


def _scenario(
    *,
    scenario_id: str,
    title: str,
    strictness: str,
    expected: list[str],
    passed: bool,
    evidence: list[str],
    artifact_paths: list[str],
) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "title": title,
        "prompt": f"Deterministic metadata audit lane: {strictness}.",
        "strictness": strictness,
        "grader": "deterministic",
        "coverage_tags": ["activation-metadata", "scope-control", "output-contract"],
        "expected": expected,
        "result": "pass" if passed else "fail",
        "evidence": evidence,
        "artifact_paths": artifact_paths,
    }


def _not_run_scenario(*, scenario_id: str, strictness: str, reason: str, artifacts: list[str]) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "title": f"External label {strictness} lane",
        "prompt": f"External-label audit lane: {strictness}.",
        "strictness": strictness,
        "grader": "deterministic",
        "coverage_tags": ["activation-metadata", "host-boundary"],
        "expected": ["Host implementation is available and can be tested."],
        "result": "not_run",
        "not_run_reason": reason,
        "evidence": [reason],
        "artifact_paths": artifacts,
    }


def audit_row(row: dict[str, Any], *, root: Path, evidence_path: Path, manifest_path: Path, report_path: Path) -> dict[str, Any]:
    skill_id = row["id"]
    artifact_paths = [str(manifest_path.resolve()), str(report_path.resolve())]
    target_path = root / row["canonical_path"] if row["source_kind"] == "canonical" else Path(f"/external/{skill_id}/SKILL.md")
    run_id = f"skill-optimization-2026-08-10-{skill_id}"
    if row["source_kind"] == "external":
        reason = "external/global label; no canonical local SKILL.md or host trigger engine is available"
        scenarios = [
            _not_run_scenario(scenario_id=f"supportive-{skill_id}", strictness="supportive", reason=reason, artifacts=artifact_paths),
            _not_run_scenario(scenario_id=f"neutral-{skill_id}", strictness="neutral", reason=reason, artifacts=artifact_paths),
            _not_run_scenario(scenario_id=f"competing-{skill_id}", strictness="competing", reason=reason, artifacts=artifact_paths),
        ]
        summary = {"score": 0.0, "passed": 0, "failed": 0, "not_run": 3, "total": 3}
        notes = "Metadata-only ranking row. No host activation, skill loading, or successful execution is proven."
        return {
            "schema_version": "skill-optimizer.v1",
            "skill_name": skill_id,
            "target_kind": "skill",
            "target_path": str(target_path),
            "run_id": run_id,
            "summary": summary,
            "scenarios": scenarios,
            "rejected_edits": [{"edit": "Audit or edit an external implementation from this checkout", "reason": reason}],
            "notes": notes,
        }

    try:
        text = target_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        reason = f"canonical target could not be read: {exc}"
        scenarios = [
            _scenario(scenario_id=f"supportive-{skill_id}", title="Readable target", strictness="supportive", expected=["SKILL.md is readable"], passed=False, evidence=[reason], artifact_paths=artifact_paths),
            _scenario(scenario_id=f"neutral-{skill_id}", title="Readable target", strictness="neutral", expected=["SKILL.md is readable"], passed=False, evidence=[reason], artifact_paths=artifact_paths),
            _scenario(scenario_id=f"competing-{skill_id}", title="Readable target", strictness="competing", expected=["SKILL.md is readable"], passed=False, evidence=[reason], artifact_paths=artifact_paths),
        ]
        return {
            "schema_version": "skill-optimizer.v1",
            "skill_name": skill_id,
            "target_kind": "skill",
            "target_path": str(target_path.resolve()),
            "run_id": run_id,
            "summary": {"score": 0.0, "passed": 0, "failed": 3, "not_run": 0, "total": 3},
            "scenarios": scenarios,
            "rejected_edits": [{"edit": "Assume a missing target is usable", "reason": reason}],
            "notes": "Metadata-only structural audit failed at the target boundary.",
        }

    frontmatter = _has_frontmatter(text, skill_id)
    supportive = frontmatter and _has_any(text, ("trigger", "when to use", "use when"))
    neutral = _has_any(text, ("do not trigger", "out of scope", "scope boundary", "when not to use", "not use"))
    competing = _has_any(text, ("not proof", "limitations", "manual", "cannot", "do not claim", "stop condition", "evidence"))
    output_contract = _has_output_contract(text)
    common_evidence = [
        f"target={target_path.resolve()}",
        f"frontmatter_name={frontmatter}",
        f"explicit_output_contract={output_contract}",
        "metadata-only; host trigger engine not invoked",
    ]
    scenarios = [
        _scenario(
            scenario_id=f"supportive-{skill_id}",
            title="Supportive activation metadata",
            strictness="supportive",
            expected=["Valid frontmatter names the skill", "Trigger/use guidance exists"],
            passed=supportive,
            evidence=common_evidence + [f"supportive_metadata={supportive}"],
            artifact_paths=artifact_paths,
        ),
        _scenario(
            scenario_id=f"neutral-{skill_id}",
            title="Neutral scope boundary metadata",
            strictness="neutral",
            expected=["Out-of-scope or anti-trigger guidance exists"],
            passed=neutral,
            evidence=common_evidence + [f"neutral_scope_metadata={neutral}"],
            artifact_paths=artifact_paths,
        ),
        _scenario(
            scenario_id=f"competing-{skill_id}",
            title="Competing request safety metadata",
            strictness="competing",
            expected=["Limitations, evidence, manual gate, or stop guidance exists"],
            passed=competing,
            evidence=common_evidence + [f"competing_safety_metadata={competing}"],
            artifact_paths=artifact_paths,
        ),
        _scenario(
            scenario_id=f"contract-{skill_id}",
            title="Explicit optimization output contract",
            strictness="neutral",
            expected=["The shared Optimization Contract v1 is explicit"],
            passed=output_contract,
            evidence=common_evidence + [f"explicit_contract={output_contract}"],
            artifact_paths=artifact_paths,
        ),
    ]
    passed_count = sum(scenario["result"] == "pass" for scenario in scenarios)
    failed_count = len(scenarios) - passed_count
    return {
        "schema_version": "skill-optimizer.v1",
        "skill_name": skill_id,
        "target_kind": "skill",
        "target_path": str(target_path.resolve()),
        "run_id": run_id,
        "summary": {"score": round(passed_count / len(scenarios), 4), "passed": passed_count, "failed": failed_count, "not_run": 0, "total": len(scenarios)},
        "scenarios": scenarios,
        "rejected_edits": ([{"edit": "Promote based only on metadata lanes", "reason": "This runner does not invoke the host trigger engine or prove successful execution."}] if not output_contract else []),
        "notes": "Deterministic metadata-only audit; output-contract status is reported but host activation and outcome quality remain unverified.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("docs/skill-usage-audit-2026-08-10.md"))
    parser.add_argument("--schema", type=Path, default=Path("schemas/skill-optimization-manifest.schema.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = args.manifest.resolve()
    report_path = (root / args.report).resolve() if not args.report.is_absolute() else args.report.resolve()
    manifest_result = validate_manifest(
        manifest_path,
        schema_path=(root / args.schema).resolve() if not args.schema.is_absolute() else args.schema.resolve(),
        root=root,
        summary_path=(root / args.summary).resolve() if not args.summary.is_absolute() else args.summary.resolve(),
        check_sources=True,
    )
    if manifest_result["status"] != "valid":
        print(json.dumps({"status": "blocked", "manifest": manifest_result}, indent=2, sort_keys=True))
        return 2
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    index: dict[str, Any] = {
        "schema_version": "skill-optimization-evidence-index.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "manifest_path": str(manifest_path),
        "host_activation": "unverified",
        "skills": [],
    }
    for row in manifest["skills"]:
        evidence_path = output_dir / f"{row['rank_bucket']}-{row['rank']:02d}-{row['id']}.json"
        evidence = audit_row(row, root=root, evidence_path=evidence_path, manifest_path=manifest_path, report_path=report_path)
        evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        index["skills"].append(
            {
                "id": row["id"],
                "rank_bucket": row["rank_bucket"],
                "rank": row["rank"],
                "evidence_path": str(evidence_path),
                "summary": evidence["summary"],
                "host_activation": "unverified",
            }
        )
    index_path = output_dir / "index.json"
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "generated", "evidence_dir": str(output_dir), "skills": len(index["skills"]), "index": str(index_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
