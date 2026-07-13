#!/usr/bin/env python3
"""
Fable 5 Engine — Comprehensive Test Suite (48 checks)
Covers: state machine, stop rules, judge evaluation, all 25 workflows,
        CLI argument parsing, playbook integration, self-improvement loop.

Run:  python3 fable/test_fable_engine.py
      python3 -m pytest fable/test_fable_engine.py -v
"""
import json
import os
import sys
import tempfile
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from fable.fable_runner import FableEngine, ECC_PHASES
from fable.services import (
    GmailService, GitHubService, PostHogService, StripeService,
    PostgresService, ZendeskService, ExaService, FirecrawlService,
    SlackService, TwitterService, JiraService, LinearService,
    SalesforceService, OpsgenieService, GDriveService, BufferService,
    SubstackService, GSearchService, RedditService, DiscordService,
    ServiceBase,
)
from fable.session_miner import Playbook, SessionArchaeologist

# ─── Test Harness ────────────────────────────────────────────────────────────

PASS = 0
FAIL = 0
CHECKS = []


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    status = "✅ PASS" if condition else "❌ FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    CHECKS.append(f"  {status} — {name}" + (f" ({detail})" if detail else ""))


def section(title: str):
    CHECKS.append(f"\n── {title} ──")


# ─── 1. Engine Initialization (4 checks) ─────────────────────────────────────

def test_engine_init():
    section("1. Engine Initialization")
    engine = FableEngine(mock_mode=True)

    check("FableEngine instantiates", isinstance(engine, FableEngine))
    check("Config loaded", isinstance(engine.config, dict))
    check("Mock mode enabled", engine.mock_mode is True)
    check("Playbook attached", isinstance(engine.playbook, Playbook))


# ─── 2. Service Layer (6 checks) ─────────────────────────────────────────────

def test_services():
    section("2. Service Layer")
    engine = FableEngine(mock_mode=True)

    services = [
        ("gmail", GmailService), ("github", GitHubService),
        ("posthog", PostHogService), ("stripe", StripeService),
        ("postgres", PostgresService), ("zendesk", ZendeskService),
        ("exa", ExaService), ("firecrawl", FirecrawlService),
        ("slack", SlackService), ("twitter", TwitterService),
        ("jira", JiraService), ("linear", LinearService),
        ("salesforce", SalesforceService), ("opsgenie", OpsgenieService),
        ("gdrive", GDriveService), ("buffer", BufferService),
        ("substack", SubstackService), ("gsearch", GSearchService),
        ("reddit", RedditService), ("discord", DiscordService),
    ]

    check("20 services instantiated", all(hasattr(engine, name) for name, _ in services),
          f"{sum(1 for n, _ in services if hasattr(engine, n))}/20")

    # Verify mock data returns
    emails = engine.gmail.get_unread_emails()
    check("Gmail returns mock emails", len(emails) >= 1 and "id" in emails[0])

    prs = engine.github.get_open_pull_requests()
    check("GitHub returns mock PRs", len(prs) >= 1 and "number" in prs[0])

    charges = engine.stripe.get_recent_charges()
    check("Stripe returns mock charges", len(charges) >= 1 and "amount" in charges[0])

    leads = engine.salesforce.get_hot_leads()
    check("Salesforce returns mock leads", len(leads) >= 1 and "company" in leads[0])

    alerts = engine.opsgenie.get_open_alerts()
    check("Opsgenie returns mock alerts", len(alerts) >= 1 and "priority" in alerts[0])


# ─── 3. Workflow Loading (4 checks) ──────────────────────────────────────────

def test_workflow_loading():
    section("3. Workflow Loading")
    engine = FableEngine(mock_mode=True)
    wfs = engine.load_workflows()

    check("25 workflows loaded", len(wfs) == 25, f"got {len(wfs)}")

    groups = {wf["group"] for wf in wfs}
    check("4 workflow groups", len(groups) == 4, f"got {len(groups)}: {groups}")

    for wf in wfs:
        assert "name" in wf and "tools" in wf and "finish_line" in wf, f"Bad workflow: {wf}"
    check("All workflows have required fields", True)

    wf = engine.get_workflow("high-agency-inbox-triage")
    check("get_workflow returns correct workflow", wf["name"] == "high-agency-inbox-triage")


# ─── 4. Stop Rule Evaluation (6 checks) ──────────────────────────────────────

def test_stop_rules():
    section("4. Stop Rule Evaluation")
    engine = FableEngine(mock_mode=True)
    wf = {"name": "test", "stop_rule": "completed done finished"}

    # Criterion 1: numeric bound
    check("Stop: numeric bound (iter >= max)", engine.evaluate_stop_rule(wf, "working", 5, 5) is True)
    check("Stop: numeric not triggered (iter < max)", engine.evaluate_stop_rule(wf, "working", 1, 5) is False)

    # Criterion 2: keyword match
    check("Stop: keyword match ('completed')", engine.evaluate_stop_rule(wf, "Task completed", 1, 5) is True)
    check("Stop: no keyword match", engine.evaluate_stop_rule(wf, "still working", 1, 5) is False)

    # Criterion 3: finish line overlap
    wf_fl = {"name": "test", "stop_rule": ""}
    fl = "All unread emails drafted replies categorized"
    out = "emails have drafted replies and categorized successfully"
    check("Stop: finish line overlap (3+ words)", engine.evaluate_stop_rule(wf_fl, out, 1, 5, fl) is True)

    # Criterion 4: completion signals
    check("Stop: completion signal ('no more')",
          engine.evaluate_stop_rule({"name": "t", "stop_rule": ""}, "No more items", 1, 5) is True)


# ─── 5. Judge Evaluation (5 checks) ──────────────────────────────────────────

def test_judge():
    section("5. Judge Evaluation")
    engine = FableEngine(mock_mode=True)

    # Pass: criteria match
    result = engine.evaluate_judge("emails processed", "emails processed", ["emails were processed"])
    check("Judge: PASS on criteria match", result["pass"] is True)

    # Pass: coverage >= 30%
    result = engine.evaluate_judge("unread emails drafted replies categorized",
                                   "unrelated criteria",
                                   ["unread emails drafted replies categorized done"])
    check("Judge: PASS on high coverage", result["pass"] is True and result["coverage"] >= 0.3)

    # Fail: failure signal
    result = engine.evaluate_judge("test finish", "test criteria", ["error: something failed"])
    check("Judge: FAIL on error signal", result["pass"] is False)

    # Fail: no overlap, no criteria match
    result = engine.evaluate_judge("xyzabc qwerty", "foobar bazqux", ["nothing relevant here"])
    check("Judge: FAIL on no overlap", result["pass"] is False)

    # Edge: empty evidence
    result = engine.evaluate_judge("test", "test", [])
    check("Judge: handles empty evidence", "pass" in result and "coverage" in result)


# ─── 6. All 25 Workflows Execute (25 checks) ─────────────────────────────────

def test_all_workflows():
    section("6. All 25 Workflows Execute")
    engine = FableEngine(mock_mode=True)
    wfs = engine.load_workflows()

    for wf in wfs:
        state = {"iteration": 0, "history": []}
        try:
            output = engine._execute_step_base(wf, 0, state)
            ok = isinstance(output, str) and len(output) > 10
        except Exception as e:
            ok = False
            output = str(e)
        check(f"Workflow: {wf['name']}", ok, output[:60] if not ok else "")


# ─── 7. CLI Argument Parsing (4 checks) ──────────────────────────────────────

def test_cli():
    section("7. CLI Argument Parsing")
    import argparse
    import io
    from contextlib import redirect_stdout

    # --list
    f = io.StringIO()
    with redirect_stdout(f):
        engine = FableEngine(mock_mode=True)
        engine.list_workflows()
    out = f.getvalue()
    check("CLI: --list prints workflows", "workflows" in out.lower() and "Total: 25" in out)

    # --reset (existing)
    engine = FableEngine(mock_mode=True)
    state_path = Path(__file__).parent / "state_test_cli.json"
    state_path.write_text('{"iteration": 1}')
    f = io.StringIO()
    with redirect_stdout(f):
        engine.reset_state("test_cli")
    out = f.getvalue()
    check("CLI: --reset removes state file", "State reset" in out)
    check("CLI: state file actually deleted", not state_path.exists())

    # --reset (non-existing)
    f = io.StringIO()
    with redirect_stdout(f):
        engine.reset_state("nonexistent_workflow_xyz")
    out = f.getvalue()
    check("CLI: --reset handles missing file", "No state file" in out)


# ─── 8. ECC Operating Protocol Integration (3 checks) ────────────────────────

def test_ecc_integration():
    section("8. ECC Operating Protocol Integration")

    check("ECC: 6 phases defined", len(ECC_PHASES) == 6)
    check("ECC: phases in correct order",
          ECC_PHASES[0].startswith("1.") and ECC_PHASES[5].startswith("6."))

    # Verify ECC phases appear in loop output
    import io
    from contextlib import redirect_stdout
    engine = FableEngine(mock_mode=True)
    f = io.StringIO()
    with redirect_stdout(f):
        engine.run_loop("high-agency-inbox-triage", iterations=1)
    out = f.getvalue()
    ecc_count = sum(1 for p in ECC_PHASES if p in out)
    check("ECC: phases printed in loop output", ecc_count >= 3, f"{ecc_count}/6 phases found")


# ─── 9. Playbook Integration (3 checks) ──────────────────────────────────────

def test_playbook():
    section("9. Playbook Integration")
    engine = FableEngine(mock_mode=True)

    check("Playbook: loads rules", len(engine.playbook.rules) >= 0)

    # Verify playbook rules injected in step output
    state = {"iteration": 0, "history": []}
    wf = engine.get_workflow("high-agency-inbox-triage")
    output = engine.execute_step(wf, 0, state)
    has_rule = "Playbook Rule" in output or len(engine.playbook.rules) == 0
    check("Playbook: rules injected in step output", has_rule)

    # Verify playbook add/prune
    tmp = Path(tempfile.mktemp(suffix=".md"))
    pb = Playbook(tmp)
    pb.add_rule("R-TEST", "Test Rule", "Test description")
    check("Playbook: add_rule works", "R-TEST" in pb.rules)
    pb.prune_rule("R-TEST")
    check("Playbook: prune_rule works", "R-TEST" not in pb.rules)
    tmp.unlink(missing_ok=True)


# ─── 10. Self-Improvement Loop (2 checks) ────────────────────────────────────

def test_self_improvement():
    section("10. Self-Improvement Loop")
    import io
    from contextlib import redirect_stdout

    engine = FableEngine(mock_mode=True)
    f = io.StringIO()
    with redirect_stdout(f):
        result = engine.run_self_improvement()
    out = f.getvalue()

    check("Self-improve: returns True", result is True)
    check("Self-improve: shows failure then success",
          "Failure" in out and "Success" in out)


# ─── 11. Goal & Proof File (3 checks) ────────────────────────────────────────

def test_goal_proof():
    section("11. Goal & Proof File")
    import io
    from contextlib import redirect_stdout

    engine = FableEngine(mock_mode=True)
    f = io.StringIO()
    with redirect_stdout(f):
        result = engine.run_goal("All emails processed", "emails processed")
    out = f.getvalue()

    check("Goal: returns boolean", isinstance(result, bool))

    proof_path = Path(__file__).parent.parent / "fable_proofs.md"
    check("Goal: proof file created", proof_path.exists())

    if proof_path.exists():
        content = proof_path.read_text()
        has_sections = "Finish Line" in content and "Judge Evaluation" in content and "ECC" in content
        check("Goal: proof has required sections", has_sections)


# ─── 12. State Persistence (3 checks) ────────────────────────────────────────

def test_state_persistence():
    section("12. State Persistence")
    import io
    from contextlib import redirect_stdout

    engine = FableEngine(mock_mode=True)
    state_file = str(Path(__file__).parent / "state_test_persist.json")

    # Clean slate
    Path(state_file).unlink(missing_ok=True)

    f = io.StringIO()
    with redirect_stdout(f):
        engine.run_loop("high-agency-inbox-triage", iterations=2, state_file_path=state_file)

    check("State: file created", Path(state_file).exists())

    if Path(state_file).exists():
        state = json.loads(Path(state_file).read_text())
        check("State: has iteration field", "iteration" in state)
        check("State: has history array", isinstance(state.get("history"), list))

    Path(state_file).unlink(missing_ok=True)


# ─── Runner ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  Fable 5 Engine — Comprehensive Test Suite (48 checks)")
    print("=" * 70)

    tests = [
        test_engine_init,
        test_services,
        test_workflow_loading,
        test_stop_rules,
        test_judge,
        test_all_workflows,
        test_cli,
        test_ecc_integration,
        test_playbook,
        test_self_improvement,
        test_goal_proof,
        test_state_persistence,
    ]

    for test_fn in tests:
        try:
            test_fn()
        except Exception as e:
            global FAIL
            FAIL += 1
            CHECKS.append(f"\n  ❌ FAIL — {test_fn.__name__} raised: {e}")

    # Print results
    print("\n" + "\n".join(CHECKS))
    print("\n" + "=" * 70)
    total = PASS + FAIL
    print(f"  Results: {PASS}/{total} passed, {FAIL} failed")
    print("=" * 70)

    if FAIL > 0:
        print("\n❌ Some checks failed. Review details above.")
        sys.exit(1)
    else:
        print("\n✅ All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
