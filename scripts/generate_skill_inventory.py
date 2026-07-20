#!/usr/bin/env python3
"""Generate the 91-skill inventory with weekly-task mapping and manual-waste analysis.

Outputs:
  - docs/skill-inventory.csv (machine-readable)
  - docs/skill-inventory.md (human-readable)
  - docs/manual-waste-audit.md (gap analysis)
"""

import csv
import json
import os
import re
import sys

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

WEEKLY_TASKS = {
    "positioning": "Run positioning audit for a repo segment",
    "offer_creation": "Create or refine an evidence-backed offer",
    "hook_generation": "Write and rank hooks for content",
    "content_calendar": "Plan 7-day content calendar",
    "funnel_audit": "Audit funnel for friction points",
    "experiment_design": "Design and register a growth experiment",
    "lead_research": "Research target accounts and build dossiers",
    "outbound_drafting": "Draft outreach messages (email, LinkedIn, X)",
    "buyer_pipeline": "Track buyer pipeline stages",
    "content_quality": "Review content for claims and quality",
    "pricing": "Prepare pricing briefs and value hypotheses",
    "revenue_attribution": "Trace revenue to marketing activities",
    "seo": "Prioritize SEO opportunities and technical fixes",
    "conversion_audit": "Audit landing pages for conversion friction",
    "analytics_readback": "Measure impact of marketing changes",
    "skill_maintenance": "Maintain and validate ECC skills",
    "code_review": "Review code changes for quality and security",
    "documentation": "Write or update documentation",
    "testing": "Write or run tests",
    "deployment": "Deploy or verify deployment readiness",
}

MARKETING_CATEGORIES = {
    "positioning": ["ecc-niche-positioning-audit"],
    "offer_creation": ["ecc-hormozi-funnel", "ecc-value-pricing"],
    "hook_generation": ["ecc-hormozi-funnel"],
    "content_calendar": ["ecc-hormozi-funnel", "content-engine", "marketing-campaign"],
    "funnel_audit": ["ecc-hormozi-funnel", "ecc-conversion-audit"],
    "experiment_design": ["ecc-growth-experiment-loop"],
    "lead_research": ["ecc-lead-dossier", "lead-intelligence"],
    "outbound_drafting": ["ecc-outbound-campaign", "ecc-buyer-pipeline"],
    "buyer_pipeline": ["ecc-buyer-pipeline"],
    "content_quality": ["ecc-content-quality-ops"],
    "pricing": ["ecc-value-pricing"],
    "revenue_attribution": ["ecc-revenue-attribution"],
    "seo": ["ecc-seo-opportunity-loop"],
    "conversion_audit": ["ecc-conversion-audit"],
    "analytics_readback": ["ecc-closed-loop-analytics"],
    "skill_maintenance": ["ecc-skill-create", "ecc-skill-health", "skill-creator", "skill-optimizer", "skill-health-monitor"],
    "code_review": ["ecc-code-review", "ecc-python-review", "ecc-rust-review", "ecc-go-review", "ecc-cpp-review", "ecc-kotlin-review"],
    "documentation": ["ecc-update-docs", "agents-md-generator", "documentation-lookup"],
    "testing": ["ecc-tdd", "ecc-test-coverage", "tdd", "tdd-workflow", "python-testing", "golang-testing", "rust-testing"],
    "deployment": ["ecc-verify", "deployment-patterns", "ecc-quality-gate"],
}


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
        result["description"] = desc[:200]
    return result


def classify_skill(name, description):
    """Classify a skill into weekly task categories."""
    categories = []
    text = (name + " " + description).lower()

    if any(k in text for k in ["positioning", "niche", "segment", "icp", "market gap"]):
        categories.append("positioning")
    if any(k in text for k in ["offer", "value equation", "pricing", "value hypothesis", "tiered"]):
        categories.append("offer_creation")
        categories.append("pricing")
    if any(k in text for k in ["hook", "content batching", "content calendar"]):
        categories.append("hook_generation")
        categories.append("content_calendar")
    if any(k in text for k in ["funnel", "conversion", "landing page", "cta"]):
        categories.append("funnel_audit")
        categories.append("conversion_audit")
    if any(k in text for k in ["experiment", "a/b", "hypothesis", "variant"]):
        categories.append("experiment_design")
    if any(k in text for k in ["lead", "dossier", "account", "buyer", "outreach", "outbound"]):
        categories.append("lead_research")
        categories.append("outbound_drafting")
        categories.append("buyer_pipeline")
    if any(k in text for k in ["content quality", "claim", "proof", "editorial"]):
        categories.append("content_quality")
    if any(k in text for k in ["revenue", "attribution", "pipeline"]):
        categories.append("revenue_attribution")
    if any(k in text for k in ["seo", "search", "keyword", "sitemap"]):
        categories.append("seo")
    if any(k in text for k in ["analytics", "closed-loop", "measurement", "metric"]):
        categories.append("analytics_readback")
    if any(k in text for k in ["skill", "validate", "validator", "scenario"]):
        categories.append("skill_maintenance")
    if any(k in text for k in ["code review", "review", "audit"]):
        categories.append("code_review")
    if any(k in text for k in ["doc", "documentation", "readme"]):
        categories.append("documentation")
    if any(k in text for k in ["test", "tdd", "coverage", "fuzz"]):
        categories.append("testing")
    if any(k in text for k in ["deploy", "ship", "release", "ci/cd"]):
        categories.append("deployment")

    return list(set(categories))


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)

    skills = []
    for entry in sorted(os.listdir(SKILLS_DIR)):
        skill_path = os.path.join(SKILLS_DIR, entry, "SKILL.md")
        if not os.path.isfile(skill_path):
            continue
        with open(skill_path, "r") as f:
            content = f.read()
        fm = extract_frontmatter(content)
        name = fm.get("name", entry)
        desc = fm.get("description", "")
        categories = classify_skill(name, desc)
        has_quick_validate = os.path.exists(os.path.join(SKILLS_DIR, entry, "agents", "openai.yaml"))
        has_allow_implicit = "allow_implicit_invocation" in content
        skills.append({
            "dir": entry,
            "name": name,
            "description": desc,
            "categories": categories,
            "has_openai_yaml": has_quick_validate,
            "had_allow_implicit": has_allow_implicit,
        })

    # Write CSV
    csv_path = os.path.join(DOCS_DIR, "skill-inventory.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["skill_dir", "name", "categories", "has_openai_yaml", "had_allow_implicit", "description"])
        for s in skills:
            writer.writerow([s["dir"], s["name"], "; ".join(s["categories"]), s["has_openai_yaml"], s["had_allow_implicit"], s["description"]])

    # Write Markdown
    md_path = os.path.join(DOCS_DIR, "skill-inventory.md")
    with open(md_path, "w") as f:
        f.write("# 91-Skill Inventory\n\n")
        f.write(f"Total skills: {len(skills)}\n\n")
        f.write("| # | Skill Dir | Name | Categories | openai.yaml | Had allow_implicit |\n")
        f.write("|---|---|---|---|---|---|\n")
        for i, s in enumerate(skills, 1):
            f.write(f"| {i} | {s['dir']} | {s['name']} | {', '.join(s['categories']) or '—'} | {'✓' if s['has_openai_yaml'] else '—'} | {'✓' if s['had_allow_implicit'] else '—'} |\n")

        # Category summary
        f.write("\n## Category Summary\n\n")
        cat_counts = {}
        for s in skills:
            for cat in s["categories"]:
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
        f.write("| Category | Skills covering it |\n|---|---|\n")
        for cat in sorted(cat_counts, key=lambda x: -cat_counts[x]):
            f.write(f"| {cat} | {cat_counts[cat]} |\n")

    # Write manual-waste audit
    audit_path = os.path.join(DOCS_DIR, "manual-waste-audit.md")
    with open(audit_path, "w") as f:
        f.write("# Manual-Waste Audit\n\n")
        f.write("## High-Leverage Marketing Tasks with Skill Coverage\n\n")
        f.write("These are weekly tasks where a skill already covers the work but may not be triggered.\n\n")
        f.write("| Task | Skill(s) | Manual waste if not triggered |\n|---|---|---|\n")
        for task, skill_names in sorted(MARKETING_CATEGORIES.items()):
            matching = [s for s in skills if s["name"] in skill_names or s["dir"] in skill_names]
            if matching:
                waste = "High" if len(matching) == 1 else "Medium"
                f.write(f"| {WEEKLY_TASKS.get(task, task)} | {', '.join(s['name'] for s in matching)} | {waste} |\n")

        f.write("\n## Gaps — High-Leverage Marketing Work with No Skill Coverage\n\n")
        covered_tasks = set()
        for s in skills:
            covered_tasks.update(s["categories"])
        gaps = [task for task in WEEKLY_TASKS if task not in covered_tasks]
        if gaps:
            f.write("| Gap task | Impact | Readiness |\n|---|---|---|\n")
            for gap in gaps:
                f.write(f"| {WEEKLY_TASKS.get(gap, gap)} | High | Needs new skill |\n")
        else:
            f.write("No gaps detected — all weekly tasks have at least one skill covering them.\n")

        f.write("\n## Top 3 Chained Skills for Immediate Impact\n\n")
        f.write("| Rank | Skill | Why |\n|---|---|---|\n")
        f.write("| 1 | ecc-niche-positioning-audit | Produces the evidence foundation all other marketing skills consume |\n")
        f.write("| 2 | ecc-hormozi-funnel | Converts positioning into distributable GTM assets (offers, hooks, content, proof) |\n")
        f.write("| 3 | ecc-growth-experiment-loop | Registers falsifiable experiments to test the assets produced by stage 2 |\n")
        f.write("\n**Chain:** positioning-audit → hormozi-funnel (weekly mode) → growth-experiment-loop\n\n")
        f.write("**Following week:** Pass `experiment-registration.json` to `ecc-closed-loop-analytics` for readback.\n")

    print(f"PASS: Generated inventory ({len(skills)} skills)")
    print(f"  CSV: {csv_path}")
    print(f"  MD:  {md_path}")
    print(f"  Audit: {audit_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
