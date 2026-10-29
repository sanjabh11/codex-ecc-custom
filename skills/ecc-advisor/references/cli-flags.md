# CLI Flags Reference

## Basic Usage

```bash
# From inside the git repo
bash skills/ecc-advisor/scripts/call_advisor.sh "<context/question>"

# Or using the bootstrap wrapper (works from any CWD)
bash skills/ecc-advisor/scripts/call_advisor.sh "<context/question>"

# Or using FABLE_DIR env var
export FABLE_DIR=/path/to/fable
python3 "$FABLE_DIR/advisor_cli.py" "<context/question>"
```

## All Flags

| Flag | Type | Description |
|---|---|---|
| `context` | positional (nargs=*) | Context/question text for the advisor |
| `--status` | flag | Show call count and history as JSON |
| `--reset` | flag | Reset session counter to 0 |
| `--json` | flag | Output structured JSON response (see schema) |
| `--context-file` | path | Load context from a file (prepended to positional args) |
| `--dry-run` | flag | Preview without consuming call budget |
| `--session` | string | Session ID for audit trail tagging (call count is global) |
| `--backend` | enum | Force backend: `jev_gateway`, `grok_cli`, `claude_native`, `codex_orchestration` |
| `--max-calls` | int | Override max advisor calls from config |
| `--timeout` | int | Override timeout in seconds from config |
| `--model` | string | Override advisor model from config |
| `--system-prompt` | string | Override advisor system prompt from config |
| `--revoke` | flag | Persist a global advisor revocation |
| `--unrevoke` | flag | Clear the persisted global advisor revocation |
| `--revoke-reason` | string | Reason recorded with `--revoke` |
| `--revoke-until` | ISO-8601 | Optional expiry for a temporary `--revoke` |

## Examples

### Get advice
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh "Should I use offset or cursor pagination for 50M rows?"
```

### Get JSON output for programmatic use
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --json "Should I use offset or cursor pagination?"
```

### Load large context from file
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --context-file ./task-context.md "What's the best approach?"
```

### Dry run (no call budget consumed)
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --dry-run "Testing advisor availability"
```

### Tag calls with session ID
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --session task-42 "Context for task 42"
```

### Force a specific backend
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --backend grok_cli "Context here"
```

### Override max calls
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --max-calls 5 --dry-run "Test with 5 calls allowed"
```

### Override timeout
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --timeout 60 --dry-run "Test with 60s timeout"
```

### Override advisor model
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --model grok-4 "Context here"
```

### Override system prompt
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --system-prompt "You are a code review advisor" "Review this approach"
```

### Check status
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --status
```

### Reset counter
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --reset
```

### Revoke globally
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --revoke --revoke-reason "incident response"
```

### Clear global revocation
```bash
bash skills/ecc-advisor/scripts/call_advisor.sh --unrevoke
```

## Security Features

- **State file permissions:** `advisor_state.json` is written with `0600` permissions (owner-only read/write) to protect context previews
- **File locking:** Uses `fcntl.flock` on Unix to prevent concurrent-write corruption when multiple agents call the advisor simultaneously
- **Context length limit:** Context is truncated at 32,000 chars with a `[... truncated]` marker to prevent API abuse
- **History pruning:** State history is pruned to the last 50 entries to prevent unbounded file growth
- **Corrupted state recovery:** Invalid JSON or missing fields in state file automatically reset to defaults instead of crashing
- **State versioning:** State file includes a `version` field for forward-compatible schema changes
- **Global revocation:** The canonical config can block all CLI/wrapper calls, optionally until an ISO-8601 expiry
- **Fail-closed config:** Missing or malformed advisor configuration blocks calls instead of silently re-enabling the backend
