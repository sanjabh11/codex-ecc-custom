---
name: ecc-closed-loop-analytics
description: >-
  Measure whether marketing, content, outreach, SEO, conversion, or revenue workflow changes improved real outcomes, then promote, hold, roll back, or retest them. Use for analytics readback, baseline-versus-candidate evaluation, workflow learning loops, and evidence-backed playbook updates.
---

# Closed-Loop Analytics

## Objective

Close the loop between a shipped workflow change and real platform or buyer evidence.

## Operating Contract

1. Define one decision, primary metric, guardrails, attribution window, and minimum evidence before changing anything.
2. Capture the comparable baseline and label its proof bucket: hosted/live, local, repository artifact, candidate/shadow, or roadmap.
3. Collect outcome data from an available verified source. If the source or credential is unavailable, return `unavailable`; never fabricate analytics.
4. Compare candidate and baseline on the primary metric, guardrails, cost, runtime, and human-correction rate. Separate correlation from attribution.
5. Choose `promote`, `hold`, `rollback`, or `retest`; state the threshold and evidence behind the choice.
6. Write a bounded playbook patch only after promotion. Queue global or cross-skill changes for explicit review.

## Required Outputs

- measurement contract
- baseline/candidate comparison
- decision with confidence boundary
- bounded playbook patch or retest plan

## Proof and Safety

- Use the proof buckets `hosted/live`, `local`, `repository artifact`, `candidate/shadow`, and `roadmap`.
- Cite the source of load-bearing claims and label inference, uncertainty, contradiction, and stale evidence.
- Return `unavailable` when required data, tools, consent, or credentials are missing.
- Default external communications and system mutations to draft or dry-run. Require explicit approval in the current turn before any send, enrollment, publish, payment, CRM write, or production action.
- Preserve product-specific safety, scientific, regulatory, privacy, and buyer-evidence gates.
- Do not add dependencies for a text-and-evidence workflow.

## Routing

Use adjacent skills rather than reproducing them: `agent-phase-ratchet`, `skill-optimizer`, `marketing-campaign`. This skill owns only the closed capability described above.

Read [repo-profiles.md](references/repo-profiles.md) before applying the workflow to one of the five audited repositories. Read [adoption-evidence.json](references/adoption-evidence.json) when provenance, scoring, or promotion evidence matters.
