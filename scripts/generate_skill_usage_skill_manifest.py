#!/usr/bin/env python3
"""Generate the hash-bound canonical skill manifest used by usage audits."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generate(*, skill_root: Path, inventory_csv: Path, output: Path) -> dict[str, Any]:
    skill_root = skill_root.resolve()
    inventory_csv = inventory_csv.resolve()
    files = []
    for path in sorted(skill_root.glob("*/SKILL.md")):
        files.append({"path": str(path.resolve()), "sha256": sha256_file(path)})
    if not files:
        raise ValueError(f"no canonical SKILL.md files found under {skill_root}")
    if not inventory_csv.is_file():
        raise ValueError(f"inventory CSV is missing: {inventory_csv}")
    return {
        "schema_version": "skill-usage-skill-manifest.v1",
        "skill_root": str(skill_root),
        "inventory_csv": str(inventory_csv),
        "inventory_sha256": sha256_file(inventory_csv),
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, required=True)
    parser.add_argument("--inventory-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = generate(skill_root=args.skill_root, inventory_csv=args.inventory_csv, output=args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(json.dumps({"status": "generated", "files": len(payload["files"]), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
