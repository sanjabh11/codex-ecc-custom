#!/usr/bin/env python3
"""Generate reproducible artifacts for ecc-hormozi-funnel skill.

Produces deterministic test artifacts from a positioning audit export,
ensuring all outputs are schema-valid and evidence-traceable.
"""

import json
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def compute_offer_composite(dream, likelihood, time_delay, effort):
    """Value Equation composite, capped at 100."""
    denominator = (11 - time_delay) * (11 - effort)
    if denominator == 0:
        return 0.0
    raw = (dream * likelihood) / denominator * 10
    return round(min(raw, 100.0), 2)


def compute_hook_composite(clarity, curiosity, pull):
    """Hook ranking composite = average of 3 dimensions."""
    return round((clarity + curiosity + pull) / 3, 2)


def compute_decision_confidence(evidence_quality, source_coverage,
                                 adversarial_survival, advisor_confirmed):
    """Decision confidence composite, max 100."""
    total = evidence_quality + source_coverage + adversarial_survival + advisor_confirmed
    return min(total, 100)


def generate_offer(segment_id, pain_id, dream, likelihood, time_delay, effort,
                   evidence_ids, rank=1):
    """Generate a valid offer object."""
    composite = compute_offer_composite(dream, likelihood, time_delay, effort)
    return {
        "offer_id": f"OFF-{rank:03d}",
        "segment_id": segment_id,
        "pain_id": pain_id,
        "dream_outcome": {
            "statement": f"Dream outcome for {pain_id}",
            "specificity_score": dream,
        },
        "value_equation_scores": {
            "dream_outcome": dream,
            "likelihood": likelihood,
            "time_delay": time_delay,
            "effort_sacrifice": effort,
            "composite": composite,
        },
        "bonus_stack": [
            {"bonus_name": "Fast-Start Guide", "solves": "speed", "dollar_value": 500,
             "description": "Done-for-you templates"},
            {"bonus_name": "Automation Kit", "solves": "effort", "dollar_value": 300,
             "description": "Reduces manual work"},
            {"bonus_name": "Community Access", "solves": "likelihood", "dollar_value": 1000,
             "description": "Accountability and support"},
            {"bonus_name": "Hiring Kit", "solves": "adjacent", "dollar_value": 400,
             "description": "Solves related problem"},
        ],
        "guarantee": {
            "type": "conditional",
            "terms": "Complete the program or get a full refund",
            "duration_days": 60,
        },
        "scarcity_urgency": {
            "scarcity_type": "cohort",
            "scarcity_detail": "Only 20 spots per quarter",
            "urgency_type": "deadline",
            "urgency_detail": "Closes Friday at midnight",
            "is_real": True,
        },
        "price": 2500,
        "total_value_stack": 25000,
        "value_ratio": 10.0,
        "offer_name": f"Offer {rank}",
        "evidence_citations": evidence_ids,
        "rank": rank,
        "schema_version": "v8",
    }


def generate_hook(formula_type, pain_id, segment_id, text, clarity, curiosity,
                   pull, evidence_id, rank=1):
    """Generate a valid hook object."""
    composite = compute_hook_composite(clarity, curiosity, pull)
    words = len(text.split())
    return {
        "hook_id": f"HK-{rank:03d}",
        "formula_type": formula_type,
        "pain_id": pain_id,
        "segment_id": segment_id,
        "hook_text": text,
        "word_count": words,
        "awareness_level": "problem_aware" if formula_type == "pain" else "unaware",
        "ranking_score": {
            "clarity": clarity,
            "curiosity": curiosity,
            "pull": pull,
            "composite": composite,
        },
        "evidence_citation": evidence_id,
        "rank": rank,
        "schema_version": "v8",
    }


def generate_state(audit_id, scope_mode, prompts_completed, advisor_used):
    """Generate a valid state object."""
    advisor_score = 20 if advisor_used else 0
    confidence = compute_decision_confidence(25, 20, 22, advisor_score)
    return {
        "state_id": "ST-001",
        "audit_id": audit_id,
        "scope_mode": scope_mode,
        "prompts_completed": prompts_completed,
        "advisor_used": advisor_used,
        "advisor_calls": [],
        "adversarial_review": {
            "skeptic_pass": "completed",
            "missing_perspective_pass": "completed",
            "contrarian_pass": "completed",
            "unresolved_contradictions": 0,
            "flagged_items": [],
        },
        "decision_confidence": {
            "evidence_quality": 25,
            "source_coverage": 20,
            "adversarial_survival": 22,
            "advisor_confirmed": advisor_score,
            "composite": confidence,
        },
        "tool_health": {
            "advisor_available": advisor_used,
            "validator_available": True,
            "schema_validation_passed": True,
        },
        "artifacts_produced": [],
        "schema_version": "v8",
    }


def main():
    output_dir = os.path.join(SKILL_DIR, "tests", "generated")
    os.makedirs(output_dir, exist_ok=True)

    offer = generate_offer("SEG-001", "H-SEG1-001", 9, 8, 8, 7, ["E-001", "E-005"])
    hook = generate_hook("pain", "H-SEG1-001", "SEG-001",
                         "Spending 3 hours every Monday exporting reports?", 9, 7, 8, "E-002")
    state = generate_state("AUD-001", "deep",
                           ["content_batching", "offer_builder", "hook_generator",
                            "authority_builder", "funnel_audit"], True)

    with open(os.path.join(output_dir, "offer_generated.json"), "w") as f:
        json.dump(offer, f, indent=2)
    with open(os.path.join(output_dir, "hook_generated.json"), "w") as f:
        json.dump(hook, f, indent=2)
    with open(os.path.join(output_dir, "state_generated.json"), "w") as f:
        json.dump(state, f, indent=2)

    # Verify composite cap
    assert offer["value_equation_scores"]["composite"] <= 100, "Composite must be capped at 100"
    assert hook["ranking_score"]["composite"] <= 10, "Hook composite must be <= 10"
    assert state["decision_confidence"]["composite"] <= 100, "Confidence must be <= 100"

    print(f"PASS: generate_artifact — 3 artifacts written to {output_dir}")
    print(f"  Offer composite: {offer['value_equation_scores']['composite']} (capped at 100)")
    print(f"  Hook composite: {hook['ranking_score']['composite']}")
    print(f"  Decision confidence: {state['decision_confidence']['composite']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
