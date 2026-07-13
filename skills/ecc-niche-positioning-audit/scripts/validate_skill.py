#!/usr/bin/env python3
"""Deterministic validator for ecc-niche-positioning-audit skill.

Checks:
1. Frontmatter description <= 1024 characters
2. SKILL.md body <= 500 lines
3. All referenced files in references/ exist
4. All referenced schemas in schemas/ exist
5. Scope DAG has valid paths (quick/standard/deep)
6. No orphan references (referenced but non-existent)
7. Trigger phrases present in description
8. Anti-trigger section present
9. Tool Truth section present
10. Upstream Source section present
"""

import sys
import re
import json
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SKILL_FILE = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"
SCHEMAS_DIR = SKILL_DIR / "schemas"
TESTS_DIR = SKILL_DIR / "tests"

MAX_DESC_LEN = 1024
MAX_BODY_LINES = 500

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from SKILL.md."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    fm_text = parts[1]
    body = parts[2]
    fm = {}
    for line in fm_text.strip().split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm, body

def extract_description(fm: dict) -> str:
    """Extract the description value, handling multi-line YAML."""
    desc = fm.get("description", "")
    if desc == ">-":
        return ""
    return desc

def extract_referenced_files(body: str) -> list[str]:
    """Find all references/X.md and schemas/X.json mentions in body."""
    refs = set()
    for m in re.finditer(r'references/([^\s)`]+)', body):
        refs.add("references/" + m.group(1))
    for m in re.finditer(r'schemas/([^\s)`]+)', body):
        refs.add("schemas/" + m.group(1))
    for m in re.finditer(r'scripts/([^\s)`]+)', body):
        refs.add("scripts/" + m.group(1))
    for m in re.finditer(r'tests/([^\s)`]+)', body):
        refs.add("tests/" + m.group(1))
    return sorted(refs)

def check_scope_dag(body: str) -> dict:
    """Check that scope DAG paths are valid."""
    scopes = {"quick": False, "standard": False, "deep": False}
    for scope in scopes:
        if f"**{scope}**" in body or f"`{scope}`" in body:
            scopes[scope] = True
    return scopes

def run_validation() -> list[dict]:
    """Run all validation checks and return list of findings."""
    findings = []

    if not SKILL_FILE.exists():
        findings.append({"check": "file_exists", "status": "FAIL", "detail": f"SKILL.md not found at {SKILL_FILE}"})
        return findings

    content = SKILL_FILE.read_text()
    fm, body = parse_frontmatter(content)
    body_lines = body.strip().split("\n")
    body_line_count = len(body_lines)

    # Check 1: Frontmatter description length
    desc = extract_description(fm)
    # For multi-line descriptions, reconstruct from raw content
    if not desc or len(desc) < 50:
        raw_fm = content.split("---")[1] if "---" in content else ""
        desc_lines = []
        in_desc = False
        for line in raw_fm.split("\n"):
            if line.strip().startswith("description:"):
                in_desc = True
                val = line.split(":", 1)[1].strip()
                if val and val != ">-":
                    desc_lines.append(val)
                continue
            if in_desc:
                if line.startswith("  ") or line.strip() == "":
                    desc_lines.append(line.strip())
                else:
                    break
        desc = " ".join(desc_lines)

    desc_len = len(desc)
    if desc_len > MAX_DESC_LEN:
        findings.append({
            "check": "frontmatter_description_length",
            "status": "FAIL",
            "detail": f"Description is {desc_len} chars, max is {MAX_DESC_LEN}",
            "remediation": "Shorten description to under 1024 chars"
        })
    else:
        findings.append({
            "check": "frontmatter_description_length",
            "status": "PASS",
            "detail": f"Description is {desc_len} chars (max {MAX_DESC_LEN})"
        })

    # Check 2: Body line count
    if body_line_count > MAX_BODY_LINES:
        findings.append({
            "check": "body_line_count",
            "status": "FAIL",
            "detail": f"Body is {body_line_count} lines, max is {MAX_BODY_LINES}",
            "remediation": "Move detailed content to references/ files"
        })
    else:
        findings.append({
            "check": "body_line_count",
            "status": "PASS",
            "detail": f"Body is {body_line_count} lines (max {MAX_BODY_LINES})"
        })

    # Check 3: Referenced files exist (skip glob patterns)
    referenced = extract_referenced_files(body)
    for ref in referenced:
        if "*" in ref:
            continue  # Glob pattern — check parent directory exists
            ref_path = SKILL_DIR / Path(ref).parent
        else:
            ref_path = SKILL_DIR / ref
        if not ref_path.exists():
            findings.append({
                "check": "referenced_file_exists",
                "status": "FAIL",
                "detail": f"Referenced file does not exist: {ref}",
                "remediation": f"Create {ref} or remove reference from SKILL.md"
            })

    # Check 4: Trigger phrases in description
    trigger_phrases = ["niche segment", "positioning"]
    desc_lower = desc.lower()
    for phrase in trigger_phrases:
        if phrase not in desc_lower:
            findings.append({
                "check": "trigger_phrase_present",
                "status": "FAIL",
                "detail": f"Trigger phrase '{phrase}' not found in description",
                "remediation": f"Add '{phrase}' to description"
            })

    # Check 5: Scope DAG
    scopes = check_scope_dag(body)
    for scope, found in scopes.items():
        if not found:
            findings.append({
                "check": "scope_dag_coverage",
                "status": "FAIL",
                "detail": f"Scope '{scope}' not found in body",
                "remediation": f"Add '{scope}' scope to SKILL.md"
            })

    # Check 6: Required sections present
    required_sections = ["## Tool Truth", "## Upstream Source", "## Prerequisites"]
    for section in required_sections:
        if section not in body:
            findings.append({
                "check": "required_section",
                "status": "FAIL",
                "detail": f"Required section '{section}' not found",
                "remediation": f"Add '{section}' section to SKILL.md"
            })

    # Check 7: Anti-trigger present
    if "DO NOT TRIGGER" not in content and "When NOT to use" not in body:
        findings.append({
            "check": "anti_trigger_present",
            "status": "FAIL",
            "detail": "No anti-trigger section found",
            "remediation": "Add 'When NOT to use' or 'DO NOT TRIGGER' section"
        })

    # Check 8: References directory
    if REFERENCES_DIR.exists():
        ref_files = list(REFERENCES_DIR.glob("*.md"))
        findings.append({
            "check": "references_directory",
            "status": "PASS",
            "detail": f"references/ exists with {len(ref_files)} files"
        })
    else:
        findings.append({
            "check": "references_directory",
            "status": "FAIL",
            "detail": "references/ directory does not exist",
            "remediation": "Create references/ directory with reference files"
        })

    # Check 9: Schemas directory
    if SCHEMAS_DIR.exists():
        schema_files = list(SCHEMAS_DIR.glob("*.json"))
        findings.append({
            "check": "schemas_directory",
            "status": "PASS",
            "detail": f"schemas/ exists with {len(schema_files)} files"
        })
    else:
        findings.append({
            "check": "schemas_directory",
            "status": "FAIL",
            "detail": "schemas/ directory does not exist",
            "remediation": "Create schemas/ directory with JSON schemas"
        })

    # Check 10: Tests directory
    if TESTS_DIR.exists():
        test_files = list(TESTS_DIR.glob("*.json"))
        findings.append({
            "check": "tests_directory",
            "status": "PASS",
            "detail": f"tests/ exists with {len(test_files)} files"
        })
    else:
        findings.append({
            "check": "tests_directory",
            "status": "FAIL",
            "detail": "tests/ directory does not exist",
            "remediation": "Create tests/ directory with test fixtures"
        })

    return findings

def main():
    findings = run_validation()
    fails = [f for f in findings if f["status"] == "FAIL"]
    passes = [f for f in findings if f["status"] == "PASS"]

    print(f"\n{'='*60}")
    print(f"ecc-niche-positioning-audit Skill Validator")
    print(f"{'='*60}\n")

    for f in findings:
        icon = "✅" if f["status"] == "PASS" else "❌"
        print(f"  {icon} [{f['check']}] {f['detail']}")
        if f["status"] == "FAIL" and "remediation" in f:
            print(f"     → {f['remediation']}")

    print(f"\n{'='*60}")
    print(f"  {len(passes)} passed, {len(fails)} failed")
    print(f"{'='*60}\n")

    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
