#!/usr/bin/env python3
"""Advisor CLI — calls Grok 4.5 for strategic advice.

Usage:
  python3 fable/advisor_cli.py "<context/question>"
  python3 fable/advisor_cli.py --status   # show call count + history
  python3 fable/advisor_cli.py --reset    # reset session counter

The executor (harness native model) runs this script at decision points.
The advisor (Grok 4.5) receives the context and returns focused guidance.
No API keys needed — uses Grok CLI token from ~/.grok/auth.json (Super Grok).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure imports work when run from project root or fable/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from fable.services import GrokService

ADVISOR_STATE = Path(__file__).parent / "advisor_state.json"
ADVISOR_CONFIG = Path(__file__).parent / "advisor_config.json"


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


def load_state() -> dict:
    """Load persistent advisor state (call count, history)."""
    if ADVISOR_STATE.exists():
        try:
            return json.loads(ADVISOR_STATE.read_text())
        except Exception:
            pass
    return {"call_count": 0, "history": []}


def save_state(state: dict) -> None:
    """Save advisor state to disk."""
    ADVISOR_STATE.write_text(json.dumps(state, indent=2))


def reset_state() -> dict:
    """Reset advisor state to initial values."""
    state = {"call_count": 0, "history": []}
    save_state(state)
    return state


def get_advice(context: str, config: dict | None = None) -> str:
    """Call Grok 4.5 for advice on the given context.

    Args:
        context: Summary of the executor's current state and question.
        config: Advisor config dict (loaded from file if None).

    Returns:
        Advice text from Grok 4.5, or a fallback message if unavailable.
    """
    if config is None:
        config = load_config()

    state = load_state()

    # Cost control: check max_advisor_calls
    max_calls = config.get("max_advisor_calls", 3)
    if state["call_count"] >= max_calls:
        return (
            f"[Advisor] Call cap reached ({max_calls}). "
            "Proceed without advisor for this task."
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

    response = svc.generate(
        prompt=user_prompt,
        system=system_prompt,
        max_output_tokens=max_tokens,
        temperature=0.7,
    )

    # Track call in state
    state["call_count"] += 1
    state["history"].append({
        "call": state["call_count"],
        "context_preview": context[:120],
        "response_preview": response[:120],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    save_state(state)

    return response


def main() -> None:
    """CLI entry point."""
    config = load_config()

    # --status: show call count and history
    if "--status" in sys.argv:
        state = load_state()
        print(json.dumps(state, indent=2))
        return

    # --reset: clear session counter
    if "--reset" in sys.argv:
        reset_state()
        print("Advisor state reset.")
        return

    # Normal mode: get advice for the given context
    context = " ".join(sys.argv[1:])
    if not context:
        print(
            "Usage: python3 fable/advisor_cli.py \"<context/question>\"\n"
            "       python3 fable/advisor_cli.py --status\n"
            "       python3 fable/advisor_cli.py --reset"
        )
        sys.exit(1)

    advice = get_advice(context, config)
    print(advice)


if __name__ == "__main__":
    main()
