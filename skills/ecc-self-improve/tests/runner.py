#!/usr/bin/env python3
"""
ecc-self-improve regression fixture runner v2.

Usage:
    python3 runner.py                          # Run all fixtures
    python3 runner.py --skill ecc-agent-reach  # Run fixtures for one skill
    python3 runner.py --verify                 # Verify fixture JSON is valid
    python3 runner.py --list                   # List all fixture IDs
    python3 runner.py --boundary-check         # Check Tier 2 boundary conditions
    python3 runner.py --check-claims <patch>   # Verify patch claims trace to LEARNINGS.md
    python3 runner.py --audit                  # Audit all auto-patches in SKILL.md files

No external dependencies — stdlib only.
"""

import json
import re
import sys
import os
import subprocess
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

FIXTURES_PATH = Path(__file__).parent / "fixtures.json"
EXPANDED_FIXTURES_PATH = Path(__file__).parent / "fixtures-expanded.json"
SKILLS_ROOT = Path(__file__).parent.parent.parent  # codex-ecc-custom/skills/
LEARNINGS_PATH = SKILLS_ROOT.parent / "LEARNINGS.md"
TERMS_PATH = Path(__file__).parent.parent / "TERMS.md"


# ─── Fixture Loading ──────────────────────────────────────────────────────────

def load_fixtures(skill_filter=None):
    """Load all fixtures from base + expanded files."""
    fixtures = []
    for path in [FIXTURES_PATH, EXPANDED_FIXTURES_PATH]:
        if path.exists():
            with open(path) as f:
                fixtures.extend(json.load(f))
    if skill_filter:
        fixtures = [fx for fx in fixtures if fx.get("skill") == skill_filter]
    return fixtures


def load_skill_text(skill_name):
    """Load the combined text of a skill's SKILL.md for content checking."""
    skill_path = SKILLS_ROOT / skill_name / "SKILL.md"
    if not skill_path.exists():
        return None
    return skill_path.read_text()


def load_patch_text(patch_path):
    """Load proposed patch text from a temp file."""
    if patch_path and Path(patch_path).exists():
        return Path(patch_path).read_text()
    return ""


def load_learnings():
    """Load all entries from LEARNINGS.md."""
    if not LEARNINGS_PATH.exists():
        return []
    entries = []
    with open(LEARNINGS_PATH) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


# ─── Regression Fixture Runner ────────────────────────────────────────────────

def run_fixture(fixture, skill_text, patch_text=""):
    """
    Run a single fixture against skill text + optional patch text.
    Returns (passed: bool, reason: str)
    """
    combined_text = (skill_text or "") + "\n" + patch_text

    # Check must_contain_any
    must_contain = fixture.get("must_contain_any", [])
    if must_contain:
        found_any = any(
            term.lower() in combined_text.lower() or
            bool(re.search(term, combined_text, re.IGNORECASE))
            for term in must_contain
        )
        if not found_any:
            return False, f"must_contain_any not satisfied: none of {must_contain} found"

    # Check must_not_contain (these are regex patterns)
    must_not = fixture.get("must_not_contain", [])
    for pattern in must_not:
        if re.search(pattern, combined_text, re.IGNORECASE):
            return False, f"must_not_contain violated: pattern '{pattern}' matched"

    return True, "PASS"


def run_all(skill_filter=None, patch_path=None, verbose=True):
    fixtures = load_fixtures(skill_filter)
    if not fixtures:
        print(f"No fixtures found{f' for skill: {skill_filter}' if skill_filter else ''}.")
        return True

    results = []
    for fx in fixtures:
        skill_name = fx["skill"]
        skill_text = load_skill_text(skill_name)
        patch_text = load_patch_text(patch_path) if patch_path else ""

        if skill_text is None:
            result = {
                "id": fx["id"],
                "skill": skill_name,
                "passed": False,
                "reason": f"SKILL.md not found at skills/{skill_name}/SKILL.md"
            }
        else:
            passed, reason = run_fixture(fx, skill_text, patch_text)
            result = {
                "id": fx["id"],
                "skill": skill_name,
                "passed": passed,
                "reason": reason
            }
        results.append(result)

    # Display results
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = len(results) - passed_count

    if verbose:
        print(f"\n🧪 Regression Fixture Runner v2 — {len(results)} fixtures\n")
        for r in results:
            icon = "✅" if r["passed"] else "❌"
            print(f"  {icon} {r['id']} ({r['skill']})")
            if not r["passed"]:
                print(f"     → {r['reason']}")
        print(f"\nResult: {passed_count} passed, {failed_count} failed\n")

        if failed_count == 0:
            print("✅ GATE PASSED — all fixtures passed. Patch may be applied.")
        else:
            print("❌ GATE BLOCKED — patch NOT applied.")
            print("   Fix the failures above or update the fixture if the test is wrong.")

    return failed_count == 0


# ─── Boundary Condition Checker (NEW) ────────────────────────────────────────

def boundary_check(verbose=True):
    """
    Check all 6 Tier 2 boundary conditions.
    Returns (all_passed: bool, results: list of (bc_id, passed, detail))
    """
    entries = load_learnings()
    unpromoted = [e for e in entries if not e.get("promoted")]

    groups = defaultdict(list)
    for e in unpromoted:
        groups[(e.get("skill_invoked"), e.get("failure_type"))].append(e)

    # BC-1: ≥ 3 unpromoted entries
    bc1 = len(unpromoted) >= 3
    bc1_detail = f"{len(unpromoted)} unpromoted entries found"

    # BC-2: At least one entry with total frequency ≥ 3
    max_freq = max((sum(e.get("frequency", 1) for e in es) for es in groups.values()), default=0)
    bc2 = max_freq >= 3
    bc2_detail = f"max frequency across groups: {max_freq}"

    # BC-3: At least one high-confidence entry
    high_conf_entries = [e for e in unpromoted if e.get("confidence") == "high"]
    bc3 = len(high_conf_entries) > 0
    bc3_detail = f"{len(high_conf_entries)} high-confidence entries found"

    # BC-4: All unpromoted entries have conversation_evidence
    entries_missing_evidence = [e for e in unpromoted if not e.get("conversation_evidence")]
    bc4 = len(entries_missing_evidence) == 0
    bc4_detail = (f"all entries have conversation_evidence"
                  if bc4 else
                  f"{len(entries_missing_evidence)} entries missing conversation_evidence")

    # BC-5: Regression fixtures pass
    fixtures_pass = run_all(verbose=False)
    bc5 = fixtures_pass
    bc5_detail = "regression fixture suite passes" if bc5 else "regression fixtures FAILED"

    # BC-6: Git working tree is clean (no uncommitted changes to SKILL.md files)
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "skills/"],
            capture_output=True, text=True, cwd=str(SKILLS_ROOT.parent)
        )
        dirty_files = [l for l in result.stdout.splitlines() if "SKILL.md" in l]
        bc6 = len(dirty_files) == 0
        bc6_detail = ("working tree clean" if bc6
                      else f"{len(dirty_files)} SKILL.md files have uncommitted changes")
    except Exception as e:
        bc6 = False
        bc6_detail = f"could not check git status: {e}"

    bcs = [
        ("BC-1", bc1, "LEARNINGS.md has ≥3 unpromoted entries", bc1_detail),
        ("BC-2", bc2, "At least one entry with frequency ≥3",    bc2_detail),
        ("BC-3", bc3, "At least one entry confidence='high'",    bc3_detail),
        ("BC-4", bc4, "All mined entries have conversation_evidence", bc4_detail),
        ("BC-5", bc5, "Regression fixtures pass",                bc5_detail),
        ("BC-6", bc6, "Git working tree is clean",               bc6_detail),
    ]

    all_passed = all(b[1] for b in bcs)

    if verbose:
        print("\n🔒 STAGE 0 — BOUNDARY CONDITIONS (Tier 2 requires ALL to pass)\n")
        for bc_id, passed, label, detail in bcs:
            icon = "✅" if passed else "❌"
            print(f"  {icon} {bc_id}: {label}")
            print(f"       → {detail}")
        print()
        if all_passed:
            print("  ✅ TIER 2 STATUS: READY — all boundary conditions met.")
            print("     Proceed with /ecc-self-improve (after reviewing TERMS.md).")
        else:
            failed = [bc_id for bc_id, passed, *_ in bcs if not passed]
            print(f"  ❌ TIER 2 STATUS: BLOCKED — {len(failed)} condition(s) not met: {', '.join(failed)}")
            print("     Use /ecc-self-improve --dry-run (Tier 1) to preview without applying.")

    return all_passed, bcs


# ─── Claims Checker (NEW) ─────────────────────────────────────────────────────

def check_claims(patch_path, verbose=True):
    """
    Verify that all specific claims in a patch file (URLs, stats, tool names)
    can be traced back to a LEARNINGS.md entry.
    Returns (all_verified: bool, report: list)
    """
    if not patch_path or not Path(patch_path).exists():
        print(f"❌ Patch file not found: {patch_path}")
        return False, []

    patch_text = Path(patch_path).read_text()
    entries = load_learnings()

    # Build searchable corpus from LEARNINGS.md
    corpus = " ".join(
        f"{e.get('context','')} {e.get('correction','')} {e.get('conversation_evidence','')}"
        for e in entries
    )

    # Extract claims from patch
    claims = []

    # URLs
    urls = re.findall(r'https?://[^\s\)\]"]+', patch_text)
    for url in urls:
        claims.append(("URL", url))

    # Percentages
    pcts = re.findall(r'\d+(?:\.\d+)?%', patch_text)
    for pct in pcts:
        claims.append(("Percentage", pct))

    # Tool names (ecc-* pattern)
    tools = re.findall(r'ecc-[a-z\-]+', patch_text)
    for tool in set(tools):
        claims.append(("Tool", tool))

    # Numbers + "times" or "sessions" or "occurrences"
    stats = re.findall(r'\d+\s+(?:times|sessions|occurrences|entries)', patch_text)
    for stat in stats:
        claims.append(("Statistic", stat))

    if not claims:
        if verbose:
            print("✅ No specific claims found in patch. Provenance check not required.")
        return True, []

    report = []
    all_verified = True
    for claim_type, claim_value in claims:
        found = claim_value.lower() in corpus.lower()
        report.append({
            "type": claim_type,
            "value": claim_value,
            "verified": found,
            "action": "KEEP" if found else "REMOVE from patch"
        })
        if not found:
            all_verified = False

    if verbose:
        print(f"\n🔍 CLAIM PROVENANCE CHECK — {len(claims)} claims in patch\n")
        for item in report:
            icon = "✅" if item["verified"] else "❌"
            print(f"  {icon} [{item['type']}] {item['value']!r}")
            if not item["verified"]:
                print(f"       → NOT FOUND in LEARNINGS.md → {item['action']}")
        print()
        if all_verified:
            print("✅ All claims verified in LEARNINGS.md. Patch provenance is clean.")
        else:
            unverified = sum(1 for r in report if not r["verified"])
            print(f"⚠️  {unverified} unverified claim(s). Remove them from the patch before applying.")

    return all_verified, report


# ─── Patch Auditor (NEW) ──────────────────────────────────────────────────────

def audit_patches(verbose=True):
    """
    Walk all skills/*/SKILL.md files, find [auto-patch] paragraphs,
    and produce an audit table.
    """
    auto_patch_pattern = re.compile(
        r'\*\*Learned rule \((\d{4}-\d{2}-\d{2})\) \[auto-patch\]\*\*: (.+?)(?:\n|$)',
        re.MULTILINE
    )

    entries = load_learnings()
    promoted_corrections = {e.get("correction", "").lower() for e in entries if e.get("promoted")}

    patches_found = []

    if SKILLS_ROOT.exists():
        for skill_dir in sorted(SKILLS_ROOT.iterdir()):
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    text = skill_md.read_text()
                    for match in auto_patch_pattern.finditer(text):
                        date_str, correction = match.group(1), match.group(2).strip()
                        in_learnings = correction.lower() in promoted_corrections
                        patches_found.append({
                            "skill": skill_dir.name,
                            "date": date_str,
                            "correction": correction[:80] + ("..." if len(correction) > 80 else ""),
                            "in_learnings": in_learnings
                        })

    if verbose:
        print(f"\n📋 AUTO-PATCH AUDIT — {len(patches_found)} patches found across SKILL.md files\n")
        if not patches_found:
            print("  No [auto-patch] paragraphs found yet.")
            print("  They appear after running /ecc-self-improve with Tier 2 conditions met.")
        else:
            print(f"  {'Skill':<25} {'Date':<12} {'In LEARNINGS':<14} Correction")
            print(f"  {'-'*25} {'-'*12} {'-'*14} {'-'*40}")
            for p in patches_found:
                icon = "✅" if p["in_learnings"] else "⚠️ "
                print(f"  {p['skill']:<25} {p['date']:<12} {icon:<14} {p['correction']}")
        print()
        print("To revert a patch: git log --grep='self-improve' --oneline | grep <skill>")
        print("Then: git revert <hash>")

    return patches_found


# ─── Fixture Validation ───────────────────────────────────────────────────────

def verify_fixtures():
    """Verify all fixture files are valid and well-formed."""
    try:
        fixtures = load_fixtures()
        required_fields = ["id", "skill", "description"]
        errors = []
        ids_seen = set()
        for fx in fixtures:
            for field in required_fields:
                if field not in fx:
                    errors.append(f"Fixture '{fx.get('id','?')}' missing field: {field}")
            if not fx.get("must_contain_any") and not fx.get("must_not_contain"):
                errors.append(f"Fixture '{fx.get('id','?')}' has no assertions")
            fx_id = fx.get("id", "")
            if fx_id in ids_seen:
                errors.append(f"Duplicate fixture ID: '{fx_id}'")
            ids_seen.add(fx_id)

        if errors:
            print("❌ Fixture validation failed:")
            for e in errors:
                print(f"  • {e}")
            return False
        else:
            print(f"✅ {len(fixtures)} fixtures validated successfully.")
            # Show breakdown by file
            base_count = len(json.load(open(FIXTURES_PATH))) if FIXTURES_PATH.exists() else 0
            exp_count = len(json.load(open(EXPANDED_FIXTURES_PATH))) if EXPANDED_FIXTURES_PATH.exists() else 0
            print(f"   • {base_count} from fixtures.json")
            print(f"   • {exp_count} from fixtures-expanded.json")
            return True
    except json.JSONDecodeError as e:
        print(f"❌ fixtures file is not valid JSON: {e}")
        return False


def list_fixtures():
    fixtures = load_fixtures()
    print(f"\n📋 {len(fixtures)} fixtures in fixture suite:\n")
    current_source = None
    for fx in fixtures:
        print(f"  [{fx['skill']}] {fx['id']}")
        print(f"    {fx['description']}")
    print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ECC self-improve regression + boundary fixture runner v2"
    )
    parser.add_argument("--skill", help="Only run fixtures for this skill")
    parser.add_argument("--patch", help="Path to proposed patch file to include in check")
    parser.add_argument("--verify", action="store_true", help="Validate fixture JSON format")
    parser.add_argument("--list", action="store_true", help="List all fixture IDs")
    parser.add_argument("--quiet", action="store_true", help="Only print PASS/FAIL")
    parser.add_argument("--boundary-check", action="store_true",
                        help="Check all 6 Tier 2 boundary conditions against current LEARNINGS.md")
    parser.add_argument("--check-claims", metavar="PATCH_FILE",
                        help="Verify all claims in a patch file trace back to LEARNINGS.md")
    parser.add_argument("--audit", action="store_true",
                        help="Audit all [auto-patch] paragraphs across all SKILL.md files")
    args = parser.parse_args()

    if args.verify:
        ok = verify_fixtures()
        sys.exit(0 if ok else 1)

    if args.list:
        list_fixtures()
        sys.exit(0)

    if args.boundary_check:
        all_passed, _ = boundary_check(verbose=not args.quiet)
        sys.exit(0 if all_passed else 1)

    if args.check_claims:
        all_verified, _ = check_claims(args.check_claims, verbose=not args.quiet)
        sys.exit(0 if all_verified else 1)

    if args.audit:
        patches = audit_patches(verbose=not args.quiet)
        sys.exit(0)

    all_passed = run_all(
        skill_filter=args.skill,
        patch_path=args.patch,
        verbose=not args.quiet
    )
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
