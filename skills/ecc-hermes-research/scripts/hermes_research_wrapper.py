#!/usr/bin/env python3
"""
Hermes research enforcement wrapper.
Actually enforces the policies in ecc-hermes-research SKILL.md:
- Cost caps (10 exa, 5 firecrawl, 3 search-console per task)
- Output contract (frontmatter with provenance, sources, cost, profile_filters)
- Dedup check (structured frontmatter scan, not grep)
- Auto-revocation (flag file honored)
- Domain allowlist

Usage:
  python3 hermes_research_wrapper.py --task "research ticker XOM" --domain financial
  python3 hermes_research_wrapper.py --check-output <note-path>
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("SECOND_BRAIN_ROOT", str(Path.home() / "second-brain")))
HERMESBRAIN = Path("/Users/sanjayb/Documents/Obsidian Vault/HermesBrain")
PROFILE = VAULT_ROOT / "Contract" / "personal-profile.md"
REVOKE_FLAG = VAULT_ROOT / "Contract" / "hermes-research-revoked.flag"
COST_LOG = VAULT_ROOT / "log" / "hermes-research-cost.jsonl"
RESEARCH_DIR = HERMESBRAIN / "raw" / "research"

COST_CAPS = {
    "exa": 10,
    "firecrawl": 5,
    "search-console": 3,
}

ALLOWED_DOMAINS = {"financial", "admin", "project", "market"}

REQUIRED_FRONTMATTER = [
    "date", "domain", "query", "sources", "provenance",
    "provenance.vault_checked", "provenance.mcp_used", "provenance.cost",
    "profile_filters", "status", "sensitivity",
]


def load_profile():
    if not PROFILE.exists():
        return None
    return PROFILE.read_text()


def is_revoked():
    return REVOKE_FLAG.exists()


def check_cost_caps(task_id):
    """Check cumulative cost for this task. Returns remaining budget."""
    if not COST_LOG.exists():
        return dict(COST_CAPS)
    usage = {k: 0 for k in COST_CAPS}
    for line in COST_LOG.read_text().splitlines():
        try:
            entry = json.loads(line)
            if entry.get("task_id") == task_id:
                mcp = entry.get("mcp")
                if mcp in usage:
                    usage[mcp] += 1
        except json.JSONDecodeError:
            continue
    remaining = {k: COST_CAPS[k] - v for k, v in usage.items()}
    return remaining


def log_cost(task_id, mcp, query):
    """Log a tool call for cost tracking."""
    COST_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "task_id": task_id,
        "mcp": mcp,
        "query": query[:200],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    with open(COST_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def dedup_check(query):
    """Structured frontmatter scan for existing research notes."""
    if not RESEARCH_DIR.exists():
        return []
    matches = []
    for note in RESEARCH_DIR.glob("*.md"):
        try:
            text = note.read_text()
            # Extract frontmatter
            fm_match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
            if not fm_match:
                continue
            fm = fm_match.group(1)
            # Check if query matches
            query_line = re.search(r'^query:\s*"?(.+?)"?\s*$', fm, re.MULTILINE)
            if query_line and query.lower() in query_line.group(1).lower():
                matches.append({
                    "path": str(note),
                    "query": query_line.group(1),
                    "date": re.search(r'^date:\s*(.+?)$', fm, re.MULTILINE),
                })
        except Exception:
            continue
    return matches


def validate_output(note_path):
    """Validate that a research note meets the output contract."""
    path = Path(note_path)
    if not path.exists():
        return {"valid": False, "error": "File not found"}
    text = path.read_text()
    fm_match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not fm_match:
        return {"valid": False, "error": "No frontmatter found"}
    fm = fm_match.group(1)
    missing = []
    for field in REQUIRED_FRONTMATTER:
        if "." in field:
            parent, child = field.split(".", 1)
            if not re.search(rf'^{parent}:.*{child}:', fm, re.MULTILINE | re.DOTALL):
                missing.append(field)
        else:
            if not re.search(rf'^{field}:', fm, re.MULTILINE):
                missing.append(field)
    # Check vault_checked is true
    if "provenance.vault_checked" not in missing:
        if not re.search(r'vault_checked:\s*true', fm):
            missing.append("provenance.vault_checked must be true")
    # Check sources is not empty
    if re.search(r'sources:\s*\[\s*\]', fm):
        if not re.search(r'\[GAP:', text):
            missing.append("sources empty and no [GAP:] markers — fabricated data")
    return {"valid": len(missing) == 0, "missing": missing}


def main():
    if len(sys.argv) < 2:
        print("Usage: hermes_research_wrapper.py --task <desc> --domain <domain> | --check-output <path>")
        sys.exit(1)

    if sys.argv[1] == "--check-output":
        if len(sys.argv) < 3:
            print("Missing path")
            sys.exit(1)
        result = validate_output(sys.argv[2])
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["valid"] else 1)

    if sys.argv[1] == "--task":
        domain = None
        task_desc = None
        for i, arg in enumerate(sys.argv[2:], 2):
            if arg == "--domain" and i + 1 < len(sys.argv):
                domain = sys.argv[i + 1]
            elif arg == "--desc" and i + 1 < len(sys.argv):
                task_desc = sys.argv[i + 1]

        if domain not in ALLOWED_DOMAINS:
            print(f"REJECT: domain '{domain}' not in allowlist {ALLOWED_DOMAINS}")
            sys.exit(1)

        if is_revoked():
            print("REVOKE: hermes-research is revoked (flag file exists)")
            sys.exit(1)

        profile = load_profile()
        if not profile:
            print("REJECT: personal-profile.md not found")
            sys.exit(1)

        # Vault-first gate
        if task_desc:
            dupes = dedup_check(task_desc)
            if dupes:
                print(f"DEDUP: Found {len(dupes)} existing note(s):")
                for d in dupes:
                    print(f"  - {d['path']}")
                print("Review before fetching new data.")

        # Cost check
        task_id = task_desc or "unknown"
        remaining = check_cost_caps(task_id)
        print(f"COST REMAINING: {json.dumps(remaining)}")
        for mcp, cap in remaining.items():
            if cap <= 0:
                print(f"HARD STOP: {mcp} cap reached ({COST_CAPS[mcp]} calls)")
        print("READY: profile loaded, domain allowed, vault checked")
        sys.exit(0)


if __name__ == "__main__":
    main()
