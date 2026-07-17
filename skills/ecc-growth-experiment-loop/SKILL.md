---
name: ecc-growth-experiment-loop
description: >-
  Design, register, monitor, and evaluate bounded marketing or commercial experiments using explicit hypotheses, variants, metrics, guardrails, and decision rules. Use for A/B tests, outreach variants, landing-page experiments, campaign pacing, weekly scorecards, and evidence-backed growth playbooks.
---

# Growth Experiment Loop

## Objective

Turn commercial ideas into falsifiable experiments instead of untracked activity.

## Operating Contract

1. Read the current positioning, proof boundaries, prior experiments, and available instrumentation.
2. State one falsifiable hypothesis with audience, variable, variants, primary metric, guardrails, sample/window, and stop rule.
3. Reject experiments that need unavailable traffic, credentials, consent, or unsafe claims; return a smaller dry-run or instrument-first plan.
4. Register the baseline and experiment before launch. Never backfill success criteria after seeing results.
5. Monitor pacing without declaring a winner early. Record missing or contaminated data explicitly.
6. Apply the predeclared decision rule and update the playbook only when evidence passes; otherwise hold or retest.

## Required Outputs

- experiment registration
- instrumentation and pacing plan
- result evaluation
- promote/hold/retest decision

## Proof and Safety

- Use the proof buckets `hosted/live`, `local`, `repository artifact`, `candidate/shadow`, and `roadmap`.
- Cite the source of load-bearing claims and label inference, uncertainty, contradiction, and stale evidence.
- Return `unavailable` when required data, tools, consent, or credentials are missing.
- Default external communications and system mutations to draft or dry-run. Require explicit approval in the current turn before any send, enrollment, publish, payment, CRM write, or production action.
- Preserve product-specific safety, scientific, regulatory, privacy, and buyer-evidence gates.
- Do not add dependencies for a text-and-evidence workflow.

## Routing

Use adjacent skills rather than reproducing them: `agent-phase-ratchet`, `ecc-niche-positioning-audit`, `marketing-campaign`. This skill owns only the closed capability described above.

Read [repo-profiles.md](references/repo-profiles.md) before applying the workflow to one of the five audited repositories. Read [adoption-evidence.json](references/adoption-evidence.json) when provenance, scoring, or promotion evidence matters.
