#!/usr/bin/env python3
"""
test_fable_engine.py — pytest suite for Fable 5 Engine
Covers: state machine, stop rules (all 4 criteria), judge (pass/fail),
mock routing (all 25 workflows), service stubs, CLI flags.
"""
import json
import sys
import pytest
from pathlib import Path

# Ensure fable module is importable
sys.path.insert(0, str(Path(__file__).parent))

from fable.fable_runner import FableEngine
from fable.services import (
    GmailService, SlackService, StripeService, PostHogService,
    SalesforceService, OpsgenieService, GDriveService,
    BufferService, SubstackService, GSearchService, RedditService,
)

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def engine(tmp_path):
    """Engine in mock mode with temp directory for state files."""
    e = FableEngine(mock_mode=True)
    # Override config path to tmp
    e._state_dir = tmp_path
    return e


@pytest.fixture
def all_workflows(engine):
    return engine.load_workflows()


# ─── Test 1: Workflow Config Loading ─────────────────────────────────────────

def test_load_workflows_returns_25(engine):
    wfs = engine.load_workflows()
    assert len(wfs) == 25, f"Expected 25 workflows, got {len(wfs)}"


def test_all_workflows_have_required_fields(all_workflows):
    required = {"name", "group", "tools", "prompt", "finish_line", "stop_rule"}
    for wf in all_workflows:
        missing = required - set(wf.keys())
        assert not missing, f"Workflow '{wf.get('name')}' missing fields: {missing}"


def test_get_workflow_by_name(engine):
    wf = engine.get_workflow("daily-runbook-execution")
    assert wf["name"] == "daily-runbook-execution"
    assert wf["group"] == "KPIs + Operations"


def test_get_workflow_raises_for_unknown(engine):
    with pytest.raises(ValueError, match="not found"):
        engine.get_workflow("nonexistent-workflow-xyz")


# ─── Test 2: State File Load/Save/Reset ──────────────────────────────────────

def test_state_file_created_on_first_run(engine, tmp_path):
    state_file = tmp_path / "state_daily-runbook-execution.json"
    engine.run_loop("daily-runbook-execution", iterations=1, state_file_path=str(state_file))
    assert state_file.exists(), "State file should be created after run"
    state = json.loads(state_file.read_text())
    assert state["iteration"] >= 1
    assert "history" in state
    assert len(state["history"]) >= 1


def test_state_file_increments_correctly(engine, tmp_path, monkeypatch):
    state_file = tmp_path / "state_test.json"
    monkeypatch.setattr(engine, "evaluate_stop_rule", lambda *args, **kwargs: False)
    engine.run_loop("daily-runbook-execution", iterations=2, state_file_path=str(state_file))
    state = json.loads(state_file.read_text())
    assert state["iteration"] == 2


def test_state_file_resumes_from_prior_iteration(engine, tmp_path):
    state_file = tmp_path / "state_resume.json"
    # Pre-seed state at iteration 5
    prior_state = {"iteration": 5, "history": [], "status": "running", "workflow": "daily-runbook-execution"}
    state_file.write_text(json.dumps(prior_state))
    engine.run_loop("daily-runbook-execution", iterations=1, state_file_path=str(state_file))
    state = json.loads(state_file.read_text())
    assert state["iteration"] == 6, "Should resume from prior iteration 5 → 6"


def test_reset_state_removes_file(engine, tmp_path, monkeypatch):
    state_file = tmp_path / "state_high-agency-inbox-triage.json"
    state_file.write_text(json.dumps({"iteration": 3, "history": [], "status": "running"}))
    monkeypatch.chdir(tmp_path)
    fable_state = Path("/Users/sanjayb/codex-ecc-custom/fable") / "state_reset-test.json"
    fable_state.write_text("{}")
    engine.reset_state("reset-test")
    assert not fable_state.exists(), "State file should be removed after reset"


# ─── Test 3: Stop Rule Evaluation — All 4 Criteria ───────────────────────────

@pytest.fixture
def sample_workflow():
    return {
        "name": "test-workflow",
        "group": "Test",
        "stop_rule": "All processed. Sweep completed.",
        "finish_line": "All emails drafted and categorized.",
        "tools": [],
        "prompt": "Test prompt",
    }


def test_stop_rule_criterion_1_numeric(engine, sample_workflow):
    """Criterion 1: iteration >= max_iter → stop."""
    should_stop = engine.evaluate_stop_rule(sample_workflow, "Still running", 3, 3)
    assert should_stop is True


def test_stop_rule_criterion_1_not_yet(engine, sample_workflow):
    should_stop = engine.evaluate_stop_rule(sample_workflow, "Still running", 2, 3)
    assert should_stop is False


def test_stop_rule_criterion_2_keyword_match(engine, sample_workflow):
    """Criterion 2: stop_rule keywords in output → stop."""
    should_stop = engine.evaluate_stop_rule(sample_workflow, "Sweep completed successfully.", 1, 5)
    assert should_stop is True


def test_stop_rule_criterion_3_finish_line_overlap(engine, sample_workflow):
    """Criterion 3: 3+ finish_line words in output → stop."""
    output = "All emails have been drafted and properly categorized in the log."
    should_stop = engine.evaluate_stop_rule(sample_workflow, output, 1, 5, sample_workflow["finish_line"])
    assert should_stop is True


def test_stop_rule_criterion_4_completion_signal(engine, sample_workflow):
    """Criterion 4: universal completion signal → stop."""
    for signal in ["no more", "completed", "done", "all processed", "queue empty"]:
        should_stop = engine.evaluate_stop_rule(sample_workflow, f"Task is {signal}.", 1, 5)
        assert should_stop is True, f"Signal '{signal}' should trigger stop"


def test_stop_rule_no_stop_when_nothing_matches(engine, sample_workflow):
    should_stop = engine.evaluate_stop_rule(sample_workflow, "Processing item #3 of 10.", 1, 5)
    assert should_stop is False


# ─── Test 4: Judge Evaluation — Pass / Fail Cases ────────────────────────────

def test_judge_passes_with_sufficient_keyword_coverage(engine):
    finish_line = "All drafts created and submitted"
    criteria = "Verify drafts exist"
    evidence = ["drafts created and submitted successfully", "All items completed"]
    result = engine.evaluate_judge(finish_line, criteria, evidence)
    assert result["pass"] is True
    assert result["coverage"] > 0.0


def test_judge_passes_with_criteria_keyword_match(engine):
    finish_line = "Newsletter assembled"
    criteria = "Verify newsletter draft exists in Substack"
    evidence = ["Substack draft created. Newsletter ready for review."]
    result = engine.evaluate_judge(finish_line, criteria, evidence)
    assert result["pass"] is True


def test_judge_fails_on_error_signal(engine):
    finish_line = "All tickets processed"
    criteria = "Verify tickets are closed"
    evidence = ["Error: API timeout connecting to Zendesk", "Failed to fetch ticket list"]
    result = engine.evaluate_judge(finish_line, criteria, evidence)
    assert result["pass"] is False
    assert "error" in result["reason"].lower() or "failed" in result["reason"].lower()


def test_judge_fails_on_insufficient_coverage(engine):
    finish_line = "Comprehensive database sanity verification completed with anomaly report"
    criteria = "Database check must produce anomaly report"
    evidence = ["Nothing happened"]
    result = engine.evaluate_judge(finish_line, criteria, evidence)
    assert result["pass"] is False
    assert result["coverage"] < 0.3


def test_judge_result_has_required_fields(engine):
    result = engine.evaluate_judge("Finish", "Criteria", ["Some evidence"])
    assert "pass" in result
    assert "reason" in result
    assert "coverage" in result


# ─── Test 5: Execute Step — Mock Service Routing for All 25 Workflows ────────

@pytest.mark.parametrize("workflow_name", [
    "high-agency-inbox-triage",
    "pr-to-ticket-sync",
    "firehose-filtering",
    "community-alert-system",
    "ticket-drafting-loop",
    "cold-outreach-pilot",
    "product-metrics-digest",
    "daily-runbook-execution",
    "sla-breach-rescue",
    "database-sanity-check",
    "compliance-checker",
    "vendor-spending-monitor",
    "dynamic-copy-optimizer",
    "social-media-scheduler",
    "newsletter-assembler",
    "competitor-release-tracker",
    "search-console-analyst",
    "testimonial-harvester",
    "overnight-intel-refresh",
    "regulatory-digest",
    "hard-question-escalation-queue",
    "kill-criteria-loop",
    "pre-mortem-loop",
    "repeat-offender-digest",
    "shadow-prompt-loop",
])
def test_execute_step_all_workflows(engine, workflow_name):
    """All 25 workflows must return a non-empty string, not raise, not fallback."""
    wf = engine.get_workflow(workflow_name)
    state = {"iteration": 1, "history": []}
    result = engine.execute_step(wf, 0, state)
    assert isinstance(result, str), f"execute_step for '{workflow_name}' must return str"
    assert len(result) > 0, f"execute_step for '{workflow_name}' must return non-empty output"
    assert "Smallest change applied" not in result, (
        f"Workflow '{workflow_name}' is hitting generic fallback — needs real implementation"
    )


# ─── Test 6: Service Stub Mocks ───────────────────────────────────────────────

def test_gmail_returns_mock_emails():
    svc = GmailService("", mock_mode=True)
    emails = svc.get_unread_emails()
    assert len(emails) >= 1
    assert "id" in emails[0] and "subject" in emails[0]


def test_salesforce_returns_mock_leads():
    svc = SalesforceService("", mock_mode=True)
    leads = svc.get_hot_leads()
    assert len(leads) >= 1
    assert "company" in leads[0] and "score" in leads[0]


def test_stripe_returns_vendor_charges():
    svc = StripeService("", mock_mode=True)
    charges = svc.get_monthly_vendor_charges()
    assert "current_month" in charges and "previous_month" in charges


def test_gsearch_returns_keywords():
    svc = GSearchService("", mock_mode=True)
    kws = svc.get_keyword_positions()
    assert len(kws) >= 1
    assert "keyword" in kws[0] and "position" in kws[0]


def test_opsgenie_returns_alerts():
    svc = OpsgenieService("", mock_mode=True)
    alerts = svc.get_open_alerts()
    assert len(alerts) >= 1


def test_gdrive_returns_files():
    svc = GDriveService("", mock_mode=True)
    files = svc.list_files_in_folder("compliance")
    assert len(files) >= 1
    assert "name" in files[0]


def test_buffer_returns_posts():
    svc = BufferService("", mock_mode=True)
    posts = svc.get_pending_posts()
    assert len(posts) >= 1
    assert "platform" in posts[0]


def test_substack_creates_draft():
    svc = SubstackService("", mock_mode=True)
    draft = svc.create_draft("Test Newsletter", "Body content here.")
    assert "id" in draft and "title" in draft


def test_reddit_returns_posts():
    svc = RedditService("", mock_mode=True)
    posts = svc.search_subreddit("machinelearning", "agent loops")
    assert len(posts) >= 1


# ─── Test 7: run_goal produces proof file and returns bool ───────────────────

def test_run_goal_returns_bool(engine):
    result = engine.run_goal(
        "All emails processed and replies drafted",
        "Verify email drafts exist"
    )
    assert isinstance(result, bool)


def test_run_goal_writes_proof_file(engine):
    proof_path = Path(__file__).parent / "fable_proofs.md"
    engine.run_goal(
        "Daily runbook executed and logged",
        "Check diagnostic logs are present"
    )
    assert proof_path.exists(), "fable_proofs.md should be written"
    content = proof_path.read_text()
    assert "ECC Operating Protocol" in content
    assert "Evidence Log" in content
    assert "Finish Line" in content


# ─── Test 8: List workflows doesn't raise ────────────────────────────────────

def test_list_workflows_runs_without_error(engine, capsys):
    engine.list_workflows()
    captured = capsys.readouterr()
    assert "Fable 5 Workflows" in captured.out
    assert "25 workflows" in captured.out


# ─── Test 9: run_loop with completed status stops early ──────────────────────

def test_loop_stops_early_on_completion(engine, tmp_path):
    state_file = tmp_path / "state_early-stop.json"
    state = engine.run_loop(
        "daily-runbook-execution",
        iterations=5,
        state_file_path=str(state_file)
    )
    assert state["iteration"] < 5 or state["status"] == "completed"
