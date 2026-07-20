# CLI Flags Reference

## Basic Usage

```bash
python3 fable/advisor_cli.py "<context/question>"
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
| `--session` | string | Session ID for state isolation |
| `--backend` | enum | Force backend: `grok_cli`, `claude_native`, `codex_orchestration` |

## Examples

### Get advice
```bash
python3 fable/advisor_cli.py "Should I use offset or cursor pagination for 50M rows?"
```

### Get JSON output for programmatic use
```bash
python3 fable/advisor_cli.py --json "Should I use offset or cursor pagination?"
```

### Load large context from file
```bash
python3 fable/advisor_cli.py --context-file ./task-context.md "What's the best approach?"
```

### Dry run (no call budget consumed)
```bash
python3 fable/advisor_cli.py --dry-run "Testing advisor availability"
```

### Session-isolated state
```bash
python3 fable/advisor_cli.py --session task-42 "Context for task 42"
```

### Force a specific backend
```bash
python3 fable/advisor_cli.py --backend grok_cli "Context here"
```

### Check status
```bash
python3 fable/advisor_cli.py --status
```

### Reset counter
```bash
python3 fable/advisor_cli.py --reset
```
