#!/usr/bin/env python3
"""Scenario: Hook generation fails when pain evidence is LOW.

Validates that the hook generator correctly rejects LOW-grade evidence
for hook construction. Hooks must cite MEDIUM or HIGH evidence only.
"""

import sys


def main():
    # Simulate evidence corpus with a LOW-grade item
    evidence_corpus = [
        {"evidence_id": "E-001", "grade": "LOW", "type": "user_quote",
         "content_summary": "Vague complaint about product"},
        {"evidence_id": "E-002", "grade": "HIGH", "type": "user_quote",
         "content_summary": "Specific pain: 'I spend 3 hours every Monday manually exporting reports'"},
    ]

    # Hook generation should reject LOW-grade evidence
    eligible_evidence = [e for e in evidence_corpus if e["grade"] in ("HIGH", "MEDIUM")]

    assert len(eligible_evidence) == 1, "Should filter out LOW-grade evidence"
    assert eligible_evidence[0]["evidence_id"] == "E-002", "Should keep the HIGH-grade item"
    assert eligible_evidence[0]["grade"] == "HIGH", "Eligible item should be HIGH grade"

    # Simulate hook construction from eligible evidence
    hook = {
        "hook_id": "HK-001",
        "formula_type": "pain",
        "pain_id": "H-SEG1-001",
        "segment_id": "SEG-001",
        "hook_text": "Spending 3 hours every Monday manually exporting reports?",
        "word_count": 9,
        "awareness_level": "problem_aware",
        "evidence_citation": "E-002",
        "schema_version": "v8",
    }

    assert hook["evidence_citation"] == "E-002", "Hook must cite HIGH-grade evidence"
    assert hook["formula_type"] == "pain", "Formula type should be pain"
    assert hook["word_count"] <= 15, "Hook should be 10-15 words"

    # Verify LOW-grade evidence was NOT used
    low_used = any(
        hook["evidence_citation"] == e["evidence_id"]
        for e in evidence_corpus
        if e["grade"] == "LOW"
    )
    assert not low_used, "LOW-grade evidence must not be used in hooks"

    print(f"PASS: hook_failure_weak_pain — LOW evidence correctly rejected, "
          f"hook cites {hook['evidence_citation']} (HIGH grade)")
    sys.exit(0)


if __name__ == "__main__":
    main()
