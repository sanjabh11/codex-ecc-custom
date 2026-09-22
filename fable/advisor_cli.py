#!/usr/bin/env python3
"""Advisor CLI — multi-backend advisor for strategic advice.

Usage:
  python3 "$(git rev-parse --show-toplevel)/fable/advisor_cli.py" "<context/question>"
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
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None  # Windows fallback

# Ensure imports work when run from project root or fable/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from fable.services import GrokService, JevGatewayService

# FABLE_DIR env var allows overriding the fable directory location.
# This enables the advisor to work from other repos or skill directories.
# When not set, defaults to the directory containing this script.
_FABLE_DIR = Path(os.environ.get("FABLE_DIR", "")).resolve() if os.environ.get("FABLE_DIR") else Path(__file__).parent

ADVISOR_STATE = _FABLE_DIR / "advisor_state.json"
ADVISOR_CONFIG = _FABLE_DIR / "advisor_config.json"

# Limits
MAX_CONTEXT_CHARS = 32_000  # Prevent excessively large context from being passed
MAX_HISTORY_ENTRIES = 50    # Prune history to prevent unbounded growth
STATE_VERSION = 1           # State file schema version

# Auto-reset periods (maps config value to timedelta)
RESET_PERIODS = {
    "none": None,
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
    "monthly": timedelta(days=30),
}

# Timeout handler for API calls
_TIMEOUT_OCCURRED = False
_CONFIG_LOAD_FAILED = False


def _timeout_handler(signum, frame):
    global _TIMEOUT_OCCURRED
    _TIMEOUT_OCCURRED = True
    raise TimeoutError("Advisor API call exceeded timeout")


def load_config() -> dict:
    """Load advisor configuration, failing closed when it is unavailable."""
    global _CONFIG_LOAD_FAILED
    try:
        with open(ADVISOR_CONFIG, "r") as f:
            config = json.load(f)
        if not isinstance(config, dict):
            raise ValueError("advisor config must be a JSON object")
        _CONFIG_LOAD_FAILED = False
        return config
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        _CONFIG_LOAD_FAILED = True
        return {
            "advisor_model": "grok-4.6",
            "max_advisor_calls": 30,
            "max_tokens_advisor": 4096,
            "advisor_system_prompt": (
                "You are a high-capability advisor reviewing a cheaper executor "
                "model's work. Provide focused, actionable guidance in under 200 words."
            ),
            "revoked": True,
            "revocation_reason": "advisor configuration is unavailable",
            "revoked_until": None,
        }


def save_config(config: dict) -> None:
    """Persist advisor configuration atomically."""
    tmp_path = ADVISOR_CONFIG.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(config, indent=2) + "\n")
    os.replace(tmp_path, ADVISOR_CONFIG)


def revocation_status(config: dict) -> tuple[bool, str]:
    """Return whether the shared advisor policy currently revokes calls."""
    if _CONFIG_LOAD_FAILED:
        return True, "advisor configuration is unavailable"

    env_revoked = os.environ.get("ECC_ADVISOR_REVOKED", "").strip().lower()
    if env_revoked in {"1", "true", "yes", "on"}:
        return True, "ECC_ADVISOR_REVOKED is enabled"

    if bool(config.get("revoked", False)):
        reason = str(config.get("revocation_reason", "")).strip()
        return True, reason or "global advisor revocation is enabled"

    revoked_until = config.get("revoked_until")
    if revoked_until:
        try:
            expiry = datetime.fromisoformat(str(revoked_until).replace("Z", "+00:00"))
            if expiry.tzinfo is None or expiry.utcoffset() is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) < expiry.astimezone(timezone.utc):
                return True, f"temporary advisor revocation active until {expiry.isoformat()}"
        except (TypeError, ValueError):
            return True, "invalid revoked_until configuration"

    return False, ""


def load_state(session_id: str | None = None) -> dict:
    """Load persistent advisor state (call count, history).

    State is global — call_count tracks all calls regardless of session_id.
    The session_id is recorded in history entries for audit trail purposes
    but does not create an isolated counter.

    Recovers gracefully from corrupted state files.
    """
    if ADVISOR_STATE.exists():
        try:
            data = json.loads(ADVISOR_STATE.read_text())
            # Validate required fields
            if "call_count" not in data or "history" not in data:
                raise ValueError("missing required fields")
            return data
        except (json.JSONDecodeError, ValueError, TypeError):
            # Corrupted state file — reset to defaults
            pass
    return {"call_count": 0, "history": [], "session_id": session_id, "version": STATE_VERSION}


def save_state(state: dict) -> None:
    """Save advisor state to disk with file locking and secure permissions.

    Uses fcntl.flock on Unix for concurrent-write safety.
    Sets file permissions to 0600 to protect context previews.
    Prunes history to MAX_HISTORY_ENTRIES to prevent unbounded growth.
    """
    # Prune history if exceeding limit
    if len(state.get("history", [])) > MAX_HISTORY_ENTRIES:
        state["history"] = state["history"][-MAX_HISTORY_ENTRIES:]
    state["version"] = STATE_VERSION

    tmp_path = ADVISOR_STATE.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(state, indent=2))
    os.chmod(tmp_path, 0o600)

    if fcntl:
        # Use a lock file to prevent race on first run (when ADVISOR_STATE doesn't exist yet)
        lock_path = ADVISOR_STATE.with_suffix(".lock")
        with open(lock_path, "w") as lock_f:
            try:
                fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
                os.replace(tmp_path, ADVISOR_STATE)
            finally:
                fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
    else:
        os.replace(tmp_path, ADVISOR_STATE)


def reset_state(session_id: str | None = None) -> dict:
    """Reset advisor state to initial values."""
    state = {"call_count": 0, "history": [], "session_id": session_id, "version": STATE_VERSION}
    save_state(state)
    return state


def maybe_auto_reset(state: dict, config: dict) -> dict:
    """Auto-reset call counter if the configured reset period has elapsed.

    Calendar-boundary semantics (not rolling window):
      - "daily":   reset at the start of the next UTC day after the last call
      - "weekly":  reset at the start of the next UTC Monday after the last call
      - "monthly": reset at the start of the first day of the next UTC month

    If the current UTC time has crossed the relevant boundary since the last
    call's timestamp, call_count is reset to 0. History is preserved for audit.

    Returns the (possibly reset) state dict.
    """
    reset_period = config.get("reset_period", "none")
    if reset_period not in ("daily", "weekly", "monthly"):
        # "none" or unknown -> no auto-reset
        return state

    history = state.get("history", [])
    if not history:
        return state

    last_entry = history[-1]
    last_timestamp = last_entry.get("timestamp")
    if not last_timestamp:
        return state

    try:
        last_dt = datetime.fromisoformat(last_timestamp)
        # Handle timezone-naive timestamps by assuming UTC
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)

        # Compute the start of the period-boundary that contains last_dt.
        if reset_period == "daily":
            last_boundary = last_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif reset_period == "weekly":
            # Monday is weekday 0
            days_since_monday = last_dt.weekday()
            last_boundary = (last_dt - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:  # monthly
            last_boundary = last_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # If now has crossed past the *next* boundary, reset.
        if reset_period == "daily":
            next_boundary = last_boundary + timedelta(days=1)
        elif reset_period == "weekly":
            next_boundary = last_boundary + timedelta(weeks=1)
        else:  # monthly
            if last_boundary.month == 12:
                next_boundary = last_boundary.replace(year=last_boundary.year + 1, month=1)
            else:
                next_boundary = last_boundary.replace(month=last_boundary.month + 1)

        if now >= next_boundary:
            state["call_count"] = 0
            save_state(state)
    except (ValueError, TypeError):
        pass

    return state


def detect_backend() -> str:
    """Auto-detect the best available advisor backend.

    Priority:
    1. claude_native — if running inside Claude Code with advisor tool
    2. codex_orchestration — if codex-orchestration plugin is installed
    3. jev_gateway — if Jev / Vercel AI Gateway credentials exist (Cline, Codex, Devin, Antigravity)
    4. grok_cli — if ~/.grok/auth.json exists (legacy fallback)
    5. fallback — no backend available
    """
    # Check for Claude Code native advisor (environment signal)
    if os.environ.get("CLAUDE_ADVISOR_ENABLED") == "true":
        return "claude_native"

    # Check for Codex-Orchestration plugin
    codex_plugin = Path.home() / ".codex" / "plugins" / "codex-orchestration"
    if codex_plugin.exists():
        return "codex_orchestration"

    # Check for Jev / Vercel AI Gateway credentials
    if JevGatewayService.has_credentials():
        return "jev_gateway"

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
        backend: Force a specific backend (jev_gateway, grok_cli, claude_native, codex_orchestration).

    Returns:
        Advice text from the advisor, or a fallback message if unavailable.
    """
    if config is None:
        config = load_config()

    revoked, reason = revocation_status(config)
    if revoked:
        return f"[Advisor] Revoked: {reason}. Proceed without advisor."

    # Context length limit — prevent excessively large payloads
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n[... truncated at {} chars]".format(MAX_CONTEXT_CHARS)

    state = load_state(session_id)

    # Auto-reset if reset period has elapsed (e.g., daily/weekly/monthly)
    state = maybe_auto_reset(state, config)

    # Cost control: check max_advisor_calls
    max_calls = config.get("max_advisor_calls", 30)

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
            "Proceed without advisor. Configure Jev / Vercel AI Gateway key (AI_GATEWAY_API_KEY or "
            "cline-jev-browser.config.json), install Grok CLI, or enable Claude Code advisor tool."
        )

    # Route unimplemented backend to available backend
    if selected_backend not in ("jev_gateway", "grok_cli"):
        if JevGatewayService.has_credentials():
            selected_backend = "jev_gateway"
        else:
            grok_auth = Path.home() / ".grok" / "auth.json"
            if grok_auth.exists():
                selected_backend = "grok_cli"
            else:
                return (
                    f"[Advisor] Backend '{selected_backend}' detected but not yet implemented in CLI. "
                    "No jev_gateway or grok_cli fallback available. "
                    "Proceed without advisor."
                )

    advisor_model = str(config.get("advisor_model", "")).strip()

    if selected_backend == "jev_gateway":
        model = advisor_model or "openai/gpt-4o"
        svc = JevGatewayService(api_key="", mock_mode=False, model=model)
        if not svc.api_key:
            return (
                "[Advisor] No Jev / Vercel AI Gateway API key available. "
                "Configure AI_GATEWAY_API_KEY or cline-jev-browser.config.json. Proceed without advisor."
            )
    else:
        model = advisor_model or "grok-4.6"
        svc = GrokService(api_key="", mock_mode=False, model=model)
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
            # Set timeout — use signal on Unix, skip on Windows
            # (Windows relies on requests library timeout in GrokService)
            if hasattr(signal, "SIGALRM"):
                signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(timeout_seconds)

            response = svc.generate(
                prompt=user_prompt,
                system=system_prompt,
                max_output_tokens=max_tokens,
                temperature=0.7,
            )

            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)  # Cancel timeout

            if _TIMEOUT_OCCURRED:
                raise TimeoutError("Advisor API call timed out")

            break  # Success

        except TimeoutError as e:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)
            last_error = str(e)
            if attempt < retry_attempts:
                continue
            return f"[Advisor] Timeout after {timeout_seconds}s. Proceed without advisor."

        except Exception as e:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)
            last_error = str(e)
            if attempt < retry_attempts:
                continue
            return f"[Advisor] Error: {last_error}. Proceed without advisor."

    if response is None:
        return f"[Advisor] Failed after {retry_attempts + 1} attempts. Proceed without advisor."

    # Fallback model: gateway returned an error string (not an exception) —
    # retry once with the configured fallback model before giving up.
    fallback_model = str(config.get("advisor_model_fallback", "")).strip()
    if (
        fallback_model
        and selected_backend == "jev_gateway"
        and isinstance(response, str)
        and response.startswith(("[Jev/Gateway]", "[Advisor]"))
    ):
        fallback_svc = JevGatewayService(api_key="", mock_mode=False, model=fallback_model)
        if fallback_svc.api_key:
            fb = fallback_svc.generate(
                prompt=user_prompt, system=system_prompt,
                max_output_tokens=max_tokens, temperature=0.7,
            )
            if isinstance(fb, str) and not fb.startswith(("[Jev/Gateway]", "[Advisor]")):
                response = f"[fallback: {fallback_model}] " + fb

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
    parser.add_argument("--backend", type=str, choices=["jev_gateway", "grok_cli", "claude_native", "codex_orchestration"],
                        help="Force a specific backend")
    parser.add_argument("--max-calls", type=int, help="Override max advisor calls from config")
    parser.add_argument("--timeout", type=int, help="Override timeout in seconds from config")
    parser.add_argument("--model", type=str, help="Override advisor model from config")
    parser.add_argument("--system-prompt", type=str, help="Override advisor system prompt from config")
    revocation_group = parser.add_mutually_exclusive_group()
    revocation_group.add_argument("--revoke", action="store_true", help="Revoke all advisor calls globally")
    revocation_group.add_argument("--unrevoke", action="store_true", help="Clear the global advisor revocation")
    parser.add_argument("--revoke-reason", type=str, default="", help="Reason recorded with --revoke")
    parser.add_argument("--revoke-until", type=str, help="ISO-8601 expiry for a temporary --revoke")

    args = parser.parse_args()
    config = load_config()

    # Apply CLI overrides
    if args.max_calls is not None:
        config["max_advisor_calls"] = args.max_calls
    if args.timeout is not None:
        config["timeout_seconds"] = args.timeout
    if args.model is not None:
        config["advisor_model"] = args.model
    if args.system_prompt is not None:
        config["advisor_system_prompt"] = args.system_prompt

    if args.revoke:
        if args.revoke_until:
            try:
                datetime.fromisoformat(args.revoke_until.replace("Z", "+00:00"))
            except ValueError:
                parser.error("--revoke-until must be an ISO-8601 timestamp")
        config["revoked"] = True
        config["revocation_reason"] = args.revoke_reason.strip() or "global advisor revocation is enabled"
        config["revoked_until"] = args.revoke_until
        save_config(config)
        print(f"Advisor revoked: {config['revocation_reason']}")
        return

    if args.unrevoke:
        config["revoked"] = False
        config["revocation_reason"] = ""
        config["revoked_until"] = None
        save_config(config)
        print("Advisor revocation cleared.")
        return

    # --status: show call count, history, and quota info
    if args.status:
        state = load_state(args.session)
        state = maybe_auto_reset(state, config)
        reset_period = config.get("reset_period", "none")
        max_calls = config.get("max_advisor_calls", 30)
        calls_remaining = max(0, max_calls - state["call_count"])
        revoked, reason = revocation_status(config)
        status_info = {
            **state,
            "advisor_model": config.get("advisor_model", "typesafe-ai/jev"),
            "backend": detect_backend(),
            "config_path": str(ADVISOR_CONFIG),
            "max_advisor_calls": max_calls,
            "calls_remaining": calls_remaining,
            "reset_period": reset_period,
            "revocation": {
                "revoked": revoked,
                "reason": reason,
                "revoked_until": config.get("revoked_until"),
            },
        }
        print(json.dumps(status_info, indent=2))
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
    revoked, reason = revocation_status(config)

    if args.json:
        state = load_state(args.session)
        max_calls = config.get("max_advisor_calls", 30)
        selected_backend = "revoked" if revoked else (args.backend or detect_backend())
        status = "revoked" if revoked else "success"
        if not revoked and "Call cap reached" in advice:
            status = "cap_reached"
        elif not revoked and ("No Grok API key" in advice or "No Jev" in advice or "No advisor backend" in advice or "No grok_cli fallback" in advice):
            status = "no_token"
        elif not revoked and "Dry run" in advice:
            status = "dry_run"
        elif not revoked and "Timeout" in advice:
            status = "timeout"
        elif not revoked and "[Advisor]" in advice and "Error" in advice:
            status = "error"

        response = {
            "status": status,
            "advice": advice,
            "advisor_model": config.get("advisor_model", "typesafe-ai/jev"),
            "config_path": str(ADVISOR_CONFIG),
            "call_count": state["call_count"],
            "calls_remaining": max(0, max_calls - state["call_count"]),
            "backend": selected_backend,
            "revocation": {"revoked": revoked, "reason": reason},
            "session_id": args.session or state.get("session_id", ""),
        }
        if status in ("error", "timeout", "revoked"):
            response["error"] = advice
        print(json.dumps(response, indent=2))
    else:
        print(advice)


    if revoked:
        sys.exit(2)


if __name__ == "__main__":
    main()
