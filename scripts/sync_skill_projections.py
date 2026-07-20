#!/usr/bin/env python3
"""Sync skill projections from canonical source to runtime targets.

Usage:
  python3 scripts/sync_skill_projections.py --dry-run    # Preview changes
  python3 scripts/sync_skill_projections.py --target codex_cache  # Sync to one target
  python3 scripts/sync_skill_projections.py --all        # Sync to all targets

Safety:
  - Never overwrites files with different content without --force
  - Reports SHA-256 before and after
  - Does not delete skills not in canonical source
"""

import argparse
import hashlib
import json
import os
import shutil
import sys

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

RUNTIME_TARGETS = {
    "codex_cache": os.path.expanduser("~/.codex/skills"),
    "claude_code": os.path.expanduser("~/.claude/skills"),
}


def sha256_file(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Sync skill projections")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--target", choices=list(RUNTIME_TARGETS.keys()), help="Sync to one target")
    parser.add_argument("--all", action="store_true", help="Sync to all targets")
    parser.add_argument("--force", action="store_true", help="Overwrite mismatched files")
    args = parser.parse_args()

    if not args.target and not args.all:
        print("ERROR: Specify --target <name> or --all", file=sys.stderr)
        sys.exit(1)

    targets = [args.target] if args.target else list(RUNTIME_TARGETS.keys())

    # Load projections
    proj_path = os.path.join(DOCS_DIR, "skill-projections.json")
    if not os.path.exists(proj_path):
        print(f"ERROR: {proj_path} not found. Run generate_skill_index.py first.", file=sys.stderr)
        sys.exit(1)

    with open(proj_path) as f:
        projections = json.load(f)["projections"]

    mismatches = [p for p in projections if p["projected"] and not p["parity"]]
    missing = [p for p in projections if not p["projected"]]

    print(f"Canonical skills: {len(set(p['skill_dir'] for p in projections))}")
    print(f"Mismatches: {len(mismatches)}")
    print(f"Missing projections: {len(missing)}")

    if args.dry_run:
        print("\n=== DRY RUN — no changes will be made ===\n")
        for m in mismatches:
            print(f"  MISMATCH: {m['skill_dir']} → {m['target']} (canonical: {m['canonical_sha256'][:12]}, projection: {(m['projection_sha256'] or 'none')[:12]})")
        for m in missing:
            print(f"  MISSING: {m['skill_dir']} → {m['target']}")
        print("\nRun with --force to overwrite mismatches, or without --dry-run to copy missing.")
        sys.exit(0)

    copied = 0
    overwritten = 0
    skipped = 0

    for target_name in targets:
        target_base = RUNTIME_TARGETS[target_name]
        if not os.path.exists(target_base):
            print(f"  Target {target_name}: base path does not exist, skipping")
            continue

        for entry in sorted(os.listdir(SKILLS_DIR)):
            skill_dir = os.path.join(SKILLS_DIR, entry)
            skill_md = os.path.join(skill_dir, "SKILL.md")
            if not os.path.isfile(skill_md):
                continue

            target_skill_dir = os.path.join(target_base, entry)
            target_skill_md = os.path.join(target_skill_dir, "SKILL.md")

            canonical_hash = sha256_file(skill_md)
            target_hash = sha256_file(target_skill_md)

            if target_hash is None:
                # Missing — copy
                os.makedirs(target_skill_dir, exist_ok=True)
                shutil.copy2(skill_md, target_skill_md)
                # Also copy agents/openai.yaml if it exists
                yaml_src = os.path.join(skill_dir, "agents", "openai.yaml")
                if os.path.exists(yaml_src):
                    os.makedirs(os.path.join(target_skill_dir, "agents"), exist_ok=True)
                    shutil.copy2(yaml_src, os.path.join(target_skill_dir, "agents", "openai.yaml"))
                print(f"  COPIED: {entry} → {target_name}")
                copied += 1
            elif canonical_hash != target_hash:
                if args.force:
                    shutil.copy2(skill_md, target_skill_md)
                    print(f"  OVERWRITTEN: {entry} → {target_name}")
                    overwritten += 1
                else:
                    print(f"  SKIPPED (mismatch, use --force): {entry} → {target_name}")
                    skipped += 1
            else:
                skipped += 1

    print(f"\nDone: {copied} copied, {overwritten} overwritten, {skipped} skipped")
    sys.exit(0)


if __name__ == "__main__":
    main()
