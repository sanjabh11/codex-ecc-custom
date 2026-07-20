#!/usr/bin/env python3
"""Generate skill-index.json and skill-projections.json.

skill-index.json: canonical inventory of all local skills with metadata.
skill-projections.json: projection status for each skill to runtime targets.
"""

import hashlib
import json
import os
import re
import sys

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

RUNTIME_TARGETS = [
    {"name": "codex_cache", "path": "~/.codex/skills", "type": "cache"},
    {"name": "claude_code", "path": "~/.claude/skills", "type": "cache"},
]


def extract_frontmatter(content):
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        return {}
    fm = fm_match.group(1)
    result = {}
    name_match = re.search(r'^name:\s*(.+)$', fm, re.MULTILINE)
    if name_match:
        result["name"] = name_match.group(1).strip()
    desc_match = re.search(r'description:\s*>-?\s*\n?(.*?)(?=\n\s*TRIGGER|\n\s*DO NOT|\n---|\n\s*allow_|\Z)', fm, re.DOTALL | re.MULTILINE)
    if desc_match:
        desc = desc_match.group(1).strip().replace('\n', ' ').replace('  ', ' ')
        result["description"] = desc[:300]
    return result


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)

    index = []
    projections = []

    for entry in sorted(os.listdir(SKILLS_DIR)):
        skill_md_path = os.path.join(SKILLS_DIR, entry, "SKILL.md")
        if not os.path.isfile(skill_md_path):
            continue

        with open(skill_md_path, "r") as f:
            content = f.read()

        fm = extract_frontmatter(content)
        name = fm.get("name", entry)
        desc = fm.get("description", "")
        skill_hash = sha256_file(skill_md_path)
        has_openai_yaml = os.path.exists(os.path.join(SKILLS_DIR, entry, "agents", "openai.yaml"))
        has_validate_script = any(
            os.path.exists(os.path.join(SKILLS_DIR, entry, "scripts", f))
            for f in ["validate_skill.py", "validate_weekly_marketing_flywheel.py"]
        )

        index.append({
            "skill_dir": entry,
            "name": name,
            "description": desc,
            "canonical_path": f"skills/{entry}/SKILL.md",
            "sha256": skill_hash,
            "has_openai_yaml": has_openai_yaml,
            "has_validate_script": has_validate_script,
            "source": "canonical",
        })

        # Check projection status for each runtime target
        for target in RUNTIME_TARGETS:
            target_path = os.path.expanduser(os.path.join(target["path"], entry, "SKILL.md"))
            projected = os.path.exists(target_path)
            projected_hash = sha256_file(target_path) if projected else None
            parity = (skill_hash == projected_hash) if projected else False

            projections.append({
                "skill_dir": entry,
                "name": name,
                "target": target["name"],
                "target_type": target["type"],
                "projected": projected,
                "canonical_sha256": skill_hash,
                "projection_sha256": projected_hash,
                "parity": parity,
            })

    # Write skill-index.json
    index_path = os.path.join(DOCS_DIR, "skill-index.json")
    with open(index_path, "w") as f:
        json.dump({"skills": index, "total": len(index)}, f, indent=2)

    # Write skill-projections.json
    proj_path = os.path.join(DOCS_DIR, "skill-projections.json")
    with open(proj_path, "w") as f:
        json.dump({"projections": projections, "targets": RUNTIME_TARGETS}, f, indent=2)

    # Summary
    projected_count = sum(1 for p in projections if p["projected"])
    parity_count = sum(1 for p in projections if p["parity"])
    mismatch_count = projected_count - parity_count

    print(f"PASS: Generated skill index and projections")
    print(f"  Index: {index_path} ({len(index)} skills)")
    print(f"  Projections: {proj_path} ({len(projections)} entries)")
    print(f"  Projected: {projected_count}, Parity: {parity_count}, Mismatches: {mismatch_count}")
    sys.exit(0)


if __name__ == "__main__":
    main()
