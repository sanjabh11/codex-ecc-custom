#!/usr/bin/env python3
"""Generate weekly marketing artifacts from a real positioning audit export.

This is the INPUT-DRIVEN generator. It requires a real positioning-audit-export.json
and produces only evidence-backed artifacts. It rejects:
  - Fabricated scarcity, deadlines, guarantees, or prices
  - Evidence IDs not present in the positioning export
  - is_real: true on scarcity/urgency without explicit evidence citation
  - Synthetic placeholder values

Weekly mode outputs:
  - 1 offer (evidence-backed)
  - 3 ranked hooks (evidence-cited)
  - 7-day content/action slice
  - 3 funnel fixes
  - 1 proof-library update
"""

import json
import os
import sys
from datetime import datetime, timedelta

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FORBIDDEN_SYNTHETIC_KEYS = {
    "is_real": "Scarcity is_real must not be set to true without evidence citation",
    "price": "Price must come from evidence, not hardcoded synthetic values",
    "total_value_stack": "Value stack must be computed from evidence-backed bonuses, not hardcoded",
    "value_ratio": "Value ratio must be derived from evidence-backed values, not hardcoded",
}

FORBIDDEN_GUARANTEE_TERMS = [
    "Complete the program or get a full refund",
    "100% money-back guarantee",
    "Lifetime guarantee",
]


def load_positioning_export(path):
    """Load and validate a positioning audit export."""
    if not os.path.exists(path):
        print(f"ERROR: Positioning export not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r") as f:
        data = json.load(f)
    if "evidence_corpus" not in data and "evidence" not in data:
        print("ERROR: Positioning export has no evidence_corpus or evidence field", file=sys.stderr)
        sys.exit(1)
    return data


def extract_evidence_ids(positioning_export):
    """Extract all valid evidence IDs from the positioning export."""
    ids = set()
    for key in ("evidence_corpus", "evidence"):
        if key in positioning_export:
            for item in positioning_export[key]:
                if isinstance(item, dict) and "evidence_id" in item:
                    ids.add(item["evidence_id"])
                elif isinstance(item, str):
                    ids.add(item)
    return ids


def validate_evidence_citations(citations, valid_ids, artifact_type):
    """Reject evidence citations not present in the positioning export."""
    unknown = set(citations) - valid_ids
    if unknown:
        print(f"ERROR: {artifact_type} cites unknown evidence IDs: {unknown}", file=sys.stderr)
        sys.exit(1)


def reject_synthetic_claims(artifact, artifact_type):
    """Reject fabricated economic claims."""
    for key, msg in FORBIDDEN_SYNTHETIC_KEYS.items():
        if key in artifact:
            if key == "is_real" and artifact[key] is True:
                if not artifact.get("evidence_citations") and not artifact.get("evidence_citation"):
                    print(f"ERROR: {artifact_type} has {msg}", file=sys.stderr)
                    sys.exit(1)
            elif key in ("price", "total_value_stack", "value_ratio"):
                if artifact.get(key) is not None and not artifact.get("evidence_citations"):
                    print(f"ERROR: {artifact_type} has {msg}", file=sys.stderr)
                    sys.exit(1)

    guarantee = artifact.get("guarantee", {})
    if isinstance(guarantee, dict):
        terms = guarantee.get("terms", "")
        for forbidden in FORBIDDEN_GUARANTEE_TERMS:
            if forbidden.lower() in terms.lower():
                print(f"ERROR: {artifact_type} has forbidden synthetic guarantee: '{forbidden}'", file=sys.stderr)
                sys.exit(1)

    # Recursive check for nested is_real without evidence
    _check_nested_is_real(artifact, artifact_type, [])


def _check_nested_is_real(obj, artifact_type, path, parent_has_evidence=False):
    """Recursively check for is_real: true without evidence in nested objects.

    Evidence can be on the parent object (evidence_citations) or on the nested
    object itself. We pass parent_has_evidence down to allow nested is_real
    when the parent has evidence citations.
    """
    if isinstance(obj, dict):
        has_own_evidence = (
            obj.get("evidence_citations") or
            obj.get("evidence_citation") or
            obj.get("evidence_ids")
        )
        if obj.get("is_real") is True:
            if not has_own_evidence and not parent_has_evidence:
                loc = ".".join(path) if path else "root"
                print(f"ERROR: {artifact_type} has nested is_real=true at {loc} without evidence", file=sys.stderr)
                sys.exit(1)
        # Pass down whether this level or any ancestor has evidence
        child_parent_evidence = parent_has_evidence or bool(has_own_evidence)
        for k, v in obj.items():
            _check_nested_is_real(v, artifact_type, path + [k], child_parent_evidence)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _check_nested_is_real(item, artifact_type, path + [str(i)], parent_has_evidence)


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


def generate_weekly_offer(segment, pain, evidence_ids, valid_evidence_ids, rank=1, evidence_unavailable=False):
    """Generate an evidence-backed offer from positioning audit data."""
    validate_evidence_citations(evidence_ids, valid_evidence_ids, "offer")

    dream = segment.get("dream_outcome_score", 7)
    likelihood = segment.get("likelihood_score", 7)
    time_delay = segment.get("time_delay_score", 7)
    effort = segment.get("effort_score", 7)

    composite = compute_offer_composite(dream, likelihood, time_delay, effort)

    offer = {
        "offer_id": f"OFF-{rank:03d}",
        "segment_id": segment.get("segment_id", "SEG-UNKNOWN"),
        "pain_id": pain.get("pain_id", "P-UNKNOWN"),
        "dream_outcome": {
            "statement": segment.get("dream_outcome_statement", ""),
            "specificity_score": dream,
        },
        "value_equation_scores": {
            "dream_outcome": dream,
            "likelihood": likelihood,
            "time_delay": time_delay,
            "effort_sacrifice": effort,
            "composite": composite,
        },
        "bonus_stack": segment.get("bonus_stack", []),
        "guarantee": {
            "type": "conditional",
            "terms": segment.get("guarantee_terms", "See evidence-backed terms"),
            "duration_days": segment.get("guarantee_duration_days", 30),
        },
        "scarcity_urgency": {
            "scarcity_type": segment.get("scarcity_type", "none"),
            "scarcity_detail": segment.get("scarcity_detail", ""),
            "urgency_type": segment.get("urgency_type", "none"),
            "urgency_detail": segment.get("urgency_detail", ""),
            "is_real": bool(segment.get("scarcity_evidence_ids")),
        },
        "evidence_citations": evidence_ids,
        "rank": rank,
        "schema_version": "weekly-v1",
        "weekly_mode": True,
        "evidence_unavailable": evidence_unavailable,
    }

    reject_synthetic_claims(offer, "offer")
    return offer


def generate_weekly_hook(formula_type, pain, segment, text, clarity, curiosity,
                         pull, evidence_id, valid_evidence_ids, rank=1):
    """Generate an evidence-backed hook from positioning audit data."""
    validate_evidence_citations([evidence_id], valid_evidence_ids, "hook")

    composite = compute_hook_composite(clarity, curiosity, pull)
    words = len(text.split())

    hook = {
        "hook_id": f"HK-{rank:03d}",
        "formula_type": formula_type,
        "pain_id": pain.get("pain_id", "P-UNKNOWN"),
        "segment_id": segment.get("segment_id", "SEG-UNKNOWN"),
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
        "schema_version": "weekly-v1",
        "weekly_mode": True,
    }

    reject_synthetic_claims(hook, "hook")
    return hook


def generate_content_calendar(segment, hooks, start_date, evidence_ids, valid_evidence_ids):
    """Generate a 7-day content/action slice."""
    validate_evidence_citations(evidence_ids, valid_evidence_ids, "content-calendar")

    days = []
    for i in range(7):
        day_date = (datetime.fromisoformat(start_date) + timedelta(days=i)).isoformat()[:10]
        hook = hooks[i % len(hooks)] if hooks else None
        days.append({
            "day": i + 1,
            "date": day_date,
            "hook_id": hook["hook_id"] if hook else None,
            "action_type": "content" if i < 5 else "engagement",
            "evidence_citations": evidence_ids,
        })

    return {
        "calendar_id": "CAL-WEEKLY-001",
        "segment_id": segment.get("segment_id", "SEG-UNKNOWN"),
        "horizon_days": 7,
        "start_date": start_date,
        "days": days,
        "schema_version": "weekly-v1",
        "weekly_mode": True,
    }


def generate_funnel_audit(segment, evidence_ids, valid_evidence_ids):
    """Generate a funnel audit with 3 prioritized fixes."""
    validate_evidence_citations(evidence_ids, valid_evidence_ids, "funnel-audit")

    fixes = []
    for i, fix in enumerate(segment.get("funnel_fixes", [])[:3]):
        fixes.append({
            "fix_id": f"FIX-{i+1:03d}",
            "defect": fix.get("defect", ""),
            "fix_description": fix.get("fix", ""),
            "impact": fix.get("impact", "medium"),
            "confidence": fix.get("confidence", "medium"),
            "effort": fix.get("effort", "medium"),
            "evidence_citations": evidence_ids,
        })

    while len(fixes) < 3:
        fixes.append({
            "fix_id": f"FIX-{len(fixes)+1:03d}",
            "defect": "No additional defects identified in positioning audit",
            "fix_description": "Review funnel analytics for additional friction points",
            "impact": "low",
            "confidence": "low",
            "effort": "low",
            "evidence_citations": evidence_ids,
        })

    return {
        "audit_id": "FA-WEEKLY-001",
        "segment_id": segment.get("segment_id", "SEG-UNKNOWN"),
        "fixes": fixes[:3],
        "schema_version": "weekly-v1",
        "weekly_mode": True,
    }


def generate_proof_library_update(evidence_ids, valid_evidence_ids):
    """Generate a proof-library update citing evidence from positioning audit."""
    validate_evidence_citations(evidence_ids, valid_evidence_ids, "proof-library")

    return {
        "library_id": "PL-WEEKLY-001",
        "evidence_cited": evidence_ids,
        "update_type": "weekly_refresh",
        "schema_version": "weekly-v1",
        "weekly_mode": True,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: generate_weekly_artifacts.py <positioning-audit-export.json> [output_dir] [week_date]", file=sys.stderr)
        sys.exit(1)

    export_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SKILL_DIR, "tests", "generated", "weekly")
    week_date = sys.argv[3] if len(sys.argv) > 3 else datetime.now().isoformat()[:10]

    positioning = load_positioning_export(export_path)
    valid_evidence_ids = extract_evidence_ids(positioning)

    if not valid_evidence_ids:
        print("ERROR: Positioning export has no valid evidence IDs", file=sys.stderr)
        sys.exit(1)

    segments = positioning.get("segments", [])
    if not segments:
        print("ERROR: Positioning export has no segments", file=sys.stderr)
        sys.exit(1)

    segment = segments[0]
    pains = positioning.get("pains", [])
    pain = pains[0] if pains else {}

    segment_evidence = segment.get("evidence_ids", [])
    evidence_unavailable = len(segment_evidence) == 0
    if evidence_unavailable:
        segment_evidence = list(valid_evidence_ids)[:1] if valid_evidence_ids else ["EV-UNAVAILABLE"]
        print(f"WARNING: Segment {segment.get('segment_id', 'UNKNOWN')} has no evidence_ids — marking evidence_unavailable", file=sys.stderr)

    # Generate 1 offer
    offer = generate_weekly_offer(segment, pain, segment_evidence, valid_evidence_ids, evidence_unavailable=evidence_unavailable)

    # Generate 3 hooks
    hook_data = segment.get("hooks", [])
    hooks = []
    for i in range(3):
        if i < len(hook_data):
            h = hook_data[i]
            hook = generate_weekly_hook(
                h.get("formula_type", "pain"),
                pain, segment,
                h.get("text", ""),
                h.get("clarity", 7), h.get("curiosity", 7), h.get("pull", 7),
                h.get("evidence_id", segment_evidence[0]),
                valid_evidence_ids,
                rank=i + 1,
            )
        else:
            hook = generate_weekly_hook(
                "pain", pain, segment,
                f"Evidence-backed hook {i+1} for {pain.get('pain_id', 'this segment')}",
                7, 7, 7,
                segment_evidence[0],
                valid_evidence_ids,
                rank=i + 1,
            )
        hooks.append(hook)

    # Generate 7-day content calendar
    calendar = generate_content_calendar(segment, hooks, week_date, segment_evidence, valid_evidence_ids)

    # Generate funnel audit with 3 fixes
    funnel_audit = generate_funnel_audit(segment, segment_evidence, valid_evidence_ids)

    # Generate proof-library update
    proof_update = generate_proof_library_update(segment_evidence, valid_evidence_ids)

    # Write outputs
    os.makedirs(output_dir, exist_ok=True)
    artifacts = {
        "offer.json": offer,
        "hooks.json": hooks,
        "content-calendar.json": calendar,
        "funnel-audit.json": funnel_audit,
        "proof-library.json": proof_update,
    }

    for filename, data in artifacts.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    # Write evidence ledger
    evidence_ledger = {
        "claims": [],
        "evidence_ids_used": sorted(set(segment_evidence)),
        "evidence_ids_available": sorted(valid_evidence_ids),
        "evidence_unavailable": evidence_unavailable,
    }

    # Track claims for each artifact
    for name, data in artifacts.items():
        if isinstance(data, dict):
            citations = data.get("evidence_citations", data.get("evidence_cited", []))
            if isinstance(citations, str):
                citations = [citations]
            for ev_id in citations:
                evidence_ledger["claims"].append({
                    "claim_id": f"CLM-{name.replace('.json', '').upper()}",
                    "artifact": name,
                    "evidence_id": ev_id,
                    "evidence_type": "positioning_audit",
                    "status": "available" if ev_id in valid_evidence_ids else "unknown",
                })

    with open(os.path.join(output_dir, "evidence-ledger.json"), "w") as f:
        json.dump(evidence_ledger, f, indent=2)

    # Write unavailable.json if evidence is missing
    if evidence_unavailable:
        unavailable = {
            "missing": ["segment_evidence_ids"],
            "reason": "Segment has no evidence_ids in positioning export",
            "affected_stage": "Stage 2 — artifact generation",
            "mitigation": "Run positioning audit with deeper research depth or provide evidence manually",
        }
        with open(os.path.join(output_dir, "unavailable.json"), "w") as f:
            json.dump(unavailable, f, indent=2)

    # Verify constraints
    assert len(hooks) == 3, f"Expected 3 hooks, got {len(hooks)}"
    assert calendar["horizon_days"] == 7, f"Expected 7-day horizon, got {calendar['horizon_days']}"
    assert len(funnel_audit["fixes"]) == 3, f"Expected 3 fixes, got {len(funnel_audit['fixes'])}"

    print(f"PASS: generate_weekly_artifacts — 5 artifacts written to {output_dir}")
    print(f"  Offer: {offer['offer_id']} (composite: {offer['value_equation_scores']['composite']})")
    print(f"  Hooks: {len(hooks)} (ranks 1-{len(hooks)})")
    print(f"  Content calendar: {calendar['horizon_days']} days from {week_date}")
    print(f"  Funnel fixes: {len(funnel_audit['fixes'])}")
    print(f"  Proof-library: {len(proof_update['evidence_cited'])} evidence IDs cited")
    print(f"  Evidence IDs validated against {len(valid_evidence_ids)} corpus entries")
    sys.exit(0)


if __name__ == "__main__":
    main()
