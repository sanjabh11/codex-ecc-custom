# CLI Flags Reference

## Basic Usage

```bash
# From inside the git repo
bash "$(git rev-parse --show-toplevel)/skills/ecc-eval/scripts/run_eval.sh" --help

# Or using EVAL_DIR env var
export EVAL_DIR=/path/to/skills/ecc-eval
bash "$EVAL_DIR/scripts/run_eval.sh" --help
```

## All Flags

| Flag | Type | Description |
|---|---|---|
| `--eval <file>` | path | Eval definition file (markdown with criteria) |
| `--batch <glob>` | string | Glob pattern for batch mode (e.g., "skills/*/SKILL.md") |
| `--prompt <text>` | string | Prompt for batch mode or custom eval prompt |
| `--output <file>` | path | Output file for last message (single mode) |
| `--output-dir <dir>` | path | Output directory for batch mode results |
| `--model <model>` | string | Pin a specific model (e.g., o3, gpt-4o) |
| `--sandbox <mode>` | enum | Sandbox mode: read-only (default), workspace-write, danger-full-access |
| `--backend <name>` | enum | Force backend: codex, claude, fallback |
| `--ephemeral` | flag | Use ephemeral session (no persisted state) [default: true] |
| `--no-ephemeral` | flag | Disable ephemeral mode (persist session) |
| `--ignore-config` | flag | Don't load user config (clean room) |
| `--ignore-rules` | flag | Don't load execpolicy rules (clean room) |
| `--workdir <dir>` | path | Working directory for the run (default: CWD) |
| `--skip-git-check` | flag | Allow running outside a git repo |
| `--json` | flag | Output structured JSON |
| `--extra-args <args>` | string | Pass extra arguments to the runner |
| `-h, --help` | flag | Show help message |

## Examples

### Single eval
```bash
bash skills/ecc-eval/scripts/run_eval.sh \
  --eval .claude/evals/feature-xyz.md \
  --output /tmp/eval-result.json
```

### Pinned model, clean room
```bash
bash skills/ecc-eval/scripts/run_eval.sh \
  --eval .claude/evals/feature-xyz.md \
  --model o3 \
  --ignore-config --ignore-rules \
  --output /tmp/eval-result.json
```

### Batch validation
```bash
bash skills/ecc-eval/scripts/run_eval.sh \
  --batch "skills/*/SKILL.md" \
  --prompt "Validate this skill for completeness and portability" \
  --output-dir /tmp/eval-results/
```

### Read-only sandbox, JSON output
```bash
bash skills/ecc-eval/scripts/run_eval.sh \
  --eval config.json \
  --prompt "Audit for security issues" \
  --sandbox read-only \
  --json \
  --output /tmp/audit.json
```

### Force backend
```bash
bash skills/ecc-eval/scripts/run_eval.sh \
  --eval feature.md \
  --backend claude \
  --output /tmp/result.json
```

### Workspace-write sandbox with workdir
```bash
bash skills/ecc-eval/scripts/run_eval.sh \
  --eval feature.md \
  --sandbox workspace-write \
  --workdir /tmp/eval-workspace \
  --output /tmp/result.json
```

## Backend Detection

The runner auto-detects in priority order:
1. `codex exec` — if `codex` is on PATH
2. `claude -p` — if `claude` is on PATH
3. `fallback` — no runner available, prints manual instructions

Override with `--backend <name>`.

## Security Features

- **Ephemeral sessions**: `--ephemeral` prevents session state from persisting
- **Sandbox isolation**: `--sandbox read-only` prevents writes and network access
- **Clean room mode**: `--ignore-config --ignore-rules` for uncontaminated baselines
- **Separate workdirs**: `--workdir` isolates each run's file access
- **No secrets in output**: Output files contain only agent responses, not config
