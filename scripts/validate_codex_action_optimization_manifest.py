#!/usr/bin/env python3
"""Validate the Codex action optimization manifest and frozen source binding."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA_VERSION = "codex-action-optimization-manifest.v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def validate_manifest(manifest_path: Path, *, schema_path: Path, check_sources: bool) -> dict[str, Any]:
    errors: list[str] = []
    try:
        import jsonschema
    except ImportError as exc:
        return {"status": "invalid", "errors": [f"jsonschema is required: {exc}"]}
    try:
        manifest = load_json(manifest_path)
        schema = load_json(schema_path)
    except ValueError as exc:
        return {"status": "invalid", "errors": [str(exc)]}
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors.extend(error.message for error in validator.iter_errors(manifest))
    if isinstance(manifest, dict) and manifest.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        errors.append(f"schema_version must be {EXPECTED_SCHEMA_VERSION}")
    if isinstance(manifest, dict) and not errors:
        rows = manifest["actions"]
        ids: set[str] = set()
        ranks: set[int] = set()
        for row in rows:
            if row["id"] in ids:
                errors.append(f"duplicate action id: {row['id']}")
            ids.add(row["id"])
            if row["rank"] in ranks:
                errors.append(f"duplicate action rank: {row['rank']}")
            ranks.add(row["rank"])
        if sorted(ranks) != list(range(1, len(rows) + 1)):
            errors.append("action ranks must be contiguous starting at 1")
        if check_sources:
            source = manifest["source_audit"]
            summary_path = Path(source["summary_path"])
            if not summary_path.is_file():
                errors.append(f"source summary is missing: {summary_path}")
            else:
                actual_hash = sha256_file(summary_path)
                if actual_hash.casefold() != source["summary_sha256"].casefold():
                    errors.append(f"source summary hash drift: expected {source['summary_sha256']}, got {actual_hash}")
                summary = load_json(summary_path)
                observed = summary.get("actions", {}).get("top_level") if isinstance(summary, dict) else None
                if not isinstance(observed, list) or len(observed) != len(rows):
                    errors.append("manifest actions do not match frozen top-level action count")
                else:
                    for row, expected in zip(rows, observed):
                        for field, expected_field in (("id", "action"), ("observed_count", "count"), ("observed_session_count", "session_count"), ("proof_level", "proof_level")):
                            if row[field] != expected[expected_field]:
                                errors.append(f"source drift for {row['id']} field {field}")
    return {
        "status": "valid" if not errors else "invalid",
        "manifest": str(manifest_path),
        "schema_version": manifest.get("schema_version") if isinstance(manifest, dict) else None,
        "actions": len(manifest.get("actions", [])) if isinstance(manifest, dict) and isinstance(manifest.get("actions"), list) else 0,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--schema", type=Path, default=Path("schemas/codex-action-optimization-manifest.schema.json"))
    parser.add_argument("--check-sources", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = validate_manifest(args.manifest, schema_path=args.schema, check_sources=args.check_sources)
    except Exception as exc:  # CLI boundary must not leak a traceback.
        result = {"status": "invalid", "errors": [f"internal validator error: {exc}"]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
