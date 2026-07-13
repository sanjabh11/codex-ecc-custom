# ECC Self-Improvement — Terms & Conditions

**Version:** 2.0  
**Effective:** 2026-06-14  
**Applies to:** All `ecc-self-improve` Tier 2+ operations

---

## Machine-Readable Tier Definitions

```
TIER 0 — READ-ONLY (auto-allowed, no approval required)
  Actions: ecc-trace-wrap, ecc-learn, runner.py --verify, runner.py --list
  Risk:    None — read/append only to LEARNINGS.md
  Gate:    None

TIER 1 — PROPOSE-ONLY (auto-allowed, output shown but never written)
  Actions: ecc-self-improve --dry-run, runner.py --audit, runner.py --boundary-check
  Risk:    None — no files modified
  Gate:    None

TIER 2 — APPLY WITH GATE (auto-allowed IF all boundary conditions pass)
  Actions: ecc-self-improve (full run — mine + propose + gate + commit)
  Risk:    Low — SKILL.md files appended (reversible via git revert)
  Gate:    ALL 6 boundary conditions below must be TRUE

TIER 3 — PRIVILEGED (always requires explicit "yes, proceed" from user)
  Actions: Patching ecc-router/SKILL.md or ecc-self-improve/SKILL.md itself
           Modifying any file outside codex-ecc-custom/skills/
           Adding fixtures that disable existing safety checks
           Applying > 3 patches in a single session
  Risk:    High — could alter safety boundaries of the flywheel itself
  Gate:    Explicit user confirmation required, no exceptions
```

---

## Tier 2 Boundary Conditions (ALL must be TRUE to proceed without user prompt)

```
BC-1  LEARNINGS.md has ≥ 3 unpromoted entries
BC-2  At least one entry has frequency ≥ 3
BC-3  At least one entry has confidence = "high"
BC-4  All entries to be mined have "conversation_evidence" field populated (non-empty)
BC-5  Regression fixture suite passes: runner.py exits 0
BC-6  Git working tree is clean (no uncommitted changes to SKILL.md files)
```

If ANY condition is false → display which conditions failed → stop → suggest `/ecc-self-improve --dry-run` instead.

---

## Scope of Permitted Modifications

| File/Directory | Tier 0 | Tier 1 | Tier 2 | Tier 3 |
|---------------|--------|--------|--------|--------|
| `LEARNINGS.md` (append only) | ✅ | ✅ | ✅ | ✅ |
| `skills/*/SKILL.md` (append paragraph only) | ❌ | ❌ | ✅ | ✅ |
| `skills/ecc-self-improve/tests/fixtures.json` | ❌ | ❌ | ✅ | ✅ |
| `skills/ecc-router/SKILL.md` | ❌ | ❌ | ❌ | ✅ |
| `skills/ecc-self-improve/SKILL.md` | ❌ | ❌ | ❌ | ✅ |
| `CLAUDE.md` or `~/.gemini/` | ❌ | ❌ | ❌ | ❌ (never auto) |
| Any `.toml` agent file | ❌ | ❌ | ❌ | ❌ (never auto) |
| Any file outside `codex-ecc-custom/` | ❌ | ❌ | ❌ | ❌ (never auto) |

---

## Patch Constraints (enforced at Stage 2 + Stage 3)

1. **Size:** Maximum 4 lines per patch paragraph
2. **Operation:** APPEND ONLY — no deletions, no rewrites of existing content
3. **Tagging:** Every patch must include `[auto-patch]` and the date
4. **Provenance:** Every factual claim in a patch must be traceable to a LEARNINGS.md entry
5. **Commit:** Patches are committed atomically with tag `[self-improve]` for audit
6. **Reversal:** Any patch can be undone with `git revert <hash>`

---

## Hallucination Prevention Contract

By proceeding with Tier 2+, the agent agrees to:

- **Never invent** LEARNINGS.md entries not grounded in actual session events
- **Never fabricate** evidence for `conversation_evidence` fields
- **Never apply** a patch that references data not present in LEARNINGS.md
- **Reject** any LEARNINGS entry where `conversation_evidence` is empty or generic
- **Log** all blocked patches to LEARNINGS.md with `"promoted": false, "block_reason": "..."`

---

## Audit Trail

Every Tier 2 action creates:
- A `git commit` tagged `[self-improve]` on the patched SKILL.md
- A `"promoted": true` flag on the mined LEARNINGS.md entries
- A runner.py audit entry accessible via `runner.py --audit`

To view full audit history:
```bash
cd /Users/sanjayb/codex-ecc-custom
git log --grep="self-improve" --oneline
```

---

## How This Document Is Used

`ecc-self-improve` reads this file at **Stage 0 (Pre-Flight)** before any Tier 2+ action.
It displays the relevant tier, boundary condition results, and requires either:
- All Tier 2 boundary conditions to pass (auto-proceed), or
- Explicit user "yes, proceed" for Tier 3 actions

If this file is missing → `ecc-self-improve` HARD STOPS with:
```
❌ TERMS.md not found at skills/ecc-self-improve/TERMS.md
   Cannot proceed with Tier 2+ action without Terms & Conditions.
   Run: git status to check if file was deleted
```
