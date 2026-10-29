---
name: ecc-graphify
description: >-
  Multimodal knowledge graph builder via graphify CLI. Turns any folder of code,
  docs, PDFs, images, or video into a queryable knowledge graph with community
  detection, god nodes, and honest audit trail (EXTRACTED/INFERRED/AMBIGUOUS).
  Query with natural language, trace paths between concepts, or explain nodes.
  Discoverable through five ECC skill paths; host loader/runtime support is
  separately verified per platform.
  TRIGGER when: "knowledge graph", "graphify", "build graph", "query codebase",
  "code relationships", "trace path", "explain concept", "multimodal graph",
  "PDF knowledge graph", "image to graph", "/graphify".
  DO NOT TRIGGER when: task is about codegraph MCP (different tool), or
  understand-anything plugin (different tool), or task is trivially grep-able.
allowed-tools: Read, Write, Bash, Grep, Glob
---

# ecc-graphify — Multimodal Knowledge Graph via Graphify

> **Usage hint:** `build knowledge graph, graphify, query codebase, trace path, explain concept`

Turn any folder of code, docs, PDFs, images, or video into a persistent,
queryable knowledge graph. Measure token reduction with the corpus-specific
`graphify benchmark` output; do not assume a fixed multiplier.
Honest audit trail: every edge tagged `EXTRACTED`, `INFERRED`, or `AMBIGUOUS`.

Graphify is the Karpathy `/raw` folder solution — drop papers, tweets,
screenshots, and notes, get a graph you query instead of grep.

---

## Step 0: Health Check (Always)

Before any graphify operation, verify the CLI is available:

```bash
bash /Users/sanjayb/codex-ecc-custom/skills/ecc-graphify/scripts/graphify-health.sh --json
```

The current local contract is audited against **Graphify 0.9.33**. If the
reported version changes, rerun `tests/test_cli_contract.py` and refresh the
references before relying on any export or MCP instruction.

If `GRAPHIFY_UNAVAILABLE`:
- Do NOT run any graphify commands
- Inform user: "graphify CLI not found. Install: `uv tool install graphifyy` (note: PyPI package is `graphifyy` with double y, CLI is `graphify`)"
- Fall back to `codegraph` MCP or `understand-anything` if available for code-only graphs
- Fall back to manual file reading for multimodal content

**Note:** unhealthy ≠ empty graph. If graphify is installed but `graphify-out/graph.json` is missing, the graph just needs to be built.

---

## Step 1: Fast Path — Query Existing Graph

Before building, check if a graph already exists:

```bash
if [ -f "graphify-out/graph.json" ]; then
  echo "GRAPH_EXISTS"
  # Show graph stats
  graphify query "summary" 2>/dev/null | head -20
else
  echo "NO_GRAPH"
fi
```

If `GRAPH_EXISTS` AND the user's request is a question (not a rebuild):
- Jump to **Step 4: Query** immediately
- Do not rebuild unless user explicitly asks

---

## Step 2: Build Graph

### Basic build (current directory)

```bash
graphify . --no-viz
```

Outputs:
- `graphify-out/graph.json` — persistent graph (query anytime)
- `graphify-out/GRAPH_REPORT.md` — god nodes, surprising connections, suggested questions
- `graphify-out/graph.html` — interactive visualization (skip with `--no-viz`)

### Build with options

```bash
# Specific path
graphify ./raw --no-viz

# Deep mode — more aggressive INFERRED edge extraction
graphify extract ./raw --mode deep --no-cluster

# Incremental update — only re-extract changed files (AST-only, no LLM)
graphify update .

# Code-only (skip docs/papers/images — no LLM needed, fully local)
graphify extract . --code-only --no-cluster

# Directed graph (preserves edge direction: source→target)
graphify extract . --directed --no-cluster

# Cluster-only on existing graph (regenerate report + community labels)
graphify cluster-only .

# Label communities with LLM (or --no-label for placeholder names)
graphify label . --no-label
```

### Large corpus handling

If the corpus has >500 files or >2M words, graphify will show a narrowing prompt with the top 5 subdirectories by file count. Wait for the user to choose before proceeding.

For large corpora, consider:
- `--no-viz` — skip HTML generation (saves time)
- `--no-cluster` — skip Leiden clustering (saves time, no community labels)
- Run on a subdirectory first, then merge with `--update`

---

## Step 3: Multimodal Extraction

Graphify handles these file types:

| Type | Extensions | Extraction Method |
|------|-----------|-------------------|
| Code | `.py .ts .js .go .rs .java .c .cpp .rb .cs .kt .scala .php .swift .lua .zig .ps1 .ex .m` | tree-sitter AST (local, no LLM) |
| Docs | `.md .txt .rst` | LLM semantic pass (concepts + relationships) |
| Papers | `.pdf` | Citation mining + concept extraction (LLM) |
| Images | `.png .jpg .webp .gif` | Vision extraction — screenshots, diagrams, any language (LLM) |
| Video/Audio | `.mp4 .mp3 .wav .webm` | Whisper transcription → text extraction (LLM) |

**Important:** Code extraction is local (tree-sitter, no API cost). Docs, papers, images, and video use the harness model or a configured API key for the semantic pass. Warn the user about token cost for large multimodal corpora.

For video/audio, graphify transcribes first (Whisper), then treats transcripts as docs. See `references/multimodal-extraction.md` for details.

---

## Step 4: Query the Graph

Once `graphify-out/graph.json` exists, query it instead of reading files:

```bash
# Natural language question (BFS traversal — broad context)
graphify query "what connects attention to the optimizer?"

# DFS — trace a specific path
graphify query "how does auth flow through the system?" --dfs

# Cap answer at N tokens
graphify query "explain the architecture" --budget 1500
```

### Path tracing

```bash
# Shortest path between two concepts
graphify path "AuthModule" "Database"
```

### Node explanation

```bash
# Plain-language explanation of a specific node
graphify explain "SwinTransformer"
```

Every edge carries a confidence tag:
- `EXTRACTED` — explicit in the source
- `INFERRED` — derived by graphify resolution
- `AMBIGUOUS` — uncertain, needs human review

---

## Step 5: Export and Integration

### Verified CLI exports (audited against v0.9.33)

```bash
# D3 collapsible tree HTML
graphify tree --output graphify-out/GRAPH_TREE.html

# Mermaid call-flow HTML (architecture diagrams)
graphify export callflow-html

# God nodes (architectural hubs — most connected)
graphify god-nodes --top 10

# Token benchmark (reduction vs naive full-corpus read)
graphify benchmark

# Affected nodes (reverse traversal — what does X impact?)
graphify affected "AuthModule" --depth 2
```

### Obsidian vault export

Use the explicit export subcommand. Do not pass `--obsidian` to the path
shortcut: in the audited CLI that shortcut performs extraction but does not
perform the export.

```bash
graphify export obsidian \
  --graph graphify-out/graph.json \
  --dir graphify-out/obsidian
```

See `references/obsidian-wiki-export.md` for the full agent workflow.

### Neo4j / FalkorDB export

Generate offline Cypher first; this does not contact a database:

```bash
graphify export neo4j --graph graphify-out/graph.json
graphify export falkordb --graph graphify-out/graph.json
```

Remote `--push` is an externally side-effecting operation. It requires the
optional database extra, an explicitly approved target, and a separate live
verification. Never place credentials in command arguments or skill examples.

See `references/mcp-neo4j-integration.md` for details.

### MCP server

```bash
# Use the interpreter that owns the graphify installation.
GRAPHIFY_PY="$(head -1 "$(command -v graphify)" | sed 's/^#!//')"
"$GRAPHIFY_PY" -m graphify.serve graphify-out/graph.json
``` 

The MCP process loads a graph snapshot at startup. Restart it after
`graphify update` or a rebuild. HTTP transport and API-key configuration are
manual runtime steps; do not claim them from a local CLI check.

### Optional or currently unverified exports

- `graphify export wiki` requires the graph's analysis sidecar; a
  `--no-cluster` code-only build does not provide that precondition.
- `graphify export svg` requires the optional SVG/matplotlib dependency, which
  is not part of the audited local install.
- `graphify export graphml` is recognized by v0.9.33 but crashed on a valid
  local code-only graph during this audit. Treat it as blocked until an
  upstream version is independently re-tested.

---

## Step 6: Maintenance

### Incremental update (AST-only, no LLM cost)

```bash
graphify update .          # re-extract changed code files only (SHA256 cache)
graphify update . --force  # full re-scan, overwrite even if fewer nodes
```

### Watch mode

```bash
graphify watch .  # auto-rebuild on code changes (AST-only, no LLM cost)
```

### Git post-commit hook

```bash
graphify hook install  # rebuilds graph after every commit
```

This mutates repository hook/config state. Inspect existing hooks and obtain
explicit approval before installing or uninstalling it.

Check for existing hooks before installing:
```bash
cat .git/hooks/post-commit 2>/dev/null | grep -q graphify && echo "HOOK_EXISTS" || echo "NO_HOOK"
```

### Full rebuild

```bash
graphify extract . --force --no-viz  # full rebuild; review token/cost impact
```

---

## Step 7: Report Results

Format graphify output for the user:

```
📊 Knowledge Graph (graphify)

Corpus: {total_files} files · ~{total_words} words
Graph: {node_count} nodes, {edge_count} edges
  EXTRACTED: {extracted_count} (explicit in source)
  INFERRED:  {inferred_count} (derived by resolution)
  AMBIGUOUS: {ambiguous_count} (needs review)

God nodes: {top_5_god_nodes}
Communities: {community_count} (Leiden)

Outputs:
  graphify-out/graph.json       — queryable graph
  graphify-out/GRAPH_REPORT.md  — highlights report
  graphify-out/graph.html       — interactive viz

Query: graphify query "<your question>"
Path:  graphify path "<A>" "<B>"
```

---

## Auto-Revocation (ECC)

All graphify calls are guarded by the health check in Step 0. Graphify is an **Advisory** tool — it enhances but never blocks.

### Tool Taxonomy

| Class | Tool | Gating Behavior |
|-------|------|----------------|
| **Core** (never gate) | `python3`, `git`, `cat`, `echo`, `grep`, `find` | Always available — no check needed |
| **Advisory** (gate + silent skip) | `graphify` CLI | `command -v graphify` health check. If absent: skip silently, fall back to codegraph MCP or manual file reading. Never block. |
| **Advisory** (fallback tier 1) | `codegraph` MCP | If graphify unavailable AND codegraph MCP available: use `codegraph_context`, `codegraph_search` for code-only graphs. No multimodal. |
| **Advisory** (fallback tier 2) | `understand-anything` plugin | If graphify AND codegraph unavailable: use `/understand` for structural code graph + dashboard. No multimodal, no query/path/explain. |
| **Advisory** (fallback tier 3) | Manual file reading | Last resort: Read tool for PDFs, images, docs. No graph, no relationships, no query. |

### Pattern for Advisory tools:

1. Check graphify availability with `graphify-health.sh --json`; this is local-first and bounded.
2. If absent: print install hint (`uv tool install graphifyy`), skip silently, fall back to tier 1/2/3
3. Preserve command exit status when proof is required; do not hide failures behind `2>/dev/null || true`.
4. For an advisory workflow, report the failed command and degrade to the fallback tier rather than fabricating graph evidence.
5. The graph is always optional — the agent proceeds without it if unavailable.

### Fallback Decision Tree

```
graphify available?
├── YES → use graphify (build/query/path/explain/multimodal)
└── NO → codegraph MCP available?
    ├── YES → use codegraph (code-only, AST-based, no multimodal)
    └── NO → understand-anything available?
        ├── YES → use /understand (structural code graph + dashboard)
        └── NO → manual file reading (Read tool, no graph)
```

---

## Trigger Precedence

If both `ecc-router` and implicit invocation fire for the same query:
1. **Router wins** — explicit routing takes precedence
2. **codegraph vs graphify:** `codegraph` MCP is for code symbols (AST-based, always-on). `graphify` is for multimodal knowledge graphs (PDFs, images, docs + code). Use graphify when multimodal content is involved.
3. **understand-anything vs graphify:** `understand-anything` produces an interactive dashboard with a structural code graph. `graphify` produces a queryable JSON graph with community detection across multimodal content. Use graphify when you need to query relationships or when non-code files are involved.

---

## Platform Notes and proof boundary

The ECC installer provides **five physical discovery symlinks**. That is not
proof that five host loaders, hooks, or always-on integrations are active.
Authenticated host-loader/runtime proof remains manual.

| Platform | Skill Location | Parallel Extraction | Always-on | Hooks |
|----------|---------------|---------------------|-----------|-------|
| Claude Code | `~/.claude/skills/ecc-graphify/` | Host-dependent | Not installed by ECC wrapper | Not installed by ECC wrapper |
| Codex | `~/.codex/skills/ecc-graphify/` | Host-dependent; config required | `AGENTS.md` only if separately configured | Not installed by ECC wrapper |
| Devin | `~/.devin/skills/ecc-graphify/` | Host-dependent | Not installed by ECC wrapper | None from ECC wrapper |
| Generic Agents / Antigravity path | `~/.agents/skills/ecc-graphify/` | Host-dependent | Not installed by ECC wrapper | None from ECC wrapper |
| Windsurf | `~/.codeium/windsurf/skills/ecc-graphify/` | Host-dependent | Not installed by ECC wrapper | None from ECC wrapper |

For platform-specific installation, see `references/platform-install.md`.

---

## References

- `references/query-path-explain.md` — Advanced query patterns, DFS vs BFS, budget control
- `references/multimodal-extraction.md` — PDF, image, video extraction details and token cost
- `references/obsidian-wiki-export.md` — Obsidian vault and wiki export configuration
- `references/mcp-neo4j-integration.md` — MCP server mode, Neo4j, FalkorDB integration
- `references/platform-install.md` — Multi-platform installation and symlink management
- `schemas/cli-contract.json` — machine-readable version/proof boundary for the audited CLI
