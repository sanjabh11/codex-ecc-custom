---
name: ecc-niche-positioning-audit
description: >-
  Identify top 3 niche customer segments and define market positioning strategy
  through codebase audit and market research. Seven-phase pipeline with approval
  gates, 95% confidence threshold, evidence-anchored scoring, ICP rubric,
  beachhead methodology, 8-lens positioning audit, adversarial review, dynamic
  per-phase skill selection, quarterly drift tracking, stack auto-detection,
  scope selection (quick/standard/deep), persistent state, and cross-codebase
  portfolio. Designed for repeated use across multiple codebases.
  TRIGGER when: "niche segment", "positioning strategy", "positioning drift",
  "customer segment identification", "codebase audit positioning", "ICP",
  "beachhead segment", or "product-market fit audit".
  DO NOT TRIGGER when: no codebase is available, or the task is purely
  marketing copy generation without strategic analysis.
---

# Niche Positioning Audit

Identify top 3 niche customer segments and define market positioning strategy through a systematic 7-phase pipeline with evidence-anchored gates.

## Prerequisites

- A web application codebase accessible in the workspace (any stack — see `references/stack-recon.md`)
- Ability to run web searches for market research
- User approval required before Phase 5 (codebase audit execution) and Phase 6 (remediation)
- If `ecc-advisor` is available, call advisor before Phase 2 and Phase 5

## Input Parameters

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| `codebase_path` | Yes | Absolute path to the codebase root | Current workspace |
| `scope` | No | `quick`, `standard`, `deep` (see `references/scope-dag.md`) | `standard` |
| `domain_hint` | No | `saas`, `ecommerce`, `fintech`, `healthtech`, `devtools`, `consumer`, `marketplace`, `other` | Auto-detected |
| `stack_hint` | No | `react`, `next`, `vue`, `angular`, `svelte`, `python`, `go`, `node`, `rust`, `ruby`, `java` | Auto-detected |
| `existing_customers` | No | Path to customer data or description | None (Phase 2 discovers) |
| `competitor_list` | No | Known competitors | Discovered in Phase 2 |
| `previous_audit` | No | Path to previous audit artifacts | None (first run) |
| `output_dir` | No | Directory for audit artifacts | `.positioning-audit/` |

## Scope Selection

Three scope modes adapt depth and time investment. See `references/scope-dag.md` for the full dependency matrix, phase I/O contracts, and gate decision table.

| Scope | Phases | Time | When to Use |
|-------|--------|------|-------------|
| **quick** | P0(light) + P1 + P2(light) + P4(scoring only) | 15-30 min | "Just tell me my top 3 segments and positioning scores" |
| **standard** | All 7 phases | 1-3 hours | First audit or quarterly re-audit |
| **deep** | All 7 phases + extended research + per-feature audit | 3-6 hours | Pre-pivot, pre-fundraise, post-major-launch |

## Pre-Audit Questionnaire

Before Phase 0, ask the user these calibration questions (skip if provided via input parameters):

1. What domain does this codebase serve?
2. What is the business model? (subscription, one-time, freemium, usage-based, marketplace, advertising)
3. What geography is the target? (US, EU, APAC, global, specific countries)
4. Are there existing paying customers? (yes/no + count)
5. What is the team size? (solo, 2-10, 11-50, 50+)
6. What is the primary competitor or alternative?
7. Has positioning been formally defined before?
8. What is the audit trigger? (quarterly, pre-pivot, post-launch, new product, investor request)

Answers stored in `.positioning-audit/questionnaire.json`.

## Per-Project Extensions

Create `.positioning-audit/extras/*.md` files to add domain-specific audit dimensions. Loaded after built-in dimensions and merged into phase methodology at execution time.

## Persistent State

All artifacts and state stored in `.positioning-audit/`:

```
.positioning-audit/
├── questionnaire.json
├── state.json                  # See schemas/state.schema.json
├── research-ledger.json        # See references/research-protocol.md
├── phase-0-pre-execution-protocol.md
├── phase-1-codebase-recon.md
├── phase-2-market-research.md
├── phase-3-priority-alignment.md
├── phase-4-positioning-strategy.md
├── phase-5-codebase-audit.md
├── phase-6-remediation-roadmap.md
├── extras/
├── history/                    # Previous runs for drift comparison
└── evidence-refresh.log        # Weekly/biweekly signals (see references/governance.md)
```

State schema: `schemas/state.schema.json`. Privacy and redaction rules: `references/state-schema.md`.

## Cross-Codebase Portfolio

When the user runs this skill on multiple codebases, each audit can contribute to a portfolio at `~/.positioning-audit-portfolio/portfolio.json`. **Requires explicit user opt-in per codebase** — see `references/state-schema.md`.

## Evidence Grading

Every finding must be graded: **HIGH** (≥ 2 independent sources, cross-validated), **MEDIUM** (1 strong or 2+ weak), **LOW** (single unverified or inference). LOW findings cannot be load-bearing. See `references/scoring-rubric.md` for the full grading and certainty assessment.

## Pipeline Overview

```
Phase 0: Pre-Execution Protocol
    → [GATE 0: Readiness Confirmation]
Phase 1: Codebase Reconnaissance
    → [GATE 1: Recon Completeness]
Phase 2: Market Deep Research & ICP Definition
    → [GATE 2: Research Validity]
Phase 3: Priority Alignment & Triangulation
    → [GATE 3: Alignment Integrity]
Phase 4: Positioning Strategy & 8-Lens Audit
    → [APPROVAL GATE — User Decision]
Phase 5: Codebase Audit Execution
    → [GATE 5: Audit Rigor]
Phase 6: Remediation Roadmap & Drift Tracking
    → [GATE 6: Roadmap Actionability]
```

No phase begins until the previous phase's gate is passed. At each gate transition, re-evaluate skill selection and confidence. See `references/scope-dag.md` for scope-specific gate thresholds and phase I/O contracts.

Artifacts must conform to `schemas/artifact.schema.json` (machine-checkable structure replacing prose "4-page" format).

---

## Gate Framework

Every gate produces exactly one: **GO**, **CONDITIONAL GO**, **RECYCLE**, or **STOP**. No gate defaults to pass. Exit criteria are defined before the phase starts.

### Pre-Gate Self-Assessment (5 dimensions, 1-5 each, composite 5-25)

| Dimension | 1 (Ad Hoc) | 5 (Continuous) |
|-----------|------------|----------------|
| Documentation completeness | No structure | All findings with citations |
| Evidence currency | Stale/single source | Multiple independent, current |
| Coverage breadth | Only obvious areas | All perspectives, blind spots listed |
| Traceability | Cannot trace to source | Full trace + forward to recommendations |
| Issue resolution | Open questions unaddressed | All addressed or deferred with rationale |

**Thresholds**: standard/deep ≥ 15/25; quick ≥ 12/25. Below = automatic RECYCLE. See `references/scoring-rubric.md`.

### Confidence Threshold

Every phase must produce a confidence score (0-100%) before gate review. See `references/scoring-rubric.md` for the deterministic formula.

| Band | Action |
|------|--------|
| ≥ 95% | Proceed to gate review |
| 80-94% | Improvisation loop (max 3 iterations) |
| 60-79% | Extended improvisation loop (max 3 iterations) |
| < 60% | RECYCLE — restart phase |
| Insufficient evidence | STOP — qualitative fallback |

### 360-Degree Coverage Checklist

Every phase must cover applicable perspectives: Customer, Competitor, Codebase, Market, Financial, Technical. Missing perspective = cannot pass gate.

### Adversarial Review (Phases 3, 4, 5)

Three hostile personas must each find at least one issue or produce a falsification statement: **The Skeptic**, **The Missing Perspective**, **The Contrarian**. See `references/governance.md` for auditor-role separation and independent review rules.

### Inter-Phase Consistency Check

Before passing each gate: verify input traceability, surface unstated assumptions, identify load-bearing findings, assess reversal cost. See `references/governance.md` for human approval thresholds.

---

## Phase 0: Pre-Execution Protocol

**Goal**: Research codebase + internet, think deeply, scan best practices, select per-phase skills, visualize execution, iterate until 95% confident.

**Steps**:
- **0a**: Dual-source research (codebase survey + internet best practices scan)
- **0b**: Deep think (7 structured reasoning questions)
- **0c**: Live best practices scan — compare embedded sources vs current research. See `references/provenance-registry.md` for source verification
- **0d**: Per-phase skill selection (6 phases, each with selected skill + rationale + confidence)
- **0e**: Execution visualization (6 phases × 5 simulation fields)
- **0f**: Plan refinement (adjust based on visualization)
- **0g**: Confidence loop (iterate until ≥ 95% or 3 iterations max)

**Quick mode**: Skip 0c, 0e, 0f; do 0a, 0b, 0d, 0g only.

**Output**: `phase-0-pre-execution-protocol.md` — research summary, deep think, skill selection, visualization, confidence scorecard.

**[GATE 0]**: Codebase surveyed, best practices scanned (standard/deep), deep think complete, skill selection done, visualization done (standard/deep), confidence ≥ 95% (standard/deep) or ≥ 80% (quick), pre-gate ≥ 15/25 (standard/deep) or ≥ 12/25 (quick).

---

## Phase 1: Codebase Reconnaissance

**Goal**: Extract product signals from the codebase. Establish maturity baseline.

**Steps**:
1. Map codebase structure: directories, entry points, feature modules, API endpoints
2. Catalog user-facing features using stack-specific enumeration — see `references/stack-recon.md`
3. Identify tech stack, frameworks, dependencies
4. Extract implicit audience signals (feature naming, domain logic, config files, README)
5. Identify feature accumulation patterns (features without strategic intent)
6. Product Maturity Assessment — score 1-5 on: PMF Evidence, Feature Completeness, Technical Debt, Scalability, Security Posture, UX Quality
7. Feature-to-business alignment scan (conversion, retention, upsell, support reduction — or bloat)

**Output**: `phase-1-codebase-recon.md` — feature inventory, tech stack, audience signals (with file:path citations), maturity scorecard, bloat candidates.

**[GATE 1]**: Feature inventory covers all enumerated routes (or "unknown coverage" flagged — see `references/stack-recon.md`), every maturity score has evidence with file:path citation, bloat candidates listed, Codebase + Technical perspectives produce findings, pre-gate ≥ threshold.

---

## Phase 2: Market Deep Research & ICP Definition

**Goal**: Identify top 3 niche segments using N.I.C.H.E. process, ICP scoring, and beachhead methodology.

**Advisor Checkpoint**: If `ecc-advisor` available, call before proceeding.

**Steps**:
- **2a**: Niche Discovery — cast wide net (20-30 candidates standard, 10-15 quick, 30-40 deep). Score against P.R.O.F.I.T. criteria. See `references/research-protocol.md` for evidence logging.
- **2b**: ICP Scoring — 4-dimension model (Firmographic, Behavioral, Intent, Technographic). Weights are configurable hypotheses — see `references/scoring-rubric.md` for sensitivity tests and minimum viable evidence.
- **2c**: Beachhead Segment Selection — TAM → SAM → beachhead using 6 filters (word-of-mouth, compelling reason, well-funded, accessible, whole product, competitive).
- **2d**: Negative ICP Definition — disqualifiers with rationale.

**If web search unavailable**: Skip Phase 2, notify user. See `references/research-protocol.md`.

**If < 3 viable segments**: Report "insufficient evidence" — see `references/scoring-rubric.md` for outcome handling.

**Output**: `phase-2-market-research.md` — niche discovery log, ICP scoring matrix, top 3 beachhead segments, negative ICP. Every market claim logged in `research-ledger.json` (see `references/research-protocol.md`).

**[GATE 2]**: Every market claim has cited source in research ledger, ICP scoring reproducible, word-of-mouth evidence present, negative ICP defined, niche discovery log shows sufficient candidates, 4 perspectives produce findings, advisor checkpoint completed or documented skip, pre-gate ≥ threshold.

---

## Phase 3: Priority Alignment & Triangulation

**Goal**: Triangulate between codebase claims (Phase 1) and market needs (Phase 2). The delta IS the audit.

**Not in quick mode**: Skipped entirely. Phase 4 uses Phase 2 segment needs directly.

**Steps**:
1. For each of 3 beachhead segments, list top 5 priorities/needs
2. Cross-reference with Phase 1 feature inventory and maturity scorecard
3. Triangulation analysis: codebase claim vs market need vs delta
4. Identify alignment gaps and drift areas
5. Synthesize top 10 cross-cutting priorities with Current/Target/Gap/Drift/Delta scores

**Output**: `phase-3-priority-alignment.md` — segment needs matrix, triangulation table, top 10 priorities with gap scores.

**[GATE 3]**: 10 priorities trace to segment needs AND codebase features, every score has evidence line, 15 needs covered, adversarial review completed, load-bearing priorities identified, assumptions surfaced, inter-phase consistency verified, pre-gate ≥ 15/25.

---

## Phase 4: Positioning Strategy & 8-Lens Audit

**Goal**: Define positioning strategy using 8-lens audit (1-10 scoring). Define outreach and drift tracking.

**Input**: Phase 3 artifact (standard/deep) or Phase 2 artifact (quick — segment needs used directly).

**Steps**:
- **4a**: 8-Lens Positioning Audit — Category Noun Clarity, Value Proposition Density, Differentiation Sharpness, Proof Density, Message Consistency, Pricing-Signal Match, Segment-Product Fit, Update Cadence. See `references/scoring-rubric.md` for scoring rubric.
- **4b**: Positioning Statement per segment (template: "For [segment] who [need], [product] is a [category] that [benefit]. Unlike [competitor], we [differentiation].")
- **4c**: Outreach Strategy per segment (standard/deep only)
- **4d**: Drift Risk Register & cadence — quarterly + monthly + weekly/biweekly. See `references/governance.md`.

**Output**: `phase-4-positioning-strategy.md` — 8-lens scorecard (3 segments × 8 lenses), positioning statements, outreach (standard/deep), drift register, recommended priority order.

**[GATE 4]**: 24 lens scores with evidence, no all-7-8s without adversarial explanation, positioning statements follow template, adversarial review (Contrarian argues alternative), quarterly + monthly + weekly cadence defined, inter-phase consistency, reversal cost assessed, pre-gate ≥ threshold.

---

## [APPROVAL GATE — User Decision]

**STOP. Present all four phase artifacts to the user.** Do not proceed to Phase 5 until user explicitly approves.

Present: top 3 segments (with ICP scores), top 10 priorities (with gap scores), 8-lens audit (with scores), Phase 5 audit plan.

Ask: "Do you approve proceeding to the codebase audit? Reply YES to proceed or provide adjustments."

**Not in quick mode**: Quick mode terminates after Phase 4.

---

## Phase 5: Codebase Audit Execution

**Goal**: Audit codebase against approved positioning. Every finding anchored to file:line.

**Advisor Checkpoint**: If `ecc-advisor` available, call before executing.

**Steps**:
1. For each top 10 priority, audit codebase (file:line citations required)
2. Classify gaps: Missing Feature, Partial Implementation, Misaligned Feature, Drift Feature
3. For drift areas: recommend Remove, Repurpose, or Retain-with-low-priority + effort estimate
4. Intent drift detection: positioning claims vs codebase reality
5. Feature-to-business alignment audit: confirm bloat

**Deep mode**: Audit ALL features, not just top 10.

**Output**: `phase-5-codebase-audit.md` — audit findings table, intent drift report, drift feature inventory, bloat confirmation.

**[GATE 5]**: Every finding cites file:line, every finding has closure criterion + post-remediation test, intent drift report with citations, adversarial review (Skeptic challenges ≥ 3 findings), drift features have disposition + effort, inter-phase consistency, load-bearing findings identified, pre-gate ≥ 15/25.

---

## Phase 6: Remediation Roadmap & Drift Tracking Setup

**Goal**: Actionable, time-boxed remediation roadmap + drift tracking loop.

**Steps**:
1. Remediation roadmap: priority-ordered, effort (S/M/L), impact (which lens score improves), dependencies, time-boxed due dates
2. Pre/post drift assessment: numeric scores, not narrative
3. Drift tracking: quarterly audit calendar + monthly drift signals + weekly/biweekly evidence refresh. See `references/governance.md`.
4. First 30-day action list (standard); + 90-day and 180-day lists (deep)

**Output**: `phase-6-remediation-roadmap.md` — remediation roadmap, pre/post drift scores, drift tracking template, 30-day action list (+ 90/180-day for deep).

**[GATE 6]**: Every item has due date (specific date), owner (named role), closure criterion, post-remediation test; 30-day list has exactly 3 items; pre/post drift scores numeric; drift tracking template ready; Financial + Technical perspectives produce findings; inter-phase consistency; reversal cost assessed for top 3; pre-gate ≥ 15/25.

---

## Dependency Gating

- Phase 0 requires: codebase access + web search capability
- Phase 1 requires: Phase 0 artifact
- Phase 2 requires: web search + Phase 1 artifact
- Phase 3 requires: Phase 1 + Phase 2 artifacts (not in quick mode)
- Phase 4 requires: Phase 3 artifact (standard/deep) or Phase 2 artifact (quick)
- Phase 5 requires: Phase 4 artifact + explicit user approval (not in quick mode)
- Phase 6 requires: Phase 5 artifact (not in quick mode)

See `references/scope-dag.md` for the full scope-to-phase DAG.

## Tool Truth

- This skill does NOT require any Claude-only slash commands
- Web research uses available search tools (firecrawl, search_web, or equivalent)
- Codebase analysis uses file read and grep tools
- No external MCP servers required for baseline path
- `ecc-advisor` integration is optional — if unavailable, skip and proceed
- If web search unavailable, Phase 2 must be skipped and user notified
- Every score requires a one-sentence evidence line — no exceptions
- Every gate produces formal GO / CONDITIONAL GO / RECYCLE / STOP — no defaults to pass
- Pre-gate self-assessment must meet threshold before requesting gate review
- Confidence score formula is deterministic — see `references/scoring-rubric.md`
- Adversarial review mandatory for Phases 3, 4, 5
- 360-degree coverage checklist must be satisfied per phase
- Closure criteria mandatory for Phase 5 and 6 findings
- Phase 0 is mandatory — no execution without pre-execution protocol
- Inter-phase skill re-evaluation mandatory at every gate transition
- Artifacts must conform to `schemas/artifact.schema.json`
- State must conform to `schemas/state.schema.json`
- Redaction-before-storage mandatory — see `references/state-schema.md`
- Portfolio opt-in required per codebase — see `references/state-schema.md`
- Auditor-role separation for load-bearing findings — see `references/governance.md`
- Human approval required for financial, legal, regulatory, or high-reversal findings — see `references/governance.md`

## Reference Index

| Reference | Content |
|-----------|---------|
| `references/provenance-registry.md` | Source registry with URLs, dates, tiers, limitations |
| `references/research-protocol.md` | PRISMA-aligned research ledger, evidence quality, bias assessment |
| `references/scope-dag.md` | Scope-to-phase dependency matrix, gate contracts, I/O contracts |
| `references/scoring-rubric.md` | Confidence formula, ICP weights, sensitivity tests, uncertainty model |
| `references/stack-recon.md` | Per-stack route enumeration commands, coverage accounting |
| `references/state-schema.md` | Data classification, redaction, schema versioning, retention, portfolio opt-in |
| `references/governance.md` | ISO 19011 alignment, auditor separation, COI, cadence, human approval |
| `references/eval-harness.md` | 10 eval scenarios with grader definitions and pass thresholds |
| `schemas/artifact.schema.json` | Machine-checkable artifact schema |
| `schemas/state.schema.json` | State file JSON schema |
| `scripts/validate_skill.py` | Deterministic skill validator |
| `tests/*.json` | 10 scenario test fixtures |

## Upstream Source

- Created from user request: "Identification of top 3 niche customer segments and positioning strategy"
- Optimized via `ecc-prompt-optimize` workflow
- Revised via `@deep-research` with web research on best practices
- Methodology sources: see `references/provenance-registry.md` for full registry with URLs, dates, tiers, and limitations
- v5: 360° hardening — progressive disclosure, deterministic scoring, provenance registry, machine-checkable schemas, audit governance, evaluation harness
