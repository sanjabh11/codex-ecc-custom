---
name: ecc-buyer-pipeline
description: >-
  Govern a privacy-safe buyer pipeline from qualified account through discovery, evidence intake, pilot, review, and outcome, with explicit stage gates and dry-run integrations. Use for lead routing, deal follow-up, buyer-evidence progression, dormant-opportunity review, and ICP learning.
---

# Buyer Pipeline

## Objective

Move buyer opportunities through evidence-backed stages without automatic CRM or campaign mutations.

## Operating Contract

1. Define canonical stages, entry criteria, exit evidence, owner, next action, and stale threshold.
2. Normalize qualified accounts from approved dossiers; deduplicate by organization and proof need, not guessed identity.
3. Route each opportunity to one offer and evidence request. Keep rejection, suppression, and no-response states.
4. Review dormant opportunities only from retained history and current public signals; never fabricate a champion or trigger.
5. Default CRM, email, and campaign integrations to dry-run payloads. Require explicit approval for external writes.
6. Update the ICP only from recorded accept/reject/outcome evidence and publish the evidence delta.

## Required Outputs

- stage model
- qualified opportunity register
- dry-run routing payload
- ICP learning delta

## Proof and Safety

- Use the proof buckets `hosted/live`, `local`, `repository artifact`, `candidate/shadow`, and `roadmap`.
- Cite the source of load-bearing claims and label inference, uncertainty, contradiction, and stale evidence.
- Return `unavailable` when required data, tools, consent, or credentials are missing.
- Default external communications and system mutations to draft or dry-run. Require explicit approval in the current turn before any send, enrollment, publish, payment, CRM write, or production action.
- Preserve product-specific safety, scientific, regulatory, privacy, and buyer-evidence gates.
- Do not add dependencies for a text-and-evidence workflow.

## Routing

Use adjacent skills rather than reproducing them: `lead-intelligence`, `commercial-launch-readiness-orchestrator`, `ecc-niche-positioning-audit`. This skill owns only the closed capability described above.

Read [repo-profiles.md](references/repo-profiles.md) before applying the workflow to one of the five audited repositories. Read [adoption-evidence.json](references/adoption-evidence.json) when provenance, scoring, or promotion evidence matters.
