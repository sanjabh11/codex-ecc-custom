# Prompt Audit Notes

| Area | Problem | Fix in this skill |
|---|---|---|
| Role overlap | The draft duplicated existing ECC workflows | This skill becomes a thin orchestrator wrapper instead of a second policy stack |
| Tool assumptions | The draft assumed subagents are always available | Subagents are optional and gated by actual platform support |
| Verification | The draft used vague critic language | The skill requires evidence-based verification artifacts |
| Safety | The draft overreached on destructive-change policy | The skill requires explicit approval plus a backup plan for hard-to-reverse work |
| Persistence | The draft insisted on updating notes every time | The skill makes persistence conditional on decision durability |
| Confidence | The draft used an arbitrary confidence threshold | The skill replaces that with explicit blockers and unverified status |

## Usage Shape

- Suitable for multi-step code changes, repo audits, refactors, and planning-heavy support.
- Not suitable as a universal always-on persona for every short answer.
- Not a replacement for existing plan, test, review, or verification skills.
