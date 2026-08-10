#!/usr/bin/env python3
"""Bind a passing before/after comparison to one manifest row."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = {"pilot", "evidence", "edit", "defer"}


def record(
    manifest_path: Path,
    *,
    skill_id: str,
    status: str,
    after_metric: dict[str, Any],
    proof_refs: list[str],
) -> None:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"unsupported status: {status}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = [row for row in data.get("skills", []) if row.get("id") == skill_id]
    if len(rows) != 1:
        raise ValueError(f"expected one manifest row for {skill_id}, found {len(rows)}")
    row = rows[0]
    if row.get("source_kind") != "canonical":
        raise ValueError(f"cannot record a local optimization for non-canonical skill {skill_id}")
    if not isinstance(after_metric, dict) or after_metric.get("status") in {None, "not_run"}:
        raise ValueError("after_metric must record an executed result")
    row["status"] = status
    row["after_metric"] = after_metric
    row["proof_ref"] = list(dict.fromkeys([*row.get("proof_ref", []), *proof_refs]))
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=manifest_path.parent, delete=False) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    os.replace(temporary, manifest_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--status", choices=sorted(ALLOWED_STATUSES), required=True)
    parser.add_argument("--after-metric", required=True, help="JSON object describing the executed after result")
    parser.add_argument("--proof-ref", action="append", default=[])
    args = parser.parse_args()
    try:
        after_metric = json.loads(args.after_metric)
        record(args.manifest, skill_id=args.skill, status=args.status, after_metric=after_metric, proof_refs=args.proof_ref)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"status": "updated", "skill": args.skill, "manifest": str(args.manifest)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
