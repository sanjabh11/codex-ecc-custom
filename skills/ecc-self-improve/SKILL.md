---
name: ecc-self-improve
description: The 4-stage self-improvement flywheel. Mines LEARNINGS.md for systematic weaknesses, generates textual gradient patches for SKILL.md files, gates them through regression fixtures, and commits only passing patches. This is the core of the self-improvement learning agent.
argument-hint: 'self-improve, improve yourself, patch skills, apply learnings'
allowed-tools: Read, Write, Bash
---

# ecc-self-improve — The 4-Stage Self-Improvement Flywheel

This skill turns raw session observations (from LEARNINGS.md) into verified,
committed improvements to your ECC skill files — automatically, safely, and
with a full audit trail.

```
Mine → Propose → Gate → Commit
```

---

## Trigger Phrases

- "self-improve", "improve yourself", "apply learnings"
- "patch skills", "run the flywheel", "what can you fix?"
- `/ecc-self-improve`
- `/ecc-self-improve --all` (include low-confidence entries)
- `/ecc-self-improve --dry-run` (show patches but don't write)

---

## Prerequisites

1. `LEARNINGS.md` exists at `/Users/sanjayb/codex-ecc-custom/LEARNINGS.md`
2. Python 3 is available (`python3 --version`)
3. `TERMS.md` exists at `/Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/TERMS.md`

If LEARNINGS.md is empty → tell user to run `/ecc-trace-wrap` after sessions first.
If TERMS.md is missing → HARD STOP: cannot proceed without Terms & Conditions file.

---

## ═══ STAGE 0: PRE-FLIGHT ═══ (Boundary Check + T&C Gate)

**Run this before any Tier 2+ action. Tier 1 (--dry-run) skips to Stage 1 directly.**

### 0a. Read and display TERMS.md

```
Read: /Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/TERMS.md
```
If file missing → HARD STOP:
```
❌ TERMS.md not found. Cannot proceed without Terms & Conditions.
Expected: skills/ecc-self-improve/TERMS.md
Run: git status to check if file was deleted.
```

### 0b. Run Boundary Condition Check (all 6 must pass for Tier 2)

```bash
python3 /Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/tests/runner.py \
    --boundary-check 2>&1
```

Display the results:
```
🔒 STAGE 0 — BOUNDARY CONDITIONS (Tier 2 requires ALL to pass)

  BC-1 LEARNINGS.md has ≥3 unpromoted entries  → [PASS/FAIL] ({N} found)
  BC-2 At least one entry with frequency ≥3     → [PASS/FAIL]
  BC-3 At least one entry confidence="high"    → [PASS/FAIL]
  BC-4 All mined entries have conversation_evidence → [PASS/FAIL]
  BC-5 Regression fixtures pass               → [PASS/FAIL]
  BC-6 Git working tree is clean              → [PASS/FAIL]

  TIER 2 STATUS: [READY / BLOCKED]
```

If Tier 2 BLOCKED → suggest `--dry-run` (Tier 1) instead and show which BCs failed.
If Tier 2 READY → show T&C summary and proceed to Stage 1.

### 0c. Hallucination Pre-Audit

Before mining, verify LEARNINGS.md is not contaminated with invented entries:
```bash
python3 -c "
import json, sys
errors = []
for i, line in enumerate(open('/Users/sanjayb/codex-ecc-custom/LEARNINGS.md'), 1):
    line = line.strip()
    if line and not line.startswith('#'):
        try:
            entry = json.loads(line)
            if not entry.get('conversation_evidence'):
                errors.append(f'Line {i}: missing conversation_evidence')
            if entry.get('confidence') == 'high' and entry.get('frequency', 0) < 2:
                errors.append(f'Line {i}: high confidence requires frequency >= 2')
        except json.JSONDecodeError:
            errors.append(f'Line {i}: invalid JSON')
if errors:
    print('CONTAMINATION DETECTED:')
    for e in errors: print(f'  ⚠️  {e}')
    print('Fix these entries before running the flywheel.')
    sys.exit(1)
else:
    print('AUDIT PASSED: all entries have valid structure and evidence.')
" 2>&1
```

If audit fails → display warnings and prompt user to review flagged entries.
Do NOT auto-delete entries — user must confirm removal.

---

## ═══ STAGE 1: MINE ═══ (Weakness Identification)

**Read LEARNINGS.md and find systematic failures.**

```bash
python3 -c "
import json, sys
from collections import defaultdict

entries = []
with open('/Users/sanjayb/codex-ecc-custom/LEARNINGS.md') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass

# Group by (skill, failure_type)
groups = defaultdict(list)
for e in entries:
    if not e.get('promoted'):  # skip already-promoted entries
        key = (e.get('skill_invoked','general'), e.get('failure_type','other'))
        groups[key].append(e)

# Find systematic weaknesses: total_frequency >= 3
weaknesses = []
for (skill, ftype), entries_list in groups.items():
    total_freq = sum(e.get('frequency',1) for e in entries_list)
    if total_freq >= 3:
        corrections = list({e['correction'] for e in entries_list})
        locations = list({e.get('proposed_fix_location','') for e in entries_list if e.get('proposed_fix_location')})
        weaknesses.append({
            'skill': skill,
            'failure_type': ftype,
            'total_frequency': total_freq,
            'corrections': corrections,
            'proposed_locations': locations,
            'entry_count': len(entries_list)
        })

weaknesses.sort(key=lambda x: -x['total_frequency'])
print(json.dumps(weaknesses, indent=2))
" 2>&1
```

**Display to user:**
```
🔍 STAGE 1 — MINING COMPLETE

Found {N} systematic weaknesses (frequency ≥ 3):

1. [{skill}] {failure_type} — occurred {total_frequency}x across {entry_count} sessions
   Corrections identified: {corrections[0]}
   Target: {proposed_locations[0]}

{repeat...}

Proceeding to Stage 2 — generating patches...
```

If 0 weaknesses found:
```
✅ No systematic weaknesses found (nothing reached frequency ≥ 3).
Keep using /ecc-trace-wrap after sessions to build up evidence.
```
→ Stop here.

---

## ═══ STAGE 2: PROPOSE ═══ (Textual Gradient Patch Generation)

For each systematic weakness from Stage 1:

### 2a. Read the target SKILL.md

```
Read: /Users/sanjayb/codex-ecc-custom/skills/{skill}/SKILL.md
```

If the file doesn't exist → skip this weakness, log "target_not_found".

### 2b. Generate a Textual Gradient

Apply this structured reasoning to generate the patch:

```
TEXTUAL GRADIENT PATTERN:
"The current instruction at {location} causes {failure_type} in context {context}
because {root_cause}. The correction is: {correction}.

Proposed new paragraph to add at the end of the relevant section:

> **Learned rule ({today's date}) [auto-patch]:** {correction}
> *Evidence: observed {total_frequency}x across sessions. Confidence: {confidence}.
>  Grounded in LEARNINGS.md entries: {date_range} | Approved: {today's date}*"
```

**Rules for the patch:**
- The patch is a PARAGRAPH ADDITION only — never delete or rewrite existing content
- Place it at the end of the section most relevant to the failure type
- Keep it ≤ 4 lines
- It must be self-contained and understandable without context
- Tag it with the date and `[auto-patch]` so it can be identified later

### 2c. Judge Gate B — Patch Validation (REQUIRED before writing any patch)

Before writing the patch to a temp file, answer these questions with YES or NO:

```
JUDGE GATE B CHECKLIST:

J1: Does the patch paragraph contradict anything already written in the target SKILL.md?
    → If YES: BLOCK. The existing instruction takes precedence unless it's being superseded.

J2: Does the patch contain any URL, specific tool name, percentage, or statistic?
    → If YES: verify each claim appears in at least one LEARNINGS.md entry's
      conversation_evidence or context field.
    → If claim NOT found in LEARNINGS.md: REMOVE the claim from the patch.

J3: Is the patch specific enough to change agent behavior?
    ("Always verify URLs" = GOOD; "Be more careful about URLs" = BAD)
    → If NOT specific: rewrite or BLOCK if cannot be made specific.

J4: Does the patch address the actual failure_type (not a related but different issue)?
    → If NO: BLOCK and log as "scope_mismatch" in proposed block reason.

J5: Is the patch ≤ 4 lines?
    → If NO: trim it. If cannot be trimmed meaningfully: BLOCK.
```

If ALL 5 pass → write patch to temp file and proceed to Stage 2d.
If ANY fail → log block to LEARNINGS.md with `"promoted": false, "block_reason": "J{N} failed"` and skip this weakness.

### 2d. Claim Provenance Rule

Before writing any patch to disk, verify claim-level provenance:

```python
# Every specific claim in the patch must trace to a LEARNINGS entry
# Scan patch text for:
# - URLs (https://...)
# - Percentages (\d+%)
# - Tool names (ecc-*, runner.py, specific library names)
# - Statistics (N times, N entries, N sessions)

# For each claim found:
# 1. Search LEARNINGS.md for it
# 2. If not found: REMOVE claim from patch
# 3. If all claims removed and patch becomes generic: BLOCK entire patch
```

Apply this check automatically — do not ask user for each claim.
Log any removed claims to the patch proposal display.

### 2e. Write proposed patch to a temp file

```
/tmp/ecc_patch_{skill}_{date}.md
```

Show the user the proposed patch:
```
📝 STAGE 2 — PROPOSED PATCH for {skill}:

--- PATCH ---
> **Learned rule (2026-06-14) [auto-patch]:** {correction}
> *Evidence: x{total_frequency} occurrences, {confidence} confidence.
>  Grounded in LEARNINGS.md: {entry_count} entries, {date_range}*
--- END ---

🔍 Judge Gate B: J1 PASS ⮏ J2 PASS ⮏ J3 PASS ⮏ J4 PASS ⮏ J5 PASS ⮏
This will be appended to: skills/{skill}/SKILL.md
```

---

## ═══ STAGE 3: GATE ═══ (Regression Fixture Check)

Before writing any patch, run the regression fixture suite.

### 3a. Check for fixtures

```bash
FIXTURES_PATH="/Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/tests/fixtures.json"
if [ -f "$FIXTURES_PATH" ]; then
    echo "fixtures_found"
else
    echo "no_fixtures"
fi
```

**If no fixtures exist:**
```
⚠️  No regression fixtures found yet.
    Patches will be applied with a USER APPROVAL GATE instead.
    Run /ecc-self-improve --add-fixture after verifying a patch works
    to build the regression suite over time.
```
→ Skip to Stage 4 with `requires_user_approval = true`

**If fixtures exist**, run the fixture runner:
```bash
python3 /Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/tests/runner.py \
    --skill {skill} \
    --patch /tmp/ecc_patch_{skill}_{date}.md 2>&1
```

### 3b. Self-Correction Loop (Feedback Loop)
If any fixture fails, do NOT immediately block the patch. Attempt a single self-correction cycle:
1. Capture the failing fixture ID, the description, and the failure reason from `runner.py`'s output.
2. Re-prompt yourself (or re-generate the patch) using this context:
   ```
   Proposed patch for {skill} failed regression fixture {fixture_id}:
   Reason: {reason}

   Re-generate the patch to satisfy this fixture's assertion while still correcting the underlying failure. Do not contradict or remove required keywords.
   ```
3. Generate the corrected patch and write it to `/tmp/ecc_patch_{skill}_{date}.md`.
4. Run the fixture runner again:
   ```bash
   python3 /Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/tests/runner.py \
       --skill {skill} \
       --patch /tmp/ecc_patch_{skill}_{date}.md 2>&1
   ```

Display result:
```
🧪 STAGE 3 — REGRESSION GATE

Running {N} fixtures for {skill}...
  ✅ fixture-001: hallucination_check — PASS
  ✅ fixture-002: url_verification — PASS
  ❌ fixture-003: routing_integrity — FAIL
     Expected: contains "verified search query"
     Got: patch doesn't address routing

🔄 Attempting self-correction loop...
Corrected patch generated. Re-running checks...
  ✅ fixture-003: routing_integrity — PASS

RESULT: GATE PASSED (after self-correction).
Proceeding to Stage 4...
```

If the self-correction run still fails any fixture, permanently block the patch and log the failure.

If ALL pass on the first or second run:
```
RESULT: GATE PASSED — all {N} fixtures passed.
Proceeding to Stage 4...
```


---

## ═══ STAGE 4: COMMIT ═══ (Atomic Patch Application)

### 4a. If requires_user_approval = true

Show the patch and ask:
```
⚡ No regression fixtures available.

Here is the proposed patch:
{patch content}

Apply this patch to skills/{skill}/SKILL.md? [yes/no]
```
Wait for user confirmation before writing.

### 4b. Write the patch (gate passed OR user approved)

1. Read the current `SKILL.md`
2. Append the patch paragraph at the end of the most relevant section
3. Write back to `SKILL.md`
4. **Scaffold & Append New Regression Fixture**:
   - Generate a new JSON object for a regression fixture:
     ```json
     {
       "id": "auto-{skill}-{hash}",
       "skill": "{skill}",
       "description": "Auto-generated fixture for {failure_type} to enforce: {correction_one_liner}",
       "must_contain_any": ["{keywords_from_correction}"],
       "must_not_contain": ["{regex_drawn_from_conversation_evidence}"],
       "context": "Auto-generated during self-improvement patch on {date}"
     }
     ```
   - Append this JSON object to `/Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/tests/fixtures-expanded.json`.
   - Run `python3 /Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/tests/runner.py --verify` to guarantee the JSON structure remains valid.
5. Mark the LEARNINGS.md entries as promoted:
   - Append `"promoted": true` and `"promoted_to": "skills/{skill}/SKILL.md"` to each mined entry

```bash
# Git commit with traceability tag
cd /Users/sanjayb/codex-ecc-custom
git add skills/{skill}/SKILL.md LEARNINGS.md skills/ecc-self-improve/tests/fixtures-expanded.json
git commit -m "[self-improve] {skill}: {one-line summary of correction}" 2>&1
```

### 4c. Report

```
✅ STAGE 4 — PATCH COMMITTED

Skill improved: {skill}
Commit: {git hash}
Patch: {correction one-liner}

📊 Flywheel complete:
   Mined {entry_count} sessions → Found weakness → Patch passed gate → Committed

Run /ecc-learn to see the full learning log.
Want to add a regression fixture for this fix? Say "add fixture".
```

---

## Adding a Fixture

When user says "add fixture" after a successful patch:

```
What should I test? Describe the scenario:
  - What input/context triggers the old (broken) behavior?
  - What should the corrected skill output contain?
  - What should it NOT contain?
```

Add the fixture to `skills/ecc-self-improve/tests/fixtures.json` and run
`runner.py --verify` to confirm it works.

---

## --dry-run Mode

When invoked with `--dry-run`:
- Run Stage 1 and Stage 2 normally
- Show proposed patches
- Skip Stage 3 and Stage 4 completely
- End with: "Dry run complete. Run /ecc-self-improve to apply."

---

## Safety Boundaries (NEVER cross these)

| Action | Tier | Allowed |
|--------|----|--------|
| Append paragraph to `skills/*/SKILL.md` | 2 | ✅ Yes (gate passed) |
| Modify `LEARNINGS.md` (mark promoted) | 2 | ✅ Yes |
| Add to `skills/ecc-self-improve/tests/fixtures.json` | 2 | ✅ Yes |
| Modify `skills/ecc-router/SKILL.md` | 3 | ⚠️ User approval required |
| Modify `skills/ecc-self-improve/SKILL.md` itself | 3 | ⚠️ User approval required |
| Rewrite or delete sections of any SKILL.md | — | ❌ Never |
| Modify `CLAUDE.md` (global rules) | — | ❌ Never auto |
| Modify any `.toml` agent file | — | ❌ Never |
| Modify files outside `codex-ecc-custom/` | — | ❌ Never |
| Apply patch without gate passing or user approval | — | ❌ Never |
| Apply patch with empty `conversation_evidence` | — | ❌ Never |
| Apply > 3 patches in a single session | 3 | ⚠️ User approval required |

---

## Integration Map

| Feeds from | Feeds into |
|-----------|----------|
| `ecc-trace-wrap` (writes LEARNINGS.md) | `ecc-learn` (human-readable view) |
| `ecc-loop-start` (triggers on loop end) | `ecc-evolve` (instinct promotion) |
| `LEARNINGS.md` (raw evidence) | `skills/*/SKILL.md` (improved rules) |
| `TERMS.md` (read at Stage 0) | Boundary gate enforcement |
| `memory.md` (3-tier memory guide) | cm, cass integration |

---

## Reference Documents

- [TERMS.md](file:///Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/TERMS.md) — Full T&C, tier definitions, boundary conditions
- [memory.md](file:///Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/memory.md) — 3-tier memory system guide
- [runner.py](file:///Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/tests/runner.py) — Regression + boundary check runner
- [fixtures.json](file:///Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/tests/fixtures.json) — Regression fixture suite
