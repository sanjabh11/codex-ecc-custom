---
name: ecc-learn
description: Read what the self-improvement agent has learned from LEARNINGS.md, summarise patterns, and offer to promote high-confidence learnings into the relevant SKILL.md files.
argument-hint: 'what did we learn, show learnings, promote instincts'
allowed-tools: Read, Write, Bash
---

# ecc-learn — Review & Promote Learnings

Surface what the self-improvement flywheel has captured from past sessions,
give you an intelligible summary, and let you selectively promote findings
into the relevant `SKILL.md` files.

---

## Trigger Phrases

- "what did we learn?", "show learnings", "review learnings"
- "what has the agent learned?", "learning summary"
- `/ecc-learn`

---

## Step 0: Memory Recall (Tier B — Optional)

Before loading LEARNINGS.md, check if `cm` has session context from recent trace-wraps:

```bash
# Health check + recall
if command -v cm >/dev/null 2>&1; then
  cm context "show ecc-self-improve history" --json 2>/dev/null | head -20 || true
fi
```

If cm returns context, display it briefly:
```
🧠 Memory Recall (from previous session):
   Last trace-wrap: {date} — {N} entries, skills: {skill_list}
   Last improvement: {date} — patched: {skill}/{failure_type}
```

If cm unavailable or returns nothing, proceed without recall (LEARNINGS.md is ground truth).

**Optional — Tier C semantic cross-check:**
If `cass` is healthy and user explicitly asks "cross-session patterns":
```bash
cass health --json 2>/dev/null | grep -q '"healthy":true' && \
  cass search "failure_type" --robot --limit 5 --fields minimal 2>/dev/null || true
```

---

## Step 1: Load LEARNINGS.md

Read `/Users/sanjayb/codex-ecc-custom/LEARNINGS.md`.

If the file is empty or missing:
```
📭 No learnings recorded yet.

Run /ecc-trace-wrap at the end of a session to start capturing.
```
Stop here if empty.

---

## Step 2: Parse & Aggregate

Parse each JSON line. Group by `(skill_invoked, failure_type)`.

For each group compute:
- `total_frequency` = sum of all `frequency` values
- `avg_confidence` = most common confidence level across entries
- `date_range` = first and last date seen
- `corrections` = all unique correction strings

**Threshold for "systematic weakness":** `total_frequency >= 3`

---

## Step 3: Display Summary (Use ecc-headroom compression if >20 entries)

Show the user a clean, scannable report:

```
📊 LEARNINGS SUMMARY — {N} entries, {date_range}

🔴 SYSTEMATIC WEAKNESSES (frequency ≥ 3) — Ready to patch:
┌────────────────────────────────────────────────────────────────┐
│ [{skill}] {failure_type}                          x{total} │
│ Fix: {top correction}                                       │
│ Target: {proposed_fix_location}                             │
│ Evidence: {entry_count} entries with conversation_evidence  │
└────────────────────────────────────────────────────────────────┘

🟡 PATTERNS TO WATCH (frequency 2) — Not yet actionable:
  • [{skill}] {failure_type} — {correction}

🟢 SINGLE OCCURRENCES (frequency 1) — Noted, not promoted:
  • {N} entries (use /ecc-self-improve --all to review)

{if any entries missing conversation_evidence:}
⚠️  {M} entries missing conversation_evidence (unverifiable):
   These will be filtered out by the Judge Gate and not patched.

💡 Run /ecc-self-improve to automatically patch the 🔴 weaknesses.
   Or ask me to explain any entry in detail.
```

---

## Step 4: On-Demand Deep Dive

If the user asks "explain {failure_type}" or "tell me more about {skill}":
- Show all raw entries for that group
- Quote the exact `context` and `correction` fields
- Explain WHY this is a systematic problem, not a one-off

---

## Step 5: Manual Promote (Optional)

If user says "promote this" or "apply this fix to {SKILL.md}":

1. Read the current target `SKILL.md`
2. Identify the section that governs the failing behaviour
3. Append a new paragraph with the correction as a named rule:
   ```markdown
   > **Learned rule ({date}):** {correction}
   ```
4. Confirm the change with the user before writing
5. Write the update
6. Append a `promoted` flag to the entry in LEARNINGS.md:
   ```json
   {"date":"...","promoted":true,"promoted_to":"skills/ecc-agent-reach/SKILL.md"}
   ```

**CRITICAL:** Only modify `skills/` files. Never touch `CLAUDE.md` or agent `.toml` files
without explicit "yes, update CLAUDE.md" from the user.

---

## Dependency Gating

- Requires: `LEARNINGS.md` to exist (created by `ecc-trace-wrap`)
- Optional: `ecc-headroom` for compression when >20 entries
- Feeds into: `ecc-self-improve` for automated patch cycle

---

## What Changed From Previous Version

The previous `ecc-learn` was a stub that only referenced `continuous-learning`
and `continuous-learning-v2` without implementing any workflow.

This version implements the full 3-tier learning loop:
1. Tier 3 read: `LEARNINGS.md` (failure diary)
2. Tier 2 promote: `SKILL.md` (task-specific rules)
3. Tier 1 gate: never auto-touch `CLAUDE.md` (global rules)
