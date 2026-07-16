# Evaluation and Release Harness

## Required checks

Run from the repository root:

```text
python3 skills/ecc-niche-positioning-audit/scripts/validate_skill.py
python3 -m py_compile skills/ecc-niche-positioning-audit/scripts/*.py skills/ecc-niche-positioning-audit/tests/scenarios/*.py
for f in skills/ecc-niche-positioning-audit/tests/scenarios/*.py; do python3 "$f"; done
python3 skills/.system/skill-creator/scripts/quick_validate.py skills/ecc-niche-positioning-audit
```

Validate all five schemas with a Draft 2020-12 meta-validator and run `git diff
--check`. A release is not green if any command is skipped, the validator lacks
`jsonschema`, or a scenario only asserts its input instead of validator output.

## Behavioral coverage

The scenarios cover evidence-rich support, neutral mixed signals, codebase-heavy
evidence-limited mode, schema drift, stale/adversarial evidence, artifact
reproducibility, state migration, scope-DAG order, and semantic contracts.
Maintain both positive and negative cases for schema, gate caps, lifecycle,
confidence arithmetic, evidence bundles, stale evidence, and identity matching.

## Artifact commands

```text
python3 scripts/generate_artifact.py --state state.json --generate --output artifact.json
python3 scripts/generate_artifact.py --state state.json --artifact artifact.json --check
python3 scripts/generate_artifact.py --state state.json --artifact artifact.json --supersede
```

Hashes use canonical parsed JSON, not formatting or key order. Writes are atomic;
supersede preserves the old file as `superseded: true` and writes a distinct
replacement. Projections in `~/.claude/skills`, `~/.codex/skills`, and
`~/.antigravity/skills` must have identical non-cache manifests and hashes.
