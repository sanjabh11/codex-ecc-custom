---
name: ecc-niche-positioning-audit
description: >-
  Identify high-potential customer segments, unmet needs, product-market gaps,
  and defensible positioning through ultra-deep market research, customer/evidence
  analysis, product evaluation, and optional codebase reconnaissance. Eight-phase
  pipeline (Phase 0 framing + 7 execution phases) with explicit approval gates,
  decision confidence mechanism (95% target), evidence-anchored scoring, ICP
  rubric, beachhead methodology, 8-type gap classification, validation experiments,
  hypothesis status tracking, adversarial review, dynamic per-phase skill selection,
  quarterly drift tracking, stack auto-detection, scope selection (quick/standard/deep),
  per-project extensions, persistent state, cross-product portfolio view, and
  evidence grading. Codebase is optional — product evidence is the primary input.
  Designed for repeated use across multiple products and codebases.
  TRIGGER when: "niche segment", "positioning strategy", "positioning drift",
  "customer segment identification", "product-market alignment", "market gap
  discovery", "unmet needs analysis", "ICP", "beachhead segment",
  "product-market fit audit", or "validation experiment design".
  DO NOT TRIGGER when: no product or codebase context is available, or the task
  is purely marketing copy generation without strategic analysis.
---

# ecc-niche-positioning-audit

Use this skill when the user needs to identify high-potential customer segments, unmet needs, product-market gaps, and defensible positioning through ultra-deep market research, customer/evidence analysis, product evaluation, and optional codebase reconnaissance.

## Purpose

Transform product-market decisions from guesswork into evidence-anchored strategy. The skill discovers where a product's actual capabilities meet real market needs, classifies the gaps between them, validates every load-bearing claim with experiments, and tracks positioning drift over time.

**Core principle**: The codebase does not determine the market opportunity. The market determines the opportunity. The codebase answers: "Does the current product support the validated market opportunity?"

## Methodology Sources

- **MIT Disciplined Entrepreneurship** (24-step framework, beachhead segment methodology)
- **Stratridge 2026 Positioning Framework** (8-lens positioning audit, claim verification)
- **ICP Scoring Rubric** (4-dimension model: firmographic 40%, behavioral 25%, intent 20%, technographic 15%)
- **N.I.C.H.E. Research Process** (Notice → Investigate → Compete → Hypothesize → Experiment)
- **Product Maturity Assessment** (6-dimension model: PMF evidence, feature completeness, tech debt, scalability, security, UX)
- **IntentGuard Intent Drift Detection** (specification vs implementation gap measurement)
- **PrismGrid Positioning Validation** (claim verification before scaling)
- **ecc-advisor pattern** (second-opinion checkpoint before substantive work)
- **Stage Gate PM** (decision forcing functions, Go/Conditional Go/Recycle/Stop outcomes, exit criteria defined before stage)
- **Adversarial Review** (independent hostile personas, falsification tests, blind spot detection)
- **Audit Readiness Framework** (5-dimension pre-gate self-assessment, closure criteria, post-remediation tests)
- **TriAdReview** (triangular adversarial review architecture, multi-perspective validation)
- **IMPACT Framework** (hypothesis-driven B2B positioning: Identify → Map → Pinpoint → Anchor → Craft → Translate)
- **plugin-gtm** (codebase-to-GTM engine: analyze codebase → product profile → GTM plan)
- **Lumen PM** (18-agent PM orchestration with evidence-graded reports and human-in-the-loop gates)
- **code-repository-audit-skill** (13-dimension tech-DD framework with stack-aware extensions and per-project extras)
- **Codebase Pattern Extraction** (parameterization pattern: collect → diff → abstract → parameterize → package)
- **Auditor Skill** (pre-audit questionnaire, scope selection, 1209-item checklist across 18 domains)
- **JTBD Framework** (Jobs To Be Done: product-market alignment through job steps and customer outcomes, not features)
- **NIST AI RMF Core** (GOVERN/MAP/MEASURE/MANAGE: documented test sets, metrics, uncertainty, repeatability, independent review)
- **NIST AI 800-3** (statistical validity, uncertainty quantification, construct validity, proxies vs direct measurement)
- **Evidence Engine** (evidence classification by type, bias mitigation, counter-evidence search, gap identification, assumption challenge)
- **Latent Spark / Iridae** (living product-market context, belief states with confidence and provenance, drift and staleness tracking)
- **AHRQ Research Gap Framework** (PICOS gap classification, 4 reasons for gaps: insufficient, biased, inconsistent, wrong information)
- **Lean Startup Validated Learning** (cheapest experiment that can falsify hypothesis, WTP tests, fidelity ladder)
- **ParallelHQ Market Gap Guide** (segment by unmet needs, high pain + WTP + low competition, validate before building)

## Backing Skills

- `deep-research` (web research for market unmet needs, counter-evidence)
- `market-research` (competitive analysis, segment sizing, alternative mapping)
- `market-research-reports` (structured output format)
- `codebase-onboarding` (codebase structure analysis — optional, when code is available)
- `ecc-plan` (phase planning and risk assessment)
- `ecc-verify` (verification gates between phases)
- `ecc-advisor` (advisor checkpoint before substantive work — if Grok CLI token available)

## Prerequisites

- **Product context**: At least one of the following must be available:
  - Codebase access (optional but valuable)
  - Product description or documentation
  - Customer evidence (interviews, feedback, support tickets, reviews)
  - Usage analytics or product telemetry
  - Pricing or sales data
  - Live product URL for inspection
- **Web search capability** for market research and counter-evidence discovery
- **Optional**: `ecc-advisor` for second-opinion checkpoints (graceful fallback if unavailable)

## Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `product_context` | YES (one of) | — | Path or description of the product being audited (codebase, product doc, URL, or evidence pack) |
| `scope` | NO | `standard` | `quick` (15-30 min), `standard` (1-3 hr), `deep` (3-6 hr) |
| `domain_hint` | NO | auto-detect | Industry/domain hint: SaaS, fintech, healthtech, devtools, ecommerce, edtech, AI/ML, other |
| `stack` | NO | auto-detect | Tech stack if codebase available: React, Next, Vue, Angular, Svelte, Python, Go, Node, Rust, Ruby, Java |
| `existing_customers` | NO | — | Known customer segments, testimonials, case studies, or references |
| `competitors` | NO | — | Known competitors or alternatives |
| `pricing_data` | NO | — | Current pricing model, tiers, or willingness-to-pay signals |
| `usage_analytics` | NO | — | Product usage data, telemetry, or behavioral signals |
| `sales_data` | NO | — | Sales pipeline, conversion rates, win/loss analysis |
| `support_data` | NO | — | Support tickets, complaint patterns, churn reasons |
| `previous_audit` | NO | — | Path to previous `.positioning-audit/` directory for drift comparison |
| `output_dir` | NO | `.positioning-audit/` | Directory for artifacts and persistent state |

## Scope Selection

| Dimension | Quick | Standard | Deep |
|-----------|-------|----------|------|
| **Time** | 15-30 min | 1-3 hr | 3-6 hr |
| **Phases** | 0+1+2+4 | 0-4 (skip 5-7) | 0-7 (all) |
| **Segments analyzed** | Top 3 | Top 5 | Top 8 |
| **Competitors researched** | Top 3 direct | Top 5 direct + 3 indirect | Top 8 direct + 5 indirect + 3 substitutes |
| **Customer evidence depth** | Available signals only | Available + 5-min interview prep | Available + interview guide + survey template |
| **Validation experiments** | Proposed only | Designed with thresholds | Designed + execution plan + success metrics |
| **Gate threshold** | 12/25 pre-gate | 15/25 pre-gate | 18/25 pre-gate |
| **Confidence target** | 85% | 90% | 95% |
| **Counter-evidence search** | 1 pass | 2 passes | 3 passes + adversarial review |
| **Research question tree depth** | 2 levels | 3 levels | 4 levels + saturation check |

## Product Truth / Evidence Corpus

Before any market research, assemble the Product Truth — what the product actually is and does, grounded in evidence rather than aspiration.

### Evidence Types (from Evidence Engine + Latent Spark)

| Type | Source | What It Reveals |
|------|--------|-----------------|
| `product_promise` | Marketing site, docs, pitch deck | What the product claims to do |
| `customer_outcome` | Interviews, JTBD analysis | What customers actually achieve |
| `user_quote` | Interviews, feedback, reviews | Customer language and framing |
| `behavioral_observation` | Analytics, telemetry, session recordings | What users actually do |
| `support_ticket` | Support data, complaint patterns | Where the product fails expectations |
| `analytics_data` | Usage metrics, conversion funnels | Quantitative product performance |
| `sales_data` | Pipeline, win/loss, deal size | Market willingness to pay |
| `pricing_signal` | Pricing page, competitor pricing | Price sensitivity and positioning |
| `stakeholder_input` | Team knowledge, internal docs | Internal assumptions and beliefs |
| `competitor_intel` | Competitor analysis, market reports | Competitive landscape and movement |
| `codebase_evidence` | Code analysis (optional) | Actual technical capabilities and constraints |

### Evidence Corpus Assembly Rules

1. **At least 3 evidence types required** to proceed past Phase 1 (any combination)
2. **Codebase evidence is one type, not the primary type** — it supplements, not replaces, customer/market evidence
3. **Absence of evidence is itself evidence** — mark as "evidence limitation" in the corpus
4. **Every evidence item gets provenance** — source, date, confidence, and whether it is observed fact, sourced claim, hypothesis, or inference
5. **Contradictions are surfaced, not hidden** — if product promise contradicts customer outcomes, flag it

## Research Question Tree Structure

Each phase generates a research question tree to operationalize "ultra-deep research."

### Tree Format

```
Phase Question
├── Sub-question 1
│   ├── Source type needed (primary/secondary)
│   ├── Coverage status (covered / partial / uncovered)
│   └── Counter-evidence found? (yes / no / not searched)
├── Sub-question 2
│   ├── ...
```

### Saturation Criteria

- **Quick scope**: 2 levels deep, 1 counter-evidence pass
- **Standard scope**: 3 levels deep, 2 counter-evidence passes
- **Deep scope**: 4 levels deep, 3 counter-evidence passes + saturation check (new sources repeat findings from existing sources)

## Gap Classification Taxonomy

Every gap identified in Phase 4 is classified into one of 8 types:

| Gap Type | Definition | Example |
|----------|-----------|---------|
| **Need gap** | Market has a need the product does not address at all | "Customers need mobile access; product is desktop-only" |
| **Product gap** | Product lacks a capability needed to serve the identified need | "Product lacks SSO; enterprise customers require it" |
| **Proof gap** | Product works but there is no evidence proving it to the market | "No case studies, testimonials, or ROI data" |
| **Positioning gap** | Product is positioned for the wrong segment or use case | "Marketed as dev tool but actual users are data scientists" |
| **Pricing gap** | Pricing model does not match the segment's WTP or buying process | | "Monthly SaaS pricing but enterprise needs annual contracts" |
| **Distribution gap** | Product is not reachable through the channels the segment uses | "Sold via website but segment buys through VARs" |
| **Adoption gap** | Product requires onboarding, integration, or migration that blocks adoption | "Requires data migration; no import tools exist" |
| **Evidence gap** | Insufficient information to reach a conclusion about a market question | "No data on retention beyond 90 days" |

## Hypothesis Status Tracking

Every positioning hypothesis gets a status that updates as evidence arrives:

| Status | Meaning | Action |
|--------|---------|--------|
| **Supported** | Evidence confirms the hypothesis | Proceed with confidence; use in positioning |
| **Weakened** | Some evidence contradicts but does not disprove | Investigate further; adjust confidence |
| **Disproven** | Evidence clearly contradicts the hypothesis | Discard; generate alternative hypothesis |
| **Stale** | No new evidence in 90+ days | Re-validate; do not rely on for decisions |
| **Unresolved** | Insufficient evidence to determine | Design validation experiment (Phase 5) |

## Decision Confidence

**This is decision confidence, not statistical confidence.** It is a composite score reflecting evidence quality, coverage, and consistency — not a probability or p-value.

### Composite Formula

```
Decision Confidence = (
  Evidence Quality Score (0-30) +
  Source Coverage Score (0-25) +
  Internal Consistency Score (0-20) +
  Counter-Evidence Survival Score (0-15) +
  Validation Evidence Score (0-10)
) / 100 * 100%
```

### Scoring Guide

| Component | What It Measures | Max |
|-----------|-----------------|-----|
| Evidence Quality | Proportion of HIGH-grade evidence vs LOW-grade | 30 |
| Source Coverage | Breadth of source types used (target: 5+ types) | 25 |
| Internal Consistency | Do evidence items contradict each other? | 20 |
| Counter-Evidence Survival | Did findings survive active disconfirmation? | 15 |
| Validation Evidence | Have any hypotheses been experimentally validated? | 10 |

### Confidence Bands

| Band | Range | Gate Decision |
|------|-------|---------------|
| **High** | 85-100% | GO — proceed to next phase |
| **Moderate** | 60-84% | CONDITIONAL GO — proceed with documented limitations |
| **Low** | 40-59% | RECYCLE — return to research; identify specific gaps |
| **Critical** | <40% | STOP — insufficient evidence; fundamental reframing needed |

## Unified Outcome Matrix

Used consistently across all gates, scope DAG, and scoring rubric:

| Condition | Decision | Action |
|-----------|----------|--------|
| Confidence ≥ target AND ≥ 3 segments identified AND evidence quality ≥ 60% | **GO** | Proceed to next phase |
| Confidence ≥ 60% of target AND ≥ 2 segments identified AND evidence quality ≥ 40% | **CONDITIONAL GO** | Proceed with documented limitations; queue validation experiments |
| Confidence < 60% of target OR < 2 segments identified OR evidence quality < 40% | **RECYCLE** | Return to research; address specific evidence gaps |
| Confidence < 40% OR 0 segments identified OR fundamental assumption disproven | **STOP** | Reframe the product-market decision; restart Phase 0 |

## Stack Auto-Detection

When a codebase is available, auto-detect the stack from project files:

| File(s) | Stack | Key Inventory Paths |
|---------|-------|-------------------|
| `package.json` with `next` | Next.js | `app/` or `pages/`, `api/`, `components/` |
| `package.json` without `next` | Node/React | `src/`, `public/`, `package.json` deps |
| `requirements.txt` or `pyproject.toml` | Python | `*.py`, `manage.py`, `app/`, `main.py` |
| `go.mod` | Go | `*.go`, `cmd/`, `internal/`, `pkg/` |
| `Cargo.toml` | Rust | `src/`, `Cargo.toml` deps |
| `Gemfile` | Ruby | `app/`, `config/`, `Gemfile` deps |
| `pom.xml` or `build.gradle` | Java | `src/main/`, `src/test/`, pom/gradle deps |

If detection fails, ask the user. If monorepo, detect all stacks and note each.

## Pre-Audit Questionnaire

Ask these before starting (unanswered = "unknown", not guessed):

1. **Domain**: What industry/domain does this product serve?
2. **Business model**: How does the product make money? (SaaS, marketplace, freemium, enterprise, usage-based, etc.)
3. **Geography**: Which markets/geographies are you targeting?
4. **Customers**: Who are your current customers? (segments, names, types)
5. **Team size**: How large is the team? (affects positioning capacity)
6. **Competitors**: Who do you consider your primary competitors?
7. **Positioning history**: Have you done positioning work before? What was the outcome?
8. **Audit trigger**: What prompted this audit? (launch, pivot, stagnation, expansion, drift, investor request)

## Per-Project Extensions

Create `.positioning-audit/extras/` directory for domain-specific audit dimensions:

- `domain-extra.md` — domain-specific evidence sources and evaluation criteria
- `competitor-extra.md` — additional competitor tracking dimensions
- `customer-extra.md` — customer evidence collection templates

Extensions are loaded automatically if present. Built-in dimensions are always evaluated; extensions add to them.

## Persistent State

All audit artifacts are stored in `.positioning-audit/` in the product/codebase root:

```
.positioning-audit/
├── state.json              # Current audit state (phase, gate, confidence, hypotheses)
├── evidence-corpus.json    # Assembled evidence with provenance
├── research-questions.json # Research question trees per phase
├── hypotheses.json         # Positioning hypotheses with status tracking
├── experiments.json        # Validation experiments and results
├── artifacts/              # Phase output documents (4-page standardized)
├── history/                # Previous audit snapshots for drift comparison
└── extras/                 # Per-project extension files
```

### State Schema

```json
{
  "audit_id": "uuid",
  "product_context": "path or description",
  "scope": "standard",
  "started_at": "ISO timestamp",
  "current_phase": 0,
  "current_gate": null,
  "decision_confidence": { "composite": 0, "quality": 0, "coverage": 0, "consistency": 0, "counter": 0, "validation": 0 },
  "hypotheses": [ { "id": "H1", "text": "...", "status": "unresolved", "evidence": [] } ],
  "evidence_types_present": [],
  "evidence_limitations": [],
  "phases_completed": [],
  "gates_passed": [],
  "last_updated": "ISO timestamp"
}
```

## Cross-Product Portfolio View

Portfolio aggregates all audited products (not just codebases) at `~/.positioning-audit-portfolio/portfolio.json`:

```json
{
  "audits": [
    {
      "product_name": "...",
      "audit_id": "uuid",
      "top_segment": "...",
      "positioning_statement": "...",
      "confidence": 0.87,
      "last_audited": "ISO timestamp",
      "drift_status": "stable|drifting|stale",
      "hypotheses_supported": 5,
      "hypotheses_disproven": 2,
      "experiments_run": 3,
      "experiments_passed": 2
    }
  ]
}
```

## Evidence Grading

Every finding and evidence item is graded:

| Grade | Criteria | Weight in Confidence |
|-------|----------|---------------------|
| **HIGH** | Direct observation, primary source, verifiable, recent (<6mo) | Full weight |
| **MEDIUM** | Secondary source, indirect observation, somewhat dated (6-18mo) | 0.6x weight |
| **LOW** | Anecdotal, inferred, old (>18mo), or unverified | 0.3x weight; **cannot be load-bearing** |

**Rule**: No positioning claim can rest solely on LOW-grade evidence. At least one HIGH or two MEDIUM evidence items required per load-bearing claim.

## Pipeline Overview

| Phase | Purpose | Gate | Key Output |
|-------|---------|------|------------|
| **0** | Frame product-market decision; define evidence requirements | Gate 0 | Research plan, question trees, evidence requirements |
| **1** | Product & evidence reconnaissance | Gate 1 | Evidence Corpus, product truth, capability inventory |
| **2** | Ultra-deep market & alternative research | Gate 2 | Market map, competitor/alternative matrix, counter-evidence |
| **3** | Segment & unmet-need triangulation | Gate 3 | Ranked segments with need intensity, urgency, WTP, proof |
| **4** | Product-market alignment & gap map | Gate 4 | 8-type gap classification, positioning hypotheses |
| **5** | Validation plan & experiments | Gate 5 | Experiment designs with thresholds, success metrics |
| **6** | Optional codebase audit & remediation | Gate 6 | Implementation gaps, remediation roadmap |
| **7** | Evidence refresh, drift tracking, re-ranking | Gate 7 | Hypothesis status update, drift report, re-ranked segments |

## Gate Framework

### Gate Decision Outcomes

Every gate produces one of four formal decisions — no gate defaults to pass:

- **GO**: All exit criteria met; proceed to next phase
- **CONDITIONAL GO**: Core criteria met with documented limitations; proceed but queue follow-up
- **RECYCLE**: Specific criteria unmet; return to earlier phase to address gaps
- **STOP**: Fundamental assumption disproven or insufficient evidence; reframe or abort

### Pre-Gate Self-Assessment (5 Dimensions)

Before requesting gate review, score each dimension 1-5:

| Dimension | 1 (Poor) | 3 (Adequate) | 5 (Strong) |
|-----------|----------|-------------|------------|
| **Evidence Quality** | Only LOW-grade evidence | Mix of MEDIUM and LOW | Multiple HIGH-grade items |
| **Source Coverage** | 1-2 source types | 3-4 source types | 5+ source types |
| **Logical Consistency** | Major contradictions | Minor tensions | No contradictions |
| **Counter-Evidence** | Not searched | Searched, found some | Searched, findings survived |
| **Decision Readiness** | Not ready to decide | Can decide with caveats | Ready to decide confidently |

**Threshold**: Composite ≥ 15/25 (standard), ≥ 12/25 (quick), ≥ 18/25 (deep) before requesting gate review.

### 360-Degree Coverage Checklist

Each phase must consider all applicable perspectives:

| Perspective | Question | Applicable Phases |
|-------------|----------|-------------------|
| **Customer** | What does the customer actually need and say? | 1, 2, 3, 4, 5 |
| **Competitor** | What do alternatives offer and how are they moving? | 2, 3, 4 |
| **Product** | What does the product actually do (evidence, not claims)? | 1, 4, 6 |
| **Market** | What structural forces shape this market? | 2, 3, 7 |
| **Financial** | What is the WTP, pricing model, and unit economics? | 3, 4, 5 |
| **Technical** | What are the implementation constraints and capabilities? | 1, 6 |

### Adversarial Review (Mandatory for Phases 3, 4, 5)

Three hostile personas review findings before gate:

1. **The Skeptic**: "This conclusion rests on assumptions, not evidence. What if the assumptions are wrong?"
2. **The Missing Perspective**: "Whose voice is not represented in this analysis? What would they say?"
3. **The Contrarian**: "The opposite conclusion is also defensible. What evidence supports the opposite?"

Findings must survive all three reviews. If a review identifies a fatal flaw, RECYCLE.

### Inter-Phase Consistency Check

At each gate, verify:
- Findings from the previous phase are still valid given new evidence
- No contradiction between phases has been silently ignored
- Evidence corpus has been updated with new findings
- Hypothesis statuses have been updated
- Research question trees have been updated with coverage status

## Phase 0: Pre-Execution Protocol — Frame the Product-Market Decision

### Purpose

Frame the product-market decision being made, define evidence requirements, build research question trees, and select skills for each phase. This phase is mandatory — no execution begins without it.

### Steps

#### 0a: Product-Market Decision Framing

Define what decision this audit will inform:
- **What product-market question are we answering?** (e.g., "Which segment should we target first?" or "Is our current positioning still valid?")
- **What would change our positioning if we knew it?** (list specific unknowns)
- **What evidence would we need to be 95% confident in the answer?**
- **What is the cost of being wrong?** (wrong segment, wrong positioning, wrong gap)

Output: Decision framing document (1 page)

#### 0b: Evidence Requirements Definition

Based on the decision framing, define:
- **What evidence types are needed?** (from the Evidence Corpus taxonomy)
- **What is available vs. what is missing?**
- **What are the evidence limitations?** (explicitly stated, not hidden)
- **What counter-evidence would disconfirm our hypotheses?**

Output: Evidence requirements matrix

#### 0c: Research Question Tree Construction

Build the initial research question tree:
- Root question: The product-market decision from 0a
- Level 1: 3-5 sub-questions that must be answered
- Level 2: 2-3 sub-questions per Level 1 question
- Mark each with: source type needed, coverage status (uncovered), counter-evidence status (not searched)

Depth: 2 levels (quick), 3 levels (standard), 4 levels (deep)

Output: Research question tree (stored in `research-questions.json`)

#### 0d: Per-Phase Skill Selection

Select the most relevant skill for each upcoming phase:

| Phase | Candidate Skills | Selection Criteria |
|-------|-----------------|-------------------|
| 1 | `codebase-onboarding` (if code available), `deep-research`, manual evidence assembly | Codebase present? → codebase-onboarding; else → manual |
| 2 | `deep-research`, `market-research`, `market-research-reports` | Always: deep-research + market-research |
| 3 | `market-research`, `deep-research` | Always: market-research for segment sizing |
| 4 | `ecc-plan`, `ecc-advisor` (if available) | Always: ecc-plan for gap mapping |
| 5 | `ecc-plan`, `ecc-verify` | Always: ecc-plan for experiment design |
| 6 | `codebase-onboarding` (if code available), skip if no codebase | Codebase present? → codebase-onboarding; else → skip Phase 6 |
| 7 | `ecc-verify`, `ecc-advisor` (if available) | Always: ecc-verify for drift detection |

**Rule**: Skill selection is re-evaluated at every gate transition. If a phase's findings change what's needed for the next phase, update the selection.

#### 0e: Execution Visualization

Before starting, visualize the full execution:
- Walk through each phase mentally
- Identify likely trouble spots (where evidence may be thin)
- Pre-plan recycling paths (if Phase 2 finds no viable segments, what do we re-research?)
- Estimate time per phase based on scope

Output: Execution plan with time estimates and risk points

#### 0f: Plan Refinement

Refine the plan based on visualization:
- Adjust scope if time constraints are identified
- Add specific research targets for thin-evidence areas
- Define stop conditions (what would make us abort the audit?)

#### 0g: Confidence Baseline

Set the initial confidence:
- Start at 0% — no confidence until evidence is gathered
- Define what 95% looks like for this specific audit (what evidence, how much, what consistency)
- Define what would trigger RECYCLE vs STOP

### Gate 0: Pre-Execution Gate

**Exit Criteria** (all must be checked):
- [ ] Product-market decision is explicitly framed
- [ ] Evidence requirements are defined with available/missing marked
- [ ] Research question tree is constructed to appropriate depth
- [ ] Per-phase skill selection is completed
- [ ] Execution is visualized with risk points identified
- [ ] Stop conditions are defined
- [ ] Confidence baseline is set with 95% target defined
- [ ] Pre-gate self-assessment composite ≥ threshold (12/25 quick, 15/25 standard, 18/25 deep)

**Gate Decision**: GO → proceed to Phase 1 | RECYCLE → refine framing | STOP → insufficient context to proceed

## Phase 1: Product & Evidence Reconnaissance

### Purpose

Assemble the Product Truth — what the product actually is and does, grounded in evidence. The codebase is one optional evidence source, not the primary one.

### Steps

#### 1a: Product Promise Extraction

- What does the product claim to do? (marketing site, docs, pitch deck, sales materials)
- What is the stated value proposition?
- What JTBD (Jobs To Be Done) does it claim to serve?
- What outcomes does it promise?

#### 1b: Customer Evidence Assembly

Gather and classify all available customer evidence:
- **Customer signals**: interviews, feedback, reviews, testimonials, complaints
- **Behavioral data**: usage analytics, telemetry, session recordings, feature adoption
- **Commercial signals**: pricing, conversion rates, deal sizes, win/loss analysis, churn reasons
- **Support signals**: support tickets, complaint patterns, feature requests, FAQ volume

Each item is classified by evidence type, graded (HIGH/MEDIUM/LOW), and given provenance.

#### 1c: Actual Capability Inventory

- What does the product actually do? (not what it claims)
- If codebase available: inventory routes, features, integrations, data models
- If no codebase: inventory from live product inspection, docs, demos, or user reports
- **Compare promise vs. actual**: Where do they diverge?

#### 1d: Evidence Limitation Statement

Explicitly document:
- What evidence types are missing?
- What questions cannot be answered with current evidence?
- What assumptions are being made without evidence?
- What is the risk of these gaps?

#### 1e: Product Truth Synthesis

Synthesize into a 1-page Product Truth document:
- **Product promise**: what it claims
- **Actual capability**: what it does
- **Customer outcomes**: what customers achieve (if known)
- **Promise-capability gap**: where they diverge
- **Evidence limitations**: what we don't know

### Gate 1: Evidence Reconnaissance Gate

**Exit Criteria**:
- [ ] Product promise is extracted and documented
- [ ] At least 3 evidence types are present in the corpus (any combination)
- [ ] Actual capability inventory is complete (from codebase, live product, or docs)
- [ ] Promise-capability gap is documented
- [ ] Evidence limitations are explicitly stated
- [ ] Product Truth synthesis is written (1 page)
- [ ] Research question tree updated with Phase 1 coverage
- [ ] 360-degree: Customer + Product perspectives covered
- [ ] Pre-gate self-assessment ≥ threshold

**Gate Decision**: GO → Phase 2 | CONDITIONAL GO → Phase 2 with evidence limitations | RECYCLE → gather more evidence | STOP → no usable product context

## Phase 2: Ultra-Deep Market & Alternative Research

### Purpose

Conduct ultra-deep market research that goes beyond "find competitors." This phase builds a complete picture of the market landscape, alternatives, structural forces, and actively searches for disconfirming evidence.

### Steps

#### 2a: Market Structure Mapping

- **Market size and growth**: TAM, SAM, SOM estimates with sources
- **Market structure**: fragmented vs. concentrated, barriers to entry, regulatory factors
- **Structural changes**: what is shifting in this market? (technology, regulation, demographics, behavior)
- **Timing**: is this market growing, maturing, or declining? What window of opportunity exists?

#### 2b: Competitor & Alternative Matrix

Research not just direct competitors but the full alternative landscape:

| Category | What to Research | Output |
|----------|-----------------|--------|
| **Direct competitors** | Same product category, same target | Feature comparison, pricing, positioning |
| **Indirect alternatives** | Different product category, same JTBD | Why customers might choose them instead |
| **Status quo** | Doing nothing or using spreadsheets/manual processes | What keeps customers in the status quo? |
| **Substitutes** | Completely different approach to the same problem | What would make the problem irrelevant? |
| **Switching costs** | What does it cost to switch from each alternative? | Switching cost matrix |
| **Distribution** | How do competitors reach customers? | Channel map |
| **Recent changes** | What has changed in the last 6-12 months? | Movement log (funding, launches, pivots) |

#### 2c: Counter-Evidence Search

Actively search for evidence that would disconfirm the product's value proposition:
- **Search for "why [product category] doesn't work"**
- **Search for negative reviews, complaints, and churn stories**
- **Search for market reports that contradict growth assumptions**
- **Search for emerging alternatives that could disrupt the category**
- **Document what was searched and what was found** (even if nothing found)

Passes: 1 (quick), 2 (standard), 3 (deep)

#### 2d: Research Question Tree Update

Update the research question tree with Phase 2 findings:
- Mark covered sub-questions
- Add new sub-questions discovered during research
- Note counter-evidence findings
- Identify remaining uncovered questions

#### 2e: Market Evidence Synthesis

Synthesize into a 2-page Market Landscape document:
- Market structure and forces
- Competitor/alternative matrix
- Counter-evidence findings
- Key uncertainties and what they mean for positioning

### Gate 2: Market Research Gate

**Exit Criteria**:
- [ ] Market structure is mapped with size, growth, and structural changes
- [ ] Competitor matrix includes direct + indirect + status quo + substitutes
- [ ] Switching costs are documented for top alternatives
- [ ] Distribution channels are mapped
- [ ] Recent market changes (6-12 months) are documented
- [ ] Counter-evidence search is completed (appropriate passes for scope)
- [ ] Research question tree is updated with coverage status
- [ ] 360-degree: Competitor + Market perspectives covered
- [ ] Pre-gate self-assessment ≥ threshold
- [ ] **Advisor checkpoint**: if `ecc-advisor` available, call for second opinion on market findings

**Gate Decision**: GO → Phase 3 | CONDITIONAL GO → Phase 3 with market uncertainties | RECYCLE → deeper market research | STOP → market does not support the product category

## Phase 3: Segment & Unmet-Need Triangulation

### Purpose

Triangulate segments not just by demographics but by need intensity, urgency, reachability, willingness to pay, and proof availability. This is where market research meets product evidence.

### Steps

#### 3a: Segment Hypothesis Generation

Generate segment hypotheses from the evidence:
- **From customer evidence**: who is already using the product? What patterns emerge?
- **From market research**: which market segments have the highest unmet need?
- **From competitor gaps**: where are competitors underserving customers?
- **From JTBD analysis**: who has the job that the product serves?

Target: 3 (quick), 5 (standard), 8 (deep) segment hypotheses

#### 3b: Segment Scoring (7 Dimensions)

Score each segment hypothesis on 7 dimensions (1-10 each):

| Dimension | What It Measures | Evidence Source |
|-----------|-----------------|-----------------|
| **Need intensity** | How severe is the pain? | Customer evidence, support data |
| **Urgency** | How soon do they need a solution? | Market research, behavioral signals |
| **Reachability** | Can we reach them through available channels? | Distribution map, competitor analysis |
| **Willingness to pay** | What will they pay? | Pricing data, sales data, market research |
| **Competition** | How well-served are they by alternatives? | Competitor matrix |
| **Product fit** | Does our product actually serve their need? | Product Truth, capability inventory |
| **Proof availability** | Can we prove our value to them? | Evidence corpus, case studies, testimonials |

**Beachhead selection**: The top-ranked segment by composite score becomes the beachhead. The beachhead is the segment where need intensity × urgency × product fit is highest, even if TAM is smaller.

#### 3c: Negative ICP Definition

For the top 3 segments, define who is NOT a fit:
- **Who should we NOT target?** (and why)
- **What signals indicate a bad fit?** (low WTP, high support burden, wrong JTBD)
- **What segments look attractive but are traps?** (high pain but no WTP, or high WTP but wrong product)

#### 3d: Unmet-Need Statement per Segment

For each top segment, write a structured unmet-need statement:

> [Segment] needs to [job to be done] because [pain point], but currently [what they use today] fails because [specific limitation]. [Product] could address this by [capability], and we can prove it with [evidence type].

#### 3e: Triangulation

Triangulate each segment by cross-referencing:
- **Customer evidence** → Do real customers show this need?
- **Market research** → Does the market data support the segment size and need?
- **Product capability** → Can the product actually serve this segment?
- **Counter-evidence** → Did the segment survive the counter-evidence search?

If any leg of the triangulation fails, the segment is downgraded.

### Gate 3: Segment Triangulation Gate

**Exit Criteria**:
- [ ] ≥ 3 segment hypotheses generated (or ≥ 2 for quick scope)
- [ ] Each segment scored on all 7 dimensions
- [ ] Beachhead segment is selected with rationale
- [ ] Negative ICP is defined for top 3 segments
- [ ] Unmet-need statements are written for top 3 segments
- [ ] Triangulation is completed for each segment (all 4 legs)
- [ ] Segments that failed triangulation are documented with reasons
- [ ] **Adversarial review completed** (3 hostile personas)
- [ ] 360-degree: Customer + Competitor + Market + Financial perspectives covered
- [ ] Pre-gate self-assessment ≥ threshold

**Gate Decision**: GO → Phase 4 | CONDITIONAL GO → Phase 4 with weakened segments | RECYCLE → generate new segments | STOP → no viable segments identified

## Phase 4: Product-Market Alignment & Gap Map

### Purpose

Compare market needs against product reality using the full alignment chain — not just "feature vs. need." Classify every gap into one of 8 types and generate positioning hypotheses that can be validated.

### The Alignment Chain

For each top segment, trace the full chain:

```
Market Need → Customer Outcome → Product Promise → Actual Capability → Proof → Positioning → Experiment
```

At each link, ask: **Is there a gap?** If yes, classify it.

### Steps

#### 4a: Alignment Chain Analysis per Segment

For each top 3 segments, trace the alignment chain link by link:

| Link | Question | Evidence Source |
|------|----------|-----------------|
| Need → Outcome | Does the customer outcome actually address the need? | Customer evidence, JTBD |
| Outcome → Promise | Does the product promise to deliver that outcome? | Marketing, docs, sales materials |
| Promise → Capability | Does the product actually have the capability to deliver? | Product Truth, codebase (optional) |
| Capability → Proof | Is there proof that the capability works? | Evidence corpus, testimonials, data |
| Proof → Positioning | Does the positioning reflect the proven capability? | Current messaging, positioning statement |
| Positioning → Experiment | What experiment would validate this positioning? | To be designed in Phase 5 |

#### 4b: Gap Classification

Classify every gap found in 4a into the 8-type taxonomy:

| Gap Type | Where in Chain | Example |
|----------|---------------|---------|
| **Need gap** | Need → Outcome | Need exists but no product outcome addresses it |
| **Product gap** | Promise → Capability | Product promises something it can't deliver |
| **Proof gap** | Capability → Proof | Product works but no evidence proves it |
| **Positioning gap** | Proof → Positioning | Positioning doesn't reflect what's proven |
| **Pricing gap** | Any link | Pricing doesn't match segment's WTP or buying process |
| **Distribution gap** | Any link | Product isn't reachable through segment's channels |
| **Adoption gap** | Any link | Onboarding/integration/migration blocks adoption |
| **Evidence gap** | Any link | Insufficient information to determine if a gap exists |

For each gap, document:
- **Gap type**: which of the 8
- **Severity**: Critical (blocks positioning) / Major (weakens positioning) / Minor (nuance adjustment)
- **Evidence**: what evidence supports this gap classification
- **Fix approach**: what would close this gap (product change, proof creation, messaging change, pricing change, etc.)

#### 4c: Positioning Hypothesis Generation

For each segment, generate 2-3 positioning hypotheses:

> **Hypothesis**: If we position [product] as [category] for [segment] who need to [JTBD], then [expected outcome] because [proof], and we will validate this by [experiment type].

Each hypothesis gets:
- **ID**: H1, H2, H3, ...
- **Status**: Unresolved (until validated in Phase 5)
- **Load-bearing claims**: which specific claims must be true for this hypothesis to hold
- **Evidence support**: what evidence currently supports it
- **Counter-evidence**: what evidence currently contradicts it
- **Confidence**: current decision confidence for this hypothesis

#### 4d: Positioning Statement Drafting

For the top hypothesis per segment, draft a positioning statement using this structure:

> For [target segment] who need to [job to be done], [product] is a [category] that [key benefit] because [proof point], unlike [primary alternative] which [key limitation].

**Proof requirements**: The "because [proof point]" must reference HIGH or MEDIUM grade evidence. No proof point may rest solely on LOW-grade evidence.

#### 4e: Gap Map Visualization

Create a visual gap map showing:
- Each segment on one axis
- Each alignment chain link on the other
- Gaps color-coded by type and severity
- Hypotheses overlaid on the map

### Gate 4: Alignment & Gap Map Gate

**Exit Criteria**:
- [ ] Alignment chain is traced for each top 3 segments
- [ ] Every gap is classified into one of 8 types with severity
- [ ] 2-3 positioning hypotheses generated per segment (6-9 total)
- [ ] Each hypothesis has load-bearing claims identified
- [ ] Positioning statements drafted for top hypothesis per segment
- [ ] All proof points reference HIGH or MEDIUM grade evidence
- [ ] Gap map is visualized
- [ ] **Adversarial review completed** (3 hostile personas)
- [ ] 360-degree: Customer + Competitor + Product + Financial perspectives covered
- [ ] Pre-gate self-assessment ≥ threshold
- [ ] **Advisor checkpoint**: if `ecc-advisor` available, call for second opinion on positioning hypotheses

**Gate Decision**: GO → Phase 5 | CONDITIONAL GO → Phase 5 with documented gaps | RECYCLE → re-analyze alignment | STOP → fundamental alignment failure

## [APPROVAL GATE — User Decision]

Before proceeding to Phase 5, present the positioning hypotheses and gap map to the user for approval. The user selects which hypothesis to validate.

**User selects**: Which positioning hypothesis to validate → determines Phase 5 experiment design

## Phase 5: Validation Plan & Experiments

### Purpose

Every load-bearing positioning claim gets a validation experiment with a measurable success threshold. This is not "we'll do some outreach" — this is structured experimental design.

### Steps

#### 5a: Load-Bearing Claim Extraction

From the approved positioning hypothesis, extract every claim that must be true:
- **Segment claim**: "This segment has this need at this intensity"
- **Product claim**: "Our product can deliver this outcome"
- **Proof claim**: "We can prove this with this evidence"
- **Pricing claim**: "This segment will pay this price"
- **Distribution claim**: "We can reach this segment through this channel"
- **Competitive claim**: "We are better than [alternative] at [dimension]"

#### 5b: Experiment Design per Claim

For each load-bearing claim, design a validation experiment using the fidelity ladder (from Lean Startup):

| Fidelity | Method | Cost | Evidence Strength | When to Use |
|-----------|--------|------|-------------------|-------------|
| **Low** | Landing page test, smoke test, fake door | Low | Weak signal | Test demand exists |
| **Medium** | Interview, survey, prototype demo | Medium | Qualitative | Test need intensity and WTP |
| **High** | Pilot, beta, paid trial, A/B test | High | Quantitative | Test conversion and retention |

**Start with the cheapest experiment that can falsify the hypothesis.**

For each experiment, define:

| Element | Description |
|---------|-------------|
| **Hypothesis being tested** | Which specific claim |
| **Experiment type** | Low/Medium/High fidelity |
| **Method** | What exactly will be done |
| **Success threshold** | What result would confirm the hypothesis |
| **Failure threshold** | What result would disprove the hypothesis |
| **Sample size** | How many data points needed |
| **Duration** | How long the experiment runs |
| **Cost** | Time, money, effort |
| **Evidence type produced** | What evidence type will result |

#### 5c: Experiment Priority Ranking

Rank experiments by:
1. **Falsification potential** — can this experiment disprove the hypothesis?
2. **Cost efficiency** — how much evidence per unit of effort?
3. **Blocking potential** — is this claim blocking other claims?

Run highest-priority experiments first.

#### 5d: Validation Plan Document

Compile all experiments into a Validation Plan:
- List of all load-bearing claims
- Experiment design for each
- Priority ranking
- Execution timeline
- Resource requirements
- Success/failure criteria

### Gate 5: Validation Plan Gate

**Exit Criteria**:
- [ ] All load-bearing claims are extracted from the approved hypothesis
- [ ] Each claim has a designed experiment with success and failure thresholds
- [ ] Experiments are priority-ranked
- [ ] Validation plan document is written
- [ ] cheapest-falsification-first principle is followed
- [ ] **Adversarial review completed** (3 hostile personas)
- [ ] 360-degree: Customer + Financial perspectives covered
- [ ] Pre-gate self-assessment ≥ threshold

**Gate Decision**: GO → Phase 6 (if codebase) or Phase 7 (if no codebase) | CONDITIONAL GO → proceed with reduced validation | RECYCLE → redesign experiments | STOP → hypothesis cannot be validated

## Phase 6: Optional Codebase Audit & Remediation

### Purpose

**This phase is optional.** If a codebase is available, audit it against the validated positioning to identify implementation gaps. If no codebase, skip to Phase 7.

### Steps

#### 6a: Positioning-to-Implementation Gap Audit

Compare validated positioning against codebase:
- **Positioning claim → Implementation**: Does the code support each claim?
- **Segment-specific features**: Are features for the target segment present and functional?
- **Proof infrastructure**: Are analytics, tracking, and reporting capabilities in place to generate proof?
- **Pricing implementation**: Does the codebase support the validated pricing model?
- **Distribution readiness**: Are integrations with target channels implemented?

#### 6b: Gap Remediation Roadmap

For each implementation gap:
- **Gap**: what's missing
- **Effort**: S/M/L
- **Priority**: P0 (blocks launch) / P1 (weakens positioning) / P2 (nice to have)
- **Remediation approach**: what to build/change
- **Dependencies**: what must happen first

#### 6c: Technical Debt Assessment (if deep scope)

- What technical debt blocks positioning delivery?
- What refactoring would unlock positioning-relevant features?
- What is the cost of not addressing each debt item?

### Gate 6: Codebase Audit Gate

**Exit Criteria** (only if codebase available):
- [ ] Positioning-to-implementation gaps are documented
- [ ] Remediation roadmap is created with priorities and effort estimates
- [ ] P0 gaps are identified as launch blockers
- [ ] Technical debt relevant to positioning is documented (deep scope only)
- [ ] 360-degree: Technical perspective covered
- [ ] Pre-gate self-assessment ≥ threshold

**Gate Decision**: GO → Phase 7 | CONDITIONAL GO → Phase 7 with remediation backlog | RECYCLE → deeper codebase analysis | STOP → codebase fundamentally cannot support positioning

## Phase 7: Evidence Refresh, Drift Tracking & Re-Ranking

### Purpose

Close the learning loop. Update hypothesis statuses based on experiment results, track positioning drift, and re-rank segments based on new evidence.

### Steps

#### 7a: Hypothesis Status Update

For each positioning hypothesis, update status based on all evidence gathered:

| Status | Criteria |
|--------|----------|
| **Supported** | Experiment confirmed; HIGH-grade evidence supports; survived counter-evidence |
| **Weakened** | Some evidence contradicts; experiment inconclusive; counter-evidence found |
| **Disproven** | Experiment failed; HIGH-grade evidence contradicts |
| **Stale** | No new evidence in 90+ days; last validation > 6 months ago |
| **Unresolved** | Experiment not yet run; insufficient evidence |

#### 7b: Evidence Refresh

- What new evidence has arrived since the audit started?
- What evidence is now stale and needs re-validation?
- What evidence gaps remain?
- What new research questions emerged?

#### 7c: Positioning Drift Assessment

Compare current positioning against:
- **Previous audit** (if `previous_audit` parameter was provided)
- **Market changes** identified in Phase 2
- **Hypothesis status changes** from 7a

Drift indicators:
- **Segment drift**: target segment has shifted or no longer fits
- **Need drift**: customer needs have evolved
- **Competitive drift**: competitors have moved significantly
- **Product drift**: product has changed capabilities
- **Evidence drift**: key evidence is now stale

#### 7d: Segment Re-Ranking

Re-score segments based on updated evidence:
- Apply new evidence to the 7-dimension scoring
- Update beachhead if a different segment now scores higher
- Document what changed and why

#### 7e: Drift Cadence Setup

Define the ongoing monitoring cadence:

| Cadence | What to Monitor | Trigger |
|---------|----------------|---------|
| **Weekly** | Experiment results, new customer signals | Active validation phase |
| **Monthly** | Competitor movement, market changes, new evidence | Post-validation monitoring |
| **Quarterly** | Full re-audit, hypothesis re-validation, segment re-ranking | Standard drift tracking |

#### 7f: Final Audit Report

Compile the complete audit into a final report:
- **Executive summary**: 1 paragraph
- **Top 3 segments**: with scores, unmet needs, and positioning statements
- **Gap map**: 8-type classification with severities
- **Hypothesis status**: all hypotheses with current status
- **Validation results**: experiments run, outcomes, evidence produced
- **Remediation roadmap** (if codebase audited): P0/P1/P2 items
- **Drift assessment**: what has changed, what to watch
- **Decision confidence**: composite score with subscores
- **Evidence limitations**: what we still don't know

### Gate 7: Audit Completion Gate

**Exit Criteria**:
- [ ] All hypotheses have updated statuses
- [ ] Evidence refresh is completed
- [ ] Positioning drift is assessed (if previous audit exists)
- [ ] Segments are re-ranked based on final evidence
- [ ] Drift cadence is defined
- [ ] Final audit report is written
- [ ] Decision confidence is calculated with all subscores
- [ ] Evidence limitations are documented
- [ ] State is persisted to `.positioning-audit/state.json`
- [ ] Portfolio is updated at `~/.positioning-audit-portfolio/portfolio.json`

**Gate Decision**: GO → audit complete | CONDITIONAL GO → complete with follow-up experiments queued | RECYCLE → re-run specific phases | STOP → fundamental positioning failure; reframe needed

## Dependency Gating

| Phase | Depends On | Can Skip If |
|-------|-----------|-------------|
| 0 | None | Never — mandatory |
| 1 | Phase 0 | Never — evidence corpus is foundational |
| 2 | Phase 1 | Never — market research needs product truth |
| 3 | Phase 2 | Never — segments need market context |
| 4 | Phase 3 | Never — alignment needs segments |
| 5 | Phase 4 + User Approval | Never — validation needs approved hypothesis |
| 6 | Phase 5 | **No codebase available** — skip entirely |
| 7 | Phase 5 (or 6 if codebase) | Never — closes the learning loop |

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
- Per-project extensions in `.positioning-audit/extras/*.md` are loaded if present — extends built-in dimensions
- Persistent state in `.positioning-audit/state.json` enables resumption and drift tracking
- Cross-product portfolio at `~/.positioning-audit-portfolio/portfolio.json` aggregates all audited products
- Evidence grading (HIGH/MEDIUM/LOW) is mandatory for every finding — LOW findings cannot be load-bearing
- **At least one HIGH or two MEDIUM evidence items required per load-bearing positioning claim**
- **Every load-bearing claim gets a validation experiment** with measurable success and failure thresholds
- **Gap classification (8 types) is mandatory** for every gap identified in Phase 4
- **Hypothesis status tracking is mandatory** — every hypothesis has a status that updates with evidence
- **Decision confidence is not statistical confidence** — it is a composite of evidence quality, coverage, and consistency
- **Unified outcome matrix is used everywhere** — gates, scope DAG, and scoring rubric all reference the same matrix
- **Counter-evidence search is mandatory** — at least 1 pass (quick), 2 (standard), 3 (deep)
- **Research question trees are mandatory** — every phase updates the tree with coverage status
- Advisor checkpoints: call `ecc-advisor` before Phase 2 and Phase 4 if available; if unavailable, proceed with documented skip
- **Absence of evidence is itself evidence** — mark as "evidence limitation" in the corpus, do not guess
- **Contradictions are surfaced, not hidden** — if product promise contradicts customer outcomes, flag it explicitly

### Artifact Format

Every phase produces a standardized 4-page artifact:

| Page | Content |
|------|---------|
| **Page 1** | Decision confidence log (composite + 5 subscores + iteration count), evidence types present, evidence limitations |
| **Page 2** | Phase findings with evidence citations (every claim cites its evidence type and grade) |
| **Page 3** | Gap analysis or segment analysis (phase-dependent), research question tree update |
| **Page 4** | Gate decision, exit criteria checklist, adversarial review results, next-phase skill selection |

## Upstream Source

- Created from user request: "Identification of top 3 niche customer segments and positioning strategy"
- Optimized via `ecc-prompt-optimize` workflow
- Revised via `@deep-research` with web research on best practices
- Methodology sources: MIT Disciplined Entrepreneurship, Stratridge 2026, ICP Scoring Rubric, N.I.C.H.E. Framework, Product Maturity Assessment, IntentGuard, PrismGrid, Stage Gate PM, Adversarial Review, Audit Readiness Framework, TriAdReview, IMPACT Framework, plugin-gtm, Lumen PM, code-repository-audit-skill, Codebase Pattern Extraction, Auditor
- v3 additions: Phase 0 Pre-Execution Protocol, Confidence Threshold Mechanism (95% target), Inter-Phase Skill Re-Evaluation, dynamic per-phase skill selection
- v4 additions: Input Parameters, Scope Selection (quick/standard/deep), Stack Auto-Detection, Pre-Audit Questionnaire, Per-Project Extensions, Persistent State, Cross-Codebase Portfolio View, Evidence Grading, IMPACT Framework integration, advisor checkpoint verification
- v5 redesign: Codebase made optional; Product Truth / Evidence Corpus added as primary input; Research Question Trees with saturation criteria; 8-type Gap Classification (need/product/proof/positioning/pricing/distribution/adoption/evidence); Alignment Chain (market need → customer outcome → product promise → actual capability → proof → positioning → experiment); Validation Experiments with fidelity ladder and success/failure thresholds; Hypothesis Status Tracking (supported/weakened/disproven/stale/unresolved); Decision Confidence renamed (not statistical); Unified Outcome Matrix; counter-evidence search mandatory; Phase 6 made optional; Phase 7 added for evidence refresh and drift tracking; Cross-product portfolio replaces cross-codebase portfolio; JTBD Framework, NIST AI RMF Core, NIST AI 800-3, Evidence Engine, Latent Spark, AHRQ Research Gap Framework, Lean Startup Validated Learning, ParallelHQ Market Gap Guide added as methodology sources
