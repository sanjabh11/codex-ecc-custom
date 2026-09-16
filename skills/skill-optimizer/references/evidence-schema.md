# Launch Evidence Schema For Skill Optimization

Use this JSON shape for scenario run evidence:

```json
{
  "schema_version": "skill-optimizer.v1",
  "skill_name": "example-skill",
  "target_kind": "skill",
  "target_path": "/absolute/path/to/SKILL.md",
  "run_id": "2026-06-04-example",
  "summary": {
    "score": 1.0,
    "passed": 3,
    "failed": 0,
    "not_run": 0,
    "total": 3
  },
  "scenarios": [
    {
      "id": "S001",
      "title": "Trigger on direct request",
      "prompt": "Improve this SKILL.md using evidence.",
      "strictness": "supportive",
      "grader": "deterministic|model|human",
      "coverage_tags": ["activation", "promotion-gate"],
      "expected": ["Runs quick_validate", "Reports promotion decision"],
      "result": "pass",
      "evidence": ["quick_validate output", "comparison report"],
      "artifact_paths": ["/absolute/path/to/report.md"]
    }
  ],
  "rejected_edits": [
    {
      "edit": "Add full external optimizer install by default",
      "reason": "Too heavy for v1 and not required by evidence"
    }
  ],
  "notes": "Optional reviewer notes."
}
```

Rules:

- `target_path` must be absolute and should exist unless the validator is run with `--allow-missing-target`.
- `target_kind` should be one of `skill`, `prompt`, `agent`, `workflow`, `commercial-launch`, or `coding-discipline`.
- Scenario IDs should be stable across before/after runs.
- `summary.score` should be between `0` and `1`.
- `summary.score`, `summary.passed`, `summary.failed`, `summary.not_run`, and `summary.total` must match the scenario results when present.
- Use `result: "not_run"` only when `not_run_reason` explicitly explains the missing evidence.
- `coverage_tags` should name the behavior under test, such as `activation`, `scope-control`, `proof-buckets`, or `diagnosis`.
- Promotion suites should cover `supportive`, `neutral`, and `competing` strictness at minimum.
- Evidence must name files, commands, transcripts, artifacts, or reviewer notes.
- Placeholder evidence is invalid. Replace scaffold text before comparing or promoting.

Useful strict validation command:

```bash
python3 scripts/validate_skill_evidence.py evidence.json \
  --require-results \
  --require-coverage-tags \
  --require-strictness supportive,neutral,competing
```
