---
name: ecc-trace-wrap
description: Session wrap-up skill. Records failures, corrections, and discoveries from the current session into LEARNINGS.md for the self-improvement flywheel. Run at the end of every work session.
argument-hint: 'wrap up, end session, record learnings'
allowed-tools: Read, Write, Bash
---

# ecc-trace-wrap — Session Wrap-Up & Trace Recorder

Run this at the END of every session to feed the self-improvement flywheel.
It turns your session's corrections and retries into structured evidence that
`ecc-self-improve` can mine for systematic weaknesses.

---

## Trigger Phrases

Activate when user says any of:
- "wrap up", "end session", "record learnings"
- "what did we learn?", "save what we learned"
- `/ecc-trace-wrap`

---

## Step 1: Reflect on the Session & Load Temporary Buffer

Before checking conversation history, read the in-session temporary buffer to capture any automatically recorded failures (such as non-zero command exits or tool retries):

```bash
# Check if temporary trace file exists in repo root
SESSION_TRACE="/Users/sanjayb/codex-ecc-custom/.session_trace.json"
if [ -f "$SESSION_TRACE" ]; then
    cat "$SESSION_TRACE"
fi
```

If entries exist in `.session_trace.json`, parse them as candidates for learnings. Merge them with your internal reflection on the following questions:

1. **Corrections** — Did the user correct you more than once for the same type of mistake?
   - Wrong URL / hallucinated reference
   - Wrong tool choice
   - Misunderstood intent
   - Broke an existing file / pattern

2. **Retries** — Did any tool call fail and need to be retried?
   - Which tool? Why did it fail?
   - How was it resolved?

3. **Discoveries** — Did we learn something that should persist?
   - A project convention not yet in any SKILL.md
   - A working pattern for a previously failing approach
   - A constraint or limitation of a tool/skill

4. **Skill invoked** — Which ECC skills were used this session?

---

## Step 2: Locate LEARNINGS.md & Clean Temporary Buffer

The learnings file lives at the root of the ECC plugin:

```
/Users/sanjayb/codex-ecc-custom/LEARNINGS.md
```

If it does not exist, create it with this header (first time only):
```
# ECC Self-Improvement Learnings Log
# Format: one JSON object per line
# Pruned monthly by ecc-prune
```

*Note: After writing the aggregated entries to `LEARNINGS.md`, delete `/Users/sanjayb/codex-ecc-custom/.session_trace.json` to prepare for the next session.*


---

## Step 3: Write Structured Entries

For each finding, append ONE JSON line to `LEARNINGS.md`.

**Entry schema (v2 — conversation_evidence is REQUIRED):**
```json
{
  "date": "YYYY-MM-DD",
  "session_id": "short-id-from-context",
  "skill_invoked": "ecc-agent-reach",
  "failure_type": "hallucinated_url | wrong_tool | misread_intent | broken_pattern | other",
  "context": "one sentence describing what the agent was trying to do",
  "correction": "one sentence describing what should happen instead",
  "conversation_evidence": "VERBATIM quote or exact tool output that proves this failure occurred",
  "frequency": 1,
  "confidence": "high | medium | low",
  "proposed_fix_location": "skills/ecc-agent-reach/SKILL.md#verification-section",
  "promoted": false
}
```

**Rules for entries:**
- `conversation_evidence` is **mandatory** — quote the exact user correction, tool error, or retry that proves the failure happened. If you cannot quote evidence, do NOT write the entry.
- `frequency` = how many times this type of mistake happened this session (1–10)
- `confidence` = how certain you are this is a real systematic issue (not a one-off)
- `proposed_fix_location` = the SKILL.md section that governs this behavior (optional but helpful)
- Use `"skill_invoked": "general"` if the session didn't involve a specific named skill
- NEVER invent or hallucinate details — only record what actually happened

---

## Step 3b: Judge Gate A — Entry Validation (run before writing each entry)

Before appending any entry, internally answer these three questions:

```
Q1: Can I quote the exact moment this failure occurred in the conversation?
    (a user correction, a tool retry, a "that's wrong" message)
    → If NO: do NOT write the entry. Add "insufficient evidence" note instead.

Q1b: Is the 'conversation_evidence' quote strong and specific?
     - It must be ≥ 5 words.
     - It must contain quotation marks or match actual tool error messages.
     - It CANNOT just be a copy/paste or paraphrase of the 'correction' field.
     → If NO: Reject the entry, or flag as "unverifiable" and downgrade confidence to "low".

Q2: Is my correction specific enough that a different agent could act on it?
    ("Always use fallback search URLs" = GOOD; "be more careful" = BAD)
    → If NOT specific: rewrite correction or lower confidence to "low"

Q3: Have I seen this failure at least once in THIS session (not just a past session)?
    → If NO: use frequency = 1 and confidence = "low" maximum
```

**Confidence Calibration Rules:**
- `"confidence": "high"` → Only if Q1=YES, Q1b=YES, Q2=YES, Q3=YES, and frequency ≥ 2
- `"confidence": "medium"` → Q1=YES, Q1b=YES and Q2=YES, but frequency = 1
- `"confidence": "low"` → Q1b=NO (unverifiable), or any Q is uncertain; default when in doubt


**Example entries:**
```json
{"date":"2026-06-14","session_id":"abc12","skill_invoked":"ecc-agent-reach","failure_type":"hallucinated_url","context":"Agent cited a Reddit post ID that did not exist","correction":"Always use fallback search query URLs, never fabricate post IDs","frequency":3,"confidence":"high","proposed_fix_location":"skills/ecc-agent-reach/SKILL.md"}
{"date":"2026-06-14","session_id":"abc12","skill_invoked":"ecc-router","failure_type":"wrong_tool","context":"Router sent a UI task to ecc-tdd instead of ecc-e2e","correction":"UI test tasks should route to ecc-e2e, not ecc-tdd","frequency":1,"confidence":"medium","proposed_fix_location":"skills/ecc-router/SKILL.md"}
```

---

## Step 4: Report to User

After writing entries, report:

```
✅ Session wrapped up. Here's what was recorded:

📝 {N} entries added to LEARNINGS.md:

1. [{skill_invoked}] {failure_type} (x{frequency}, {confidence} confidence)
   → Correction: {correction}
   → Evidence: "{conversation_evidence_excerpt}"

{repeat for each entry}

{if any entries were REJECTED by Judge Gate A:}
⚠️  {M} entries REJECTED — insufficient conversation evidence:
   • {context} → could not find supporting quote in this session

💡 Run /ecc-self-improve when you're ready to turn these into skill patches.
   Only high-frequency, high-confidence entries with evidence will be patched.
```

If nothing significant happened this session:
```
✅ Session wrapped up. No systematic issues detected — nothing to record.
```

---

## Step 5: Memory Write (Optional — Tier B)

After writing to LEARNINGS.md, optionally persist a summary to `cm` for cross-session recall:

```bash
# Health check first — never block on cm failure
if command -v cm >/dev/null 2>&1; then
  cm context "ecc-trace-wrap [$(date +%Y-%m-%d)]: ${N} entries recorded; skills: ${skill_list}; confidence: ${max_confidence}" --json 2>/dev/null || true
fi
```

This enables `ecc-learn` to recall what was logged last session without re-reading LEARNINGS.md.
If cm is unavailable, skip silently — LEARNINGS.md is the ground truth.

---

## Zero-Invention Rule (Constitutional Constraint)

**CRITICAL — Non-Negotiable:** Do NOT invent failures or corrections that didn't actually occur.
Only record things you can quote verbatim from the conversation.

The `conversation_evidence` field is the enforcement mechanism:
- **Empty or vague evidence** = entry is fabricated = REJECT
- **Paraphrased evidence** = acceptable only if clearly attributed: `"User said approximately: ..."`
- **Tool output as evidence** = best form: copy the exact error or retry message

Invented entries corrupt the improvement flywheel, cause hallucinated patches,
and degrade the regression fixture suite.

**If you are tempted to write a LEARNINGS entry without clear evidence, do not write it.
Wait until the next session where the failure recurs, then record it with evidence.**

---

## Integration

- Feeds into: `ecc-self-improve` (mines LEARNINGS.md for systematic weaknesses)
- Related to: `ecc-learn`, `ecc-loop-start` (calls trace-wrap at loop end)
- Pruning: `ecc-prune` handles old low-confidence entries monthly
