# Regression Fixtures

These evidence files are the minimum local regression suite for the ECC skill set:

- `skill-optimizer-baseline.json`
- `coding-judgment-baseline.json`
- `commercial-launch-readiness-orchestrator-baseline.json`

Before future edits to any of these skills, validate the relevant fixture with:

```bash
python3 /Users/sanjayb/.codex/skills/skill-optimizer/scripts/validate_skill_evidence.py <fixture.json> \
  --require-results \
  --require-all-pass \
  --require-coverage-tags \
  --require-strictness supportive,neutral,competing
```

If behavior changes, create a before/after evidence pair and run `scripts/compare_skill_runs.py`.
