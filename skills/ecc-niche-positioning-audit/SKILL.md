---
name: ecc-niche-positioning-audit
description: >-
  Identify high-potential customer segments, unmet needs, product-market gaps,
  and defensible positioning through ultra-deep market research, customer/evidence
  analysis, product evaluation, and optional codebase reconnaissance. Eight-phase
  pipeline with approval gates, decision confidence (95% target), 8-type gap
  classification, validation experiments, hypothesis tracking, adversarial review,
  scope selection (quick/standard/deep), persistent state, and cross-product
  portfolio. Codebase is optional — product evidence is the primary input.
  TRIGGER when: "niche segment", "positioning strategy", "positioning drift",
  "customer segment identification", "product-market alignment", "market gap
  discovery", "unmet needs analysis", "ICP", "beachhead segment",
  "product-market fit audit", or "validation experiment design".
  DO NOT TRIGGER when: no product or codebase context is available, or the task
  is purely marketing copy generation without strategic analysis.
---

# ecc-niche-positioning-audit

Use this skill to align a product with market needs and discover evidence-backed
market gaps. The Product Evidence Corpus is primary; a codebase is optional and
answers only whether the product can deliver a validated opportunity.

## Operating Contract

1. Frame one product-market decision and define the customer, geography, domain,
   business model, decision owner, scope, and evidence limitations.
2. Assemble a versioned Product Evidence Corpus before market research. Use the
   canonical `schemas/evidence-corpus.schema.json`; do not treat state claims as
   evidence.
3. Research needs, alternatives, competitors, status quo, switching costs,
   distribution, and recent movement using a question tree and counter-evidence.
4. Map `need → customer outcome → product promise → actual capability → proof →
   positioning → experiment`; classify every gap and cite the evidence IDs.
5. Require user approval before Phase 5. Designed experiments are not validation
   evidence; only recorded results can change hypothesis status.
6. Persist state, artifacts, hypotheses, experiments, research queries, tool
   health, and adversarial reviews. Run the validator at each gate.

## Direct References

Read only the references needed for the selected scope; all are one level below
this file. The package contains eight references in total.

| Need | Reference |
|---|---|
| source quality, question trees, saturation, counter-evidence | [research-protocol.md](references/research-protocol.md) |
| quick/standard/deep dependencies and terminal states | [scope-dag.md](references/scope-dag.md) |
| confidence, evidence bundles, and outcome decisions | [scoring-rubric.md](references/scoring-rubric.md) |
| state, privacy, migration, and lifecycle persistence | [state-schema.md](references/state-schema.md) |
| optional stack-aware codebase evidence | [stack-recon.md](references/stack-recon.md) |
| approvals, independence, COI, cadence, and drift | [governance.md](references/governance.md) |
| schemas, fixtures, scenarios, and release verification | [eval-harness.md](references/eval-harness.md) |
| methodology sources, dates, applicability, limitations | [methodology-provenance.md](references/methodology-provenance.md) |

## Inputs and Outputs

`product_context` is required and may be a product description, product docs,
URL, evidence pack, analytics/sales/support data, or codebase. Optional inputs:
`scope` (`quick`, `standard`, `deep`; default `standard`), `domain_hint`, `stack`,
`existing_customers`, `competitors`, `pricing_data`, `usage_analytics`,
`sales_data`, `support_data`, `previous_audit`, and `output_dir` (default
`.positioning-audit/`). Unanswered questionnaire fields are `unknown`, never
guessed.

The output is a 4-page phase artifact plus the canonical state, evidence corpus,
hypotheses, experiments, research log, and gap table. Every load-bearing claim
has an evidence bundle, counter-evidence result, confidence contribution, and
validation experiment or an explicit evidence limitation.

## Product Evidence Corpus

Use these 11 evidence types: `product_promise`, `customer_outcome`, `user_quote`,
`behavioral_observation`, `support_ticket`, `analytics_data`, `sales_data`,
`pricing_signal`, `stakeholder_input`, `competitor_intel`, and optional
`codebase_evidence`.

- At least three types are required to proceed past Phase 1; at least one must be
  first-party customer or commercial evidence: `customer_outcome`, `user_quote`,
  `behavioral_observation`, `support_ticket`, `analytics_data`, or `sales_data`.
- If the first-party condition is not met, set `evidence_limited_mode: true`,
  document the limitation, and never issue a full GO.
- Every item requires source, source tier, timestamp, freshness, grade,
  confidence, provenance, `authority_tier`, `checked_at`, `expiry`, `url_health`,
  `content_summary`, and `is_customer_commercial`.
- State evidence-type lists must equal the corpus types. A corpus is required for
  persisted audits; absence of evidence is a recorded evidence gap, not a guess.
- Surface contradictions. LOW evidence cannot be load-bearing; each load-bearing
  claim needs at least one HIGH or two MEDIUM items.

## Research and Gap Rules

Use a phase question tree with source type, query, coverage, bias, and
counter-evidence fields. Stop only when coverage, repetition, and the required
counter-evidence passes are satisfied; see [research-protocol.md](references/research-protocol.md).

Every Phase 4 gap uses exactly one of these eight types:

| Gap type | Meaning |
|---|---|
| **Need gap** | A market need is not addressed. |
| **Product gap** | A capability needed for a validated need is absent. |
| **Proof gap** | The product may work but proof is missing. |
| **Positioning gap** | Segment, job, or use-case framing is wrong. |
| **Pricing gap** | Price or buying process conflicts with WTP. |
| **Distribution gap** | The product is not reachable through buying channels. |
| **Adoption gap** | Onboarding, integration, or migration blocks use. |
| **Evidence gap** | Information is insufficient, biased, inconsistent, or stale. |

Hypothesis states are `supported`, `weakened`, `disproven`, `stale`, or
`unresolved`. No hypothesis becomes Supported until first-party results are
recorded and the evidence bundle passes.

## Decision Confidence and Gates

Decision confidence is not statistical confidence or probability. It is the
deterministic sum of evidence quality (0–30), source coverage (0–25), internal
consistency (0–20), counter-evidence survival (0–15), and validation evidence
(0–10). The composite must equal the subscore sum and is recorded in state and
artifacts. See [scoring-rubric.md](references/scoring-rubric.md).

Use one outcome matrix everywhere:

| Condition | Decision | Required action |
|---|---|---|
| Target confidence and evidence gates met | **GO** | Advance only within the selected path. |
| Partial evidence or designed experiments | **CONDITIONAL GO** | Record limitations; queue validation. |
| Evidence contradiction or insufficient coverage | **RECYCLE** | Re-run named research or experiments. |
| Fundamental assumption disproven or no viable segment | **STOP** | Reframe the product-market decision. |

`evidence_limited_mode` caps all gates and artifacts at `CONDITIONAL_GO`; never
GO. With zero executed experiments, set
`market_validation_status: validation_pending`, `current_phase: VALIDATION_PENDING`,
and validation confidence to `0`.

Lifecycle rule: `P5 design → VALIDATION_PENDING`. Designed experiments are not
validation evidence. No hypothesis becomes Supported until first-party results are recorded; first-party buyer evidence is required for a full GO.

## Phase Spine

### Phase 0: Frame the Product-Market Decision

Define the decision, user/customer, domain, geography, business model, scope,
success threshold, risks, conflicts of interest, available tools, and evidence
sources. Record unknowns. Output: approved audit brief and empty v8 state.

### Phase 1: Product and Evidence Reconnaissance

Assemble and validate the Product Evidence Corpus, inspect product promise versus
customer outcomes, record provenance and contradictions, and identify evidence
gaps. Output: schema-valid corpus and Product Truth. Do not proceed with fewer
than three evidence types; use evidence-limited mode without first-party proof.

### Phase 2: Ultra-Deep Market and Alternative Research

Research direct and indirect competitors, substitutes, status quo, switching
costs, distribution, pricing context, recent changes, and unmet jobs. Log every
query, source, bias, counter-evidence pass, and saturation decision.

### Phase 3: Segment and Unmet-Need Triangulation

Rank segments using firmographic, behavioral, intent, technographic, pain,
urgency, WTP, competition, reachability, and adoption evidence. Include negative
ICP evidence and produce no more than the scope limit of candidate segments.

### Phase 4: Product-Market Alignment and Gap Map

Complete the seven-link alignment chain. Produce the 8-type gap table, positioning
hypotheses, evidence bundles, confidence subscores, proof requirements, and three
adversarial reviews: skeptic, missing perspective, and contrarian.

### Phase 5: Validation Plan and Experiments

After user approval, extract every load-bearing segment, outcome, product, proof,
pricing, distribution, and competitive claim. Design the cheapest experiment that
can falsify each claim with method, sample, success threshold, failure threshold,
decision rule, risk check, instrumentation, and owner. Standard scope ends at
`VALIDATION_PENDING`; design is not market validation.

### Phase 6: Optional Codebase Audit

Only when a codebase is available, compare validated positioning to actual
capability, proof instrumentation, pricing implementation, integrations, and
technical debt. Codebase evidence can identify product gaps but cannot validate
market demand. See [stack-recon.md](references/stack-recon.md).

### Phase 7: Refresh, Drift, and Re-Ranking

After experiment results exist, update hypothesis states, refresh stale evidence,
assess segment/need/competitive/product/evidence drift, re-rank segments, define
weekly/monthly/quarterly cadence, and publish the final report. GO requires
recorded results that support the decision.

## Dependency Gating

| Phase | Depends on | Skip rule |
|---|---|---|
| 0 | none | never |
| 1 | 0 | never; corpus is foundational |
| 2 | 1 | never |
| 3 | 2 | quick uses P3-lite |
| 4 | 3 or P3-lite | never; quick uses P4-lite |
| 5 | 4 + user approval | quick skips; standard designs only |
| 6 | 5 design | skip when no codebase |
| 7 | executed results and optional 6 | quick skips; standard pauses |

### Quick Mode Path

```text
P0 → P1 → P2 → P3-lite → P4-lite → TERMINAL
```

### Standard Mode Path

```text
P0 → P1 → P2 → P3 → P4 → [APPROVAL] → P5 design → VALIDATION_PENDING → TERMINAL
```

### Deep Mode Path

```text
P0 → P1 → P2 → P3 → P4 → [APPROVAL] → P5 design → execute → P6 (if codebase) → P7 → TERMINAL
```

See [scope-dag.md](references/scope-dag.md) for thresholds and the no-code Deep
variant.

## Tool Truth

### Enforcement Rules

- Phase 0 is mandatory — no phase execution begins without completing the pre-execution protocol
- Inter-phase skill re-evaluation is mandatory at every gate transition — skill selection is dynamic, not static
- Decision confidence log (composite + subscores + iterations) is mandatory on every artifact's Page 1
- **Codebase is optional** — the skill works without code access if product evidence is available
- **Product Evidence Corpus is required** — at least 3 evidence types must be present to pass Gate 1
- **Codebase evidence is one type, not the primary type** — it supplements customer/market evidence
- Input parameters are accepted but auto-detected/defaulted when not provided — skill works zero-config
- Scope selection (quick/standard/deep) adjusts phase depth, gate thresholds, and confidence targets — default is standard
- Stack auto-detection runs in Phase 0a only if codebase is available — if detection fails, ask user
- Pre-audit questionnaire calibrates the audit — unanswered questions are "unknown" not guessed
- Per-project extensions in `.positioning-audit/extras/*.md` are explicitly inspected and recorded; no automatic loader is claimed
- Persistent state enables resumption and drift tracking; migrate v5-v7 state with `scripts/migrate_state.py --input old/state.json --output new/state.json`, never overwrite input
- Cross-product portfolio output is optional manual work, not an automatic aggregation service
- Evidence grading (HIGH/MEDIUM/LOW) is mandatory for every finding — LOW findings cannot be load-bearing
- **At least one HIGH or two MEDIUM evidence items required per load-bearing positioning claim**
- **Every load-bearing claim gets a validation experiment** with measurable success and failure thresholds
- **Gap classification (8 types) is mandatory** for every gap identified in Phase 4
- **Hypothesis status tracking is mandatory** — every hypothesis has a status that updates with evidence
- **Decision confidence is not statistical confidence** — it is a composite of evidence quality, coverage, and consistency
- **Unified outcome matrix is used everywhere** — gates, scope DAG, and scoring rubric all reference the same matrix
- **Counter-evidence search is mandatory** — at least 1 pass (quick), 2 (standard), 3 (deep)
- **Research question trees are mandatory** — every phase updates the tree with coverage status
- Advisor checkpoints use `ecc-advisor` only if exposed and healthy; otherwise document the skip
- **Absence of evidence is itself evidence** — mark as an evidence limitation, do not guess
- **Contradictions are surfaced, not hidden** — if product promise contradicts customer outcomes, flag it explicitly
- **Evidence-limited mode is explicitly flagged** — all subsequent gates are capped at CONDITIONAL GO and never GO without direct customer or commercial evidence
- **Designed experiments are not validation evidence** — with zero executed first-party experiments, use `VALIDATION_PENDING`, score validation as 0, and keep hypotheses unresolved
- **Tool health is recorded** — every tool used during the audit has a status and `checked_at` in state
- **Artifact reproducibility** — validate against `schemas/artifact.schema.json`, hash canonical state JSON, write atomically, and preserve superseded artifacts with `scripts/generate_artifact.py`

## Artifact and State Contract

Artifacts use the canonical v8 schema and four pages: confidence/evidence,
findings with evidence IDs, gap or segment analysis with research updates, and
gate/exit criteria with adversarial reviews. Generate/check/supersede with
`scripts/generate_artifact.py`; generation rejects invalid source state.

Canonical state lives in `.positioning-audit/`. Required companion files are
`evidence-corpus.json`, `hypotheses.json`, `experiments.json`, and `artifacts/`.
Use `scripts/validate_skill.py --audit-dir .positioning-audit` for persisted
instances. See [state-schema.md](references/state-schema.md),
[eval-harness.md](references/eval-harness.md), and the five JSON schemas.

## Upstream Source

- Origin: user request for top niche customer segments and positioning strategy.
- Redesign objective: product-market alignment and ultra-deep market-gap discovery;
  codebase reconnaissance is optional evidence, not the objective.
- Methodology registry: [methodology-provenance.md](references/methodology-provenance.md).
- v8 release includes schemas, source-state validation, migration, canonical
  artifact hashing, ordered scope verification, 9 behavioral scenarios, and
  adversarial semantic checks.

## Optimization Contract v1

This shared contract makes the positioning audit's inputs, outputs, and proof
boundary machine-detectable while preserving the existing phase gates.

```yaml
contract_version: skill-optimization.v1
scope: evidence-backed product-market positioning audit
inputs:
  - product_context
  - product_evidence_corpus
  - selected_scope
  - research_question_tree
outputs:
  - four_page_phase_artifact
  - evidence_corpus
  - hypotheses
  - experiments
  - gap_table
  - confidence_and_gate_record
evidence_policy:
  every_load_bearing_claim_has_evidence_ids: true
  designed_experiments_are_not_validation: true
  first_party_evidence_required_for_full_go: true
  evidence_limited_mode_caps_decision: CONDITIONAL_GO
completion_gate:
  validate_state_and_artifact_schemas: true
  record_counter_evidence: true
  record_unknowns_and_limitations: true
  preserve_reproducible_hashes: true
stop_conditions:
  - missing_product_context
  - insufficient_evidence_corpus
  - missing_first_party_evidence_for_go
  - unresolved_contradiction
```

This block is a contract index, not a shortcut around the phase DAG. The
existing state validator and evidence gates remain authoritative for any
persisted audit or decision.
