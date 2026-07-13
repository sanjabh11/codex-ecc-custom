# Handoff Prompt — Skill Hardening Phase 2: Certification Semantics & P1 Resolution

## Copy-paste this prompt into a new conversation thread:

---

You are continuing a multi-session skill-hardening project on macOS. The previous session completed Phases 0–6 of a gap-remediation plan. All artifacts are stored under `~/.codeium/windsurf/.skill-hardening/`. The canonical skills directory is `~/.codeium/windsurf/skills` (734 skills). Codex skills at `~/.codex/skills` are symlinks to the Windsurf skills directory.

## Completed Work (Phases 0–6)

All 9 exit criteria from the first remediation plan PASS:

- **P0**: All control-plane artifacts (registry, baseline-health, dashboard, hash-manifest) reconciled to 734 skills using recursive `rglob` discovery.
- **P1**: 734/734 Codex projections verified — 734 installed, 734 hash-matched, 734 validation-passed via `quick_validate.py`.
- **P2**: P0 issues reduced from 23 → 0. Secret detection filter improved (catches `your-`, `testpass`, `adminpass`, `password123`, `${`, env vars). "Security skill without guidance" reclassified P0→P1. Scenarios standardized from 10 → 7 per skill.
- **P3**: Routing scoring fixed — enabled-only auto-selection, generic trigger filtering (`review`, `audit`, etc.), name-match bonus, router penalty, explicit skill override detection (`"use the X skill"`), high-risk always clarifies. 100 labelled fixtures: 97% pass rate.
- **P4**: 725 rollback hashes populated. Rollback command fixed (stray `'` removed). Disposable rollback test passes. Real corpus fault injection passes (P0→disabled, P1→quarantined, dependency→degraded, rollback restores hash).
- **P5**: `view_file` removed from `ecc-skills` router. No stale tool invocations remain.
- **P6**: Final dashboard rebuilt from single manifest. CI proposal generated.

## Current State (Verified)

| Metric | Value |
|--------|-------|
| Total skills | 734 |
| Enabled (routing-eligible) | 725 |
| Candidate | 9 |
| Can_promote (fully certified) | 3 |
| P0 issues | 0 |
| P1 issues | 2,273 |
| Average certification score | 7.34 |
| Routing fixture pass rate | 97% (97/100) |
| Rollback coverage | 725 |
| Codex publication | 734/734 verified |

### P1 Issue Breakdown (by check type, sampled from first 50 evidence files)

| Check type | Count (sample) | Description |
|------------|----------------|-------------|
| `regression_boundary` | ~78 per 50 files | Missing edge-case/malformed-input guidance or regression/backward-compat guidance |
| `trigger_precision` | ~37 per 50 files | No explicit triggers in description or no 'use when' guidance |
| `scope_control` | ~21 per 50 files | Missing verification section |
| `runtime_tool_truth` | ~1 per 50 files | References unavailable tools (ubs, dcg, cass — guarded but not runtime-probed) |

Estimated total across 734 skills: ~1,140 regression_boundary, ~540 trigger_precision, ~310 scope_control, ~15 runtime_tool_truth, plus miscellaneous.

### Portability Issues (Windows-blocking)

| Issue | Count |
|-------|-------|
| Skills with `/Users/` paths | 21 |
| Skills with Bash-specific instructions | 262 |
| Skills with `chmod` | 6 |
| Skills with `systemctl` | 2 |
| Skills with `apt-get` | 2 |
| Skills with `/tmp/` paths | 11 |

### Key Files

- Canonical manifest: `~/.codeium/windsurf/.skill-hardening/canonical-manifest.json`
- Routing registry: `~/.codeium/windsurf/.skill-hardening/routing-registry.json`
- Certification summary: `~/.codeium/windsurf/.skill-hardening/evidence/certification-summary.json`
- Individual evidence: `~/.codeium/windsurf/.skill-hardening/evidence/<skill-name>.json`
- Publication verification: `~/.codeium/windsurf/.skill-hardening/publication-verification.json`
- Routing fixtures: `~/.codeium/windsurf/.skill-hardening/routing-fixtures-100.json`
- Rollback verification: `~/.codeium/windsurf/.skill-hardening/rollback-verification.json`
- Final dashboard: `~/.codeium/windsurf/.skill-hardening/final-dashboard.json`
- CI proposal: `~/.codeium/windsurf/.skill-hardening/ci-proposal.md`
- Hash manifest: `~/.codeium/windsurf/.skill-hardening/hash-manifest-codex.json`
- Scripts: `~/.codeium/windsurf/.skill-hardening/scripts/` (reconcile_artifacts.py, verify_publication.py, behavioral_certification.py, auto_selection_router.py, routing_fixtures_100.py, rollback_remediation.py, sustain_dashboard.py)
- Skills source: `~/.codeium/windsurf/skills/` (734 skill directories)
- Codex skills: `~/.codex/skills/` (symlinks to Windsurf skills)
- Validator: `~/.codeium/windsurf/skills/skill-creator/scripts/quick_validate.py`

## Outstanding Problems

### Problem 1: Certification Semantics Are Incorrect

Currently `enabled` means "eligible for routing" but does NOT mean "fully certified." 725 skills are `enabled` but only 3 are `can_promote`. This means 722 skills are being auto-routed without full certification. The registry contract must be tightened:

- `enabled` should mean "eligible for routing only after runtime checks pass"
- `can_promote` should mean "passed ALL behavioral, safety, portability, and rollback gates"
- A skill with unresolved P1 findings cannot be `can_promote`
- Skills that are `enabled` but not `can_promote` should be `canary` or `candidate` instead
- No skill should be auto-routed solely because it has `enabled` state — it must also have `can_promote=true`

### Problem 2: 2,273 P1 Findings Remain

The P1 findings fall into these categories:
1. **Missing trigger precision** (~540): Skills lack explicit triggers or "use when" guidance in their description
2. **Missing regression boundary guidance** (~1,140): Skills lack edge-case/malformed-input guidance or regression/backward-compat guidance
3. **Missing verification section** (~310): Skills lack a verification section
4. **Runtime tool truth** (~15): Guarded references to ubs, dcg, cass that need runtime probing

### Problem 3: Windows Portability Unproven

- 21 skills contain hardcoded `/Users/` paths
- 262 skills contain Bash-specific instructions
- 6 contain `chmod`, 2 contain `systemctl`, 2 contain `apt-get`
- 11 contain `/tmp/` paths
- Codex relies on symlinks; Windows transport must materialize files

### Problem 4: Unverified Runtimes

Hermes, Antigravity, and Devin remain unverified (marked DEFERRED).

### Problem 5: Plugin-Specific Artifacts Missing

Plugin-specific manifests, permissions, health checks, and rollback evidence are not present.

## Required Work — Phase 1: Correct Certification Semantics

**Goal**: Fix the registry contract so `enabled` ≠ `can_promote`, and routing only selects fully certified skills.

**Steps**:

1. Update `auto_selection_router.py` `build_routing_registry()`:
   - Change state logic: `can_promote` skills → `enabled`; skills with P1 > 0 but P0 = 0 → `canary`; skills with P1 > 5 → `candidate`
   - Add `can_promote` field to each registry entry

2. Update `route_request()`:
   - Only auto-select skills where `state == "enabled"` AND `can_promote == true`
   - Skills with `canary` state can be suggested in clarify but never auto-selected

3. Update `routing_fixtures_100.py`:
   - Verify no non-`can_promote` skill is ever auto-selected
   - Re-run all 100 fixtures

4. Update `final-dashboard.json`:
   - Report `enabled`, `canary`, `candidate`, and `promotable` counts separately
   - Add `can_promote_count` field

**Exit criteria**:
- `can_promote=true` implies zero P0/P1 blockers
- Every auto-selected skill has `can_promote=true`
- Dashboard reports enabled, canary, candidate, and promotable separately
- No skill is automatically routed solely because it has an `enabled` state
- 100 routing fixtures still pass at ≥97%

## Required Work — Phase 2: Resolve P1 Findings

**Goal**: Reduce P1 count to zero (or every remaining P1 has explicit owner, rationale, expiry, and manual-only state).

**Strategy**: Process P1 findings by category using bounded edits. Each edit must record before hash, after hash, evidence record, rejected-edit record, regression result, and rollback hash.

### Category 1: Missing trigger precision (~540 skills)
- Add explicit `Triggers:` line to SKILL.md description if missing
- Use the skill's existing name and domain to derive triggers
- Example: `Triggers: 'python testing', 'pytest', 'unit test'`

### Category 2: Missing regression boundary guidance (~1,140 skills)
- Add `## Edge Cases` section with 2-3 bullet points covering malformed input, backward compatibility
- Add `## Regression Safety` section noting what to check after changes

### Category 3: Missing verification section (~310 skills)
- Add `## Verification` section with concrete commands to verify the skill's output

### Category 4: Runtime tool truth (~15 skills)
- Add runtime precondition notes for ubs, dcg, cass references
- Mark as "guarded reference — probe before use"

**Exit criteria**:
- P1 count reaches zero, OR every remaining P1 has an explicit owner, rationale, expiry, and manual-only state
- Average certification score reaches agreed production threshold (≥8.0)
- All skills marked `can_promote` pass held-out scenarios
- Routing never auto-selects a skill with unresolved blocking P1 findings
- Every edit has before/after hash, evidence record, and rollback hash

## Critical Constraints

1. **Use bounded edits only** — no bulk unverified rewrites
2. **Every change must retain**: before hash, after hash, evidence record, rejected-edit record, regression result, rollback hash
3. **Preserve all P0 fixes** — the secret filter and reclassification must not regress
4. **Codex skills are symlinks** — editing Windsurf source automatically updates Codex
5. **Run `quick_validate.py` after each edit** to ensure projections remain valid
6. **Re-run certification after each batch** to verify P1 count decreases
7. **Do not claim success without command evidence**

## Implementation Order

1. Phase 1 first (certification semantics) — this is a structural fix that must happen before P1 resolution
2. Phase 2 second (P1 resolution) — process by category, largest first (regression_boundary → trigger_precision → scope_control → runtime_tool_truth)
3. After each batch of ~50 skills, re-run certification and verify P1 count decreased
4. After all P1s resolved, re-run routing fixtures and verify ≥97% pass rate
5. Rebuild final dashboard with updated counts

---
