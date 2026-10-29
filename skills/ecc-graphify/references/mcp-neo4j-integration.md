# MCP, Neo4j, and FalkorDB Integration

This reference distinguishes commands accepted by the audited local CLI from
optional extras and remote side effects. No database or host integration is
proven by the ECC symlink installation.

## MCP server

The audited CLI does not expose a top-level MCP flag. The MCP entrypoint is the
installed package module:

```bash
GRAPHIFY_PY="$(head -1 "$(command -v graphify)" | sed 's/^#!//')"
"$GRAPHIFY_PY" -m graphify.serve graphify-out/graph.json
```

If the `mcp` extra is not installed, install it in the same isolated Graphify
environment before attempting a live server:

```bash
uv tool install --upgrade 'graphifyy[mcp]'
```

The stdio server is a process boundary and loads a graph snapshot at startup.
Restart it after `graphify update` or a rebuild. A shared HTTP server is a
manual runtime operation and must bind locally by default or require an API
key:

```bash
"$GRAPHIFY_PY" -m graphify.serve graphify-out/graph.json \
  --transport http --host 127.0.0.1 --port 8080
```

Do not bind an unauthenticated server to a public interface. Do not claim MCP
runtime proof from `python -m graphify.serve --help`; a real client handshake
is still manual.

Example client configuration uses the same interpreter and graph path:

```json
{
  "mcpServers": {
    "graphify": {
      "command": "/absolute/path/to/graphify-python",
      "args": ["-m", "graphify.serve", "/absolute/path/to/graphify-out/graph.json"]
    }
  }
}
```

Replace the placeholder with the shebang interpreter discovered above. Never
put secrets in this file.

## Offline Cypher export

The database exporters can produce a local Cypher artifact without contacting a
database. This path was verified on a temporary graph:

```bash
GRAPH="graphify-out/graph.json"
graphify export neo4j --graph "$GRAPH"
graphify export falkordb --graph "$GRAPH"
```

Both commands write `cypher.txt` beside the graph. The second command may
overwrite the first artifact, so copy or hash the file if both outputs are
needed.

## Remote push: manual gate only

The CLI exposes `--push`, but pushing is an external mutation and requires the
matching optional extra, target approval, credentials, and a live smoke test.
Use environment-managed secrets; do not put passwords in shell history or
skill documentation:

```bash
export NEO4J_PASSWORD='provided-by-secret-manager'
graphify export neo4j --graph "$GRAPH" \
  --push 'bolt://127.0.0.1:7687' --user 'neo4j'
```

The same pattern applies to FalkorDB with `FALKORDB_PASSWORD` and a reviewed
FalkorDB target. A local Cypher file is `verified-local`; a successful remote
push is `live` only after an authenticated read-back confirms the intended
graph and target.

## Optional exports with current limitations

| Export | Invocation | Current boundary |
|---|---|---|
| Neo4j Cypher | `graphify export neo4j --graph ...` | Verified offline |
| FalkorDB Cypher | `graphify export falkordb --graph ...` | Verified offline |
| Neo4j/FalkorDB push | `... --push ...` | Manual/remote; not run |
| SVG | `graphify export svg --graph ...` | Optional SVG/matplotlib dependency; not installed locally |
| GraphML | `graphify export graphml --graph ...` | v0.9.33 crashed on a valid local graph; blocked pending re-audit |

Do not silently fall back from a failed exporter to a fabricated artifact.
