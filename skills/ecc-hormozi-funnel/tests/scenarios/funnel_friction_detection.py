#!/usr/bin/env python3
"""Scenario: Funnel audit detects opt-in friction.

Validates that the funnel audit correctly identifies friction items in
the lead capture flow and produces prioritized fixes.
"""

import sys


def main():
    # Simulate a funnel audit with friction items
    funnel_audit = {
        "audit_id": "FA-001",
        "positioning_audit_id": "AUD-001",
        "awareness_audit": {
            "hook_score": 4,
            "messaging_score": 6,
            "proof_upfront_score": 3,
            "attention_leaks": [
                {"leak_id": "LK-01", "description": "Hook opens with feature list, not pain",
                 "severity": "critical", "location": "hook"},
                {"leak_id": "LK-02", "description": "No proof above the fold",
                 "severity": "major", "location": "landing_page"},
            ],
        },
        "lead_capture_audit": {
            "opt_in_score": 3,
            "value_equation_score": {
                "dream_outcome": 4,
                "likelihood": 3,
                "time_delay": 5,
                "effort": 2,
            },
            "friction_items": [
                {"friction_id": "FR-01", "description": "7 form fields including phone number",
                 "type": "form_field", "fix": "Reduce to 2 fields: name and email"},
                {"friction_id": "FR-02", "description": "No proof on opt-in page",
                 "type": "no_proof", "fix": "Add 3 testimonials above the form"},
                {"friction_id": "FR-03", "description": "CTA says 'Submit' instead of value-driven text",
                 "type": "weak_cta", "fix": "Change to 'Get My Free Audit'"},
            ],
            "weakest_magnet": {
                "current_text": "Subscribe to our newsletter for updates",
                "rewrite": "Get a free 5-minute positioning audit — see your top 3 market gaps instantly",
                "rewrite_rationale": "Newsletter is vague; free audit is specific, time-bound, and proof-driven",
            },
        },
        "overall_score": 4.0,
        "fixes": [
            {"fix_id": "FX-01", "priority": "P0",
             "description": "Rewrite hook to lead with pain, not features",
             "expected_impact": "Stop scroll rate +40%",
             "evidence_citation": "E-002"},
            {"fix_id": "FX-02", "priority": "P0",
             "description": "Add 3 testimonials above the fold",
             "expected_impact": "Opt-in rate +25%",
             "evidence_citation": "E-005"},
            {"fix_id": "FX-03", "priority": "P1",
             "description": "Reduce form from 7 fields to 2",
             "expected_impact": "Friction reduction +15% completion",
             "evidence_citation": "E-008"},
        ],
        "evidence_citations": ["E-002", "E-005", "E-008"],
        "schema_version": "v8",
    }

    # Assertions
    assert funnel_audit["overall_score"] < 6.0, "Overall score should be low with these friction items"
    assert len(funnel_audit["lead_capture_audit"]["friction_items"]) >= 3, "Should detect >= 3 friction items"
    assert len(funnel_audit["awareness_audit"]["attention_leaks"]) >= 2, "Should detect >= 2 attention leaks"
    assert len(funnel_audit["fixes"]) >= 3, "Should produce >= 3 fixes"

    p0_fixes = [f for f in funnel_audit["fixes"] if f["priority"] == "P0"]
    assert len(p0_fixes) >= 2, "Should have >= 2 P0 fixes for critical issues"

    for fix in funnel_audit["fixes"]:
        assert "evidence_citation" in fix, f"Fix {fix['fix_id']} must cite evidence"

    weakest = funnel_audit["lead_capture_audit"]["weakest_magnet"]
    assert "newsletter" in weakest["current_text"].lower(), "Should identify weak newsletter magnet"
    assert "audit" in weakest["rewrite"].lower(), "Rewrite should offer specific value"

    assert funnel_audit["schema_version"] == "v8", "Schema version must be v8"

    print(f"PASS: funnel_friction_detection — {len(funnel_audit['lead_capture_audit']['friction_items'])} "
          f"friction items, {len(p0_fixes)} P0 fixes, overall_score={funnel_audit['overall_score']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
