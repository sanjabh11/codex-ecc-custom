---
name: ecc-router
description: Master router for custom ECC skills. Automatically detects and loads the relevant skill via view_file to bypass context limits.
---

# ECC Router

Use this skill at the beginning of any session or task to route the task to the correct custom ECC skill.

## Dynamic Routing Logic

0. **Silent Pre-Flight Check**: At session start, run a silent check against the boundary conditions:
   ```bash
   python3 /Users/sanjayb/codex-ecc-custom/skills/ecc-self-improve/tests/runner.py --boundary-check --quiet 2>/dev/null
   ```
   If it exits with `0` (READY), display a notice card before routing:
   ```
   🔄 SYSTEM NOTICE: Self-improvement is ready (unpatched systematic weaknesses exist).
      Type '/ecc-self-improve' to apply, or '/ecc-self-improve --dry-run' to preview.
   ```

1. Scan the list of custom skills in `/Users/sanjayb/codex-ecc-custom/skills/` (or search for skills prefixed with `ecc-` or matching custom names like `last30days` in the excluded skills list).
2. If the user request matches the purpose of any specific skill (e.g., `ecc-tdd` for TDD, `ecc-e2e` for E2E, `last30days` for recent research, `ecc-agent-reach` for multi-platform searching, `ecc-headroom` for token compression, `ecc-self-improve` for the self-improvement flywheel, `ecc-trace-wrap` for session wrap-up, `ecc-learn` for reviewing learnings, etc.):
   - Immediately run `view_file` on `/Users/sanjayb/codex-ecc-custom/skills/<skill-name>/SKILL.md` (or the fallback config path `/Users/sanjayb/.gemini/config/plugins/codex-ecc-custom/skills/<skill-name>/SKILL.md`) to load the full instructions.
   - Adopt and follow the loaded instructions for the remainder of the task.

## Self-Improvement Routing

Route to `ecc-self-improve` when user says any of:
- "self-improve", "improve yourself", "apply learnings", "patch skills"
- "run the flywheel", "what can you fix?", "learn from failures"
- "run flywheel", "apply patches", "commit improvements"

Route to `ecc-trace-wrap` when user says any of:
- "wrap up", "end session", "record learnings", "what did we learn?"
- "save session", "log outcomes", "record what happened"

Route to `ecc-learn` when user says any of:
- "show learnings", "review learnings", "what has the agent learned?"
- "learning summary", "what patterns did you find?", "show failures"

Route to `ecc-self-improve --dry-run` when user says any of:
- "preview patches", "show proposed patches", "dry run", "what would you patch?"

## Self-Improvement Tier Gate (Pre-Flight Display)

Before routing ANY Tier 2+ `ecc-self-improve` invocation (i.e. NOT --dry-run), display:

```
🔒 Invocation Tier: TIER 2 (Apply with Gate)
   Reading TERMS.md before proceeding...
```

Then load and briefly summarise the TERMS.md tier definition and the 6 boundary conditions.
This is non-optional. If TERMS.md cannot be read, HARD STOP with the error message defined in TERMS.md.

## Known-Weakness Pre-Flight Warning

When routing to a skill that has known LEARNINGS.md entries (unpromoted, not yet patched),
display a pre-flight warning BEFORE executing the skill:

```bash
# Quick check: does LEARNINGS.md have any unpromoted entries for this skill?
python3 -c "
import json
entries = [json.loads(l) for l in open('/Users/sanjayb/codex-ecc-custom/LEARNINGS.md') if l.strip() and not l.startswith('#')]
matches = [e for e in entries if e.get('skill_invoked') == '{skill_name}' and not e.get('promoted')]
if matches:
    print(f'WARNING: {len(matches)} known unpatched weaknesses for {skill_name}')
    for m in matches[:3]: print(f'  ⚠️  {m.get("failure_type")}: {m.get("correction")}')
" 2>/dev/null || true
```

If warnings exist, display them above the routed skill output:
```
⚠️  Known weakness in {skill}: {failure_type} — {correction}
    (Not yet patched. Run /ecc-self-improve to fix.)
```


## Global Link Verification & Zero Hallucination Rule

To prevent broken or hallucinated links (which result in 404 or "Nothing to see here" errors) across all routed tasks and searches:
- **NEVER invent status IDs, video IDs, post/comment IDs, or deep paths**.
- **Use Tool-Returned Source Links**: Only output exact URLs returned by the search tool (`search_web`, Exa, or API results) that you have verified are present in the tool's raw output.
- **Fallback to Search Query URLs**: If the exact direct link or ID is not present in the tool results, construct a search query link which is guaranteed to resolve:
  - **Twitter/X Search Link**: `https://x.com/search?q=[URL-encoded-query]`
  - **YouTube Search Link**: `https://www.youtube.com/results?search_query=[URL-encoded-query]`
  - **Reddit Search Link**: `https://www.reddit.com/search/?q=[URL-encoded-query]`
  - **General Web Search**: Use the exact URL returned in the search citation.

## Completion Tracking Requirement

Once the task is completed, you must clearly articulate the custom skills loaded and used to perform the task. End your response with a **Skills Applied Card**:

```markdown
---
🛠️ ECC Custom Skills Applied:
├─ [x] ecc-router (Master Router)
├─ [x] <skill-1> (Reason for use)
├─ [x] <skill-2> (Reason for use)
└─ Verification: [Describe checks/evidence]
---
```

