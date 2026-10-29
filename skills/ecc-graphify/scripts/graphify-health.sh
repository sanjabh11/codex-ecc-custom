#!/usr/bin/env bash
# graphify-health.sh — Health check and interpreter detection for graphify CLI
# Usage: bash graphify-health.sh [--json]
# Exit 0 = healthy, 1 = unavailable

set -euo pipefail

JSON_MODE=false
[ "${1:-}" = "--json" ] && JSON_MODE=true

# Check if graphify binary exists
GRAPHIFY_BIN=""
if command -v graphify >/dev/null 2>&1; then
    GRAPHIFY_BIN="$(command -v graphify)"
elif [ -x "$HOME/.local/bin/graphify" ]; then
    GRAPHIFY_BIN="$HOME/.local/bin/graphify"
fi

if [ -z "$GRAPHIFY_BIN" ]; then
    if [ "$JSON_MODE" = true ]; then
        echo '{"healthy":false,"reason":"graphify binary not found","install":"uv tool install graphifyy"}'
    else
        echo "GRAPHIFY_UNAVAILABLE: graphify binary not found"
        echo "Install: uv tool install graphifyy (PyPI package is 'graphifyy', CLI is 'graphify')"
    fi
    exit 1
fi

# Detect the local Python interpreter graphify uses. Do not invoke package
# managers here: package-manager discovery may perform network resolution and
# turn a health check into an unbounded operation.
PYTHON=""
# 1. Read shebang from graphify binary (pipx and direct pip installs)
if [ -z "$PYTHON" ]; then
    _SHEBANG=$(head -1 "$GRAPHIFY_BIN" | tr -d '#!')
    case "$_SHEBANG" in
        *[!a-zA-Z0-9/_.@-]*) ;;
        *) "$_SHEBANG" -c "import graphify" 2>/dev/null && PYTHON="$_SHEBANG" ;;
    esac
fi
# 2. Fall back to the local python3 on PATH
if [ -z "$PYTHON" ]; then
    if python3 -c "import graphify" 2>/dev/null; then
        PYTHON="python3"
    fi
fi

if [ -z "$PYTHON" ]; then
    if [ "$JSON_MODE" = true ]; then
        echo '{"healthy":false,"reason":"graphify module not importable from any Python","binary":"'"$GRAPHIFY_BIN"'"}'
    else
        echo "GRAPHIFY_UNAVAILABLE: binary found at $GRAPHIFY_BIN but module not importable"
        echo "Try: uv tool install --reinstall graphifyy"
    fi
    exit 1
fi

# Verify the same binary that was discovered and get its version. This avoids
# reporting a healthy Python module when the executable itself is stale or
# broken.
VERSION_OUTPUT=$("$GRAPHIFY_BIN" --version 2>/dev/null || true)
if [ -z "$VERSION_OUTPUT" ]; then
    if [ "$JSON_MODE" = true ]; then
        echo '{"healthy":false,"reason":"graphify binary did not return a version","binary":"'"$GRAPHIFY_BIN"'"}'
    else
        echo "GRAPHIFY_UNAVAILABLE: graphify binary did not return a version"
    fi
    exit 1
fi
VERSION=$(printf '%s\n' "$VERSION_OUTPUT" | head -1)

# Check for existing graph in current directory
GRAPH_EXISTS="false"
GRAPH_NODES=0
GRAPH_EDGES=0
if [ -f "graphify-out/graph.json" ]; then
    GRAPH_EXISTS="true"
    GRAPH_NODES=$("$PYTHON" -c "import json; g=json.load(open('graphify-out/graph.json')); print(len(g.get('nodes',[])))" 2>/dev/null || echo 0)
    GRAPH_EDGES=$("$PYTHON" -c "import json; g=json.load(open('graphify-out/graph.json')); print(len(g.get('edges', g.get('links',[]))))" 2>/dev/null || echo 0)
fi

if [ "$JSON_MODE" = true ]; then
    cat <<EOF
{"healthy":true,"binary":"$GRAPHIFY_BIN","python":"$PYTHON","version":"$VERSION","graph_exists":$GRAPH_EXISTS,"graph_nodes":$GRAPH_NODES,"graph_edges":$GRAPH_EDGES}
EOF
else
    echo "GRAPHIFY_READY"
    echo "  binary:  $GRAPHIFY_BIN"
    echo "  python:  $PYTHON"
    echo "  version: $VERSION"
    if [ "$GRAPH_EXISTS" = true ]; then
        echo "  graph:   $GRAPH_NODES nodes, $GRAPH_EDGES edges"
    else
        echo "  graph:   none (run 'graphify . --no-viz' to build)"
    fi
fi
exit 0
