# ECC Self-Improvement — 3-Tier Memory System

## Architecture Overview

The self-improvement flywheel uses three memory tiers in priority order:

```
┌─────────────────────────────────────────────────────┐
│  TIER A — Local (always available)                  │
│  File: /Users/sanjayb/codex-ecc-custom/LEARNINGS.md │
│  Format: JSON lines (one failure entry per line)     │
│  Scope: Project-scoped (codex-ecc-custom only)       │
│  Written by: ecc-trace-wrap                          │
│  Read by: ecc-self-improve, ecc-learn               │
└────────────────────┬────────────────────────────────┘
                     │ (if cm is healthy)
┌────────────────────▼────────────────────────────────┐
│  TIER B — Session Memory (cm, if installed)         │
│  Purpose: Cross-session continuity                   │
│  Stores: What was improved, blocked, or pending      │
│  Written by: ecc-trace-wrap Step 5 (advisory)        │
│  Read by: ecc-learn Step 0 (memory recall)           │
│  Health check: cm context "health" --json 2>/dev/null│
└────────────────────┬────────────────────────────────┘
                     │ (if cass is healthy)
┌────────────────────▼────────────────────────────────┐
│  TIER C — Semantic Search (cass, if installed)      │
│  Purpose: Find similar patterns across all sessions  │
│  Queries: cass search "failure_type" --robot         │
│  Cross-ref: Strengthens LEARNINGS.md signal           │
│  Health check: cass health --json 2>/dev/null         │
└─────────────────────────────────────────────────────┘
```

---

## Tier A: LEARNINGS.md (Core Memory)

**Always used. No health check needed.**

### Schema (each JSON line)
```json
{
  "date": "YYYY-MM-DD",
  "session_id": "short-id",
  "skill_invoked": "ecc-agent-reach",
  "failure_type": "hallucinated_url | wrong_tool | misread_intent | broken_pattern | other",
  "context": "One sentence: what the agent was doing",
  "correction": "One sentence: what should happen instead",
  "conversation_evidence": "Direct quote or tool output proving the failure occurred",
  "frequency": 1,
  "confidence": "high | medium | low",
  "proposed_fix_location": "skills/ecc-agent-reach/SKILL.md#verification-section",
  "promoted": false
}
```

### Key fields added in v2:
- **`conversation_evidence`** (NEW, REQUIRED): A verbatim quote or exact tool output from the session. Empty = entry rejected by Judge Gate A.

### Commands
```bash
# Count unpromoted entries
python3 -c "
import json
entries = [json.loads(l) for l in open('LEARNINGS.md') if l.strip() and not l.startswith('#')]
unpromoted = [e for e in entries if not e.get('promoted')]
print(f'{len(unpromoted)} unpromoted entries')
"

# Find high-confidence systematic entries
python3 -c "
import json
from collections import defaultdict
entries = [json.loads(l) for l in open('LEARNINGS.md') if l.strip() and not l.startswith('#')]
groups = defaultdict(list)
for e in entries:
    if not e.get('promoted'):
        groups[(e.get('skill_invoked'), e.get('failure_type'))].append(e)
for (skill, ftype), es in groups.items():
    freq = sum(e.get('frequency',1) for e in es)
    conf = [e.get('confidence') for e in es]
    if freq >= 3 and 'high' in conf:
        print(f'READY: [{skill}] {ftype} — {freq}x — evidence: {all(e.get(\"conversation_evidence\") for e in es)}')
" /Users/sanjayb/codex-ecc-custom/LEARNINGS.md
```

---

## Tier B: Session Memory (cm)

**Optional. Used for cross-session continuity.**

### Health Check (run before any Tier B operation)
```bash
cm_available() {
  command -v cm >/dev/null 2>&1 && cm context "health" --json 2>/dev/null | grep -q '"status":"ok"'
}
```

### Write (after ecc-trace-wrap)
```bash
# Write a summary to cm after trace-wrap completes
if cm_available; then
  cm context "ecc-self-improve [$(date +%Y-%m-%d)]: recorded ${N} entries; failures: ${failure_types}; pending patches: ${pending_count}" --json 2>/dev/null || true
fi
```
Note: `|| true` — cm failure is advisory, never blocking.

### Read (at start of ecc-learn)
```bash
# Recall last self-improve session context
if cm_available; then
  cm context "show ecc-self-improve history" --json 2>/dev/null
fi
```

### What cm stores
- Date of last trace-wrap
- Number of entries logged
- Whether any patches were applied last session
- Which skills were improved
- Pending patches that didn't pass the gate (so user can investigate)

---

## Tier C: Semantic Search (cass)

**Optional. Used to strengthen signal with cross-session patterns.**

### Health Check
```bash
cass_available() {
  command -v cass >/dev/null 2>&1 && cass health --json 2>/dev/null | grep -q '"healthy":true'
}
```

### Usage in ecc-self-improve Stage 1 (mining)
```bash
# Cross-reference a mined weakness with historical cass context
if cass_available; then
  cass search "${failure_type}" --robot --limit 5 --fields minimal 2>/dev/null
fi
```

If cass returns matching sessions → increases confidence in the pattern.
If cass returns nothing → keep LEARNINGS.md signal, reduce confidence by one level.

### Projection into patch decision
- cass confirms pattern → add to patch evidence
- cass contradicts pattern (shows it's rare) → downgrade to `"confidence": "medium"`, require user to approve even in Tier 2

---

## Memory Scope Policy

| Memory Store | Scope | Searchable Across Projects |
|-------------|-------|--------------------------|
| LEARNINGS.md | Project-only (`codex-ecc-custom/`) | ❌ No |
| cm context | Session-specific key | ❌ No (namespaced by key) |
| cass search | All indexed sessions | ✅ Yes — cross-project |

> [!NOTE]
> cass is the only tier that crosses project boundaries. This is intentional — it helps detect if the same failure pattern appears in unrelated work sessions. It reads only; never writes to other project memory.

---

## Graceful Degradation

If both cm and cass are unavailable, the flywheel runs entirely on Tier A (LEARNINGS.md).
This is the baseline design. Tier B and C are enhancements only.

```
All tiers healthy:  Maximum signal quality + cross-session recall
Tier A + B only:    Good signal, session continuity preserved
Tier A only:        Baseline — still safe and functional
No tiers:           Hard stop — LEARNINGS.md is required (create with ecc-trace-wrap)
```
