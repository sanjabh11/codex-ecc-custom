# Example: Content Creation Pipeline

A marketing content creation graph using the diamond pattern for parallel
research, independent reviewers, and a human gate before publish.

## Diagram

```
                    ┌── Research-Competitors ──┐
                    │                          │
Plan-Content ──────┤── Research-Audience ─────├── Synthesize-Research ── Draft-Post ──┬── Review-Correctness ──┐
                    │                          │                                       │                        │
                    └── Research-Trends ───────┘                                       ├── Review-Currency ────┤
                                                                                         │                        ├── Synthesize-Reviews ── Human-Gate ── Publish
                                                                                         └── Review-Source ──────┘
```

## Graph Definition

```json
{
  "name": "content-creation-pipeline",
  "description": "Research, draft, review, and publish a marketing blog post with parallel research and independent reviewers",
  "diagram": "Plan-Content → [Research-Competitors, Research-Audience, Research-Trends] → Synthesize-Research → Draft-Post → [Review-Correctness, Review-Currency, Review-Source] → Synthesize-Reviews → Human-Gate → Publish",
  "nodes": [
    {
      "id": "plan-content",
      "type": "planner",
      "responsibility": "Decompose the blog post objective into research angles, draft spec, and review dimensions",
      "inputs": [],
      "outputs": ["research-brief.json", "draft-spec.json", "review-criteria.json"]
    },
    {
      "id": "research-competitors",
      "type": "worker",
      "responsibility": "Research competitor pricing and positioning for the target topic",
      "inputs": ["plan-content"],
      "outputs": ["competitor-research.json"],
      "loop_cap": 2
    },
    {
      "id": "research-audience",
      "type": "worker",
      "responsibility": "Research target audience pain points and language patterns",
      "inputs": ["plan-content"],
      "outputs": ["audience-research.json"],
      "loop_cap": 2
    },
    {
      "id": "research-trends",
      "type": "worker",
      "responsibility": "Research current trends and news for the target topic in the last 30 days",
      "inputs": ["plan-content"],
      "outputs": ["trends-research.json"],
      "loop_cap": 2
    },
    {
      "id": "synthesize-research",
      "type": "synthesizer",
      "responsibility": "Merge the three research outputs into one research brief for the drafter",
      "inputs": ["research-competitors", "research-audience", "research-trends"],
      "outputs": ["research-brief-merged.json"]
    },
    {
      "id": "draft-post",
      "type": "worker",
      "responsibility": "Write the blog post draft using the merged research brief",
      "inputs": ["synthesize-research"],
      "outputs": ["draft-post.md"],
      "loop_cap": 3
    },
    {
      "id": "review-correctness",
      "type": "reviewer",
      "responsibility": "Check whether every factual claim in the draft is verifiable",
      "inputs": ["draft-post"],
      "outputs": ["correctness-review.json"],
      "review_questions": ["Is every factual claim in the draft verifiable with a cited source?"]
    },
    {
      "id": "review-currency",
      "type": "reviewer",
      "responsibility": "Check whether the information in the draft is current within the last 30 days",
      "inputs": ["draft-post"],
      "outputs": ["currency-review.json"],
      "review_questions": ["Is all time-sensitive information in the draft current within the last 30 days?"]
    },
    {
      "id": "review-source",
      "type": "reviewer",
      "responsibility": "Check whether every cited source in the draft is real and accessible",
      "inputs": ["draft-post"],
      "outputs": ["source-review.json"],
      "review_questions": ["Is every cited source in the draft a real, accessible URL or document?"]
    },
    {
      "id": "synthesize-reviews",
      "type": "synthesizer",
      "responsibility": "Merge the three review results into a single pass-or-fail decision with feedback",
      "inputs": ["review-correctness", "review-currency", "review-source"],
      "outputs": ["review-summary.json"]
    },
    {
      "id": "human-gate-publish",
      "type": "human-gate",
      "responsibility": "Human reviews the final draft and review summary before publishing",
      "inputs": ["synthesize-reviews"],
      "outputs": ["approval-decision.json"],
      "human_gate_action": "publish"
    }
  ],
  "edges": [
    {"from": "plan-content", "to": "research-competitors", "dependency_reason": "Workers need the research brief to know what to research", "type": "data"},
    {"from": "plan-content", "to": "research-audience", "dependency_reason": "Workers need the research brief to know what to research", "type": "data"},
    {"from": "plan-content", "to": "research-trends", "dependency_reason": "Workers need the research brief to know what to research", "type": "data"},
    {"from": "research-competitors", "to": "synthesize-research", "dependency_reason": "Synthesizer needs all three research outputs to merge", "type": "data"},
    {"from": "research-audience", "to": "synthesize-research", "dependency_reason": "Synthesizer needs all three research outputs to merge", "type": "data"},
    {"from": "research-trends", "to": "synthesize-research", "dependency_reason": "Synthesizer needs all three research outputs to merge", "type": "data"},
    {"from": "synthesize-research", "to": "draft-post", "dependency_reason": "Drafter needs the merged research to write the post", "type": "data"},
    {"from": "draft-post", "to": "review-correctness", "dependency_reason": "Reviewer needs the draft to check factual claims", "type": "data"},
    {"from": "draft-post", "to": "review-currency", "dependency_reason": "Reviewer needs the draft to check information freshness", "type": "data"},
    {"from": "draft-post", "to": "review-source", "dependency_reason": "Reviewer needs the draft to check source validity", "type": "data"},
    {"from": "review-correctness", "to": "synthesize-reviews", "dependency_reason": "Synthesizer needs all review results to make a pass/fail decision", "type": "data"},
    {"from": "review-currency", "to": "synthesize-reviews", "dependency_reason": "Synthesizer needs all review results to make a pass/fail decision", "type": "data"},
    {"from": "review-source", "to": "synthesize-reviews", "dependency_reason": "Synthesizer needs all review results to make a pass/fail decision", "type": "data"},
    {"from": "review-correctness", "to": "draft-post", "dependency_reason": "Failed correctness review routes feedback back to the drafter for revision", "type": "failure"},
    {"from": "review-currency", "to": "draft-post", "dependency_reason": "Failed currency review routes feedback back to the drafter for revision", "type": "failure"},
    {"from": "review-source", "to": "draft-post", "dependency_reason": "Failed source review routes feedback back to the drafter for revision", "type": "failure"},
    {"from": "synthesize-reviews", "to": "human-gate-publish", "dependency_reason": "Human gate needs the review summary to make an informed approval decision", "type": "data"}
  ],
  "caps": {
    "max_review_rounds": 3,
    "max_spawned_agents": 8,
    "max_total_agents": 20
  },
  "human_gates": [
    {"position": "human-gate-publish", "action": "publish"}
  ]
}
```

## Key Design Notes

- **Diamond pattern**: Three research workers run in parallel, each with an
  independent angle. They don't see each other's work.
- **Independent reviewers**: Three reviewers each ask a different question —
  correctness, currency, source validity. No overlapping blind spots.
- **Failure routing**: Each reviewer has a failure edge back to `draft-post`.
  If a review fails, the draft is revised and re-reviewed.
- **Loop cap**: `draft-post` has `loop_cap: 3` — after 3 failed review rounds,
  the run routes to the human gate instead of looping forever.
- **Human gate**: Placed immediately before publish — the only
  expensive-to-undo action in this graph.
