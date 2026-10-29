# Query, Path, and Explain — Advanced Patterns

## Query Modes

### BFS (default) — Broad Context

```bash
graphify query "what connects attention to the optimizer?"
```

BFS (Breadth-First Search) traversal returns a scoped subgraph with broad context. Best for:
- "How does X work?"
- "What is the architecture of Y?"
- "Give me an overview of Z"

### DFS — Trace a Specific Path

```bash
graphify query "how does auth flow through the system?" --dfs
```

DFS (Depth-First Search) traces a specific path through the graph. Best for:
- "Trace the data flow from input to output"
- "How does X call Y?"
- "Follow the chain from A to B"

### Budget Control

```bash
graphify query "explain the architecture" --budget 1500
```

Caps the answer at N tokens. Useful when:
- Working within a context window limit
- Getting a quick summary before deep-diving
- Controlling token cost in automated pipelines

## Path Tracing

```bash
# Shortest path between two concepts
graphify path "AuthModule" "Database"

# Real output example:
# Shortest path (3 hops):
#   AuthModule --uses--> SessionStore <--references-- get_user() --references--> Database
```

Use cases:
- "How are these two modules connected?"
- "What's the dependency chain between X and Y?"
- "Find the coupling between frontend and backend"

## Node Explanation

```bash
graphify explain "SwinTransformer"

# Real output example:
# Node: SwinTransformer
#   Source:    models/swin.py L45
#   Community: 3
#   Degree:    12
#
# Connections (12):
#   --> WindowAttention [uses] [INFERRED]
#   --> PatchMerging [uses] [INFERRED]
#   <-- __init__.py [imports] [EXTRACTED]
#   ...
```

Use cases:
- "What is this class/function and what does it connect to?"
- "Explain this concept I found in the graph"
- "What depends on X?"

## Confidence Tags

Every edge in the graph carries one of three tags:

| Tag | Meaning | Trust Level |
|-----|---------|-------------|
| `EXTRACTED` | Explicit in the source (e.g., `import`, `call`, `inherits`) | High — verified by AST |
| `INFERRED` | Derived by graphify resolution (e.g., cross-file call resolution) | Medium — algorithmic inference |
| `AMBIGUOUS` | Uncertain, needs human review | Low — verify manually |

When querying, prefer `EXTRACTED` edges for definitive answers and treat `INFERRED` edges as hypotheses to verify.

## Querying Across Multiple Graphs

If you have multiple `graphify-out/` directories (e.g., from different repos), you can merge them:

```bash
graphify merge-graphs \
  ./repo1/graphify-out/graph.json \
  ./repo2/graphify-out/graph.json \
  --out ./graphify-out/merged-graph.json
graphify query "how does auth work?" --graph ./graphify-out/merged-graph.json
```

Or build separately and query each:

```bash
cd repo1 && graphify query "how does auth work?" && cd ..
cd repo2 && graphify query "how does auth work?" && cd ..
```

## Token Benchmark

Use the built-in benchmark for a corpus-specific measurement:

```bash
graphify benchmark graphify-out/graph.json
```

The benchmark compares:
- Reading all raw files into context (baseline)
- Querying the graph instead (graphify)

Token reduction is corpus- and query-dependent. Do not reuse a fixed multiplier
as a performance claim; record the benchmark output for the exact corpus.
