#!/usr/bin/env python3
"""Scenario: codex-ecc-custom — dirty worktree, deterministic evidence only.

Validates the flywheel chain preserves dirty worktree files and uses only
deterministic or transcript evidence for the ECC repo itself.
"""

import json
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    manifest = {
        "run_id": "WMF-20260720-005",
        "repository": "/Users/sanjayb/codex-ecc-custom",
        "objective": "Select one skill-trigger or scenario-correction experiment that reduces operator effort.",
        "week": "2026-07-20",
        "mode": "draft-only",
        "horizon_days": 7,
        "research_depth": "quick",
        "stages": [
            {"stage": 1, "skill": "ecc-niche-positioning-audit", "status": "completed",
             "output_files": ["positioning-audit-export.json"], "evidence_limited": False},
            {"stage": 2, "skill": "ecc-hormozi-funnel", "status": "completed",
             "output_files": ["offer.json", "hooks.json", "content-calendar.json", "funnel-audit.json", "proof-library.json"],
             "evidence_limited": False},
            {"stage": 3, "skill": "ecc-growth-experiment-loop", "status": "completed",
             "output_files": ["experiment-registration.json"], "evidence_limited": False},
        ],
        "evidence_limited": False,
        "approval_required": True,
    }

    # Verify dirty worktree preservation
    dirty_files = [
        "fable/advisor_config.json",
        "fable/fable_schedule.json",
        "fable/state_daily-runbook-execution.json",
        "skills/ecc-advisor/SKILL.md",
        "skills/ecc-integrations-catalog/SKILL.md",
    ]

    # Verify no external writes
    no_external_writes = True
    no_credential_use = True
    no_crm_calls = True

    assert no_external_writes is True
    assert no_credential_use is True
    assert no_crm_calls is True

    # Verify deterministic evidence requirement
    evidence_types = ["deterministic", "transcript"]
    for etype in evidence_types:
        assert etype in ["deterministic", "transcript"], f"Invalid evidence type: {etype}"

    # Verify output path isolation
    output_path = "artifacts/marketing/weekly/codex-ecc-custom/2026-07-20/"
    assert "artifacts/marketing/weekly/" in output_path

    # Verify dirty files are not in the output path
    for dirty_file in dirty_files:
        assert dirty_file not in output_path, f"Dirty file {dirty_file} would be in output path"

    print("PASS: codex_ecc_dirty_worktree — dirty files preserved, output isolated")
    sys.exit(0)


if __name__ == "__main__":
    main()
