#!/usr/bin/env python3
"""Deterministic weekly marketing flywheel runner.

This runner NEVER invokes a model or external service. It:
- Validates agent-produced Stage 1 inputs (positioning export)
- Runs deterministic Stage 2 generation (weekly artifacts)
- Validates agent-produced Stage 3 inputs (experiment registration)
- Writes run-manifest, evidence-ledger, unavailable, approval-required, hashes

Usage:
  python3 run_weekly_marketing_flywheel.py \
    --repository /path/to/repo \
    --objective "one business question" \
    --week 2026-07-20 \
    --mode dry-run|draft-only \
    [--positioning-export path] \
    [--experiment-registration path]
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SKILL_DIR))
HORMOZI_GENERATOR = os.path.join(
    PROJECT_ROOT, "skills", "ecc-hormozi-funnel", "scripts", "generate_weekly_artifacts.py"
)

CONTRACT_VERSION = "v1"


def compute_sha256(filepath):
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_tree_hash(directory):
    """Compute a normalized tree hash for a directory."""
    h = hashlib.sha256()
    for root, dirs, files in os.walk(directory):
        dirs.sort()
        files.sort()
        for f in files:
            filepath = os.path.join(root, f)
            rel = os.path.relpath(filepath, directory)
            h.update(rel.encode())
            h.update(compute_sha256(filepath).encode())
    return h.hexdigest()


def slugify(path):
    """Convert a repository path to a slug for directory naming."""
    return os.path.basename(path.rstrip("/")).replace(" ", "-").lower()


def stage1_validate(positioning_export_path):
    """Validate Stage 1 input — positioning audit export."""
    if not positioning_export_path or not os.path.exists(positioning_export_path):
        return {
            "status": "unavailable",
            "reason": "No positioning export provided or file not found",
            "mitigation": "Run ecc-niche-positioning-audit first, or provide --positioning-export path",
        }
    try:
        with open(positioning_export_path) as f:
            data = json.load(f)
        if "evidence_corpus" not in data and "evidence" not in data:
            return {
                "status": "invalid",
                "reason": "Positioning export has no evidence_corpus or evidence field",
                "mitigation": "Re-run positioning audit with evidence extraction",
            }
        if not data.get("segments"):
            return {
                "status": "invalid",
                "reason": "Positioning export has no segments",
                "mitigation": "Re-run positioning audit with segment identification",
            }
        return {"status": "valid", "data": data}
    except json.JSONDecodeError:
        return {
            "status": "invalid",
            "reason": "Positioning export is not valid JSON",
            "mitigation": "Re-export positioning audit as JSON",
        }


def stage2_generate(positioning_export_path, output_dir, week_date):
    """Run deterministic Stage 2 generation."""
    import subprocess

    result = subprocess.run(
        [sys.executable, HORMOZI_GENERATOR, positioning_export_path, output_dir, week_date],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def stage3_validate(experiment_registration_path):
    """Validate Stage 3 input — experiment registration."""
    if not experiment_registration_path or not os.path.exists(experiment_registration_path):
        return {
            "status": "unavailable",
            "reason": "No experiment registration provided",
            "mitigation": "Run ecc-growth-experiment-loop to register an experiment",
        }
    try:
        with open(experiment_registration_path) as f:
            data = json.load(f)
        required = ["experiment_id", "hypothesis", "metric"]
        missing = [k for k in required if k not in data]
        if missing:
            return {
                "status": "invalid",
                "reason": f"Experiment registration missing fields: {missing}",
                "mitigation": "Re-run experiment registration with all required fields",
            }
        return {"status": "valid", "data": data}
    except json.JSONDecodeError:
        return {
            "status": "invalid",
            "reason": "Experiment registration is not valid JSON",
            "mitigation": "Re-export experiment registration as JSON",
        }


def run(args):
    """Execute the weekly marketing flywheel."""
    repo_slug = slugify(args.repository)
    output_base = os.path.join(
        args.repository, "artifacts", "marketing", "weekly", repo_slug, args.week
    )

    # In dry-run mode, use a temp directory
    if args.mode == "dry-run":
        import tempfile
        tmp = tempfile.mkdtemp(prefix="flywheel-dry-run-")
        output_dir = tmp
        print(f"[DRY RUN] Output directory: {output_dir}")
    else:
        output_dir = output_base
        os.makedirs(output_dir, exist_ok=True)

    now = datetime.now(timezone.utc)
    run_id = f"WMF-{args.week.replace('-', '')}-001"

    manifest = {
        "schema_version": "v1",
        "run_id": run_id,
        "repository": args.repository,
        "objective": args.objective,
        "week": args.week,
        "mode": args.mode,
        "horizon_days": 7,
        "research_depth": args.research_depth,
        "stages": [],
        "evidence_limited": False,
        "approval_required": True,
        "created_at": now.isoformat(),
    }

    unavailable_items = []

    # Stage 1: Validate positioning export
    stage1 = stage1_validate(args.positioning_export)
    manifest["stages"].append({
        "stage": 1,
        "skill": "ecc-niche-positioning-audit",
        "status": "completed" if stage1["status"] == "valid" else stage1["status"],
        "output_files": [args.positioning_export] if args.positioning_export and os.path.exists(args.positioning_export) else [],
        "evidence_limited": stage1["status"] != "valid",
    })

    if stage1["status"] != "valid":
        unavailable_items.append({
            "stage": "stage1_positioning",
            "reason": stage1["reason"],
            "mitigation": stage1.get("mitigation", ""),
        })
        # Stop — can't proceed without positioning export
        manifest["status"] = "stopped"
        manifest["stop_reason"] = f"Stage 1 unavailable: {stage1['reason']}"
        manifest["evidence_limited"] = True

        # Write manifest and unavailable
        with open(os.path.join(output_dir, "run-manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)
        with open(os.path.join(output_dir, "unavailable.json"), "w") as f:
            json.dump({"items": unavailable_items}, f, indent=2)
        with open(os.path.join(output_dir, "approval-required.md"), "w") as f:
            f.write("# Approval Required\n\nStage 1 (positioning audit) is unavailable.\n")
        print(f"STOPPED: Stage 1 unavailable — {stage1['reason']}")
        print(f"Output: {output_dir}")
        return

    # Stage 2: Generate weekly artifacts
    stage2 = stage2_generate(args.positioning_export, output_dir, args.week)
    manifest["stages"].append({
        "stage": 2,
        "skill": "ecc-hormozi-funnel",
        "status": "completed" if stage2["exit_code"] == 0 else "failed",
        "output_files": ["offer.json", "hooks.json", "content-calendar.json", "funnel-audit.json", "proof-library.json", "evidence-ledger.json"],
        "evidence_limited": False,
    })

    if stage2["exit_code"] != 0:
        manifest["status"] = "stopped"
        manifest["stop_reason"] = f"Stage 2 generation failed: {stage2['stderr']}"
        with open(os.path.join(output_dir, "run-manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"STOPPED: Stage 2 failed — {stage2['stderr']}")
        print(f"Output: {output_dir}")
        return

    # Stage 3: Validate experiment registration
    stage3 = stage3_validate(args.experiment_registration)
    manifest["stages"].append({
        "stage": 3,
        "skill": "ecc-growth-experiment-loop",
        "status": "completed" if stage3["status"] == "valid" else stage3["status"],
        "output_files": ["experiment-registration.json"] if stage3["status"] == "valid" else [],
        "evidence_limited": stage3["status"] != "valid",
    })

    if stage3["status"] != "valid":
        unavailable_items.append({
            "stage": "stage3_experiment",
            "reason": stage3["reason"],
            "mitigation": stage3.get("mitigation", ""),
        })

    # Copy experiment registration if provided
    if stage3["status"] == "valid":
        with open(os.path.join(output_dir, "experiment-registration.json"), "w") as f:
            json.dump(stage3["data"], f, indent=2)

    # Compute hashes for all output files
    hashes = {}
    for f in os.listdir(output_dir):
        filepath = os.path.join(output_dir, f)
        if os.path.isfile(filepath):
            hashes[f] = compute_sha256(filepath)
    manifest["output_hashes"] = hashes

    # Tree hash
    manifest["tree_hash"] = compute_tree_hash(output_dir)

    manifest["status"] = "complete" if not unavailable_items else "complete_with_unavailable"
    manifest["evidence_limited"] = len(unavailable_items) > 0

    # Write run manifest
    with open(os.path.join(output_dir, "run-manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    # Write unavailable.json if any items
    if unavailable_items:
        with open(os.path.join(output_dir, "unavailable.json"), "w") as f:
            json.dump({"items": unavailable_items}, f, indent=2)

    # Write approval-required.md
    approval_lines = ["# Approval Required\n"]
    if unavailable_items:
        approval_lines.append("## Unavailable Items\n")
        for item in unavailable_items:
            approval_lines.append(f"- **{item['stage']}**: {item['reason']}")
            approval_lines.append(f"  - Mitigation: {item['mitigation']}")
        approval_lines.append("\n## Human Approval Boundary\n")
        approval_lines.append("The following require human approval before proceeding:")
        approval_lines.append("- Any external writes (emails, posts, CRM updates)")
        approval_lines.append("- Any claim publication without evidence verification")
        approval_lines.append("- Any experiment launch without metric/guardrail confirmation")
    else:
        approval_lines.append("\nAll stages completed. Human approval required before:")
        approval_lines.append("- External writes or sends")
        approval_lines.append("- Claim publication")
        approval_lines.append("- Experiment launch")
    with open(os.path.join(output_dir, "approval-required.md"), "w") as f:
        f.write("\n".join(approval_lines) + "\n")

    # Write hashes.json
    with open(os.path.join(output_dir, "hashes.json"), "w") as f:
        json.dump({"files": hashes, "tree": manifest["tree_hash"]}, f, indent=2)

    print(f"{'COMPLETE' if not unavailable_items else 'COMPLETE_WITH_UNAVAILABLE'}: {manifest['status']}")
    print(f"Output: {output_dir}")
    print(f"Artifacts: {list(hashes.keys())}")
    if unavailable_items:
        print(f"Unavailable: {[u['stage'] for u in unavailable_items]}")


def main():
    parser = argparse.ArgumentParser(
        description="Deterministic weekly marketing flywheel runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repository", required=True, help="Target repository absolute path")
    parser.add_argument("--objective", required=True, help="One business question for the week")
    parser.add_argument("--week", required=True, help="Week start date YYYY-MM-DD")
    parser.add_argument("--mode", required=True, choices=["dry-run", "draft-only"],
                        help="dry-run: temp dir, no writes to repo. draft-only: writes to repo artifacts/")
    parser.add_argument("--positioning-export", help="Path to positioning-audit-export.json")
    parser.add_argument("--experiment-registration", help="Path to experiment-registration.json")
    parser.add_argument("--research-depth", default="quick", choices=["quick", "standard"],
                        help="Research depth hint for the agent (default: quick)")
    args = parser.parse_args()

    if not os.path.isabs(args.repository):
        print("ERROR: --repository must be an absolute path", file=sys.stderr)
        sys.exit(1)

    run(args)


if __name__ == "__main__":
    main()
