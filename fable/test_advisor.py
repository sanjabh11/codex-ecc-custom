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
    ADVISOR_STATE,
    ADVISOR_CONFIG,
)

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
    check("config advisor_model is grok-4.5", config.get("advisor_model") == "grok-4.5")
    check("config has max_advisor_calls", "max_advisor_calls" in config, str(config.get("max_advisor_calls")))
    check("config max_advisor_calls is 3", config.get("max_advisor_calls") == 3)
    check("config has max_tokens_advisor", "max_tokens_advisor" in config)
    check("config has advisor_system_prompt", "advisor_system_prompt" in config)
    check("config has nudge_text", "nudge_text" in config)
    check("config has executor_system_prompt_addition", "executor_system_prompt_addition" in config)


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
    state["call_count"] = 3  # max_advisor_calls is 3
    save_state(state)

    config = load_config()
    result = get_advice("test question", config)

    check("cap reached returns fallback message", "[Advisor] Call cap reached" in result, result[:80])
    check("cap message mentions 3", "3" in result)

    reset_state()


def test_mock_advice():
    section("Mock Advice — GrokService mock mode")

    reset_state()

    config = load_config()

    # Patch GrokService to use mock mode
    with patch("fable.advisor_cli.GrokService") as MockGrok:
        mock_instance = MagicMock()
        mock_instance.api_key = "fake-key"
        mock_instance.generate.return_value = "[Grok mock] Advice: Use cursor-based pagination."
        MockGrok.return_value = mock_instance

        result = get_advice("Should I use pagination?", config)

        check("mock returns advice text", "cursor-based pagination" in result, result[:80])
        check("mock generate was called", mock_instance.generate.called)

        # Verify state was updated
        state = load_state()
        check("call_count incremented after mock call", state["call_count"] == 1, str(state["call_count"]))
        check("history has 1 entry", len(state["history"]) == 1)

    reset_state()


def test_no_token_fallback():
    section("No Token Fallback")

    reset_state()

    config = load_config()

    # Patch GrokService to simulate no token
    with patch("fable.advisor_cli.GrokService") as MockGrok:
        mock_instance = MagicMock()
        mock_instance.api_key = ""  # No token
        MockGrok.return_value = mock_instance

        result = get_advice("test question", config)

        check("no token returns fallback", "[Advisor] No Grok API key" in result, result[:80])

        # State should NOT increment when no token
        state = load_state()
        check("call_count not incremented without token", state["call_count"] == 0, str(state["call_count"]))

    reset_state()


def test_multiple_calls_increment():
    section("Multiple Calls Increment Counter")

    reset_state()
    config = load_config()

    with patch("fable.advisor_cli.GrokService") as MockGrok:
        mock_instance = MagicMock()
        mock_instance.api_key = "fake-key"
        mock_instance.generate.return_value = "Advice text"
        MockGrok.return_value = mock_instance

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

        # Call 4 — should hit cap
        result = get_advice("question 4", config)
        check("call 4 hits cap", "[Advisor] Call cap reached" in result, result[:80])

        state = load_state()
        check("call_count stays at 3 after cap", state["call_count"] == 3, str(state["call_count"]))

    reset_state()


def test_history_tracking():
    section("History Tracking")

    reset_state()
    config = load_config()

    with patch("fable.advisor_cli.GrokService") as MockGrok:
        mock_instance = MagicMock()
        mock_instance.api_key = "fake-key"
        mock_instance.generate.return_value = "Specific advice text here."
        MockGrok.return_value = mock_instance

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
        check("SKILL.md mentions Anti-Gravity", "Anti-Gravity" in content)
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


def test_cli_flag_in_runner():
    section("CLI Flag in fable_runner.py")

    runner_path = Path(__file__).parent.parent / "fable" / "fable_runner.py"
    content = runner_path.read_text()
    check("runner has --advisor argument", "--advisor" in content)
    check("runner imports get_advice", "get_advice" in content)
    check("runner imports load_config", "load_config" in content)


# ─── Live Integration Test (skipped if no token) ─────────────────────────────

def test_live_advisor():
    section("Live Advisor (Grok 4.5 via CLI token)")

    # Check if Grok CLI token exists
    auth_path = Path.home() / ".grok" / "auth.json"
    if not auth_path.exists():
        check("live test skipped — no ~/.grok/auth.json", True, "skipped")
        return

    reset_state()
    config = load_config()

    try:
        result = get_advice(
            "I'm building a REST API for a 50M row dataset. "
            "Should I use offset pagination or cursor-based navigation? "
            "Brief recommendation please.",
            config,
        )

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
    test_no_token_fallback()
    test_multiple_calls_increment()
    test_history_tracking()
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
    assert config.get("advisor_model") == "grok-4.5"
    assert config.get("max_advisor_calls") == 3

def test_state_management_pytest():
    reset_state()
    state = load_state()
    assert state["call_count"] == 0
    assert len(state["history"]) == 0
    reset_state()

def test_cost_control_pytest():
    reset_state()
    state = load_state()
    state["call_count"] = 3
    save_state(state)
    config = load_config()
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
        result = get_advice("test", config)
        assert "cursor pagination" in result
    reset_state()

def test_no_token_pytest():
    reset_state()
    config = load_config()
    with patch("fable.advisor_cli.GrokService") as MockGrok:
        mock_instance = MagicMock()
        mock_instance.api_key = ""
        MockGrok.return_value = mock_instance
        result = get_advice("test", config)
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
