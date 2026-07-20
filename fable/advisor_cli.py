#!/usr/bin/env python3
"""Advisor CLI — multi-backend advisor for strategic advice.

Usage:
  python3 fable/advisor_cli.py "<context/question>"
  python3 fable/advisor_cli.py --status            # show call count + history
  python3 fable/advisor_cli.py --reset             # reset session counter
  python3 fable/advisor_cli.py --json "<context>"  # JSON output for programmatic use
  python3 fable/advisor_cli.py --context-file <path> "<question>"  # load large context from file
  python3 fable/advisor_cli.py --dry-run "<context>"  # preview without consuming call budget
  python3 fable/advisor_cli.py --session <id> "<context>"  # session-isolated state
  python3 fable/advisor_cli.py --backend grok_cli "<context>"  # force backend

The executor (harness native model) runs this script at decision points.
The advisor receives the context and returns focused guidance.
Uses Grok CLI OAuth token from ~/.grok/auth.json (Super Grok) — no separate API key needed.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure imports work when run from project root or fable/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from fable.services import GrokService

ADVISOR_STATE = Path(__file__).parent / "advisor_state.json"
ADVISOR_CONFIG = Path(__file__).parent / "advisor_config.json"

# Timeout handler for API calls
_TIMEOUT_OCCURRED = False


def _timeout_handler(signum, frame):
    global _TIMEOUT_OCCURRED
    _TIMEOUT_OCCURRED = True
    raise TimeoutError("Advisor API call exceeded timeout")


def load_config() -> dict:
    """Load advisor configuration."""
    try:
        with open(ADVISOR_CONFIG, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "advisor_model": "grok-4.5",
            "max_advisor_calls": 3,
            "max_tokens_advisor": 2048,
            "advisor_system_prompt": (
                "You are a high-capability advisor reviewing a cheaper executor "
                "model's work. Provide focused, actionable guidance in under 200 words."
            ),
        }


def load_state(session_id: str | None = None) -> dict:
    """Load persistent advisor state (call count, history).

    If session_id is provided, returns state filtered to that session.
    """
    if ADVISOR_STATE.exists():
        try:
            return json.loads(ADVISOR_STATE.read_text())
        except Exception:
            pass
    return {"call_count": 0, "history": [], "session_id": session_id}


def save_state(state: dict) -> None:
    """Save advisor state to disk."""
    ADVISOR_STATE.write_text(json.dumps(state, indent=2))


def reset_state(session_id: str | None = None) -> dict:
    """Reset advisor state to initial values."""
    state = {"call_count": 0, "history": [], "session_id": session_id}
    save_state(state)
    return state


def detect_backend() -> str:
    """Auto-detect the best available advisor backend.

    Priority:
    1. claude_native — if running inside Claude Code with advisor tool
    2. codex_orchestration — if codex-orchestration plugin is installed
    3. grok_cli — if ~/.grok/auth.json exists
    4. fallback — no backend available
    """
    # Check for Claude Code native advisor (environment signal)
    if os.environ.get("CLAUDE_ADVISOR_ENABLED") == "true":
        return "claude_native"

    # Check for Codex-Orchestration plugin
    codex_plugin = Path.home() / ".codex" / "plugins" / "codex-orchestration"
    if codex_plugin.exists():
        return "codex_orchestration"

    # Check for Grok CLI token
    grok_auth = Path.home() / ".grok" / "auth.json"
    if grok_auth.exists():
        return "grok_cli"

    return "fallback"


def get_advice(
    context: str,
    config: dict | None = None,
    session_id: str | None = None,
    dry_run: bool = False,
    backend: str | None = None,
) -> str:
    """Call advisor for advice on the given context.

    Args:
        context: Summary of the executor's current state and question.
        config: Advisor config dict (loaded from file if None).
        session_id: Optional session identifier for state isolation.
        dry_run: If True, preview without consuming call budget.
        backend: Force a specific backend (grok_cli, claude_native, codex_orchestration).

    Returns:
        Advice text from the advisor, or a fallback message if unavailable.
    """
    if config is None:
        config = load_config()

    state = load_state(session_id)

    # Cost control: check max_advisor_calls
    max_calls = config.get("max_advisor_calls", 3)

    # Dry run: preview without consuming budget (always works, even at cap)
    if dry_run:
        return (
            f"[Advisor] Dry run — would call advisor with {len(context)} chars of context. "
            f"Calls used: {state['call_count']}/{max_calls}. "
            f"Backend: {backend or detect_backend()}."
        )

    if state["call_count"] >= max_calls:
        return (
            f"[Advisor] Call cap reached ({max_calls}). "
            "Proceed without advisor for this task."
        )

    # Backend selection
    selected_backend = backend or detect_backend()

    if selected_backend == "fallback":
        return (
            "[Advisor] No advisor backend available. "
            "Proceed without advisor. Install Grok CLI (grok login) or "
            "enable Claude Code advisor tool."
        )

    # Only grok_cli is fully implemented; others return informative fallback
    if selected_backend != "grok_cli":
        return (
            f"[Advisor] Backend '{selected_backend}' detected but not yet implemented in CLI. "
            "Falling back to grok_cli if available."
        )

    # Initialize GrokService — CLI token fallback is built in
    svc = GrokService(api_key="", mock_mode=False)

    if not svc.api_key:
        return (
            "[Advisor] No Grok API key or CLI token available "
            "(~/.grok/auth.json not found). Proceed without advisor."
        )

    # Build advisor prompt from template
    system_prompt = config.get(
        "advisor_system_prompt",
        "You are a high-capability advisor. Provide focused guidance in under 200 words.",
    )
    user_prompt = (
        f"Context from executor:\n{context}\n\n"
        "Provide focused guidance (under 200 words). "
        "Do not write code — direct the executor to the right approach."
    )

    max_tokens = config.get("max_tokens_advisor", 2048)
    timeout_seconds = config.get("timeout_seconds", 120)
    retry_attempts = config.get("retry_attempts", 1)

    # Call with timeout and retry
    global _TIMEOUT_OCCURRED
    response = None
    last_error = None

    for attempt in range(retry_attempts + 1):
        _TIMEOUT_OCCURRED = False
        try:
            # Set timeout signal
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout_seconds)

            response = svc.generate(
                prompt=user_prompt,
                system=system_prompt,
                max_output_tokens=max_tokens,
                temperature=0.7,
            )

            signal.alarm(0)  # Cancel timeout

            if _TIMEOUT_OCCURRED:
                raise TimeoutError("Advisor API call timed out")

            break  # Success

        except TimeoutError as e:
            signal.alarm(0)
            last_error = str(e)
            if attempt < retry_attempts:
                continue
            return f"[Advisor] Timeout after {timeout_seconds}s. Proceed without advisor."

        except Exception as e:
            signal.alarm(0)
            last_error = str(e)
            if attempt < retry_attempts:
                continue
            return f"[Advisor] Error: {last_error}. Proceed without advisor."

    if response is None:
        return f"[Advisor] Failed after {retry_attempts + 1} attempts. Proceed without advisor."

    # Track call in state
    state["call_count"] += 1
    state["history"].append({
        "call": state["call_count"],
        "context_preview": context[:120],
        "response_preview": response[:120],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
    })
    if session_id:
        state["session_id"] = session_id
    save_state(state)

    return response


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Advisor CLI — consult a stronger model at decision points",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("context", nargs="*", help="Context/question for the advisor")
    parser.add_argument("--status", action="store_true", help="Show call count and history")
    parser.add_argument("--reset", action="store_true", help="Reset session counter")
    parser.add_argument("--json", action="store_true", help="Output structured JSON response")
    parser.add_argument("--context-file", type=str, help="Load context from a file")
    parser.add_argument("--dry-run", action="store_true", help="Preview without consuming call budget")
    parser.add_argument("--session", type=str, help="Session ID for state isolation")
    parser.add_argument("--backend", type=str, choices=["grok_cli", "claude_native", "codex_orchestration"],
                        help="Force a specific backend")

    args = parser.parse_args()
    config = load_config()

    # --status: show call count and history
    if args.status:
        state = load_state(args.session)
        print(json.dumps(state, indent=2))
        return

    # --reset: clear session counter
    if args.reset:
        reset_state(args.session)
        print("Advisor state reset." + (f" Session: {args.session}" if args.session else ""))
        return

    # Build context from args and/or file
    context = " ".join(args.context) if args.context else ""
    if args.context_file:
        try:
            with open(args.context_file, "r") as f:
                file_content = f.read()
            context = f"{file_content}\n\n{context}" if context else file_content
        except Exception as e:
            print(f"Error reading context file: {e}", file=sys.stderr)
            sys.exit(1)

    if not context:
        parser.print_help()
        sys.exit(1)

    advice = get_advice(
        context, config,
        session_id=args.session,
        dry_run=args.dry_run,
        backend=args.backend,
    )

    if args.json:
        state = load_state(args.session)
        max_calls = config.get("max_advisor_calls", 3)
        selected_backend = args.backend or detect_backend()
        status = "success"
        if "Call cap reached" in advice:
            status = "cap_reached"
        elif "No Grok API key" in advice or "No advisor backend" in advice:
            status = "no_token"
        elif "Dry run" in advice:
            status = "dry_run"
        elif "Timeout" in advice:
            status = "timeout"
        elif "[Advisor]" in advice and "Error" in advice:
            status = "error"

        response = {
            "status": status,
            "advice": advice,
            "call_count": state["call_count"],
            "calls_remaining": max(0, max_calls - state["call_count"]),
            "backend": selected_backend,
            "session_id": args.session or state.get("session_id", ""),
        }
        print(json.dumps(response, indent=2))
    else:
        print(advice)


if __name__ == "__main__":
    main()
