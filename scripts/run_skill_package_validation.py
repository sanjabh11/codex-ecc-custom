#!/usr/bin/env python3
"""Run the shared skill validator and emit hash-bound package evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read optimization manifest: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "skill-optimization-manifest.v1":
        raise ValueError("optimization manifest schema_version is invalid")
    return payload


def run_validation(*, root: Path, manifest_path: Path, validator_path: Path, output_path: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    validator_path = validator_path.resolve()
    if not validator_path.is_file():
        raise ValueError(f"validator is missing: {validator_path}")
    manifest = load_manifest(manifest_path)
    rows = [row for row in manifest["skills"] if row.get("source_kind") == "canonical"]
    results: list[dict[str, Any]] = []
    for row in rows:
        target = (root / row["canonical_path"]).resolve()
        skills_root = (root / "skills").resolve()
        try:
            target.relative_to(skills_root)
        except ValueError as exc:
            raise ValueError(f"target escapes skills root: {target}") from exc
        if target.name != "SKILL.md" or not target.is_file():
            raise ValueError(f"canonical target is missing: {target}")
        actual_target_hash = sha256_file(target)
        if actual_target_hash.casefold() != str(row.get("target_sha256", "")).casefold():
            raise ValueError(f"target hash drift for {row['id']}: manifest binding does not match {target}")
        package_path = target.parent
        try:
            completed = subprocess.run(
                [sys.executable, str(validator_path), str(package_path)],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            status = "pass" if completed.returncode == 0 else "fail"
            exit_code: int | None = completed.returncode
            stdout = completed.stdout[-4000:]
            stderr = completed.stderr[-4000:]
        except subprocess.TimeoutExpired as exc:
            status = "timeout"
            exit_code = None
            stdout = str(exc.stdout or "")[-4000:]
            stderr = str(exc.stderr or "")[-4000:]
        results.append(
            {
                "id": row["id"],
                "target_path": str(target),
                "target_sha256": actual_target_hash,
                "package_path": str(package_path),
                "status": status,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
            }
        )
    summary = {
        "total": len(results),
        "passed": sum(result["status"] == "pass" for result in results),
        "failed": sum(result["status"] == "fail" for result in results),
        "timed_out": sum(result["status"] == "timeout" for result in results),
    }
    payload = {
        "schema_version": "skill-package-validation.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "manifest_path": str(manifest_path),
        "validator_path": str(validator_path),
        "validator_sha256": sha256_file(validator_path),
        "summary": summary,
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = run_validation(root=args.root, manifest_path=args.manifest, validator_path=args.validator, output_path=args.output)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(json.dumps({"status": "generated", **payload["summary"], "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
