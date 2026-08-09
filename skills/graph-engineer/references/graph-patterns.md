# Graph Patterns

Reference guide for choosing the right graph pattern for your workflow.

## Diamond Pattern

**Use when:** A problem splits into 2-5 independent angles.

```
        ┌── Worker A ──┐
Planner ──┤── Worker B ──├── Synthesizer
        └── Worker C ──┘
```

**Rules:**
- Workers run in parallel without seeing each other's work.
- Each worker has its own reviewer (or shared reviewers that check each independently).
- The synthesizer merges only the outputs that passed review.
- Drop outputs that failed review — do not merge broken work.

**Example:** Content research (competitors, audience, trends) → merge into one brief.

## Linear Chain

**Use when:** Each step genuinely depends on the full output of the previous step.

```
Step A → Step B → Step C → Output
```

**Rules:**
- Every edge has a real dependency reason.
- No parallelism possible — each step needs the prior step's complete output.
- This is NOT a graph — it's a pipeline. Consider whether one agent could do it cheaper.

**Example:** Read spec → implement code → write tests (each needs the prior step's full output).

## Diamond with Review Loop

**Use when:** The diamond pattern's workers need review with retry.

```
        ┌── Worker A ── Reviewer A ──┐
Planner ──┤── Worker B ── Reviewer B ──├── Synthesizer
        └── Worker C ── Reviewer C ──┘
```

**Rules:**
- Each worker has its own reviewer.
- Failed review routes back to the worker with feedback.
- Loop cap limits retries (default 3).
- After cap, route to human-gate.

**Example:** Draft post → review correctness/currency/source → revise → re-review.

## Fan-out / Fan-in (Wide Diamond)

**Use when:** Many independent workers (5+) each handle one slice.

```
              ┌── Worker 1 ──┐
              ├── Worker 2 ──┤
Orchestrator ──┤── Worker 3 ──├── Synthesizer
              ├── ...        ┤
              └── Worker N ──┘
```

**Rules:**
- Cap spawned agents (default 8).
- Each worker handles a non-overlapping slice.
- Synthesizer merges all outputs.
- Use for large-scale file-by-file audits.

**Example:** Fan-out audit where each worker reads 5-8 files and reports findings.

## When NOT to Use a Graph

Per @VibeMarketer_: "Graphs buy breadth, not better judgment. If every step
needs the full context from the step before it, one agent will usually be
cheaper and better."

**Use one agent instead when:**
- Each step depends on the full output of the previous step.
- The task is a single coherent reasoning chain.
- The cost of orchestration exceeds the cost of one good agent doing it linearly.
- There are no independent angles to exploit.
- There are no separate review dimensions that a single agent would miss.
