---
name: ecc-content-quality-ops
description: >-
  Evaluate and improve evidence-heavy marketing, technical, scientific, or sales content against audience-specific rubrics and proof boundaries. Use for content quality gates, expert-panel review, editorial consistency, quote mining, messaging variants, and pre-publication claim checks.
---

# Content Quality Ops

## Objective

Apply a reproducible editorial and claim-quality gate without treating simulated expert scores as market evidence.

## Operating Contract

1. Identify artifact, audience, decision stage, source set, proof boundary, and publication channel.
2. Build a small panel of relevant review lenses; label simulated personas as heuristics, not real expert approval.
3. Score source fidelity, clarity, specificity, audience fit, differentiation, actionability, and claim safety using explicit evidence.
4. Block unsupported numbers, testimonials, authority claims, certifications, outcomes, and live-status language.
5. Revise at most three focused rounds and preserve the source meaning and author voice.
6. Return the scored artifact, unresolved claim ledger, and publish/hold decision.

## Required Outputs

- review rubric
- scored findings
- bounded revision
- publish/hold decision

## Proof and Safety

- Use the proof buckets `hosted/live`, `local`, `repository artifact`, `candidate/shadow`, and `roadmap`.
- Cite the source of load-bearing claims and label inference, uncertainty, contradiction, and stale evidence.
- Return `unavailable` when required data, tools, consent, or credentials are missing.
- Default external communications and system mutations to draft or dry-run. Require explicit approval in the current turn before any send, enrollment, publish, payment, CRM write, or production action.
- Preserve product-specific safety, scientific, regulatory, privacy, and buyer-evidence gates.
- Do not add dependencies for a text-and-evidence workflow.

## Routing

Use adjacent skills rather than reproducing them: `content-engine`, `brand-voice`, `marketing-campaign`. This skill owns only the closed capability described above.

Read [repo-profiles.md](references/repo-profiles.md) before applying the workflow to one of the five audited repositories. Read [adoption-evidence.json](references/adoption-evidence.json) when provenance, scoring, or promotion evidence matters.
