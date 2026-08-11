#!/usr/bin/env python3
"""Validate the evidence-bound skill optimization manifest.

The schema handles shape.  This validator handles cross-file provenance and
ranking invariants so a clean Git tree cannot silently omit user-owned skills.
It fails closed when jsonschema is unavailable or any required source drifts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA_VERSION = "skill-optimization-manifest.v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load JSON {path}: {exc}") from exc


def _resolve(root: Path, raw: str) -> Path:
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def _error(errors: list[str], message: str) -> None:
    errors.append(message)


def _validate_snapshot(snapshot: dict[str, Any], *, root: Path, errors: list[str]) -> None:
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
        _error(errors, f"cannot verify Git snapshot: {exc}")
        return
    binding = snapshot.get("binding")
    if binding == "exact-head":
        if snapshot["git_head"].casefold() != head.casefold():
            _error(errors, f"snapshot Git HEAD drift: expected {snapshot['git_head']}, got {head}")
    elif binding == "ancestor-commit":
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", snapshot["git_head"], head],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            _error(errors, f"snapshot commit is not an ancestor of current HEAD: {snapshot['git_head']} -> {head}")
    else:
        _error(errors, f"unsupported snapshot binding: {binding}")
    actual_status = "dirty" if status.strip() else "clean"
    if snapshot["worktree_status"] != actual_status:
        _error(errors, f"snapshot worktree status drift: expected {snapshot['worktree_status']}, got {actual_status}")
    expected_scope = "working-tree" if actual_status == "dirty" else "clean-checkout"
    if snapshot["scope"] != expected_scope:
        _error(errors, f"snapshot scope does not match worktree: expected {expected_scope}, got {snapshot['scope']}")
    expected_policy = "working-tree" if actual_status == "dirty" else "tracked-only"
    if snapshot["tracked_file_policy"] != expected_policy:
        _error(errors, f"snapshot tracked-file policy drift: expected {expected_policy}, got {snapshot['tracked_file_policy']}")


def _validate_cross_file(
    manifest: dict[str, Any],
    *,
    root: Path,
    summary_path: Path | None,
    check_targets: bool,
) -> list[str]:
    errors: list[str] = []
    rows = manifest.get("skills", [])
    ids: set[str] = set()
    paths: set[str] = set()
    aliases: dict[str, str] = {}

    for row in rows:
        skill_id = row["id"]
        if skill_id in ids:
            _error(errors, f"duplicate skill id: {skill_id}")
        ids.add(skill_id)
        path = row["canonical_path"]
        if path in paths:
            _error(errors, f"duplicate canonical path: {path}")
        paths.add(path)
        for alias in row["aliases"]:
            key = alias.casefold()
            previous = aliases.get(key)
            if previous is not None and previous != skill_id:
                _error(errors, f"alias collision: {alias} maps to {previous} and {skill_id}")
            aliases[key] = skill_id
        for scenario_id in ("supportive", "neutral", "competing"):
            if not any(scenario_id in value.casefold() for value in row["optimization"]["scenario_ids"]):
                _error(errors, f"{skill_id}: missing {scenario_id} scenario id")

        if not check_targets:
            continue
        if row["source_kind"] == "external":
            continue
        target = _resolve(root, path)
        if not target.is_file():
            _error(errors, f"{skill_id}: canonical target is missing: {target}")
            continue
        actual_hash = _sha256(target)
        if actual_hash.casefold() != row["target_sha256"].casefold():
            _error(errors, f"{skill_id}: target hash drift: expected {row['target_sha256']}, got {actual_hash}")
        if target.name != "SKILL.md":
            _error(errors, f"{skill_id}: canonical target must be SKILL.md: {target}")

    if summary_path is not None:
        try:
            summary = _load_json(summary_path)
        except ValueError as exc:
            _error(errors, str(exc))
            return errors
        expected: list[tuple[str, str, int]] = []
        expected.extend((row["name"], "top20", index) for index, row in enumerate(summary["ranked_top_skills"], 1))
        expected.extend((row["name"], "under10", index) for index, row in enumerate(summary["underutilized_candidates"], 1))
        actual = {(row["id"], row["rank_bucket"]): row["rank"] for row in rows}
        for skill_id, bucket, rank in expected:
            if (skill_id, bucket) not in actual:
                _error(errors, f"missing frozen ranking row: {bucket} #{rank} {skill_id}")
            elif actual[(skill_id, bucket)] != rank:
                _error(errors, f"rank drift for {bucket} #{rank} {skill_id}: got {actual[(skill_id, bucket)]}")
        if len(rows) != len(expected):
            _error(errors, f"manifest row count {len(rows)} does not match frozen ranking count {len(expected)}")

    return errors


def validate_manifest(
    manifest_path: Path,
    *,
    schema_path: Path,
    root: Path,
    summary_path: Path | None,
    check_sources: bool,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        import jsonschema
    except ImportError as exc:
        return {"status": "invalid", "errors": [f"jsonschema is required: {exc}"]}
    try:
        manifest = _load_json(manifest_path)
        schema = _load_json(schema_path)
    except ValueError as exc:
        return {"status": "invalid", "errors": [str(exc)]}
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors.extend(error.message for error in validator.iter_errors(manifest))
    if isinstance(manifest, dict) and manifest.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        errors.append(f"schema_version must be {EXPECTED_SCHEMA_VERSION}")
    if isinstance(manifest, dict) and not errors:
        if check_sources:
            source = manifest["source_audit"]
            _validate_snapshot(source["snapshot"], root=root, errors=errors)
            for field, expected_path in (
                ("summary_sha256", source["summary_path"]),
                ("skill_manifest_sha256", source["skill_manifest_path"]),
                ("inventory_sha256", source["inventory_path"]),
            ):
                path = _resolve(root, expected_path)
                if not path.is_file():
                    errors.append(f"source file is missing: {path}")
                else:
                    actual = _sha256(path)
                    if actual.casefold() != source[field].casefold():
                        errors.append(f"source hash drift for {expected_path}: expected {source[field]}, got {actual}")
        errors.extend(_validate_cross_file(manifest, root=root, summary_path=summary_path, check_targets=check_sources))
    result: dict[str, Any] = {
        "status": "valid" if not errors else "invalid",
        "manifest": str(manifest_path),
        "schema_version": manifest.get("schema_version") if isinstance(manifest, dict) else None,
        "skills": len(manifest.get("skills", [])) if isinstance(manifest, dict) and isinstance(manifest.get("skills"), list) else 0,
        "errors": errors,
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--schema", type=Path, default=Path("schemas/skill-optimization-manifest.schema.json"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--summary", type=Path, default=None, help="Check exact top20/under10 membership against this summary")
    parser.add_argument("--check-sources", action="store_true", help="Verify source and target SHA-256 bindings")
    args = parser.parse_args(argv)
    try:
        result = validate_manifest(
            args.manifest,
            schema_path=args.schema,
            root=args.root.resolve(),
            summary_path=args.summary,
            check_sources=args.check_sources,
        )
    except Exception as exc:  # CLI boundary must never leak a traceback.
        result = {"status": "invalid", "errors": [f"internal validator error: {exc}"]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
