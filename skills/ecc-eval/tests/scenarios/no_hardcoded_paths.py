#!/usr/bin/env python3
"""Scenario: No hardcoded paths — SKILL.md, references, openai.yaml have no /Users/sanjayb paths."""

import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent

def main():
    files_to_check = [
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "agents" / "openai.yaml",
        SKILL_DIR / "references" / "ci-examples.md",
        SKILL_DIR / "references" / "cli-flags.md",
        SKILL_DIR / "references" / "eval-templates.md",
    ]

    for fpath in files_to_check:
        assert fpath.exists(), f"File not found: {fpath}"
        content = fpath.read_text()
        assert "/Users/sanjayb/" not in content, f"Hardcoded /Users/sanjayb/ path found in {fpath.name}"
        # Allow $(git root) when preceded by "No " (checking for the anti-pattern, not using it)
        git_root_uses = [m for m in re.finditer(r'\$\(git root\)', content)
                         if not content[max(0, m.start()-3):m.start()].strip().lower().endswith("no")]
        assert len(git_root_uses) == 0, f"$(git root) anti-pattern found in {fpath.name}"

    print("PASS: no_hardcoded_paths — no /Users/sanjayb/ or $(git root) in skill files")
    sys.exit(0)


if __name__ == "__main__":
    main()
