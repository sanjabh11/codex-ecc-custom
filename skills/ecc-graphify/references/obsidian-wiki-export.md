# Obsidian and Wiki Export

This reference is intentionally split between the **verified local path** and
exports that need a sidecar, optional dependency, or a fresh upstream audit.
The examples use explicit subcommands from the locally audited Graphify 0.9.33
CLI.

## Verified Obsidian export

Build a graph for a source directory, then export it to a new target directory:

```bash
SOURCE="$HOME/Documents/Obsidian Vault/HermesBrain/raw"
GRAPH="$SOURCE/graphify-out/graph.json"
TARGET="$HOME/Documents/Obsidian Vault/HermesBrain/graphify-export"

graphify "$SOURCE" --no-viz
graphify export obsidian --graph "$GRAPH" --dir "$TARGET"
```

The exporter writes node notes, frontmatter, wikilinks, and
`$TARGET/graph.canvas`. Prefer a new or explicitly approved target directory;
an export is a filesystem mutation even though the graph build is local.

Do not append the obsolete Obsidian option to the path shortcut as a substitute
for the export subcommand. On the audited install, the path shortcut extracts
the graph but does not perform the Obsidian export. The skill shorthand
`/graphify ... --obsidian` is an agent workflow request, not a guaranteed raw
CLI flag.

## Vault safety

- Never export directly over a working vault without approval.
- Check the target path and existing files before writing.
- Keep `SCHEMA.md` and user-authored notes outside the generated target unless
  the user explicitly wants a merge.
- Preserve the exporter ownership manifest so later Graphify versions can
  distinguish generated notes from user notes.
- Treat the result as a generated artifact; inspect a small sample before
  integrating it into the canonical vault.

## Wiki export: currently unverified

The CLI exposes `graphify export wiki --graph PATH`, but the command requires a
matching `.graphify_analysis.json` sidecar with current community/node IDs. A
code-only `--no-cluster` build does not satisfy that precondition, and the
audited local run also exposed a stale-analysis failure. Therefore this is not
part of the bounded “green” proof.

Before using it, fail closed if the sidecar is absent, regenerate the graph and
analysis together, and verify the output in a temporary directory:

```bash
GRAPH="/path/to/graphify-out/graph.json"
test -s "$(dirname "$GRAPH")/.graphify_analysis.json" || {
  echo "wiki export blocked: matching analysis sidecar is missing" >&2
  exit 1
}
graphify export wiki --graph "$GRAPH"
```

Do not delete an existing wiki to force a rebuild. Treat stale-analysis errors
as an upstream/runtime issue requiring a fresh audit.

## Export choice

| Need | Command | Local proof status |
|---|---|---|
| Queryable graph | `graphify-out/graph.json` | Verified |
| Obsidian notes/canvas | `graphify export obsidian --graph ... --dir ...` | Verified on a temporary code graph |
| Agent wiki | `graphify export wiki --graph ...` | Sidecar-dependent; stale-analysis path unverified |
| Static summary | `graphify-out/GRAPH_REPORT.md` | Build-dependent |

The JSON graph remains the safest default for precise queries. Use Obsidian
export for human navigation only after checking the generated notes.
