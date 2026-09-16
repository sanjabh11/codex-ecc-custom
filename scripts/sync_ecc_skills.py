#!/usr/bin/env python3
"""Sync skills from an ECC checkout (local path or git URL) into a skills dir.

Usage:
    python3 scripts/sync_ecc_skills.py <source> [--target skills] [--dry-run]

Source can be:
  - a local path to the everything-claude-code repo (or any dir tree of skills)
  - a git URL (cloned to a temp dir first)

Behavior:
  - Finds every directory containing a SKILL.md under the source
  - Skips .system and dot-directories
  - Validates frontmatter has name + description; invalid skills are skipped
  - Copies each valid skill into <target>/<skill-name>/ (deduped by name)
  - Prints a report: copied, updated, skipped, invalid

Stdlib only. No third-party dependencies.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---", re.DOTALL)
NAME_RE = re.compile(r"^name:\s*[\"']?([\w.-]+)[\"']?\s*$", re.MULTILINE)
DESC_RE = re.compile(r"^description:\s*[\"']?(.+?)[\"']?\s*$", re.MULTILINE)

SKIP_DIRS = {".git", ".github", ".claude-plugin", ".codex-plugin", "node_modules", "__pycache__"}


def parse_frontmatter(skill_md: Path) -> tuple[str | None, str | None]:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None, None
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, None
    block = m.group(1)
    name = NAME_RE.search(block)
    desc = DESC_RE.search(block)
    return (name.group(1) if name else None, desc.group(1) if desc else None)


def validate(skill_md: Path) -> tuple[bool, str]:
    name, desc = parse_frontmatter(skill_md)
    if not name:
        return False, "missing name in frontmatter"
    if not desc:
        return False, "missing description in frontmatter"
    return True, name


def discover_skills(source: Path) -> dict[str, Path]:
    """Map skill-name -> SKILL.md path for all valid skills under source."""
    found: dict[str, Path] = {}
    invalid: list[tuple[Path, str]] = []
    for skill_md in sorted(source.rglob("SKILL.md")):
        if any(part in SKIP_DIRS or part.startswith(".") for part in skill_md.parts):
            continue
        ok, info = validate(skill_md)
        if ok:
            # First occurrence wins (top-level skills beat nested projections)
            found.setdefault(info, skill_md)
        else:
            invalid.append((skill_md, info))
    return found, invalid


def materialize_source(source: str) -> tuple[Path, Path | None]:
    """Return (source_path, temp_dir_or_None). For git URLs, clone first."""
    candidate = Path(source).expanduser().resolve()
    if candidate.exists():
        return candidate, None
    if re.match(r"^[\w.-]+@[\w.-]+:", source) or source.startswith(("http://", "https://", "git://", "ssh://")):
        tmp = Path(tempfile.mkdtemp(prefix="ecc-sync-"))
        subprocess.run(["git", "clone", "--depth", "1", source, str(tmp / "repo")], check=True)
        return tmp / "repo", tmp
    raise FileNotFoundError(f"Source not found and not a git URL: {source}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync ECC skills into a target skills directory")
    ap.add_argument("source", help="Local path or git URL of the ECC repo")
    ap.add_argument("--target", default="skills", help="Target skills directory (default: skills)")
    ap.add_argument("--dry-run", action="store_true", help="Report only, copy nothing")
    args = ap.parse_args()

    try:
        src, tmp = materialize_source(args.source)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    try:
        found, invalid = discover_skills(src)
        target = Path(args.target).expanduser().resolve()
        target.mkdir(parents=True, exist_ok=True)

        copied, updated, skipped = [], [], []
        for name, skill_md in sorted(found.items()):
            dest = target / name
            if dest.exists() and (dest / "SKILL.md").exists():
                if (dest / "SKILL.md").read_text(encoding="utf-8") == skill_md.read_text(encoding="utf-8"):
                    skipped.append(name)
                    continue
                updated.append(name)
            else:
                copied.append(name)
            if not args.dry_run:
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(skill_md.parent, dest)

        print(f"Source: {src}")
        print(f"Target: {target}")
        print(f"Discovered: {len(found)} valid skills, {len(invalid)} invalid")
        print(f"Would copy: {len(copied)}" if args.dry_run else f"Copied: {len(copied)}")
        for n in copied:
            print(f"  + {n}")
        print(f"Would update: {len(updated)}" if args.dry_run else f"Updated: {len(updated)}")
        for n in updated:
            print(f"  ~ {n}")
        print(f"Unchanged: {len(skipped)}")
        if invalid:
            print(f"Invalid ({len(invalid)}):")
            for p, why in invalid[:20]:
                print(f"  ! {p.relative_to(src)}: {why}")
            if len(invalid) > 20:
                print(f"  ... and {len(invalid) - 20} more")
        return 0
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
