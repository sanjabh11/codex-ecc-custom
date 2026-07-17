#!/usr/bin/env python3
"""Validate the ECC-native AI marketing skill adoption portfolio."""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

TOP_SKILLS = {
    "ecc-closed-loop-analytics",
    "ecc-growth-experiment-loop",
    "ecc-revenue-attribution",
    "ecc-lead-dossier",
    "ecc-outbound-campaign",
    "ecc-content-quality-ops",
    "ecc-value-pricing",
    "ecc-buyer-pipeline",
    "ecc-conversion-audit",
    "ecc-seo-opportunity-loop",
}
REPOSITORIES = {
    "Career Automation Insights Engine",
    "Canada Energy Intelligence Platform",
    "codex-ecc-custom",
    "Strategic Intelligence Platform",
    "Avalanche Insight Hub",
}
REPOSITORY_IDS = {
    "career-automation-insights-engine",
    "canada-energy-dashboard",
    "codex-ecc-custom",
    "strategic-intelligence-platform",
    "avalanche-insight-hub",
}
STRICTNESS = {"supportive", "neutral", "competing"}
SOURCE_COMMIT = "a9f11007aca31cc85f231698e22b64412f847b76"
FORBIDDEN = (
    "telemetry/version_check.py",
    "telemetry/telemetry_init.py",
    "claude --chrome",
    ".git/hooks/pre-commit",
    "singlebrain.com",
)


def _load_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError(f"{path}: invalid JSON: {exc}") from exc


def validate_repo(root):
    errors = []
    report_path = root / "docs/audits/AI_MARKETING_SKILLS_CROSS_REPO_ADOPTION_2026-07-17.md"
    prompt_path = root / "docs/audits/AI_MARKETING_SKILLS_REPO_PROMPTS_2026-07-17.md"
    evidence_path = root / "docs/audits/ai-marketing-skill-scenario-evidence.json"
    if not report_path.is_file():
        errors.append(f"missing audit report: {report_path}")
    if not prompt_path.is_file():
        errors.append(f"missing repo prompt guide: {prompt_path}")
    try:
        suite = _load_json(evidence_path)
    except AssertionError as exc:
        errors.append(str(exc))
        suite = {}
    scenarios = suite.get("scenarios", [])
    summary = suite.get("summary", {})
    counts = Counter(item.get("result") for item in scenarios)
    if len(scenarios) != 70:
        errors.append(f"expected 70 scenarios, found {len(scenarios)}")
    if counts != Counter({"pass": 70}):
        errors.append(f"scenario results are not all pass: {dict(counts)}")
    if summary != {"score": 1.0, "passed": 70, "failed": 0, "not_run": 0, "total": 70}:
        errors.append(f"invalid scenario summary: {summary}")
    by_skill = defaultdict(list)
    for item in scenarios:
        by_skill[item.get("skill_name", "")].append(item)
    if set(by_skill) != TOP_SKILLS:
        errors.append("scenario skill set does not match top-ten skill set")

    for skill in sorted(TOP_SKILLS):
        skill_dir = root / "skills" / skill
        skill_md = skill_dir / "SKILL.md"
        profile_path = skill_dir / "references/repo-profiles.md"
        manifest_path = skill_dir / "references/adoption-evidence.json"
        agent_path = skill_dir / "agents/openai.yaml"
        for required in (skill_md, profile_path, manifest_path, agent_path):
            if not required.is_file():
                errors.append(f"{skill}: missing {required.relative_to(root)}")
        if skill_md.is_file():
            text = skill_md.read_text()
            match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
            if not match:
                errors.append(f"{skill}: invalid frontmatter placement")
            else:
                frontmatter = match.group(1)
                if not re.search(r"^name:\s*" + re.escape(skill) + r"\s*$", frontmatter, re.MULTILINE):
                    errors.append(f"{skill}: frontmatter name mismatch")
                if not re.search(r"^description:\s*(>|>-|\S)", frontmatter, re.MULTILINE):
                    errors.append(f"{skill}: missing description")
                allowed = {"name", "description"}
                extra = []
                for line in frontmatter.splitlines():
                    if line and not line.startswith((" ", "\t")) and ":" in line:
                        key = line.split(":", 1)[0]
                        if key not in allowed:
                            extra.append(key)
                if extra:
                    errors.append(f"{skill}: unexpected frontmatter keys {extra}")
            package_text = "\n".join(
                path.read_text(errors="ignore")
                for path in skill_dir.rglob("*")
                if path.is_file()
            ).lower()
            for forbidden in FORBIDDEN:
                if forbidden.lower() in package_text:
                    errors.append(f"{skill}: forbidden imported behavior {forbidden}")
        if profile_path.is_file():
            profile_text = profile_path.read_text()
            for repo in REPOSITORIES:
                if repo not in profile_text:
                    errors.append(f"{skill}: missing repo profile {repo}")
        if agent_path.is_file():
            if ("$" + skill) not in agent_path.read_text():
                errors.append(f"{skill}: agents/openai.yaml prompt missing skill trigger")
        if manifest_path.is_file():
            try:
                manifest = _load_json(manifest_path)
            except AssertionError as exc:
                errors.append(str(exc))
            else:
                if manifest.get("schema_version") != "ecc-adoption.v1":
                    errors.append(f"{skill}: wrong adoption schema")
                if manifest.get("upstream", {}).get("commit") != SOURCE_COMMIT:
                    errors.append(f"{skill}: upstream commit mismatch")
                if manifest.get("decision") != "create-new-ecc-native":
                    errors.append(f"{skill}: adoption decision mismatch")
                if len(manifest.get("scenario_ids", [])) != 7:
                    errors.append(f"{skill}: expected seven scenario ids")
        skill_scenarios = by_skill.get(skill, [])
        if len(skill_scenarios) != 7:
            errors.append(f"{skill}: expected seven suite scenarios")
        if {item.get("strictness") for item in skill_scenarios} != STRICTNESS:
            errors.append(f"{skill}: strictness coverage incomplete")
        covered = {item.get("repository") for item in skill_scenarios}
        if not REPOSITORY_IDS.issubset(covered):
            errors.append(f"{skill}: five-repo scenario coverage incomplete")
    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    errors = validate_repo(root)
    if errors:
        print("AI marketing skill adoption validation: FAIL")
        for error in errors:
            print("- " + error)
        return 1
    print("AI marketing skill adoption validation: PASS")
    print("10 skills, 50 repo profiles, 70 scenarios, 0 forbidden imports")
    return 0


if __name__ == "__main__":
    sys.exit(main())
