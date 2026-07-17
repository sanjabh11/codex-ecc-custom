---
name: ecc-revenue-attribution
description: >-
  Trace content, outreach, calls, pilots, and conversion events to qualified pipeline or revenue evidence while preserving attribution uncertainty. Use for buyer-journey analysis, sales-call insight extraction, content ROI, pipeline reporting, and commercial evidence reconciliation.
---

# Revenue Attribution

## Objective

Connect commercial activity to defensible buyer and revenue evidence without overclaiming causality.

## Operating Contract

1. Define the commercial event taxonomy and identify the authoritative systems or retained artifacts.
2. Normalize touchpoints, buyer lane, artifact identity, timestamps, consent, and outcome status; redact direct identifiers.
3. Build first-touch, last-touch, and multi-touch views when data supports them. Keep unknown and unattributed buckets.
4. Extract objections, buying signals, requested proof, and next actions from calls or notes; label model-derived interpretation.
5. Reconcile attributed outcomes with accepted payment, pilot, or reviewer evidence. Never infer revenue from intent alone.
6. Publish a report with coverage, attribution assumptions, contradictions, and the next instrumentation gap.

## Required Outputs

- event taxonomy
- attribution table
- buyer-signal summary
- coverage and uncertainty report

## Proof and Safety

- Use the proof buckets `hosted/live`, `local`, `repository artifact`, `candidate/shadow`, and `roadmap`.
- Cite the source of load-bearing claims and label inference, uncertainty, contradiction, and stale evidence.
- Return `unavailable` when required data, tools, consent, or credentials are missing.
- Default external communications and system mutations to draft or dry-run. Require explicit approval in the current turn before any send, enrollment, publish, payment, CRM write, or production action.
- Preserve product-specific safety, scientific, regulatory, privacy, and buyer-evidence gates.
- Do not add dependencies for a text-and-evidence workflow.

## Routing

Use adjacent skills rather than reproducing them: `commercial-launch-readiness-orchestrator`, `customer-billing-ops`, `marketing-campaign`. This skill owns only the closed capability described above.

Read [repo-profiles.md](references/repo-profiles.md) before applying the workflow to one of the five audited repositories. Read [adoption-evidence.json](references/adoption-evidence.json) when provenance, scoring, or promotion evidence matters.
