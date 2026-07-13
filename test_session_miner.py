#!/usr/bin/env python3
"""
test_session_miner.py — Pytest suite for Fable Session Archaeology Engine
Covers: excavation file discovery, distillation triggers/sweeps/capping/sampling,
interview Q&A progression, mirror & leverage generation, residue diffs.
"""
import sys
import pytest
from pathlib import Path

# Ensure fable is importable
sys.path.insert(0, str(Path(__file__).parent))

from fable.session_miner import SessionArchaeologist

@pytest.fixture
def archaeologist():
    """Initializes the archaeologist in mock mode."""
    return SessionArchaeologist(workspace_path=str(Path(__file__).parent), mock_mode=True)

# ─── Test Phase 1: Excavate ──────────────────────────────────────────────────

def test_excavate_mock_inventory(archaeologist):
    inv = archaeologist.excavate()
    assert len(inv["claude_projects"]) == 2
    assert len(inv["hermes_sessions"]) == 2
    assert inv["hermes_db_exists"] is True
    assert inv["hermes_msg_count"] == 1450
    assert inv["bash_log_exists"] is True
    assert inv["bash_log_size"] > 0

# ─── Test Phase 2: Distill ───────────────────────────────────────────────────

def test_distill_capping_and_triggers(archaeologist):
    res = archaeologist.distill(max_files=10, max_lines_per_file=50)
    assert res["files_processed"] == 4  # 2 claude + 2 hermes
    assert res["triggers"]["again"] > 0
    assert len(res["receipts"]) > 0
    assert res["receipts"][0]["trigger"] == "again"

# ─── Test Phase 3: Interview ──────────────────────────────────────────────────

def test_run_interview_mock_answers(archaeologist):
    mock_answers = {
        "H1": "yes",
        "H2": "no",
        "H3": "yes",
        "H4": "yes",
        "H5": "no"
    }
    answers = archaeologist.run_interview(mock_answers=mock_answers)
    assert answers["H1"] == "yes"
    assert answers["H2"] == "no"
    assert answers["H3"] == "yes"

# ─── Test Phase 4 & 5: Mirror & Leverage ─────────────────────────────────────

def test_mirror_generation(archaeologist):
    answers = {"H1": "yes", "H2": "yes", "H3": "yes", "H4": "yes", "H5": "yes"}
    mirror = archaeologist.generate_mirror(answers)
    assert "Ruthless Self-Portrait Summary" in mirror
    assert "Meta-Builder Identity" in mirror
    assert "Avoidance of Deployments" in mirror

def test_leverage_generation(archaeologist):
    leverage = archaeologist.generate_leverage()
    assert "Leverage Action Items" in leverage
    assert "Waste" in leverage
    assert "Delegate" in leverage
    assert "Rhythm" in leverage

# ─── Test Phase 6: Residue ───────────────────────────────────────────────────

def test_residue_diff(archaeologist):
    diff = archaeologist.residue(apply=False)
    assert "AGENTS.md" in diff

# ─── System Prompt Learning Integration Tests ─────────────────────────────────

def test_playbook_load_save(tmp_path):
    from fable.session_miner import Playbook
    playbook_file = tmp_path / "playbook.md"
    playbook = Playbook(playbook_file)
    
    # Verify initial empty
    assert len(playbook.rules) == 0
    
    # Add rules
    playbook.add_rule("R-101", "Test Rule", "Test Description", "2026-07-08")
    assert len(playbook.rules) == 1
    assert playbook.rules["R-101"]["title"] == "Test Rule"
    
    # Save and reload
    playbook.save()
    
    playbook2 = Playbook(playbook_file)
    assert len(playbook2.rules) == 1
    assert playbook2.rules["R-101"]["title"] == "Test Rule"
    
    # Prune rule
    playbook2.prune_rule("R-101", "2026-07-08")
    assert len(playbook2.rules) == 0

def test_review_rule_extraction(archaeologist, tmp_path):
    archaeologist.playbook_path = tmp_path / "playbook.md"
    from fable.session_miner import Playbook
    archaeologist.playbook = Playbook(archaeologist.playbook_path)
    
    distill_results = {
        "triggers": {"again": 5, "instead of": 3, "wrong": 4, "error": 2, "mismatch": 1},
        "receipts": []
    }
    
    rules = archaeologist.review(distill_results)
    assert len(rules) == 3
    assert any(r["id"] == "R-101" for r in rules)
    assert any(r["id"] == "R-102" for r in rules)
    assert any(r["id"] == "R-103" for r in rules)

def test_runner_playbook_injection(tmp_path):
    from fable.fable_runner import FableEngine
    engine = FableEngine(mock_mode=True)
    engine.playbook_path = tmp_path / "playbook.md"
    from fable.session_miner import Playbook
    engine.playbook = Playbook(engine.playbook_path)
    
    # Add R-101 to playbook
    engine.playbook.add_rule("R-101", "Decompose Reasoning", "Decompose reasoning.", "2026-07-08")
    
    workflow = {
        "name": "daily-runbook-execution",
        "group": "KPIs + Operations",
        "prompt": "Test prompt"
    }
    output = engine.execute_step(workflow, 0, {"iteration": 1, "history": []})
    assert "[Playbook Rule R-101 Adhered]" in output

def test_self_improve_loop(tmp_path):
    from fable.fable_runner import FableEngine
    engine = FableEngine(mock_mode=True)
    engine.playbook_path = tmp_path / "playbook.md"
    from fable.session_miner import Playbook
    engine.playbook = Playbook(engine.playbook_path)
    
    success = engine.run_self_improvement()
    assert success is True
    
    # Check that playbook.md contains the generated rules
    engine.playbook.load()
    assert len(engine.playbook.rules) > 0
