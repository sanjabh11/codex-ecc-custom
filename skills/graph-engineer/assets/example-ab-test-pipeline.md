# Example: A/B Creative Variant Testing

A graph for generating and testing A/B creative variants using the diamond
pattern for parallel variant generation, independent quality reviewers, and
a human gate before committing budget.

## Diagram

```
                    ┌── Generate-Variant-A ──┐
                    │                        │
Plan-Campaign ─────┤── Generate-Variant-B ──├── Synthesize-Variants ── Human-Gate ── Commit-Budget
                    │                        │
                    └── Generate-Variant-C ──┘
```

## Graph Definition

```json
{
  "name": "ab-test-creative-pipeline",
  "description": "Generate parallel A/B creative variants, review each independently, merge survivors, and gate human approval before committing ad budget",
  "diagram": "Plan-Campaign → [Generate-Variant-A, Generate-Variant-B, Generate-Variant-C] → [Review-Compliance, Review-Brand-Fit] → Synthesize-Variants → Human-Gate → Commit-Budget",
  "nodes": [
    {
      "id": "plan-campaign",
      "type": "planner",
      "responsibility": "Define the campaign objective, target audience, and creative constraints for variant generation",
      "inputs": [],
      "outputs": ["campaign-brief.json", "creative-constraints.json"]
    },
    {
      "id": "generate-variant-a",
      "type": "worker",
      "responsibility": "Generate creative variant A using the campaign brief and a bold angle",
      "inputs": ["plan-campaign"],
      "outputs": ["variant-a.json"],
      "loop_cap": 2
    },
    {
      "id": "generate-variant-b",
      "type": "worker",
      "responsibility": "Generate creative variant B using the campaign brief and an emotional angle",
      "inputs": ["plan-campaign"],
      "outputs": ["variant-b.json"],
      "loop_cap": 2
    },
    {
      "id": "generate-variant-c",
      "type": "worker",
      "responsibility": "Generate creative variant C using the campaign brief and a data-driven angle",
      "inputs": ["plan-campaign"],
      "outputs": ["variant-c.json"],
      "loop_cap": 2
    },
    {
      "id": "review-compliance",
      "type": "reviewer",
      "responsibility": "Check whether all variants comply with advertising platform policies",
      "inputs": ["generate-variant-a", "generate-variant-b", "generate-variant-c"],
      "outputs": ["compliance-review.json"],
      "review_questions": ["Do all variants comply with the target advertising platform's content policies?"]
    },
    {
      "id": "review-brand-fit",
      "type": "reviewer",
      "responsibility": "Check whether all variants align with the brand voice and positioning",
      "inputs": ["generate-variant-a", "generate-variant-b", "generate-variant-c"],
      "outputs": ["brand-fit-review.json"],
      "review_questions": ["Do all variants align with the established brand voice and positioning guidelines?"]
    },
    {
      "id": "synthesize-variants",
      "type": "synthesizer",
      "responsibility": "Merge the surviving variants (those that passed both reviews) into a final test plan",
      "inputs": ["review-compliance", "review-brand-fit"],
      "outputs": ["test-plan.json"]
    },
    {
      "id": "human-gate-budget",
      "type": "human-gate",
      "responsibility": "Human reviews the test plan and approves budget allocation before campaign launch",
      "inputs": ["synthesize-variants"],
      "outputs": ["budget-approval.json"],
      "human_gate_action": "send"
    }
  ],
  "edges": [
    {"from": "plan-campaign", "to": "generate-variant-a", "dependency_reason": "Variant generator needs the campaign brief and constraints to produce a creative", "type": "data"},
    {"from": "plan-campaign", "to": "generate-variant-b", "dependency_reason": "Variant generator needs the campaign brief and constraints to produce a creative", "type": "data"},
    {"from": "plan-campaign", "to": "generate-variant-c", "dependency_reason": "Variant generator needs the campaign brief and constraints to produce a creative", "type": "data"},
    {"from": "generate-variant-a", "to": "review-compliance", "dependency_reason": "Compliance reviewer needs all variants to check policy adherence", "type": "data"},
    {"from": "generate-variant-b", "to": "review-compliance", "dependency_reason": "Compliance reviewer needs all variants to check policy adherence", "type": "data"},
    {"from": "generate-variant-c", "to": "review-compliance", "dependency_reason": "Compliance reviewer needs all variants to check policy adherence", "type": "data"},
    {"from": "generate-variant-a", "to": "review-brand-fit", "dependency_reason": "Brand-fit reviewer needs all variants to check voice alignment", "type": "data"},
    {"from": "generate-variant-b", "to": "review-brand-fit", "dependency_reason": "Brand-fit reviewer needs all variants to check voice alignment", "type": "data"},
    {"from": "generate-variant-c", "to": "review-brand-fit", "dependency_reason": "Brand-fit reviewer needs all variants to check voice alignment", "type": "data"},
    {"from": "review-compliance", "to": "synthesize-variants", "dependency_reason": "Synthesizer needs both review results to determine which variants survived", "type": "data"},
    {"from": "review-brand-fit", "to": "synthesize-variants", "dependency_reason": "Synthesizer needs both review results to determine which variants survived", "type": "data"},
    {"from": "review-compliance", "to": "generate-variant-a", "dependency_reason": "Failed compliance review routes feedback back to the variant generator for revision", "type": "failure"},
    {"from": "review-compliance", "to": "generate-variant-b", "dependency_reason": "Failed compliance review routes feedback back to the variant generator for revision", "type": "failure"},
    {"from": "review-compliance", "to": "generate-variant-c", "dependency_reason": "Failed compliance review routes feedback back to the variant generator for revision", "type": "failure"},
    {"from": "synthesize-variants", "to": "human-gate-budget", "dependency_reason": "Human needs the test plan to approve budget allocation", "type": "data"}
  ],
  "caps": {
    "max_review_rounds": 2,
    "max_spawned_agents": 5,
    "max_total_agents": 10
  },
  "human_gates": [
    {"position": "human-gate-budget", "action": "send"}
  ]
}
```

## Key Design Notes

- **Diamond pattern**: Three creative variants generated in parallel, each
  with a different angle (bold, emotional, data-driven). Workers don't see
  each other's work — true independence.
- **Independent reviewers**: Two reviewers with different questions —
  compliance (policy) and brand-fit (voice). No overlapping blind spots.
- **Failure routing**: Compliance failures route back to the specific variant
  generator that failed, not all of them.
- **Human gate**: Placed before budget commit — spending ad budget is
  expensive to undo. The human decides which variants to test and how much
  budget to allocate.
- **Quote from @codewithimanshu on the original thread**: "The diamond
  pattern is perfect for A/B testing creative variants or campaign angles.
  Each parallel branch can pull its own data, then merge into a single report
  for the human gate before budget commits."
