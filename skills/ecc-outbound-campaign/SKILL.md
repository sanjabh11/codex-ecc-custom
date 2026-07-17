---
name: ecc-outbound-campaign
description: >-
  Design evidence-backed outbound campaign drafts from an approved ICP and source-cited dossiers, with claim checks, suppression rules, variants, and response logging. Use for cold or warm email, LinkedIn, or X outreach planning and optimization; never send or enroll contacts without explicit approval.
---

# Outbound Campaign

## Objective

Convert approved account evidence into personalized, compliant outreach drafts and measurable response loops.

## Operating Contract

1. Require an approved ICP, offer, proof boundary, source-cited dossier, channel, and explicit campaign objective.
2. Apply suppression and exclusion rules before drafting: prior opt-out, conflicts, sensitive roles, unsupported contact data, and prohibited claims.
3. Draft short personalized variants tied to one verified signal and one bounded value proposition.
4. Run claim, privacy, tone, and message-match checks; reject generic personalization or fabricated familiarity.
5. Default to draft-only. Live send, enrollment, scheduling, or CRM mutation requires a separate explicit approval in the current turn.
6. Create an anonymized response log and feed outcomes to the growth and closed-loop analytics skills.

## Required Outputs

- campaign brief
- approved draft variants
- suppression and claim-check report
- response-log schema

## Proof and Safety

- Use the proof buckets `hosted/live`, `local`, `repository artifact`, `candidate/shadow`, and `roadmap`.
- Cite the source of load-bearing claims and label inference, uncertainty, contradiction, and stale evidence.
- Return `unavailable` when required data, tools, consent, or credentials are missing.
- Default external communications and system mutations to draft or dry-run. Require explicit approval in the current turn before any send, enrollment, publish, payment, CRM write, or production action.
- Preserve product-specific safety, scientific, regulatory, privacy, and buyer-evidence gates.
- Do not add dependencies for a text-and-evidence workflow.

## Routing

Use adjacent skills rather than reproducing them: `lead-intelligence`, `marketing-campaign`, `ceip-linkedin-outreach-draft-generator`. This skill owns only the closed capability described above.

Read [repo-profiles.md](references/repo-profiles.md) before applying the workflow to one of the five audited repositories. Read [adoption-evidence.json](references/adoption-evidence.json) when provenance, scoring, or promotion evidence matters.
