#!/usr/bin/env python3
"""Read-only mapping audit for labels whose implementation is external to this repo."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_LABELS = (
    "deep-research",
    "prompt-optimizer",
    "conformance-gate",
    "agent-phase-ratchet",
    "skill-optimizer",
    "codebase-onboarding",
)
DEFAULT_HOST_ROOTS = (
    Path("~/.codeium/windsurf/skills"),
    Path("~/.codex/skills"),
    Path("~/.claude/skills"),
    Path("~/.agents/skills"),
    Path("~/.gemini/skills"),
    Path("~/.devin/skills"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _frontmatter_name(path: Path) -> str | None:
    lines = path.read_text(encoding="utf-8").splitlines()[:40]
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip().startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


def _candidate(host_root: Path, label: str) -> dict[str, object]:
    skill_dir = host_root / label
    skill_file = skill_dir / "SKILL.md"
    base = {
        "host_root": str(host_root),
        "skill_path": str(skill_file),
        "resolved_target": str(skill_dir.resolve(strict=False)) if skill_dir.exists() or skill_dir.is_symlink() else None,
        "content_sha256": None,
        "frontmatter_name": None,
    }
    if not skill_dir.exists() and not skill_dir.is_symlink():
        return {**base, "status": "missing", "projection_kind": "missing"}
    if skill_dir.is_symlink():
        projection_kind = "symlink"
    elif skill_dir.is_dir():
        projection_kind = "directory"
    elif skill_dir.is_file():
        projection_kind = "file"
    else:
        projection_kind = "other"
    try:
        content_hash = _sha256(skill_file)
        frontmatter_name = _frontmatter_name(skill_file)
    except (OSError, UnicodeDecodeError):
        return {**base, "status": "unreadable", "projection_kind": projection_kind}
    status = "present" if frontmatter_name == label else "present-invalid-frontmatter"
    return {
        **base,
        "status": status,
        "projection_kind": projection_kind,
        "content_sha256": content_hash,
        "frontmatter_name": frontmatter_name,
    }


def audit(labels: list[str], host_roots: list[Path]) -> dict[str, object]:
    expanded_roots = [root.expanduser().resolve() for root in host_roots]
    return {
        "schema_version": "external-skill-label-audit.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "discovery-only",
        "authenticated_loader_proof": False,
        "labels": [
            {
                "id": label,
                "implementation_audit": "discovery-only",
                "loader_status": "unverified",
                "trigger_status": "unverified",
                "candidates": [_candidate(root, label) for root in expanded_roots],
            }
            for label in labels
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", action="append", dest="labels", help="Label to map; repeat for multiple labels")
    parser.add_argument("--host-root", action="append", type=Path, dest="host_roots", help="Host skill root; repeat for multiple roots")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()
    try:
        result = audit(args.labels or list(DEFAULT_LABELS), args.host_roots or list(DEFAULT_HOST_ROOTS))
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "errors": [str(exc)]}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
