# Evidence Contract

This document specifies the evidence chain between the three stages of the
weekly marketing flywheel.

## Stage 1 → Stage 2: Positioning Export → Funnel Artifacts

The positioning audit export (`positioning-audit-export.json`) must contain:

- `audit_id`: unique identifier for the audit
- `evidence_corpus`: array of evidence objects with `evidence_id`, `type`, `source`
- `segments`: array of segment objects with `segment_id`, `evidence_ids`, scores
- `pains`: array of pain objects with `pain_id`, `description`

Stage 2 (Hormozi funnel) must:
- Extract all valid evidence IDs from the corpus
- Validate every citation in offer/hooks/content/proof against the corpus
- Reject unknown evidence IDs with an error
- Reject fabricated economic claims (price, guarantee, scarcity, is_real) without evidence

## Stage 2 → Stage 3: Funnel Artifacts → Experiment Registration

The experiment registration must cite:
- The `audit_id` from Stage 1
- The `offer_id` from Stage 2
- At least one `hook_id` from Stage 2
- The evidence IDs used in the offer

Stage 3 (growth experiment loop) must:
- Design a falsifiable hypothesis based on the funnel artifacts
- Define guardrails (metrics, thresholds, stopping conditions)
- Register the experiment with a unique ID
- NOT execute, enroll, or send anything

## Evidence Ledger

The composite skill produces `evidence-ledger.json` aggregating all evidence
IDs cited across all three stages. This ledger is the audit trail for the
weekly packet.

## Unavailable Components

When a component (analytics, CRM, advisor, Search Console) is not available:
- Write the component name and reason to `unavailable.json`
- Continue with available evidence
- Never fabricate or substitute missing evidence
- Label the packet as `evidence_limited` in the run manifest
