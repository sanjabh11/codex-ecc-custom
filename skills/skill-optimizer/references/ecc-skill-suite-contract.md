# ECC Skill Suite Contract

Use this contract when editing `skill-optimizer`, `coding-judgment`, `commercial-launch-readiness-orchestrator`, or ECC routing that activates them.

## Boundaries

- `skill-optimizer` owns reusable instruction, prompt, agent, and workflow improvement. It requires scenario evidence before promotion.
- `coding-judgment` owns coding discipline for repo edits: inspect first, choose the simplest viable change, keep diffs surgical, and verify before claims.
- `commercial-launch-readiness-orchestrator` owns one-repo commercial launch audits, market research, launch evidence, and safe P0/P1 fix lanes.

## Shared Gates

- Repo, file, runtime, or source truth comes before broad conclusions.
- Do not claim tool availability from package names or docs alone; verify current session or installed cache when it matters.
- Use proof buckets: hosted/live, local, repo artifact, candidate/shadow, and roadmap.
- Stop before production deploys, credential changes, payment changes, destructive actions, live outreach, or costly worker execution without approval.
- Validate global skills before mirroring to ECC source and installed cache.

## Regression Requirement

Before future edits to any of these three skills, run the relevant `skill-optimizer/fixtures/*.json` evidence file through:

```bash
python3 /Users/sanjayb/.codex/skills/skill-optimizer/scripts/validate_skill_evidence.py <fixture.json> \
  --require-results \
  --require-all-pass \
  --require-coverage-tags \
  --require-strictness supportive,neutral,competing
```

If the edit changes behavior, create a before/after pair and compare with `scripts/compare_skill_runs.py`. Hold the edit if a baseline scenario disappears or previously passing scenario regresses.
