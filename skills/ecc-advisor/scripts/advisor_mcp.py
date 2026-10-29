#!/usr/bin/env python3
"""ECC Advisor — stdio MCP server.

Exposes the fable advisor as proper MCP tools so harnesses that only
surface MCP connectors (e.g. Codex) can call the advisor directly instead
of discovering the skill and shelling out to call_advisor.sh.

Tools:
  advisor(context, session?)  -> advice text from the configured backend
  advisor_status()            -> call count, backend, revocation state
  advisor_probe()             -> timed health check of gateway endpoints

Protocol: newline-delimited JSON-RPC 2.0 over stdin/stdout (MCP stdio).
Stdlib only — no dependencies.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_CLI = Path.home() / "codex-ecc-custom" / "fable" / "advisor_cli.py"
_TIMEOUT_S = 110  # slightly above the advisor's own 90s wall-clock budget
_MAX_OUTPUT = 64_000

TOOLS = [
    {
        "name": "advisor",
        "description": (
            "Consult the ECC advisor (Jev/Vercel AI Gateway) for a second "
            "opinion at decision points — before committing to an approach, "
            "when stuck, or before declaring done. Pass a concise context: "
            "task, findings so far, and the specific decision or question."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "context": {
                    "type": "string",
                    "description": "Task context + the decision or question to review.",
                },
                "session": {
                    "type": "string",
                    "description": "Optional session id tagged into advisor history.",
                },
            },
            "required": ["context"],
        },
    },
    {
        "name": "advisor_status",
        "description": (
            "Show advisor call count, remaining budget, detected backend, "
            "and revocation state. Consumes no call budget."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "advisor_probe",
        "description": (
            "Timed health check of every advisor gateway endpoint "
            "(typesafe eval, gemini chat, gpt-4o fallback, vercel eval). "
            "Use when the advisor seems slow or unavailable. Consumes no budget."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def _run_cli(*args: str) -> str:
    if not _CLI.is_file():
        return f"[advisor-mcp] advisor_cli.py not found at {_CLI}"
    env = dict(os.environ)
    try:
        proc = subprocess.run(
            [sys.executable, str(_CLI), *args],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_S,
            env=env,
        )
        out = proc.stdout.strip() or proc.stderr.strip()
        if proc.returncode != 0 and not out:
            out = f"[advisor-mcp] advisor_cli exited {proc.returncode} with no output"
        return out[:_MAX_OUTPUT]
    except subprocess.TimeoutExpired:
        return f"[advisor-mcp] advisor timed out after {_TIMEOUT_S}s"
    except Exception as e:  # noqa: BLE001 — surface as tool text, never crash the server
        return f"[advisor-mcp] invocation failed: {e}"


def _tool_text(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}], "isError": False}


def _handle_tool_call(params: dict) -> dict:
    name = params.get("name", "")
    args = params.get("arguments") or {}

    if name == "advisor":
        context = str(args.get("context", "")).strip()
        if not context:
            return _tool_text("[advisor-mcp] 'context' argument is required")
        cli_args = ["--json"]
        session = str(args.get("session", "")).strip()
        if session:
            cli_args += ["--session", session]
        cli_args.append(context)
        return _tool_text(_run_cli(*cli_args))

    if name == "advisor_status":
        return _tool_text(_run_cli("--status"))

    if name == "advisor_probe":
        return _tool_text(_run_cli("--probe"))

    return {
        "content": [{"type": "text", "text": f"unknown tool: {name}"}],
        "isError": True,
    }


def _respond(msg_id, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main() -> None:
    server_info = {"name": "ecc-advisor", "version": "1.0.0"}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict):
            continue

        method = msg.get("method")
        msg_id = msg.get("id")
        params = msg.get("params") or {}

        # Notifications have no id and expect no response.
        if msg_id is None:
            continue

        if method == "initialize":
            _respond(msg_id, {
                "protocolVersion": params.get("protocolVersion", "2025-03-26"),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": server_info,
            })
        elif method == "ping":
            _respond(msg_id, {})
        elif method == "tools/list":
            _respond(msg_id, {"tools": TOOLS})
        elif method == "tools/call":
            _respond(msg_id, _handle_tool_call(params))
        else:
            _respond(msg_id, error={
                "code": -32601,
                "message": f"method not found: {method}",
            })


if __name__ == "__main__":
    main()
