# Failure Routing

How to design explicit failure paths in agent graphs.

## Core Principle

Per @VibeMarketer_: "Turn failures into explicit paths. A failed check
shouldn't end the run or disappear inside a prompt. Route the feedback back
to the worker, retry, then check again."

## Failure Routing Pattern

```
Worker → Reviewer → [PASS] → Synthesizer (or next node)
                   → [FAIL] → Worker (with structured feedback) → Reviewer → ...
                                                                    → [FAIL after cap] → Human-gate
```

## Rules

1. **A failed review is not a crash.** The graph continues — it routes the
   failure as input to the next step.
2. **Feedback is structured.** The reviewer outputs: what failed, where
   (file:line, section, claim), and what to fix. The worker uses this as
   additional input for its retry.
3. **The worker retries.** The worker runs again with the original input
   plus the feedback. It does not start from scratch — it revises.
4. **The reviewer checks again.** The same reviewer (or a fresh one) checks
   the revised output.
5. **Cap the loop.** After `max_review_rounds` (default 3), route to a
   human-gate instead of looping forever.
6. **Never swallow a failure.** A failure that disappears inside a prompt
   is worse than a crash — the graph continues with broken output.

## Failure Edge in Graph Definition

```json
{
  "from": "review-correctness",
  "to": "draft-post",
  "dependency_reason": "Failed correctness review routes feedback back to the drafter for revision",
  "type": "failure"
}
```

The `type: "failure"` field distinguishes failure edges from normal data
edges. This makes failure paths visible in the graph diagram and
enforceable by the validator.

## What NOT to Do

| Anti-pattern | Why it fails |
|---|---|
| End the run on first failure | One bad review kills the entire pipeline — no recovery |
| Swallow failure in a prompt | The failure disappears — the graph continues with broken output |
| Infinite retry loop | Expensive recursion — the worker keeps making the same mistake |
| No structured feedback | The worker can't fix what it doesn't understand |
| Route failure to a different worker | The original worker has the most context to fix its own output |

## Human Gate as Fallback

When a loop hits its cap, the failure routes to a human-gate. The human
can:
- **Approve with caveats** — accept the imperfect output with noted issues
- **Reject with feedback** — provide manual guidance and let the worker retry
- **Abort the run** — stop the entire graph

This prevents runaway costs while still giving the workflow a chance to
succeed with human judgment.
