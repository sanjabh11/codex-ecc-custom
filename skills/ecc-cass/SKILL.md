---
name: ecc-cass
description: Cross-tool session search via cass. Search all agent histories (Claude Code, Codex, Cursor, Gemini, Aider, and 15+ others) with sub-ms lexical search. Auto-invocable for cross-session pattern detection.
allowed-tools: Read, Write, Bash
---

# ecc-cass — Cross-Tool Agent Session Search

> **Usage hint:** `search sessions, find in history, cross-session search, have I done this before`

Search across ALL coding agent session histories (Claude Code, Codex, Cursor, Gemini,
Aider, Cline, OpenCode, ChatGPT, Copilot, Kimi, Qwen, and more) using the cass
local index. Sub-millisecond lexical search with robot-mode JSON output.

---

## Trigger Phrases

- "search sessions", "find in history", "cross-session search"
- "what did we discuss", "have I done this before"
- "search agent history", "find conversation"
- "find in past sessions", "search across tools"
- `/ecc-cass`

---

## Step 0: Health Check + Stale Refresh (Always)

Before any cass operation, verify health. If stale, attempt one refresh before searching:

```bash
cass_ready() {
  command -v cass >/dev/null 2>&1 || return 1
  cass health --json 2>/dev/null | grep -q '"healthy":true' && return 0
  # Stale — attempt one refresh with 15s timeout
  timeout 15 cass index --json >/dev/null 2>&1
  cass health --json 2>/dev/null | grep -q '"healthy":true'
}

cass_ready && echo "CASS_READY" || echo "CASS_UNAVAILABLE"
```

If `CASS_UNAVAILABLE`:
- Do NOT run any cass commands
- Fall back to callimachus MCP `search_threads` if available
- Inform user that cass index needs rebuild: `cass index --full`

**Note:** unhealthy ≠ empty results. If index is stale, refresh once then search. If refresh fails, skip silently.

**Timeout safety:** All cass calls should be wrapped with `timeout` to prevent hangs:
```bash
timeout 30 cass search "query" --robot --limit 5 --fields minimal 2>/dev/null || true
```

---

## Step 1: Search Sessions

**ALWAYS use `--robot` or `--json`. NEVER run bare `cass` — it launches interactive TUI.**

### Basic search (token-efficient)
```bash
cass search "query terms" --robot --limit 5 --fields minimal
```
Returns: `source_path`, `line_number`, `agent` only.

### Search with snippet
```bash
cass search "query terms" --robot --limit 5 --fields summary
```
Returns: `source_path`, `line_number`, `agent`, `title`, `score`.

### Filter by agent
```bash
cass search "query" --robot --limit 5 --agent codex
cass search "query" --robot --limit 5 --agent claude_code
cass search "query" --robot --limit 5 --agent cursor
```

### Filter by time
```bash
cass search "query" --robot --limit 5 --today
cass search "query" --robot --limit 5 --week
cass search "query" --robot --limit 5 --days 30
```

### Aggregation (overview — 99% token reduction)
```bash
cass search "*" --robot --aggregate agent
cass search "*" --robot --aggregate agent,workspace
cass search "error" --robot --aggregate date --week
```

### Pagination
```bash
cass search "query" --robot --limit 5 --offset 5
```

---

## Step 2: View Specific Result

After finding a relevant hit, retrieve the exact context:

```bash
# View a specific line
cass view /path/to/session.jsonl -n 42 --json

# Expand context around a line (3 lines before/after)
cass view /path/to/session.jsonl -n 42 -C 3 --json

# More context for complex decisions
cass view /path/to/session.jsonl -n 42 -C 10 --json
```

---

## Step 3: Report Results

Format search results for the user:

```
🔎 Session Search Results (cass)

Query: "{query}"
Matches: {total_matches} (showing top {limit})

1. [{agent}] {source_path}:{line_number}
   Score: {score}
   Snippet: {snippet}

2. [{agent}] {source_path}:{line_number}
   ...

Use `cass view <path> -n <line> -C <context>` to expand any result.
```

---

## Trigger Precedence

If both `ecc-router` and Codex `allow_implicit_invocation` fire for the same query:
1. **Router wins** — explicit routing takes precedence over implicit invocation
2. **Calls are idempotent** — duplicate cass searches return the same results, no side effects
3. **No double-fire risk** — cass is read-only; multiple invocations are harmless

## Auto-Invocation Patterns

### Pattern A: Before solving from scratch
When about to solve a problem, auto-search cass first:
```bash
cass health --json 2>/dev/null | grep -q '"healthy":true' && \
  cass search "{problem_description}" --robot --limit 3 --fields minimal 2>/dev/null || true
```
If results found → review them before proceeding. If no results → proceed fresh.

### Pattern B: Cross-session pattern detection (ecc-self-improve)
During self-improvement mining, auto-cross-reference:
```bash
cass search "${failure_type}" --robot --limit 5 --fields minimal 2>/dev/null
```
- cass confirms pattern → increase confidence
- cass returns nothing → decrease confidence by one level

### Pattern C: Session resume context
When resuming a project, auto-search for recent decisions:
```bash
cass search "{project_name} decision" --robot --limit 5 --days 14 --fields summary 2>/dev/null
```

### Pattern D: Loop completion pattern check
After loop completion, check for recurring failures:
```bash
cass search "{failure_pattern}" --robot --limit 5 --days 7 --fields minimal 2>/dev/null
```

---

## Graceful Degradation

```
cass healthy:    Full cross-tool search, line-level retrieval, aggregation
cass stale:      Attempt one refresh, then search. If refresh fails, treat as unhealthy.
cass unhealthy:  Fall back to callimachus MCP search_threads (if available)
cass absent:     Skip silently, rely on LEARNINGS.md + cm context
cass hanging:    Timeout kills the call after 30s, treated as unavailable
```

All cass calls use `timeout`, `|| true`, or `2>/dev/null` — cass failure never blocks ECC workflows.
Agents must never block on cass availability — it is advisory enrichment only.

---

## Index Maintenance

### Refresh index after sessions
```bash
cass health --json 2>/dev/null | grep -q '"healthy":true' && \
  cass index --json 2>/dev/null | tail -1 || true
```

### Full rebuild (if index corrupt)
```bash
cass index --full --json
```

### Doctor (self-repair)
```bash
cass doctor check --json
cass doctor repair --dry-run --json
cass doctor repair --yes --plan-fingerprint <fp> --json
```

---

## Dependency Gating

- Requires: `cass` binary installed (`command -v cass`)
- Requires: healthy index (`cass health --json` → `"healthy": true`)
- Optional: semantic models (`cass models install` for hybrid search)
- Fallback: callimachus MCP `search_threads` if cass unavailable

---

## Integration Points

- **ecc-self-improve**: Tier C memory — cross-session pattern confirmation
- **ecc-learn**: Auto cross-session check during learning review
- **ecc-trace-wrap**: Post-write index refresh (advisory)
- **ecc-loop-start**: Post-loop index refresh (advisory)
- **ecc-router**: Routes "search sessions" triggers to this skill
- **callimachus MCP**: Fallback when cass unavailable
