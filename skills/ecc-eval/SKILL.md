---
name: ecc-eval
description: >-
  Formal evaluation framework for AI-assisted development sessions using
  eval-driven development (EDD) principles. Wraps `codex exec` (and
  `claude -p` fallback) for non-interactive eval execution with ephemeral
  sessions, pinned models, sandbox isolation, and structured JSON output.
  Supports capability evals, regression evals, model-as-judge grading,
  pass@k metrics, batch validation, and CI integration.
  TRIGGER when: "eval harness", "eval-driven development", "EDD",
  "pass@k", "regression eval", "capability eval", "model grader",
  "batch validation", "CI eval", "prompt A/B testing", "codex exec eval",
  "skill quality gate", "eval report", "eval definition".
  DO NOT TRIGGER when: task is trivially one-line, or no non-interactive
  runner is available.
---

# ecc-eval

## When to Use

- Setting up eval-driven development (EDD) for AI-assisted workflows
- Defining pass/fail criteria for skill or code task completion
- Measuring agent reliability with pass@k metrics
- Creating regression test suites for prompt or agent changes
- Benchmarking agent performance across model versions
- Batch validation of multiple skills or repos in parallel
- CI gates for skill quality before merge
- Scheduled audits (security, config, dependency) without human intervention
- Prompt A/B testing with isolated ephemeral sessions
- Model-as-judge grading of weaker model outputs

## How It Works

You define evals (markdown files with criteria), then the runner executes them
non-interactively using `codex exec` or `claude -p` with clean, isolated state.

### Runner Backend Selection (auto-detected)

| Priority | Backend | Harness | How | Status |
|---|---|---|---|---|
| 1 | **codex exec** | Codex CLI | `codex exec --ephemeral --json -o <file> "<prompt>"` | **Fully implemented** |
| 2 | **claude -p** | Claude Code | `claude -p --output-format json "<prompt>"` | **Detected, fallback** |
| 3 | **Graceful fallback** | Any | Report that no runner is available | **Always available** |

The runner script at `scripts/run_eval.sh` auto-detects the best available backend.

### Backend 1: codex exec (preferred for Codex)

`codex exec` runs Codex non-interactively with powerful isolation flags:

```bash
# Ephemeral session, pinned model, read-only sandbox, JSON output
codex exec --ephemeral -m o3 -s read-only --json \
  -o /tmp/eval-result.json \
  "Validate all skills in this repo. Output JSON with pass/fail per skill."
```

Key flags:
- `--ephemeral` — no session files persisted to disk
- `-m <model>` — pin a specific model
- `-s read-only` — sandbox: no writes, no network
- `-s workspace-write` — sandbox: writes to workspace only
- `--json` — structured JSONL event output
- `-o <file>` — write last message to file
- `-C <dir>` — working directory (separate per run)
- `--ignore-user-config` — don't load user config (clean room)
- `--ignore-rules` — don't load execpolicy rules (clean room)
- `--skip-git-repo-check` — run outside git repos
- `--add-dir <dir>` — additional writable directories

### Backend 2: claude -p (fallback for Claude Code)

```bash
claude -p --output-format json "<prompt>" > /tmp/eval-result.json
```

### Backend 3: Graceful Fallback

If no non-interactive runner is available, the skill reports this and provides
manual eval templates for human execution.

## Eval Types

### Capability Evals
Test if the agent can do something it couldn't before:
```markdown
[CAPABILITY EVAL: feature-name]
Task: Description of what the agent should accomplish
Success Criteria:
  - [ ] Criterion 1
  - [ ] Criterion 2
  - [ ] Criterion 3
Expected Output: Description of expected result
```

### Regression Evals
Ensure changes don't break existing functionality:
```markdown
[REGRESSION EVAL: feature-name]
Baseline: SHA or checkpoint name
Tests:
  - existing-test-1: PASS/FAIL
  - existing-test-2: PASS/FAIL
Result: X/Y passed (previously Y/Y)
```

### Model-Grader Evals
Use a strong model to evaluate open-ended outputs:
```markdown
[MODEL GRADER PROMPT]
Evaluate the following output:
1. Does it solve the stated problem?
2. Is it well-structured?
3. Are edge cases handled?

Score: 1-5 (1=poor, 5=excellent)
Reasoning: [explanation]
```

## Metrics

### pass@k
"At least one success in k attempts"
- pass@1: First attempt success rate
- pass@3: Success within 3 attempts
- Typical target: pass@3 > 90%

### pass^k
"All k trials succeed"
- pass^3: 3 consecutive successes
- Use for critical paths

## Eval Workflow

### 1. Define (Before Coding)
```markdown
## EVAL DEFINITION: feature-xyz

### Capability Evals
1. Can create new user account
2. Can validate email format
3. Can hash password securely

### Regression Evals
1. Existing login still works
2. Session management unchanged

### Success Metrics
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
```

### 2. Implement
Write code to pass the defined evals.

### 3. Evaluate
```bash
# Run a single eval
bash skills/ecc-eval/scripts/run_eval.sh \
  --eval .claude/evals/feature-xyz.md \
  --output /tmp/eval-result.json

# Run with pinned model
bash skills/ecc-eval/scripts/run_eval.sh \
  --eval .claude/evals/feature-xyz.md \
  --model o3 \
  --output /tmp/eval-result.json

# Batch run across all skills
bash skills/ecc-eval/scripts/run_eval.sh \
  --batch "skills/*/SKILL.md" \
  --prompt "Validate this skill for completeness and portability" \
  --output-dir /tmp/eval-results/
```

### 4. Report
```markdown
EVAL REPORT: feature-xyz
========================

Capability Evals:
  create-user:     PASS (pass@1)
  validate-email:  PASS (pass@2)
  Overall:         2/3 passed

Regression Evals:
  login-flow:      PASS
  session-mgmt:    PASS
  Overall:         2/2 passed

Metrics:
  pass@1: 67% (2/3)
  pass@3: 100% (3/3)

Status: READY FOR REVIEW
```

## Top 10 Use Cases

1. **Prompt A/B testing** — same prompt, different models, diff outputs
2. **Regression evals for skill changes** — catch stale assertions before merge
3. **CI gate for skill quality** — `codex exec --ephemeral --json` for structured pass/fail
4. **Batch skill validation** — parallel runs with separate `--cd` directories
5. **Clean-room advisor evals** — `--ephemeral --ignore-user-config --ignore-rules`
6. **Model-as-judge grading** — strong model grades weaker model outputs
7. **Scheduled security/MCP audits** — cron-triggered runs
8. **Prompt regression testing** — version prompts, pin model, compare to baseline
9. **EDD for new skills** — define evals before coding, check during development
10. **Batch file processing** — isolated `--cd` per file, no cross-contamination

## CI Integration

### GitHub Actions Example
```yaml
- name: Run skill validation evals
  run: |
    for skill in skills/*/; do
      bash skills/ecc-eval/scripts/run_eval.sh \
        --eval "${skill}SKILL.md" \
        --prompt "Validate this skill: check frontmatter, sections, triggers, platform mentions" \
        --output "/tmp/eval-$(basename $skill).json" \
        --sandbox read-only &
    done
    wait
    # Check all results
    for f in /tmp/eval-*.json; do
      python3 -c "import json,sys; r=json.load(open('$f')); sys.exit(0 if r.get('status')=='pass' else 1)"
    done
```

### Cron Example
```bash
# Weekly MCP config audit (Mondays 9am)
0 9 * * 1 bash skills/ecc-eval/scripts/run_eval.sh \
  --eval ~/.codeium/windsurf/mcp_config.json \
  --prompt "Audit MCP servers for disabled status and security issues" \
  --output /tmp/mcp-audit-$(date +\%Y\%m\%d).json \
  --sandbox read-only
```

## Dependency Gating

### codex exec (preferred)
- Requires Codex CLI installed (`command -v codex`)
- No API key needed — uses Codex subscription
- Python 3.11+ for script runner

### claude -p (fallback)
- Requires Claude Code CLI installed (`command -v claude`)
- No separate API key — uses Claude subscription

### Fallback
- If no runner is available, use manual eval templates from `references/`
- Templates are tool-agnostic markdown files

## Auto-Revocation (ECC)

Eval runners follow the ECC tool taxonomy with mixed gating:

| Class | Tools | Gating Behavior |
|-------|-------|----------------|
| **Core** (never gate) | `bash`, `git`, `cat`, `echo`, `mkdir` | Always available — no check needed |
| **Workflow** (gate + fail loud) | `codex`, `claude` | `command -v <tool>` check. If missing AND task depends on it: report limitation, do NOT silently succeed. Exit 1. |
| **Advisory** (gate + silent skip) | `jsonschema` (Python), `python3` (for validator) | `command -v <tool>` or import check. If absent: skip validation silently, degrade to manual templates. Never block. |

### Pattern for Workflow tools (codex, claude):
1. `command -v codex >/dev/null 2>&1` — if absent, try next backend
2. `command -v claude >/dev/null 2>&1` — if absent, try next backend
3. If both absent: print manual eval template to stderr, exit 1
4. Do NOT silently succeed — the eval task depends on a runner

### Pattern for Advisory tools (jsonschema, python3):
1. `python3 -c "import jsonschema"` — if absent, skip schema validation in validator
2. Wrap with `2>/dev/null` and `|| true`
3. Never block on advisory tooling — degrade to manual templates

## Backend Auto-Detection

The runner script auto-detects the best available backend:
1. `codex exec` — if `codex` is on PATH
2. `claude -p` — if `claude` is on PATH
3. `fallback` — no runner available, print manual instructions

Override with `--backend <name>` flag.

## Platform Compatibility

Works across all harnesses with automatic backend selection:

- **Codex** → `codex exec` (ephemeral, pinned model, sandbox) — preferred
- **Claude Code** → `claude -p` (print mode, JSON output) — fallback
- **Windsurf / Devin** → `codex exec` if Codex CLI installed, else manual templates
- **Autogravity** → `codex exec` if Codex CLI installed, else manual templates

## Path Resolution

The runner script resolves its own location automatically:
```bash
# From repo root
bash skills/ecc-eval/scripts/run_eval.sh --help

# From any CWD (uses script-relative path)
bash /path/to/repo/skills/ecc-eval/scripts/run_eval.sh --help

# With EVAL_DIR env var
export EVAL_DIR=/path/to/skills/ecc-eval
bash $EVAL_DIR/scripts/run_eval.sh --help
```

## Portability Note

The eval methodology (templates, metrics, grader types) is tool-agnostic.
Only the runner needs platform-specific implementation. When using this skill
in a different repository, either:
1. Copy the `scripts/run_eval.sh` to the target repo, or
2. Set `EVAL_DIR` environment variable to the absolute path of this skill directory, or
3. Use the manual eval templates from `references/` (no script dependency)

## Backing Skills

- `eval-harness` — full EDD methodology, grader types, pass@k metrics
- `verification-loop` — comprehensive verification system for sessions

## References

- [Eval Templates](references/eval-templates.md) — capability, regression, model-grader templates
- [CI Examples](references/ci-examples.md) — GitHub Actions, cron, batch scripts
- [CLI Flags](references/cli-flags.md) — all run_eval.sh flags and examples

## Upstream Source

- Command file: `eval.md`
- Original description: Codex adaptation of ECC /eval
