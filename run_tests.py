#!/usr/bin/env python3
import sys
import os
import shutil
import tempfile
from pathlib import Path

# Ensure workspace is on path
sys.path.insert(0, str(Path(__file__).parent))

from fable.session_miner import SessionArchaeologist
import test_session_miner

def run_all_tests():
    print("🧪 Running Session Archaeology Unit Tests (Custom Runner)...\n")
    
    # Initialize mock archaeologist
    arch = SessionArchaeologist(workspace_path=str(Path(__file__).parent), mock_mode=True)
    
    tests = [
        ("test_excavate_mock_inventory", lambda: test_session_miner.test_excavate_mock_inventory(arch)),
        ("test_distill_capping_and_triggers", lambda: test_session_miner.test_distill_capping_and_triggers(arch)),
        ("test_run_interview_mock_answers", lambda: test_session_miner.test_run_interview_mock_answers(arch)),
        ("test_mirror_generation", lambda: test_session_miner.test_mirror_generation(arch)),
        ("test_leverage_generation", lambda: test_session_miner.test_leverage_generation(arch)),
        ("test_residue_diff", lambda: test_session_miner.test_residue_diff(arch)),
    ]
    
    # Setup temp path for pytest-style tmp_path fixture
    temp_dir = tempfile.mkdtemp()
    tmp_path = Path(temp_dir)
    
    try:
        tests += [
            ("test_playbook_load_save", lambda: test_session_miner.test_playbook_load_save(tmp_path)),
            ("test_review_rule_extraction", lambda: test_session_miner.test_review_rule_extraction(arch, tmp_path)),
            ("test_runner_playbook_injection", lambda: test_session_miner.test_runner_playbook_injection(tmp_path)),
            ("test_self_improve_loop", lambda: test_session_miner.test_self_improve_loop(tmp_path)),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            print(f"Running {name}...")
            try:
                test_func()
                print(f"  ✅ {name} passed!")
                passed += 1
            except Exception as e:
                print(f"  ❌ {name} FAILED! Error: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
            print("-" * 50)
            
        print(f"\n📊 RESULTS: {passed} passed, {failed} failed.")
        if failed > 0:
            sys.exit(1)
        else:
            print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
            sys.exit(0)
            
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    run_all_tests()
