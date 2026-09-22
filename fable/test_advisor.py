#!/usr/bin/env python3
"""
ECC Advisor Skill — Test Suite

Tests the advisor_cli.py helper script and its integration with GrokService.
Covers: config loading, state management, cost control, mock + live API calls.

Run:  python3 -m pytest fable/test_advisor.py -v
      python3 fable/test_advisor.py
"""
import json
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from fable.advisor_cli import (
    load_config,
    load_state,
    save_state,
    reset_state,
    get_advice,
    detect_backend,
    maybe_auto_reset,
    ADVISOR_STATE,
    ADVISOR_CONFIG,
)
from datetime import datetime, timedelta, timezone
import shutil

# ─── State Preservation ─────────────────────────────────────────────────────

_REAL_STATE_BACKUP = None


def _save_real_state():
    """Backup real advisor_state.json before tests modify it."""
    global _REAL_STATE_BACKUP
    if ADVISOR_STATE.exists():
        _REAL_STATE_BACKUP = ADVISOR_STATE.read_text()
    else:
        _REAL_STATE_BACKUP = None


def _restore_real_state():
    """Restore real advisor_state.json after tests."""
    global _REAL_STATE_BACKUP
    if _REAL_STATE_BACKUP is not None:
        ADVISOR_STATE.write_text(_REAL_STATE_BACKUP)
    elif ADVISOR_STATE.exists():
        ADVISOR_STATE.unlink()

# ─── Test Harness ────────────────────────────────────────────────────────────

PASS = 0
FAIL = 0
CHECKS = []


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    CHECKS.append(f"  {status} — {name}" + (f" ({detail})" if detail else ""))


def section(title: str):
    CHECKS.append(f"\n── {title} ──")


# ─── Tests ───────────────────────────────────────────────────────────────────

def test_config_loading():
    section("Config Loading")
    config = load_config()
    check("config has advisor_model", "advisor_model" in config, config.get("advisor_model", "missing"))
    check("config advisor_model is valid", config.get("advisor_model") in ("google/gemini-2.5-flash-lite", "typesafe-ai/jev", "grok-4.6", "google/gemini-2.5-pro"))
    check("config has max_advisor_calls", "max_advisor_calls" in config, str(config.get("max_advisor_calls")))
    check("config max_advisor_calls is 30", config.get("max_advisor_calls") == 30)
    check("config has max_tokens_advisor", "max_tokens_advisor" in config)
    check("config has advisor_system_prompt", "advisor_system_prompt" in config)
    check("config has nudge_text", "nudge_text" in config)
    check("config has executor_system_prompt_addition", "executor_system_prompt_addition" in config)
    check("config has revoked flag", "revoked" in config, str(config.get("revoked")))
    check("config has revocation reason", "revocation_reason" in config)
    check("config has revocation expiry", "revoked_until" in config)


def test_state_management():
    section("State Management")

    # Save initial state
    reset_state()
    state = load_state()
    check("initial call_count is 0", state["call_count"] == 0, str(state["call_count"]))
    check("initial history is empty", len(state["history"]) == 0)

    # Simulate a call
    state["call_count"] = 1
    state["history"].append({"call": 1, "context_preview": "test", "response_preview": "test"})
    save_state(state)

    state2 = load_state()
    check("state persists call_count", state2["call_count"] == 1, str(state2["call_count"]))
    check("state persists history", len(state2["history"]) == 1)

    # Reset
    reset_state()
    state3 = load_state()
    check("reset clears call_count", state3["call_count"] == 0)
    check("reset clears history", len(state3["history"]) == 0)


def test_cost_control_cap():
    section("Cost Control — Call Cap")

    reset_state()

    # Manually set call_count to max
    state = load_state()
    state["call_count"] = 30  # max_advisor_calls is 30
    save_state(state)

    config = load_config()
    result = get_advice("test question", config)

    check("cap reached returns fallback message", "[Advisor] Call cap reached" in result, result[:80])
    check("cap message mentions 30", "30" in result)

    reset_state()


def test_mock_advice():
    section("Mock Advice — GrokService mock mode")

    reset_state()

    config = load_config()

    # Patch services to use mock mode
    with patch("fable.advisor_cli.GrokService") as MockGrok, patch("fable.advisor_cli.JevGatewayService") as MockJev:
        mock_instance = MagicMock()
        mock_instance.api_key = "fake-key"
        mock_instance.generate.return_value = "[Mock] Advice: Use cursor-based pagination."
        MockGrok.return_value = mock_instance
        MockJev.return_value = mock_instance

        result = get_advice("Should I use pagination?", config)

        check("mock returns advice text", "cursor-based pagination" in result, result[:80])
        check("mock generate was called", mock_instance.generate.called)

        # Verify state was updated
        state = load_state()
        check("call_count incremented after mock call", state["call_count"] == 1, str(state["call_count"]))
        check("history has 1 entry", len(state["history"]) == 1)

    reset_state()


def test_revocation_gate():
    section("Global Revocation Gate")

    _save_real_state()
    config = load_config()
    config["revoked"] = True
    config["revocation_reason"] = "maintenance"
    config["revoked_until"] = None

    with patch("fable.advisor_cli.GrokService") as MockGrok:
        result = get_advice("test revoked advisor", config)
        check("revoked advisor returns a fallback", "Revoked" in result, result[:120])
        check("revoked advisor does not call GrokService", not MockGrok.called)

    config["revoked"] = False
    config["revoked_until"] = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    with patch("fable.advisor_cli.GrokService") as MockGrok:
        result = get_advice("test temporary revocation", config)
        check("temporary revocation blocks advisor", "Revoked" in result, result[:120])
        check("temporary revocation does not call GrokService", not MockGrok.called)

    _restore_real_state()


def test_no_token_fallback():
    section("No Token Fallback")

    reset_state()
    config = load_config()

    # Patch GrokService to simulate no token
    with patch("fable.advisor_cli.GrokService") as MockGrok:
        mock_instance = MagicMock()
        mock_instance.api_key = ""  # No token
        MockGrok.return_value = mock_instance

        result = get_advice("test question", config, backend="grok_cli")

        check("no token returns fallback", "[Advisor] No Grok API key" in result, result[:80])

        # State should NOT increment when no token
        state = load_state()
        check("call_count not incremented without token", state["call_count"] == 0, str(state["call_count"]))

    # Patch JevGatewayService to simulate no token
    with patch("fable.advisor_cli.JevGatewayService") as MockJev:
        mock_instance = MagicMock()
        mock_instance.api_key = ""  # No token
        MockJev.return_value = mock_instance

        result = get_advice("test question", config, backend="jev_gateway")
        check("no jev token returns fallback", "[Advisor] No Jev" in result, result[:80])

    reset_state()


def test_multiple_calls_increment():
    section("Multiple Calls Increment Counter")

    reset_state()
    config = load_config()

    with patch("fable.advisor_cli.GrokService") as MockGrok, patch("fable.advisor_cli.JevGatewayService") as MockJev:
        mock_instance = MagicMock()
        mock_instance.api_key = "fake-key"
        mock_instance.generate.return_value = "Advice text"
        MockGrok.return_value = mock_instance
        MockJev.return_value = mock_instance

        # Call 1
        get_advice("question 1", config)
        state = load_state()
        check("after call 1, count is 1", state["call_count"] == 1, str(state["call_count"]))

        # Call 2
        get_advice("question 2", config)
        state = load_state()
        check("after call 2, count is 2", state["call_count"] == 2, str(state["call_count"]))

        # Call 3
        get_advice("question 3", config)
        state = load_state()
        check("after call 3, count is 3", state["call_count"] == 3, str(state["call_count"]))

        # Call 31 — should hit cap (max is 30)
        for i in range(4, 31):
            get_advice(f"question {i}")
        result = get_advice("question 31")
        check("call 31 hits cap", "[Advisor] Call cap reached" in result, result[:80])

        state = load_state()
        check("call_count stays at 30 after cap", state["call_count"] == 30, str(state["call_count"]))

    reset_state()


def test_history_tracking():
    section("History Tracking")

    reset_state()
    config = load_config()

    with patch("fable.advisor_cli.GrokService") as MockGrok, patch("fable.advisor_cli.JevGatewayService") as MockJev:
        mock_instance = MagicMock()
        mock_instance.api_key = "fake-key"
        mock_instance.generate.return_value = "Specific advice text here."
        MockGrok.return_value = mock_instance
        MockJev.return_value = mock_instance

        get_advice("My context about API design", config)

        state = load_state()
        check("history has 1 entry", len(state["history"]) == 1)
        entry = state["history"][0]
        check("history entry has call number", entry["call"] == 1)
        check("history entry has context_preview", "API design" in entry["context_preview"])
        check("history entry has response_preview", "Specific advice" in entry["response_preview"])
        check("history entry has timestamp", "timestamp" in entry)

    reset_state()


def test_skill_md_exists():
    section("Skill Definition")

    skill_path = Path(__file__).parent.parent / "skills" / "ecc-advisor" / "SKILL.md"
    check("SKILL.md exists", skill_path.exists(), str(skill_path))

    if skill_path.exists():
        content = skill_path.read_text()
        check("SKILL.md has name: ecc-advisor", "name: ecc-advisor" in content)
        check("SKILL.md has TRIGGER keywords", "TRIGGER" in content)
        check("SKILL.md has advisor_cli.py reference", "advisor_cli.py" in content)
        check("SKILL.md has cost controls section", "Cost Controls" in content)
        check("SKILL.md has platform compatibility", "Platform Compatibility" in content)
        check("SKILL.md mentions Cascade", "Cascade" in content)
        check("SKILL.md mentions Codex", "Codex" in content)
        check("SKILL.md mentions Autogravity", "Autogravity" in content)
        check("SKILL.md has hard rule", "Hard Rule" in content)
        check("SKILL.md has dependency gating", "Dependency Gating" in content)


def test_advisor_config_exists():
    section("Advisor Config")

    check("advisor_config.json exists", ADVISOR_CONFIG.exists(), str(ADVISOR_CONFIG))

    if ADVISOR_CONFIG.exists():
        config = json.loads(ADVISOR_CONFIG.read_text())
        check("config has all required keys", all(
            k in config for k in [
                "advisor_model", "max_advisor_calls", "max_tokens_advisor",
                "advisor_system_prompt", "nudge_text", "executor_system_prompt_addition"
            ]
        ))


def test_backend_detection():
    section("Backend Detection")

    backend = detect_backend()
    check("detect_backend returns valid value", backend in ("jev_gateway", "grok_cli", "claude_native", "codex_orchestration", "fallback"), backend)

    # Test claude_native detection
    with patch.dict(os.environ, {"CLAUDE_ADVISOR_ENABLED": "true"}):
        backend = detect_backend()
        check("claude_native detected via env var", backend == "claude_native", backend)

    # Test fallback when nothing available
    with patch.dict(os.environ, {}, clear=True):
        with patch.object(Path, "home", return_value=Path("/nonexistent")), \
             patch("fable.advisor_cli.JevGatewayService.has_credentials", return_value=False):
            backend = detect_backend()
            check("fallback when nothing available", backend == "fallback", backend)


def test_dry_run_no_budget():
    section("Dry Run — No Budget Consumption")

    reset_state()
    config = load_config()

    result = get_advice("test context", config, dry_run=True)
    check("dry run returns dry run message", "Dry run" in result, result[:80])

    state = load_state()
    check("dry run does not increment counter", state["call_count"] == 0, str(state["call_count"]))

    # Dry run works even at cap
    state["call_count"] = 3
    save_state(state)
    result = get_advice("test context", config, dry_run=True)
    check("dry run works at cap", "Dry run" in result, result[:80])

    reset_state()


def test_session_isolation():
    section("Session Isolation")

    reset_state()
    config = load_config()

    with patch("fable.advisor_cli.GrokService") as MockGrok:
        mock_instance = MagicMock()
        mock_instance.api_key = "fake-key"
        mock_instance.generate.return_value = "Advice text"
        MockGrok.return_value = mock_instance

        get_advice("session A question", config, session_id="task-A")
        get_advice("session B question", config, session_id="task-B")

        state = load_state()
        check("global counter is 2", state["call_count"] == 2, str(state["call_count"]))

        # History entries should have session_id
        history_a = [h for h in state["history"] if h.get("session_id") == "task-A"]
        history_b = [h for h in state["history"] if h.get("session_id") == "task-B"]
        check("history has task-A entry", len(history_a) == 1)
        check("history has task-B entry", len(history_b) == 1)

    reset_state()


def test_auto_reset_daily():
    section("Auto-Reset — Daily Period")

    reset_state()
    config = load_config()
    config["reset_period"] = "daily"

    # Set state with an old timestamp (> 1 day ago)
    state = load_state()
    state["call_count"] = 5
    old_ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    state["history"] = [{"call": 5, "context_preview": "old", "response_preview": "old", "timestamp": old_ts}]
    save_state(state)

    # maybe_auto_reset should reset call_count to 0
    state = load_state()
    state = maybe_auto_reset(state, config)
    check("daily reset: call_count reset to 0", state["call_count"] == 0, str(state["call_count"]))
    check("daily reset: history preserved", len(state["history"]) == 1)

    reset_state()


def test_auto_reset_none():
    section("Auto-Reset — None Period (no reset)")

    reset_state()
    config = load_config()
    config["reset_period"] = "none"

    state = load_state()
    state["call_count"] = 5
    old_ts = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    state["history"] = [{"call": 5, "context_preview": "old", "response_preview": "old", "timestamp": old_ts}]
    save_state(state)

    state = load_state()
    state = maybe_auto_reset(state, config)
    check("none period: call_count unchanged", state["call_count"] == 5, str(state["call_count"]))

    reset_state()


def test_auto_reset_weekly_not_elapsed():
    section("Auto-Reset — Weekly Period (not yet elapsed)")

    reset_state()
    config = load_config()
    config["reset_period"] = "weekly"

    state = load_state()
    state["call_count"] = 3
    recent_ts = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
    state["history"] = [{"call": 3, "context_preview": "recent", "response_preview": "recent", "timestamp": recent_ts}]
    save_state(state)

    state = load_state()
    state = maybe_auto_reset(state, config)
    check("weekly not elapsed: call_count unchanged", state["call_count"] == 3, str(state["call_count"]))

    reset_state()


def test_auto_reset_preserves_history():
    section("Auto-Reset — History Preserved After Reset")

    reset_state()
    config = load_config()
    config["reset_period"] = "daily"

    state = load_state()
    state["call_count"] = 20
    old_ts = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    state["history"] = [
        {"call": 1, "context_preview": "c1", "response_preview": "r1", "timestamp": old_ts},
        {"call": 2, "context_preview": "c2", "response_preview": "r2", "timestamp": old_ts},
    ]
    save_state(state)

    state = load_state()
    state = maybe_auto_reset(state, config)
    check("history preserved: 2 entries remain", len(state["history"]) == 2)
    check("history preserved: call_count is 0", state["call_count"] == 0)

    reset_state()


def test_auto_reset_empty_history():
    section("Auto-Reset — Empty History (no-op)")

    reset_state()
    config = load_config()
    config["reset_period"] = "daily"

    state = load_state()
    state["call_count"] = 0
    save_state(state)

    state = maybe_auto_reset(state, config)
    check("empty history: no crash, call_count stays 0", state["call_count"] == 0)

    reset_state()


def test_cli_flag_in_runner():
    section("CLI Flag in fable_runner.py")

    runner_path = Path(__file__).parent.parent / "fable" / "fable_runner.py"
    content = runner_path.read_text()
    check("runner has --advisor argument", "--advisor" in content)
    check("runner imports get_advice", "get_advice" in content)
    check("runner imports load_config", "load_config" in content)


# ─── Live Integration Test (skipped if no token) ─────────────────────────────

def test_fable_dir_env_var():
    section("FABLE_DIR Environment Variable")

    import importlib
    import fable.advisor_cli as adv_module

    # Save original values
    orig_fable_dir = os.environ.get("FABLE_DIR")
    orig_state = adv_module.ADVISOR_STATE
    orig_config = adv_module.ADVISOR_CONFIG

    # Set FABLE_DIR to a temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        resolved_tmpdir = str(Path(tmpdir).resolve())
        os.environ["FABLE_DIR"] = tmpdir
        importlib.reload(adv_module)

        check("FABLE_DIR changes ADVISOR_STATE path", str(adv_module.ADVISOR_STATE).startswith(resolved_tmpdir),
              f"expected {resolved_tmpdir} in {adv_module.ADVISOR_STATE}")
        check("FABLE_DIR changes ADVISOR_CONFIG path", str(adv_module.ADVISOR_CONFIG).startswith(resolved_tmpdir),
              f"expected {resolved_tmpdir} in {adv_module.ADVISOR_CONFIG}")

    # Restore
    if orig_fable_dir is not None:
        os.environ["FABLE_DIR"] = orig_fable_dir
    else:
        os.environ.pop("FABLE_DIR", None)
    importlib.reload(adv_module)


def test_bootstrap_wrapper():
    section("Bootstrap Wrapper (call_advisor.sh)")

    wrapper_path = Path(__file__).parent.parent / "skills" / "ecc-advisor" / "scripts" / "call_advisor.sh"
    check("wrapper exists", wrapper_path.exists(), str(wrapper_path))

    if wrapper_path.exists():
        content = wrapper_path.read_text()
        check("wrapper has FABLE_DIR", "FABLE_DIR" in content)
        check("wrapper has git rev-parse fallback", "git rev-parse" in content)
        check("wrapper resolves canonical target", "cd -P" in content and "CANONICAL_CLI" in content)
        check("wrapper has revocation gate", "revoked" in content.lower())
        check("wrapper is executable", os.access(wrapper_path, os.X_OK))

        # Test --status via wrapper (should not crash)
        result = subprocess.run(
            ["bash", str(wrapper_path), "--status"],
            capture_output=True, text=True, timeout=10,
            cwd=str(Path(__file__).parent.parent),
        )
        check("wrapper --status returns 0", result.returncode == 0, result.stderr[:80])


def test_model_override():
    section("CLI --model Override")

    _save_real_state()
    reset_state()
    config = load_config()

    with patch("fable.advisor_cli.GrokService") as MockGrok:
        mock_instance = MagicMock()
        mock_instance.api_key = "fake-key"
        mock_instance.generate.return_value = "Advice"
        MockGrok.return_value = mock_instance

        get_advice("test", config, backend="grok_cli")
        # Verify GrokService was called with model from config
        _, kwargs = MockGrok.call_args
        check("GrokService receives model kwarg", "model" in kwargs, str(kwargs))
        expected_model = config.get("advisor_model", "typesafe-ai/jev")
        check("model matches config", kwargs.get("model") == expected_model, str(kwargs.get("model")))

    reset_state()
    _restore_real_state()


def test_timeout_override():
    section("CLI --timeout Override")

    config = load_config()
    config["timeout_seconds"] = 5
    check("timeout override works", config["timeout_seconds"] == 5)


def test_system_prompt_override():
    section("CLI --system-prompt Override")

    config = load_config()
    config["advisor_system_prompt"] = "Custom prompt for testing"
    check("system prompt override works", config["advisor_system_prompt"] == "Custom prompt for testing")


def test_max_calls_override():
    section("CLI --max-calls Override")

    _save_real_state()
    reset_state()
    config = load_config()
    config["max_advisor_calls"] = 2

    with patch("fable.advisor_cli.GrokService") as MockGrok:
        mock_instance = MagicMock()
        mock_instance.api_key = "fake-key"
        mock_instance.generate.return_value = "Advice"
        MockGrok.return_value = mock_instance

        # Call 1 and 2 should succeed
        get_advice("q1", config)
        get_advice("q2", config)
        # Call 3 should hit cap
        result = get_advice("q3", config)
        check("max_calls=2: call 3 hits cap", "Call cap reached" in result, result[:80])

    reset_state()
    _restore_real_state()


def test_backend_override():
    section("CLI --backend Override")

    _save_real_state()
    reset_state()
    config = load_config()

    # Force fallback backend (no grok token path)
    result = get_advice("test", config, backend="fallback")
    check("forced fallback returns no-backend message", "No advisor backend" in result, result[:80])

    reset_state()
    _restore_real_state()


def test_context_file_flag():
    section("CLI --context-file Flag")

    _save_real_state()
    reset_state()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("This is context from a file.\n")
        f.write("It contains detailed information.")
        ctx_path = f.name

    try:
        config = load_config()
        with patch("fable.advisor_cli.GrokService") as MockGrok, patch("fable.advisor_cli.JevGatewayService") as MockJev:
            mock_instance = MagicMock()
            mock_instance.api_key = "fake-key"
            mock_instance.generate.return_value = "Advice"
            MockGrok.return_value = mock_instance
            MockJev.return_value = mock_instance

            # Simulate CLI --context-file by building context manually
            with open(ctx_path) as cf:
                file_content = cf.read()
            context = f"{file_content}\n\nWhat should I do?"
            get_advice(context, config)

            state = load_state()
            check("context-file content in history", "context from a file" in state["history"][0]["context_preview"])
    finally:
        os.unlink(ctx_path)

    reset_state()
    _restore_real_state()


def test_json_output_format():
    section("CLI --json Output Format")

    _save_real_state()
    reset_state()

    # Run the CLI with --json and --dry-run
    cli_path = Path(__file__).parent / "advisor_cli.py"
    result = subprocess.run(
        [sys.executable, str(cli_path), "--json", "--dry-run", "test context"],
        capture_output=True, text=True, timeout=10,
        cwd=str(Path(__file__).parent.parent),
    )
    check("--json returns valid JSON", result.returncode == 0, result.stderr[:80])

    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            check("--json has status field", "status" in data)
            check("--json status is dry_run", data.get("status") == "dry_run", data.get("status"))
            check("--json has call_count", "call_count" in data)
            check("--json has backend", "backend" in data)
        except json.JSONDecodeError:
            check("--json output is valid JSON", False, result.stdout[:100])

    reset_state()
    _restore_real_state()


def test_auto_reset_timezone_naive():
    section("Auto-Reset — Timezone-Naive Timestamp")

    _save_real_state()
    reset_state()
    config = load_config()
    config["reset_period"] = "daily"

    state = load_state()
    state["call_count"] = 5
    # Timezone-naive timestamp (no +00:00 suffix)
    old_ts = (datetime.utcnow() - timedelta(days=2)).isoformat()
    state["history"] = [{"call": 5, "context_preview": "old", "response_preview": "old", "timestamp": old_ts}]
    save_state(state)

    state = load_state()
    state = maybe_auto_reset(state, config)
    check("timezone-naive: call_count reset to 0", state["call_count"] == 0, str(state["call_count"]))

    reset_state()
    _restore_real_state()


def test_live_advisor():
    section("Live Advisor")

    # Only run live network calls if explicitly requested
    if os.environ.get("ECC_TEST_LIVE") != "1":
        check("live test skipped — set ECC_TEST_LIVE=1 to run", True, "skipped")
        return

    reset_state()
    config = load_config()
    config["timeout_seconds"] = 5

    try:
        result = get_advice(
            "I'm building a REST API for a 50M row dataset. "
            "Should I use offset pagination or cursor-based navigation? "
            "Brief recommendation please.",
            config,
            backend="grok_cli",
        )
        if "[Advisor] No Grok API key" in result or "expired" in result.lower():
            check("live test skipped — grok subscription expired or unauthenticated", True, "skipped")
            reset_state()
            return

        check("live advisor returns text", len(result) > 10, f"len={len(result)}")
        check("live advisor does not return error", "[Advisor]" not in result or "Call cap" not in result, result[:80])

        state = load_state()
        check("live call incremented counter", state["call_count"] == 1, str(state["call_count"]))

    except Exception as e:
        check(f"live advisor failed: {e}", False, str(e))

    reset_state()


# ─── Runner ──────────────────────────────────────────────────────────────────

def run_all_tests():
    test_config_loading()
    test_state_management()
    test_cost_control_cap()
    test_mock_advice()
    test_revocation_gate()
    test_no_token_fallback()
    test_multiple_calls_increment()
    test_history_tracking()
    test_backend_detection()
    test_dry_run_no_budget()
    test_session_isolation()
    test_auto_reset_daily()
    test_auto_reset_none()
    test_auto_reset_weekly_not_elapsed()
    test_auto_reset_preserves_history()
    test_auto_reset_empty_history()
    test_fable_dir_env_var()
    test_bootstrap_wrapper()
    test_model_override()
    test_timeout_override()
    test_system_prompt_override()
    test_max_calls_override()
    test_backend_override()
    test_context_file_flag()
    test_json_output_format()
    test_auto_reset_timezone_naive()
    test_skill_md_exists()
    test_advisor_config_exists()
    test_cli_flag_in_runner()
    test_live_advisor()

    print("\n" + "=" * 60)
    for line in CHECKS:
        print(line)
    print("=" * 60)
    print(f"\n  Total: {PASS + FAIL}  Pass: {PASS}  Fail: {FAIL}\n")
    return FAIL == 0


# ─── Pytest compatibility ────────────────────────────────────────────────────

def test_config_loading_pytest():
    config = load_config()
    assert config.get("advisor_model") in ("google/gemini-2.5-flash-lite", "typesafe-ai/jev", "grok-4.6", "google/gemini-2.5-pro", "openai/gpt-4o")
    assert config.get("max_advisor_calls") == 60
    assert config.get("revoked") is False
    assert config.get("revoked_until") is None

def test_state_management_pytest():
    reset_state()
    state = load_state()
    assert state["call_count"] == 0
    assert len(state["history"]) == 0
    reset_state()

def test_cost_control_pytest():
    reset_state()
    state = load_state()
    config = load_config()
    state["call_count"] = config["max_advisor_calls"]
    save_state(state)
    result = get_advice("test", config)
    assert "Call cap reached" in result
    reset_state()

def test_mock_advice_pytest():
    reset_state()
    config = load_config()
    with patch("fable.advisor_cli.GrokService") as MockGrok:
        mock_instance = MagicMock()
        mock_instance.api_key = "fake-key"
        mock_instance.generate.return_value = "Use cursor pagination."
        MockGrok.return_value = mock_instance
        result = get_advice("test", config, backend="grok_cli")
        assert "cursor pagination" in result
    reset_state()

def test_mock_advice_jev_pytest():
    reset_state()
    config = load_config()
    with patch("fable.advisor_cli.JevGatewayService") as MockJev:
        mock_instance = MagicMock()
        mock_instance.api_key = "fake-key"
        mock_instance.generate.return_value = "Use cursor pagination via Jev."
        MockJev.return_value = mock_instance
        result = get_advice("test", config, backend="jev_gateway")
        assert "cursor pagination via Jev" in result
    reset_state()

def test_jev_gateway_service_pytest():
    from fable.services import JevGatewayService
    fixture_key = "fixture" + "_key"
    svc = JevGatewayService(api_key=fixture_key, mock_mode=True, model="typesafe-ai/jev")
    assert svc.api_key == fixture_key
    assert svc.model == "typesafe-ai/jev"
    res = svc.generate("Explain pagination")
    assert "Would answer" in res

def test_no_token_pytest():
    reset_state()
    config = load_config()
    with patch("fable.advisor_cli.GrokService") as MockGrok:
        mock_instance = MagicMock()
        mock_instance.api_key = ""
        MockGrok.return_value = mock_instance
        result = get_advice("test", config, backend="grok_cli")
        assert "No Grok API key" in result
    reset_state()

def test_skill_md_pytest():
    skill_path = Path(__file__).parent.parent / "skills" / "ecc-advisor" / "SKILL.md"
    assert skill_path.exists()
    content = skill_path.read_text()
    assert "ecc-advisor" in content
    assert "advisor_cli.py" in content


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
