---
name: ecc-loop-start
description: Codex adaptation of ECC `/loop-start`. Codex adaptation of ECC /loop-start.
---

# ecc-loop-start

Use this skill when the user is asking for the ECC `/loop-start` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/loop-start` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `autonomous-loops`
- `enterprise-agent-ops`

## Workflow

1. Restate the user's goal in the language of the `/loop-start` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

- None for the baseline guidance path.

## Loop Completion Hook — Auto-Invocation with Boundary Conditions

When a loop completes (all iterations done, goal achieved, or loop explicitly terminated),
automatically run the following sequence:

### Step 1: Record session outcomes (always)
```
Invoke: ecc-trace-wrap
Purpose: Record what succeeded, failed, and was discovered this loop.
Result: Entries appended to LEARNINGS.md with conversation_evidence.
```

### Step 2: Check auto-improvement boundary conditions

Run this check against the current LEARNINGS.md state:

```bash
python3 -c "
import json
from collections import defaultdict

entries = []
with open('/Users/sanjayb/codex-ecc-custom/LEARNINGS.md') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            try: entries.append(json.loads(line))
            except: pass

unpromoted = [e for e in entries if not e.get('promoted')]
groups = defaultdict(list)
for e in unpromoted:
    groups[(e.get('skill_invoked'), e.get('failure_type'))].append(e)

bc1 = len(unpromoted) >= 3
bc2 = any(sum(e.get('frequency',1) for e in es) >= 3 for es in groups.values())
bc3 = any(e.get('confidence') == 'high' for e in unpromoted)
bc4 = all(e.get('conversation_evidence') for e in unpromoted)

ready = bc1 and bc2 and bc3 and bc4
pending = len(unpromoted)
print(f'READY:{ready}|PENDING:{pending}|BC1:{bc1}|BC2:{bc2}|BC3:{bc3}|BC4:{bc4}')
" 2>&1
```

### Step 3: Display readiness notification

**If READY=True (Tier 2 threshold met):**
```
🔄 Self-Improvement Ready!

{N} systematic patterns found in LEARNINGS.md meeting Tier 2 threshold:
  ✓ BC-1: ≥ 3 unpromoted entries ({N} found)
  ✓ BC-2: At least one failure occurred ≥ 3 times
  ✓ BC-3: At least one high-confidence entry
  ✓ BC-4: All entries grounded with conversation_evidence

Options:
  ▶ Run /ecc-self-improve --dry-run   (preview patches without applying)
  ▶ Run /ecc-self-improve              (mine → propose → gate → commit)
  ▶ Run /ecc-learn                     (review what was recorded this session)
```

**If READY=False (threshold not yet met):**
```
📊 Session wrapped. {N} learnings recorded.

Progress to next auto-improvement threshold:
  {icon} BC-1: ≥ 3 unpromoted entries — {N} found {remaining note}
  {icon} BC-2: At least one failure ≥ 3x — {status}
  {icon} BC-3: High-confidence entry — {status}
  {icon} BC-4: All entries have evidence — {status}

Keep using /ecc-trace-wrap after sessions. When all 4 conditions are met,
the system will notify you to run /ecc-self-improve.
```

**CRITICAL:** This hook NEVER auto-commits patches. It only:
1. Runs `ecc-trace-wrap` (records session outcomes to LEARNINGS.md)
2. Checks boundary conditions
3. Displays a readiness notification

Auto-commit requires the user to explicitly run `/ecc-self-improve`.
Skip this entire hook if user says "no wrap-up" or "skip learning".

## Upstream Source

- Command file: `loop-start.md`
- Original description: Codex adaptation of ECC /loop-start.
