# CI Examples

## GitHub Actions: Batch Skill Validation

```yaml
name: Skill Validation Evals
on:
  pull_request:
    paths:
      - 'skills/**'
  schedule:
    - cron: '0 9 * * 1'  # Weekly Mondays

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Codex CLI
        run: npm install -g @anthropic-ai/codex
      - name: Run skill validation evals
        run: |
          for skill in skills/*/; do
            bash skills/ecc-eval/scripts/run_eval.sh \
              --eval "${skill}SKILL.md" \
              --prompt "Validate this skill: check frontmatter, sections, triggers, platform mentions, no hardcoded paths" \
              --output "/tmp/eval-$(basename $skill).json" \
              --sandbox read-only \
              --json &
          done
          wait
          # Aggregate results
          python3 -c "
          import json, glob, sys
          results = []
          for f in glob.glob('/tmp/eval-*.json'):
              try:
                  r = json.load(open(f))
                  results.append({'file': f, 'status': r.get('status', 'unknown')})
              except: pass
          passed = sum(1 for r in results if r['status'] == 'pass')
          print(f'Eval results: {passed}/{len(results)} passed')
          if passed < len(results):
              sys.exit(1)
          "
```

## Cron: Weekly MCP Config Audit

```bash
# /etc/cron.d/ecc-mcp-audit
# Weekly MCP config audit (Mondays 9am)
0 9 * * 1 sanjayb bash "$(git rev-parse --show-toplevel)/skills/ecc-eval/scripts/run_eval.sh" \
  --eval ~/.codeium/windsurf/mcp_config.json \
  --prompt "Audit all MCP servers for: disabled status, missing fields, security issues. Output JSON." \
  --output /tmp/mcp-audit-$(date +\%Y\%m\%d).json \
  --sandbox read-only \
  --json
```

## Batch: Parallel Skill Validation

```bash
#!/usr/bin/env bash
# validate-all-skills.sh — Run evals across all skills in parallel
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
OUTPUT_DIR="/tmp/eval-results-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "Starting batch validation..."
bash "$REPO_ROOT/skills/ecc-eval/scripts/run_eval.sh" \
  --batch "skills/*/SKILL.md" \
  --prompt "Validate this skill for: frontmatter completeness, required sections, platform mentions, no hardcoded paths, no anti-patterns. Output JSON with pass/fail per check." \
  --output-dir "$OUTPUT_DIR" \
  --sandbox read-only \
  --json

echo "Results in $OUTPUT_DIR/"
ls -la "$OUTPUT_DIR/"
```

## Pre-Commit Hook: Skill Quality Gate

```bash
#!/usr/bin/env bash
# .githooks/pre-commit — Run eval on changed skills
CHANGED_SKILLS=$(git diff --cached --name-only --diff-filter=ACM | grep '^skills/.*/SKILL.md' || true)
if [[ -z "$CHANGED_SKILLS" ]]; then
    exit 0
fi

for skill_md in $CHANGED_SKILLS; do
    skill_dir="$(dirname "$skill_md")"
    echo "Running eval for: $skill_dir"
    bash skills/ecc-eval/scripts/run_eval.sh \
      --eval "$skill_md" \
      --prompt "Validate this skill. Check: frontmatter, required sections, triggers, platform mentions, no hardcoded paths. Output PASS or FAIL." \
      --output /tmp/pre-commit-eval.json \
      --sandbox read-only || {
        echo "Eval failed for $skill_md — see /tmp/pre-commit-eval.json"
        exit 1
      }
done
```
