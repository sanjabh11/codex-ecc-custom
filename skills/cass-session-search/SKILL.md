---
name: cass-session-search
description: "Find and summarize prior session context with CASS, memory, and repo-grounded fallbacks."
origin: ECC
---

# CASS Session Search Skill

Use this skill when the user asks to find prior context, recover a previous fix, locate an old handoff, explain what happened in an earlier session, or answer "we solved this before" questions.

## Trigger Phrases

- "find the previous session"
- "what did we do last time"
- "search CASS"
- "recover the handoff"
- "where did we fix this before"
- "use prior context"

## Workflow

1. Define the search target in one sentence: repo, feature, error text, command, or artifact.
2. Check tool truth before relying on CASS:
   ```bash
   command -v cass
   cass health --json
   ```
3. If CASS is healthy, run a narrow robot search:
   ```bash
   cass search "<query>" --robot --limit 5 --fields minimal
   ```
4. If a result is relevant, open only the smallest available detail view for exact commands, files, or decision text.
5. If CASS is unavailable or unhealthy, fall back to local memory and repo search:
   ```bash
   rg -n "<keyword>" /Users/sanjayb/.codex/memories/MEMORY.md
   rg -n "<keyword>" .
   ```
6. Report what is confirmed, what is inferred, and what remains stale or unverified.

## Output Contract

Return:
- `Search target`: the exact query or evidence target.
- `Best hits`: 3 to 5 compact bullets with source, why it matters, and confidence.
- `Actionable context`: files, commands, constraints, or prior decisions that affect the current task.
- `Staleness warning`: say when context is memory-derived or could have drifted.
- `Next command`: the single most useful follow-up command if further verification is needed.

## Safety Rules

- Do not print secrets, credentials, tokens, or private payloads from sessions.
- Do not claim a prior result is current unless it was re-verified in this session.
- Prefer exact error text and file paths over broad semantic searches.
- Keep result loading targeted; avoid dumping entire session logs.
