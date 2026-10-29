#!/usr/bin/env bash
# run_eval.sh — Multi-backend eval runner for ecc-eval
#
# Auto-detects and uses the best available non-interactive AI runner:
#   1. codex exec (preferred — ephemeral, pinned model, sandbox, JSON)
#   2. claude -p  (fallback — print mode, JSON output)
#   3. fallback   (no runner — prints manual instructions)
#
# Usage:
#   bash run_eval.sh --eval <file> --output <file> [options]
#   bash run_eval.sh --batch "<glob>" --prompt "<text>" --output-dir <dir> [options]
#   bash run_eval.sh --help
set -euo pipefail

# ─── Path Resolution ─────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVAL_DIR="${EVAL_DIR:-$(dirname "$SCRIPT_DIR")}"

# ─── Defaults ───────────────────────────────────────────────────────────────
BACKEND=""
MODEL=""
SANDBOX="read-only"
OUTPUT=""
OUTPUT_DIR=""
EVAL_FILE=""
BATCH_GLOB=""
PROMPT=""
EPHEMERAL=true
IGNORE_CONFIG=false
IGNORE_RULES=false
WORKDIR=""
SKIP_GIT_CHECK=false
JSON_OUTPUT=false
EXTRA_ARGS=""

# ─── Help ────────────────────────────────────────────────────────────────────
usage() {
    cat << 'EOF'
run_eval.sh — Multi-backend eval runner for ecc-eval

Usage:
  bash run_eval.sh --eval <file> --output <file> [options]
  bash run_eval.sh --batch "<glob>" --prompt "<text>" --output-dir <dir> [options]

Options:
  --eval <file>          Eval definition file (markdown with criteria)
  --batch <glob>          Glob pattern for batch mode (e.g., "skills/*/SKILL.md")
  --prompt <text>         Prompt for batch mode or custom eval prompt
  --output <file>         Output file for last message (single mode)
  --output-dir <dir>       Output directory for batch mode results
  --model <model>         Pin a specific model (e.g., o3, gpt-4o)
  --sandbox <mode>        Sandbox mode: read-only (default), workspace-write, danger-full-access
  --backend <name>        Force backend: codex, claude, fallback
  --ephemeral             Use ephemeral session (no persisted state) [default: true]
  --no-ephemeral          Disable ephemeral mode (persist session)
  --ignore-config         Don't load user config (clean room)
  --ignore-rules          Don't load execpolicy rules (clean room)
  --workdir <dir>         Working directory for the run (default: CWD)
  --skip-git-check        Allow running outside a git repo
  --json                  Output structured JSON
  --extra-args <args>     Pass extra arguments to the runner
  -h, --help              Show this help message

Backend Detection (auto):
  1. codex exec  — if `codex` is on PATH
  2. claude -p   — if `claude` is on PATH
  3. fallback    — manual instructions

Examples:
  # Single eval
  bash run_eval.sh --eval .claude/evals/feature.md --output /tmp/result.json

  # Pinned model, clean room
  bash run_eval.sh --eval .claude/evals/feature.md --model o3 --ignore-config --output /tmp/result.json

  # Batch validation
  bash run_eval.sh --batch "skills/*/SKILL.md" --prompt "Validate this skill" --output-dir /tmp/evals/

  # Read-only sandbox, JSON output
  bash run_eval.sh --eval config.json --prompt "Audit for security" --sandbox read-only --json --output /tmp/audit.json
EOF
    exit 0
}

# ─── Arg Parsing ─────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --eval)         EVAL_FILE="$2"; shift 2 ;;
        --batch)       BATCH_GLOB="$2"; shift 2 ;;
        --prompt)      PROMPT="$2"; shift 2 ;;
        --output)      OUTPUT="$2"; shift 2 ;;
        --output-dir)  OUTPUT_DIR="$2"; shift 2 ;;
        --model)       MODEL="$2"; shift 2 ;;
        --sandbox)     SANDBOX="$2"; shift 2 ;;
        --backend)     BACKEND="$2"; shift 2 ;;
        --ephemeral)   EPHEMERAL=true; shift ;;
        --no-ephemeral) EPHEMERAL=false; shift ;;
        --ignore-config) IGNORE_CONFIG=true; shift ;;
        --ignore-rules)  IGNORE_RULES=true; shift ;;
        --workdir)     WORKDIR="$2"; shift 2 ;;
        --skip-git-check|--skip-git-repo-check) SKIP_GIT_CHECK=true; shift ;;
        --json)        JSON_OUTPUT=true; shift ;;
        --extra-args)  EXTRA_ARGS="$2"; shift 2 ;;
        -h|--help)     usage ;;
        *)             echo "Unknown option: $1" >&2; usage ;;
    esac
done

# ─── Backend Detection ──────────────────────────────────────────────────────
detect_backend() {
    if [[ -n "$BACKEND" ]]; then
        echo "$BACKEND"
        return
    fi
    if command -v codex &>/dev/null; then
        echo "codex"
    elif command -v claude &>/dev/null; then
        echo "claude"
    else
        echo "fallback"
    fi
}

# ─── Build Command ───────────────────────────────────────────────────────────
build_codex_cmd() {
    local cmd=(codex exec)
    [[ "$EPHEMERAL" == "true" ]] && cmd+=(--ephemeral)
    [[ -n "$MODEL" ]] && cmd+=(-m "$MODEL")
    [[ -n "$SANDBOX" ]] && cmd+=(-s "$SANDBOX")
    [[ "$JSON_OUTPUT" == "true" ]] && cmd+=(--json)
    [[ -n "$OUTPUT" ]] && cmd+=(-o "$OUTPUT")
    [[ -n "$WORKDIR" ]] && cmd+=(-C "$WORKDIR")
    [[ "$IGNORE_CONFIG" == "true" ]] && cmd+=(--ignore-user-config)
    [[ "$IGNORE_RULES" == "true" ]] && cmd+=(--ignore-rules)
    [[ "$SKIP_GIT_CHECK" == "true" ]] && cmd+=(--skip-git-repo-check)
    [[ -n "$EXTRA_ARGS" ]] && cmd+=($EXTRA_ARGS)
    echo "${cmd[@]}"
}

build_claude_cmd() {
    local cmd=(claude -p)
    [[ "$JSON_OUTPUT" == "true" ]] && cmd+=(--output-format json)
    [[ -n "$MODEL" ]] && cmd+=(--model "$MODEL")
    echo "${cmd[@]}"
}

# ─── Build Prompt ────────────────────────────────────────────────────────────
build_prompt() {
    local prompt_text=""

    if [[ -n "$PROMPT" ]]; then
        prompt_text="$PROMPT"
    fi

    if [[ -n "$EVAL_FILE" && -f "$EVAL_FILE" ]]; then
        local eval_content
        eval_content="$(cat "$EVAL_FILE")"
        if [[ -n "$prompt_text" ]]; then
            prompt_text="${prompt_text}

Eval Definition:
---
${eval_content}
---
Execute the eval above and report PASS/FAIL for each criterion."
        else
            prompt_text="Execute the following eval definition and report PASS/FAIL for each criterion.

${eval_content}"
        fi
    fi

    if [[ -z "$prompt_text" ]]; then
        echo "Error: No prompt or eval file provided" >&2
        exit 1
    fi

    echo "$prompt_text"
}

# ─── Single Run ──────────────────────────────────────────────────────────────
run_single() {
    local backend
    backend="$(detect_backend)"
    local prompt_text
    prompt_text="$(build_prompt)"

    echo "[eval] Backend: $backend" >&2

    case "$backend" in
        codex)
            local -a cmd_arr
            cmd_arr=(codex exec)
            [[ "$EPHEMERAL" == "true" ]] && cmd_arr+=(--ephemeral)
            [[ -n "$MODEL" ]] && cmd_arr+=(-m "$MODEL")
            [[ -n "$SANDBOX" ]] && cmd_arr+=(-s "$SANDBOX")
            [[ "$JSON_OUTPUT" == "true" ]] && cmd_arr+=(--json)
            [[ -n "$OUTPUT" ]] && cmd_arr+=(-o "$OUTPUT")
            [[ -n "$WORKDIR" ]] && cmd_arr+=(-C "$WORKDIR")
            [[ "$IGNORE_CONFIG" == "true" ]] && cmd_arr+=(--ignore-user-config)
            [[ "$IGNORE_RULES" == "true" ]] && cmd_arr+=(--ignore-rules)
            [[ "$SKIP_GIT_CHECK" == "true" ]] && cmd_arr+=(--skip-git-repo-check)
            [[ -n "$EXTRA_ARGS" ]] && cmd_arr+=($EXTRA_ARGS)
            echo "[eval] Running: ${cmd_arr[*]} \"<prompt>\"" >&2
            "${cmd_arr[@]}" "$prompt_text"
            ;;
        claude)
            local -a cmd_arr
            cmd_arr=(claude -p)
            [[ "$JSON_OUTPUT" == "true" ]] && cmd_arr+=(--output-format json)
            [[ -n "$MODEL" ]] && cmd_arr+=(--model "$MODEL")
            echo "[eval] Running: ${cmd_arr[*]} \"<prompt>\"" >&2
            if [[ -n "$OUTPUT" ]]; then
                "${cmd_arr[@]}" "$prompt_text" > "$OUTPUT"
            else
                "${cmd_arr[@]}" "$prompt_text"
            fi
            ;;
        fallback)
            echo "[eval] No non-interactive runner available (codex or claude)." >&2
            echo "[eval] Manual eval template:" >&2
            echo "-----BEGIN EVAL-----" >&2
            echo "$prompt_text" >&2
            echo "-----END EVAL-----" >&2
            echo "[eval] Copy the above into your AI assistant to run manually." >&2
            exit 1
            ;;
    esac
}

# ─── Batch Run ───────────────────────────────────────────────────────────────
run_batch() {
    if [[ -z "$BATCH_GLOB" ]]; then
        echo "Error: --batch requires a glob pattern" >&2
        exit 1
    fi
    if [[ -z "$OUTPUT_DIR" ]]; then
        echo "Error: --batch requires --output-dir" >&2
        exit 1
    fi
    mkdir -p "$OUTPUT_DIR"

    local backend
    backend="$(detect_backend)"

    echo "[eval] Batch mode: backend=$backend, glob=$BATCH_GLOB" >&2

    local count=0
    local evaluated=0
    local -a files=()
    # Use nullglob to safely expand the glob pattern
    shopt -s nullglob
    for file in $BATCH_GLOB; do
        [[ -f "$file" ]] && files+=("$file")
    done
    shopt -u nullglob

    for file in "${files[@]}"; do
        local fname
        fname="$(basename "$file" | tr '/' '_')"
        local out="${OUTPUT_DIR}/eval-${fname}.txt"
        count=$((count + 1))

        echo "[eval] Processing: $file → $out" >&2

        case "$backend" in
            codex)
                local -a cmd_arr=(codex exec --ephemeral -s "$SANDBOX")
                [[ -n "$MODEL" ]] && cmd_arr+=(-m "$MODEL")
                [[ "$JSON_OUTPUT" == "true" ]] && cmd_arr+=(--json)
                cmd_arr+=(-o "$out" "${PROMPT}

File: $file
Content:
$(cat "$file")")
                "${cmd_arr[@]}" 2>/dev/null &
                evaluated=$((evaluated + 1))
                ;;
            claude)
                local prompt_text="${PROMPT}

File: $file
Content:
$(cat "$file")"
                claude -p "$prompt_text" > "$out" 2>/dev/null &
                evaluated=$((evaluated + 1))
                ;;
            fallback)
                echo "[eval] No runner for $file — skipping" >&2
                ;;
        esac

        # Limit parallelism to 5
        if (( count % 5 == 0 )); then
            wait
        fi
    done
    wait
    echo "[eval] Batch complete: $count files processed, $evaluated evaluated" >&2
    if [[ "$evaluated" -eq 0 ]]; then
        echo "[eval] Error: No files were evaluated (backend=$backend)" >&2
        exit 1
    fi
}

# ─── Main ────────────────────────────────────────────────────────────────────
if [[ -n "$BATCH_GLOB" ]]; then
    run_batch
else
    run_single
fi
