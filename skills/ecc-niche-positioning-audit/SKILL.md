---
name: ecc-niche-positioning-audit
description: >-
  Identify top 3 niche customer segments and define market positioning strategy
  through codebase audit and market research. Seven-phase pipeline (Phase 0
  pre-execution protocol + 6 execution phases) with explicit approval gates,
  confidence threshold mechanism (95% target), evidence-anchored scoring, ICP
  rubric, beachhead methodology, 8-lens positioning audit, adversarial review,
  dynamic per-phase skill selection, quarterly drift tracking, stack auto-detection,
  scope selection (quick/standard/deep), per-project extensions, persistent state,
  cross-codebase portfolio view, and evidence grading. Designed for repeated use
  across multiple codebases. Outputs standardized 4-page artifacts per phase.
  TRIGGER when: "niche segment", "positioning
  strategy", "positioning drift", "customer segment identification",
  "codebase audit positioning", "market positioning alignment", "ICP",
  "beachhead segment", or "product-market fit audit".
  DO NOT TRIGGER when: no codebase is available, or the task is purely
  marketing copy generation without strategic analysis.
---

# ecc-niche-positioning-audit

Use this skill when the user needs to identify niche customer segments, align product priorities, and define market positioning strategy based on a codebase audit of their web applications.

## Purpose

This skill solves the **positioning drift** problem: when a codebase has accumulated features without strategic intent, the product's target customer, market niche, and competitive positioning become unclear. This skill provides a structured, evidence-backed pipeline to rediscover and realign — and to make the audit **repeatable** so drift is caught quarterly, not just once.

## Methodology Sources

This skill synthesizes best practices from:
- **MIT Disciplined Entrepreneurship** (beachhead segment methodology, market segmentation matrix)
- **Stratridge Positioning Audit Framework 2026** (8-lens scoring, 1-10 rubric, 4-page artifact, quarterly cadence)
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

## Backing Skills

- `deep-research` (web research for market unmet needs)
- `market-research` (competitive analysis, segment sizing)
- `market-research-reports` (structured output format)
- `codebase-onboarding` (codebase structure analysis)
- `ecc-plan` (phase planning and risk assessment)
- `ecc-verify` (verification gates between phases)
- `ecc-advisor` (advisor checkpoint before substantive work — if Grok CLI token available)

## Prerequisites

- A web application codebase accessible in the workspace (any stack — see Stack Auto-Detection)
- Ability to run web searches for market research
- User approval required before Phase 5 (codebase audit execution) and Phase 6 (remediation)
- If `ecc-advisor` is available, call advisor before Phase 2 (market research) and before Phase 5 (audit execution)

## Input Parameters

When invoking this skill, the user may provide any of these optional parameters. Unspecified parameters are auto-detected or defaulted.

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| `codebase_path` | Yes | Absolute path to the codebase root | Current workspace |
| `scope` | No | Audit scope: `quick`, `standard`, `deep` (see Scope Selection) | `standard` |
| `domain_hint` | No | Industry/domain hint: `saas`, `ecommerce`, `fintech`, `healthtech`, `devtools`, `consumer`, `marketplace`, `other` | Auto-detected from codebase |
| `stack_hint` | No | Tech stack hint: `react`, `next`, `vue`, `angular`, `svelte`, `python`, `go`, `node`, `other` | Auto-detected from codebase |
| `existing_customers` | No | Path to customer data (CSV, JSON) or description of known customers | None (Phase 2 discovers) |
| `competitor_list` | No | Known competitors to include in analysis | Discovered in Phase 2 |
| `previous_audit` | No | Path to previous audit artifacts for comparison | None (first run) |
| `output_dir` | No | Directory for audit artifacts | `.positioning-audit/` in codebase root |

## Scope Selection

Not every codebase needs the full 7-phase pipeline. Three scope modes adapt the depth and time investment:

| Scope | Phases | Time | When to Use |
|-------|--------|------|-------------|
| **quick** | Phase 0 (light) + Phase 1 + Phase 2 (light) + Phase 4 (scoring only) | 15-30 min | "Just tell me who my top 3 segments are and how my positioning scores" |
| **standard** | All 7 phases | 1-3 hours | First audit on a codebase, or quarterly re-audit |
| **deep** | All 7 phases + extended research + per-feature audit + competitor deep-dive | 3-6 hours | Pre-pivot, pre-fundraise, or post-major-feature-launch positioning reassessment |

**Quick mode adjustments**:
- Phase 0: Skip 0c (live best practices scan) and 0e (visualization); do 0a, 0b, 0d, 0g only
- Phase 2: Reduce niche candidates from 20-30 to 10-15; skip landing page test
- Phase 4: Score 8 lenses but skip outreach strategy and drift risk register
- Gates: Reduce pre-gate self-assessment threshold to 12/25 (quick mode tolerates less rigor)

**Deep mode adjustments**:
- Phase 1: Add per-feature code quality assessment (not just inventory)
- Phase 2: Expand to 30-40 niche candidates; add competitor feature-by-feature comparison matrix
- Phase 5: Audit every feature (not just top 10 priorities) for alignment
- Phase 6: Add 90-day and 180-day action lists in addition to 30-day

## Stack Auto-Detection

Phase 0a automatically detects the tech stack to adapt the audit approach:

| Signal File | Detects | Adapts |
|-------------|---------|--------|
| `package.json` | Node.js ecosystem: React, Next, Vue, Angular, Svelte, Express, Nest | Feature inventory scans `src/`, `pages/`, `app/`, `components/`; API endpoints from route files |
| `requirements.txt` / `pyproject.toml` | Python: Django, FastAPI, Flask | Feature inventory scans `apps/`, `views/`, `routes/`; API endpoints from URL patterns |
| `go.mod` | Go: Gin, Echo, Fiber, standard library | Feature inventory scans `cmd/`, `internal/`, `pkg/`; API endpoints from handler registrations |
| `Cargo.toml` | Rust: Actix, Axum, Rocket | Feature inventory scans `src/`; API endpoints from route macros |
| `Gemfile` | Ruby: Rails, Sinatra | Feature inventory scans `app/controllers/`, `config/routes.rb` |
| `pom.xml` / `build.gradle` | Java: Spring Boot, Quarkus | Feature inventory scans `src/main/`, controller annotations |

If stack cannot be auto-detected, ask the user. If multi-stack (monorepo), detect all and inventory each separately.

## Pre-Audit Questionnaire

Before Phase 0 begins, ask the user these calibration questions. If the user has already provided answers via input parameters, skip the corresponding question. Keep unanswered questions as "unknown — to be discovered in Phase X."

1. **What domain does this codebase serve?** (saas, ecommerce, fintech, healthtech, devtools, consumer, marketplace, other)
2. **What is the business model?** (subscription, one-time, freemium, usage-based, marketplace fees, advertising)
3. **What geography is the target?** (US, EU, APAC, global, specific countries)
4. **Are there existing paying customers?** (yes/no + count if known)
5. **What is the team size?** (solo, 2-10, 11-50, 50+)
6. **What is the primary competitor or alternative?** (if known)
7. **Has positioning been formally defined before?** (yes/no + document if available)
8. **What is the audit trigger?** (quarterly review, pre-pivot, post-launch, new product, investor request, other)

Answers are stored in `.positioning-audit/questionnaire.json` for future runs.

## Per-Project Extensions

Create `.positioning-audit/extras/*.md` files in the codebase root to add domain-specific audit dimensions. The skill loads these after the built-in dimensions and incorporates them into the relevant phases.

Example `.positioning-audit/extras/healthtech-compliance.md`:
```markdown
# HealthTech Compliance Extension

## Additional Phase 1 Dimension
- HIPAA compliance signals: encryption at rest, audit logging, BAAs in dependencies

## Additional Phase 2 ICP Dimension
- Regulatory readiness: Does the segment require FDA/HIPAA/GDPR compliance?

## Additional Phase 5 Audit Lens
- PHI handling: Audit all data flows for protected health information exposure
```

Extensions are merged into the phase methodology at execution time. If no extras exist, the skill runs with built-in dimensions only.

## Persistent State

All audit artifacts and state are stored in `.positioning-audit/` within the codebase root:

```
.positioning-audit/
├── questionnaire.json          # Pre-audit questionnaire answers
├── state.json                  # Current audit state (phase, gate decisions, confidence scores)
├── phase-0-pre-execution-protocol.md
├── phase-1-codebase-recon.md
├── phase-2-market-research.md
├── phase-3-priority-alignment.md
├── phase-4-positioning-strategy.md
├── phase-5-codebase-audit.md
├── phase-6-remediation-roadmap.md
├── extras/                     # Per-project extensions
│   └── *.md
├── history/                    # Previous audit runs for drift comparison
│   ├── 2025-Q1/
│   ├── 2025-Q2/
│   └── ...
└── portfolio.json              # Cross-codebase comparison data (if multiple codebases audited)
```

**`state.json` structure**:
```json
{
  "codebase_path": "/path/to/codebase",
  "audit_started": "2025-07-13T12:00:00Z",
  "current_phase": "phase-2",
  "gate_decisions": {
    "gate-0": "GO",
    "gate-1": "GO",
    "gate-2": "CONDITIONAL_GO"
  },
  "confidence_scores": {
    "phase-0": 96,
    "phase-1": 92,
    "phase-2": 88
  },
  "scope": "standard",
  "stack_detected": "next",
  "domain_detected": "saas"
}
```

This enables:
- **Resumption**: If a session is interrupted, the next session reads `state.json` and resumes from the current phase
- **Drift tracking**: Quarterly re-audits compare current artifacts against `history/` directory
- **Cross-codebase comparison**: `portfolio.json` aggregates scores across all audited codebases

## Cross-Codebase Portfolio View

When the user runs this skill on multiple codebases, each audit contributes to a portfolio view stored at `~/.positioning-audit-portfolio/portfolio.json`:

```json
{
  "codebases": [
    {
      "path": "/path/to/codebase-a",
      "name": "Codebase A",
      "last_audited": "2025-07-13",
      "top_segment": "B2B SaaS - Mid-market",
      "icp_score": 82,
      "positioning_score": 6.2,
      "drift_risk": "Medium",
      "next_audit_due": "2025-10-13"
    }
  ]
}
```

After each audit completes, the portfolio is updated. The user can request a portfolio summary at any time to see all codebases' positioning health at a glance.

## Evidence Grading

Every finding across all phases must be graded for evidence quality:

| Grade | Meaning | Criteria |
|-------|---------|----------|
| **HIGH** | Strong evidence — multiple independent sources, cross-validated | ≥ 2 independent sources, adversarial review survived, no contradicting evidence |
| **MEDIUM** | Moderate evidence — single strong source or multiple weak sources | 1 strong source OR 2+ weak sources, no contradicting evidence |
| **LOW** | Weak evidence — inference, assumption, or single unverified source | 1 unverified source, or inference from indirect signals |

Findings graded LOW cannot be load-bearing. If a load-bearing finding is graded LOW, it must be upgraded to MEDIUM or HIGH through additional research before the gate can pass.

Evidence grade is recorded alongside every finding in the artifact and in the confidence score calculation (HIGH findings count fully, MEDIUM at 0.7x, LOW at 0.3x toward evidence density subscore).

## Pipeline Overview

```
Phase 0: Pre-Execution Protocol (research → think → scan → select → visualize → plan → confidence loop)
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
Phase 6: Remediation Roadmap & Drift Tracking Setup
    → [GATE 6: Roadmap Actionability]
```

Each phase produces a **standardized 4-page artifact** (see Artifact Format below). No phase begins until the previous phase's gate is passed. At each gate transition, the executing agent re-evaluates skill selection and confidence before proceeding (see Inter-Phase Skill Re-Evaluation below).

### Artifact Format (all phases)

Every phase ships one document with the same structure:
- **Page 1**: Scores/summary table with one-sentence evidence per item
- **Page 2**: Top 3 ranked recommendations with owner, surface, and due date
- **Page 3**: Supporting evidence (quotes, citations, data points)
- **Page 4**: Comparison to previous run (blank if first run)

This format ensures the PMM, CMO, head of sales, and CEO can each read it in under 7 minutes.

---

## Gate Framework

### Gate Decision Outcomes

Every gate produces exactly one of four decisions. No gate defaults to "pass" — progression must be earned.

| Decision | Meaning | Action |
|----------|---------|--------|
| **GO** | All exit criteria met with evidence | Proceed to next phase |
| **CONDITIONAL GO** | Most criteria met; minor gaps tracked as action items | Proceed with documented conditions and due dates |
| **RECYCLE** | Critical criteria unmet | Repeat specific phase activities; do NOT proceed |
| **STOP** | Fundamental issue invalidates prior phases | Escalate to user; strategic reassessment required |

### Gate Exit Criteria — Defined Before Stage Begins

Exit criteria for each gate are defined **before** the phase starts, not at the gate. This prevents retrospective criteria shaping (adjusting criteria to match what was done vs what should have been done).

### Pre-Gate Self-Assessment (5 Dimensions)

Before requesting a gate review, the executing agent must self-assess on 5 dimensions (1-5 each, composite 5-25). A composite below 15 triggers automatic RECYCLE — do not even request gate review.

| Dimension | Score 1 (Ad Hoc) | Score 3 (Periodic) | Score 5 (Continuous) |
|-----------|------------------|---------------------|----------------------|
| **Documentation completeness** | Findings lack structure; no evidence trail | Key findings documented; evidence attached | All findings documented with citations; reviewed for completeness |
| **Evidence currency** | Evidence is stale or from single source | Multiple sources but not cross-validated | Multiple independent sources, cross-validated, current |
| **Coverage breadth** | Only obvious areas examined | Main areas covered; some blind spots remain | All required perspectives examined; blind spots explicitly listed |
| **Traceability** | Findings cannot trace to source data | Key findings trace to sources | Every finding traces to source data AND forward to recommendations |
| **Issue resolution** | Open questions remain unaddressed | Most questions addressed; some deferred | All questions addressed or explicitly deferred with rationale |

### 360-Degree Coverage Checklist

Every phase must demonstrate coverage across these **six perspectives**. A phase missing any perspective cannot pass its gate. Each perspective must produce at least one finding or an explicit "no findings — here's why" statement.

| Perspective | Question It Must Answer | Applies To |
|-------------|------------------------|------------|
| **Customer Lens** | What does the target customer see, feel, and need? | Phases 2, 3, 4 |
| **Competitor Lens** | What are competitors doing better, differently, or not at all? | Phases 2, 4 |
| **Codebase Lens** | What does the code actually do (not what it claims to do)? | Phases 1, 3, 5 |
| **Market Lens** | What market forces, trends, and regulatory shifts affect this? | Phases 2, 4 |
| **Financial Lens** | What is the revenue, cost, and willingness-to-pay reality? | Phases 2, 3, 6 |
| **Technical Lens** | What are the technical constraints, debt, and scalability limits? | Phases 1, 5, 6 |

### Adversarial Review Step (Phases 3, 4, 5)

After completing the primary analysis but BEFORE requesting gate review, the executing agent must run an **adversarial self-review** using three hostile personas. Each persona MUST find at least one issue or produce an explicit "no issues — here's the falsification test I ran" statement. A persona that finds nothing is not evidence of quality — it's evidence of insufficient scrutiny.

| Persona | Mandate | Question |
|---------|---------|----------|
| **The Skeptic** | Challenge every score and finding | "What evidence would prove this finding WRONG? Is that evidence available? Did anyone look for it?" |
| **The Missing Perspective** | Find what's NOT being examined | "What perspective, data source, or customer voice is absent from this analysis? What are we NOT looking at?" |
| **The Contrarian** | Argue for the opposite conclusion | "If the top 3 segments are wrong, what would the right 3 be? If this positioning is wrong, what would the right positioning be?" |

Adversarial findings are logged in the artifact as **Page 3, Section: Adversarial Review Notes**. Findings caught by 2+ personas are promoted in severity.

### Inter-Phase Consistency Check

Before passing each gate, verify consistency with prior phase outputs:

| Check | Question | Failure Action |
|-------|----------|----------------|
| **Input traceability** | Does this phase's output trace back to the prior phase's inputs? | RECYCLE — re-examine using prior phase data |
| **Assumption surfacing** | What unstated assumptions does this phase depend on? List them. | Log assumptions; flag any that could invalidate findings |
| **Load-bearing identification** | Which findings are load-bearing (other findings depend on them)? | Mark load-bearing findings; these get extra scrutiny |
| **Reversal cost** | If a recommendation is wrong, how expensive is it to reverse? | High reversal cost + low evidence = flag for user review |

### Closure Criteria (Phase 5 and 6 findings)

Every finding in Phase 5 and every recommendation in Phase 6 must include:
- **Closure criteria**: How will we prove this is fixed? (specific test, metric, or verification)
- **Post-remediation test**: What test will be run after the fix to verify? (scheduled, not aspirational)
- **Owner**: Who is accountable for confirming closure?

### Confidence Threshold Mechanism

Every phase (including Phase 0) must produce a **confidence score** (0-100%) before requesting gate review. This is not the same as the pre-gate self-assessment — confidence measures belief in the findings' correctness, not the process quality.

| Confidence Band | Meaning | Action |
|----------------|---------|--------|
| **≥ 95%** | Findings are evidence-backed, cross-validated, and adversarial review found no fatal flaws | Proceed to gate review |
| **80-94%** | Findings are solid but have identified gaps | **Improvisation loop**: target the specific gap, do focused re-research/re-analysis, re-score. Loop until ≥ 95% or 3 iterations max |
| **60-79%** | Findings have significant uncertainty | **Extended improvisation loop**: re-examine assumptions, re-run adversarial review with fresh personas, seek additional data sources. Loop until ≥ 95% or 3 iterations max |
| **Below 60%** | Findings are unreliable | **RECYCLE**: do not request gate review. Restart the phase with a different approach. Escalate to user if second attempt also falls below 60% |

**Confidence scoring criteria** (score each, average for composite):
1. **Evidence density**: What % of findings have ≥ 2 independent evidence sources? (target: ≥ 80%)
2. **Adversarial survival**: What % of findings survived adversarial review without modification? (target: ≥ 70%)
3. **Assumption risk**: How many load-bearing assumptions are unverified? (target: 0)
4. **Coverage completeness**: What % of applicable 360-degree perspectives produced findings? (target: 100%)
5. **Triangulation strength**: For phases 3-5, what % of findings are triangulated across ≥ 2 data sources? (target: ≥ 80%)

**Confidence log**: Every artifact must include a confidence scorecard on Page 1 with: composite score, subscores, iterations run, what was improved, and final score.

### Inter-Phase Skill Re-Evaluation

At each gate transition (after gate decision is GO or CONDITIONAL GO, before starting next phase), the executing agent must:

1. **Re-scan available skills**: Check if new skills/plugins became available, or if prior phase execution revealed that a different skill would be better suited for the next phase
2. **Evaluate fit**: Score each candidate skill on relevance (1-5), availability (1-5), and prior-phase evidence of need (1-5)
3. **Select and document**: Choose the best-fit skill, document the selection rationale in one sentence, and note any skills considered but rejected
4. **Confidence check on selection**: Assess confidence (0-100%) that the selected skill is the right tool. If below 80%, proceed without a skill (manual execution) and note the gap

This ensures the skill selection is **dynamic and evidence-driven**, not static. The Backing Skills list is a starting point, not a mandate.

---

## Phase 0: Pre-Execution Protocol

**Goal**: Before touching any phase, systematically research both the codebase and the internet, think deeply about the problem, scan for current best practices, select per-phase skills, visualize the full execution, refine the plan, and iterate until 95% confident. This phase exists because jumping straight into Phase 1 without meta-reasoning produces shallow, tool-blind, over-confident audits.

**Steps**:

### 0a: Dual-Source Research Survey

Run codebase survey and internet research **in parallel**:

**Codebase survey** (quick scan, not deep audit — that's Phase 1):
1. Read the project root: `package.json`, `README.md`, directory structure, config files
2. Identify the app type (SPA, SSR, API, monorepo, etc.), framework, and primary language
3. Count feature modules and estimate codebase size (LOC, file count)
4. Note any existing positioning signals: product name, tagline, meta tags, landing page copy

**Internet research** (current best practices, not market research — that's Phase 2):
1. Search for "niche customer segmentation best practices 2025 2026"
2. Search for "market positioning audit framework 2025 2026"
3. Search for "ICP scoring rubric best practices 2025 2026"
4. Search for "codebase audit for product-market fit methodology"
5. Note any new frameworks, tools, or methodologies not already in the skill's Methodology Sources

### 0b: Deep Think

Synthesize the dual-source research into a structured reasoning block. This is NOT analysis — it's **deliberate reasoning before action**. Address each question with a 2-3 sentence answer:

1. **What is this codebase?** (product type, intended user, domain, maturity stage)
2. **Who was it built for?** (explicit audience signals from code, implicit signals from feature choices)
3. **What market does it serve?** (industry, segment, geography, business model)
4. **What positioning assumptions are embedded in the code?** (feature naming, UX patterns, pricing logic, domain language)
5. **What are the 3 most likely positioning drift signals?** (features without strategic intent, audience ambiguity, competitor ambiguity)
6. **What is the risk of getting this audit wrong?** (wrong segment → wrong roadmap → wasted engineering cycles)
7. **What would a 95%-confident audit look like?** (what evidence, what coverage, what validation would be needed)

### 0c: Live Best Practices Scan

Compare the skill's pre-baked Methodology Sources against the live internet research from 0a:
1. Are there newer frameworks published in 2025-2026 that supersede the embedded sources?
2. Are there scoring rubrics with better validation than the current ICP model?
3. Are there positioning audit frameworks with more lenses or better evidence requirements?
4. If yes to any: note the update and incorporate into the phase methodology. If no: confirm the embedded sources are current.

### 0d: Per-Phase Skill Selection

For each of the 6 phases, evaluate available skills and select the best fit:

| Phase | Primary Skill Candidates | Selection Criteria |
|-------|------------------------|-------------------|
| Phase 1 | `codebase-onboarding`, `understand`, `repo-scan` | Codebase structure analysis capability, file-tree mapping, feature inventory |
| Phase 2 | `deep-research`, `market-research`, `market-research-reports` | Web research depth, competitive analysis, structured output |
| Phase 3 | `ecc-plan`, manual triangulation | Cross-referencing capability, gap analysis |
| Phase 4 | `market-research`, `market-research-reports`, manual scoring | Positioning framework application, scoring rubric execution |
| Phase 5 | `codebase-onboarding`, `understand-explain`, manual audit | Code-level audit, file:line citation, gap detection |
| Phase 6 | `ecc-plan`, `ecc-verify`, manual roadmap | Action planning, verification design, time-boxing |

For each phase, document:
- Selected skill (or "manual execution")
- Selection rationale (one sentence)
- Skills considered but rejected (with reason)
- Confidence in selection (0-100%)

### 0e: Execution Visualization

Mentally simulate the full pipeline before executing. For each phase, document:

| Simulation Field | Question |
|-----------------|----------|
| **Expected input** | What data/artifacts will this phase receive? |
| **Expected output** | What artifact will this phase produce? |
| **Potential failure mode** | What could go wrong? (missing data, tool unavailable, low confidence) |
| **Gate outcome prediction** | Will this phase pass its gate? (GO / CONDITIONAL GO / RECYCLE) |
| **Fallback plan** | If the primary approach fails, what's the backup? |

Also simulate:
- **Worst case**: What if Phase 2 finds no viable segments? (STOP → escalate to user)
- **Best case**: What if all phases pass cleanly? (proceed to remediation)
- **Most likely case**: What if 1-2 phases need RECYCLE? (iterate, don't panic)

### 0f: Plan Refinement

Based on the visualization:
1. Adjust phase steps if simulation revealed issues (e.g., add a sub-step for data that might be missing)
2. Adjust skill selections if simulation showed a skill wouldn't work for the expected data
3. Adjust gate criteria if simulation showed a criterion is unrealistic for this codebase
4. Document all adjustments and the reasoning behind them

### 0g: Confidence Loop

Assess confidence in the overall execution plan:
1. Score confidence (0-100%) using the Confidence Threshold Mechanism criteria
2. If below 95%: identify the specific gap(s), do targeted re-research/re-thinking, re-score
3. Loop until ≥ 95% or 3 iterations max
4. If still below 95% after 3 iterations: proceed with documented confidence level and flag the specific uncertainties for the user

**Output Artifact**: `phase-0-pre-execution-protocol.md`
- Dual-source research summary (codebase snapshot + best practices scan)
- Deep think reasoning block (7 questions answered)
- Per-phase skill selection table (6 phases, selected skill, rationale, confidence)
- Execution visualization table (6 phases × 5 fields)
- Plan adjustments log (what was changed from the base skill and why)
- Confidence scorecard (composite, subscores, iterations, final score)

**[GATE 0: Readiness Confirmation]**

Exit criteria (defined before phase starts):
- [ ] Codebase survey completed (app type, framework, size, positioning signals identified)
- [ ] Internet best practices scan completed (≥ 4 searches, results documented)
- [ ] Deep think block completed (all 7 questions answered with 2-3 sentences each)
- [ ] Live best practices scan: confirmed embedded sources are current OR documented updates
- [ ] Per-phase skill selection completed (6 phases, each with selected skill + rationale + confidence)
- [ ] Execution visualization completed (6 phases × 5 simulation fields)
- [ ] Plan refinement completed (adjustments documented, or "no adjustments needed" with reasoning)
- [ ] Confidence score ≥ 95% (or documented reasoning for proceeding below 95% after 3 iterations)
- [ ] Pre-gate self-assessment composite ≥ 15/25

Gate decision: GO / CONDITIONAL GO / RECYCLE / STOP

---

## Phase 1: Codebase Reconnaissance

**Goal**: Extract product signals from the codebase to understand what was built, for whom, and what features exist. Establish a product maturity baseline.

**Steps**:
1. Map the codebase structure: directories, entry points, feature modules, API endpoints
2. Catalog all user-facing features (UI routes, API endpoints, user flows)
3. Identify technology stack, frameworks, and dependencies
4. Extract implicit target audience signals from:
   - Feature naming and UX patterns
   - Domain-specific logic (e.g., healthcare, finance, e-commerce)
   - Configuration files and environment variables
   - README, docs, and inline comments
5. Identify feature accumulation patterns — features added without clear strategic intent
6. **Product Maturity Assessment** — score 1-5 on six dimensions (with evidence):
   - **PMF Evidence**: Retention signals, user data, paying customers (1=no data, 5=dominant PMF)
   - **Feature Completeness**: Core workflow coverage vs market expectations (1=MVP only, 5=feature leader)
   - **Technical Debt**: Test coverage, deploy frequency, MTTR (1=crippling, 5=managed)
   - **Scalability**: Architecture readiness for 10x load (1=buckles, 5=proven)
   - **Security Posture**: Dependency health, auth design, data protection (1=porous, 5=hardened)
   - **UX Quality**: Consistency, accessibility, error handling (1=ad hoc, 5=polished)
7. **Feature-to-business alignment scan**: For each feature, ask "Does this drive conversion, retention, upsell, or support reduction?" Features that serve none are **bloat candidates**

**Output Artifact**: `phase-1-codebase-recon.md`
- Feature inventory table (feature name, module, user-facing?, inferred audience, business purpose?)
- Tech stack summary
- Implicit audience signals (with file:path evidence citations)
- Feature accumulation heatmap (which areas have drift)
- Product maturity scorecard (6 dimensions, 1-5, with evidence)
- Bloat candidate list (features with no clear business purpose)

**[GATE 1: Recon Completeness]**

Exit criteria (defined before phase starts):
- [ ] Feature inventory covers 100% of user-facing routes/endpoints (verified by route enumeration)
- [ ] Every maturity score (6 dimensions) has a one-sentence evidence line with file:path citation
- [ ] Bloat candidate list includes every feature with no clear business purpose
- [ ] 360-degree coverage: Codebase Lens AND Technical Lens both produce findings
- [ ] Pre-gate self-assessment composite ≥ 15/25
- [ ] Implicit audience signals cite at least 3 distinct code locations

Gate decision: GO / CONDITIONAL GO / RECYCLE / STOP

---

## Phase 2: Market Deep Research & ICP Definition

**Goal**: Identify top 3 niche customer segments using the N.I.C.H.E. process, ICP scoring rubric, and beachhead methodology. Define both positive and negative ICPs.

**Advisor Checkpoint**: If `ecc-advisor` is available, call advisor with the Phase 1 summary and the research plan before proceeding.

**Steps**:

### 2a: Niche Discovery (N.I.C.H.E. Process)

1. **Notice** — Cast a wide net (20-30 candidate niches) from multiple sources:
   - Codebase domain signals from Phase 1
   - Audience intersection: [Profession] x [Life Stage] = Niche
   - Problem taxonomy: Break broad problems into specific variants
   - Industry vertical deep-dives
   - Complaint mining: Search Reddit, HN, Stack Overflow, industry forums for frustration signals
   - Platform exploitation: underserved platforms or ecosystems
2. **Investigate** — Score each candidate against P.R.O.F.I.T. criteria:
   - **P**roblem is real and painful (evidence: forum complaints, support tickets)
   - **R**eachable through known channels
   - **O**bvious value proposition can be articulated
   - **F**inancially capable (budget to spend, value quality over price)
   - **I**nterest alignment (founder/team can sustain focus for 6+ years)
   - **T**iming is right (market conditions, regulatory shifts, tech maturity)
3. **Compete** — Analyze existing solutions for each candidate niche:
   - Direct competitors, adjacent tools, manual workarounds
   - Competitive white space mapping: where are the gaps?
   - Feature gap analysis: what do competitors lack?
4. **Hypothesize** — Define positioning hypothesis for top 5-7 candidates
5. **Experiment** — Validate demand signals:
   - Search volume analysis (Google Keyword Planner or equivalent)
   - Community size (Reddit, Discord, Slack groups)
   - High-engagement posts as market validation (500+ upvotes = signal)
   - Landing page or waitlist test if feasible

### 2b: ICP Scoring Rubric (4-Dimension Model)

Score each surviving candidate segment on a 0-100 scale across four dimensions:

| Dimension | Weight | Criteria | Signal Sources |
|-----------|--------|----------|----------------|
| **Firmographic** | 40% | Industry, company size, revenue band, geography, growth stage | Data providers, LinkedIn, public databases |
| **Behavioral** | 25% | Content engagement, hiring in target role, product usage patterns | CRM, analytics, job boards |
| **Intent** | 20% | Category research activity, competitor evaluation, RFP/RFI signals | G2, Bombora, 6sense, search trends |
| **Technographic** | 15% | Tech stack match, integration adjacency, stack maturity | BuiltWith, Wappalyzer, job postings |

Scoring bands:
- **70+**: Trigger outreach immediately
- **40-69**: Mid-priority, nurture sequence
- **Below 40**: Disqualify

### 2c: Beachhead Segment Selection

For each high-scoring segment, apply the **beachhead narrowing** process:
1. Start with Total Addressable Market (TAM)
2. Narrow to Serviceable Addressable Market (SAM)
3. Narrow to beachhead segment using these filters:
   - **Word-of-mouth test**: Do members of this segment communicate with each other? (Critical — without this, marketing is inefficient)
   - **Compelling reason to buy**: Is the pain acute enough to drive purchase?
   - **Well-funded**: Can they afford the solution?
   - **Accessible**: Can your sales motion reach them?
   - **Whole product**: Can you deliver a complete solution (possibly with partners)?
4. Select top 3 beachhead segments, ranked by ICP score

### 2d: Negative ICP Definition

Define attributes that reliably predict bad outcomes (churn, non-renewal, low LTV, implementation failure):
- Industries that consistently fail to adopt
- Company sizes too small to afford or too large to care
- Tech stack incompatibilities
- Behavioral red flags (no budget authority, no urgency)
- Encode as hard disqualifiers (-100 point penalties)

**Output Artifact**: `phase-2-market-research.md`
- Niche discovery log (all 20-30 candidates with P.R.O.F.I.T. scores)
- Competitive white space map per domain
- ICP scoring matrix (all candidates, 4-dimension, weighted 0-100)
- Top 3 beachhead segments with full justification
- For each segment: persona sketch, pain points, current alternatives, unmet needs, word-of-mouth evidence
- Negative ICP definition with disqualifier list

**[GATE 2: Research Validity]**

Exit criteria (defined before phase starts):
- [ ] Every market claim has at least one cited web source (URL present)
- [ ] ICP scoring is reproducible: all 4 dimension scores can be recalculated from presented data
- [ ] Word-of-mouth test has evidence (community links, forum activity, or conference attendance data)
- [ ] Negative ICP defined with at least 5 hard disqualifiers
- [ ] Niche discovery log shows ≥ 20 candidates (not just the top 3)
- [ ] 360-degree coverage: Customer Lens, Competitor Lens, Market Lens, AND Financial Lens all produce findings
- [ ] Pre-gate self-assessment composite ≥ 15/25
- [ ] Advisor checkpoint completed (if available) or documented as skipped

Gate decision: GO / CONDITIONAL GO / RECYCLE / STOP

---

## Phase 3: Priority Alignment & Triangulation

**Goal**: Articulate top 10 priorities that must be aligned. **Triangulate** between what the codebase claims to do (Phase 1) and what the market actually needs (Phase 2). The delta IS the audit.

**Steps**:
1. For each of the 3 beachhead segments, list their top 5 priorities/needs (from Phase 2 research)
2. Cross-reference with the Phase 1 feature inventory and maturity scorecard
3. **Triangulation analysis** — for each segment need, compare:
   - **What the codebase claims**: Feature exists, partially exists, or missing
   - **What the market needs**: From Phase 2 research and complaint mining
   - **The delta**: This gap is the positioning drift signal
4. Identify alignment gaps: segment needs that the codebase does not serve
5. Identify drift areas: codebase features that no selected segment needs (bloat from Phase 1)
6. Synthesize the top 10 cross-cutting priorities that, if aligned, would minimize positioning drift
7. For each priority, define:
   - **Current State** (1-10): How well the codebase currently serves this priority (with evidence)
   - **Target State** (1-10): Required level to win the segment (with evidence)
   - **Gap Score**: Target - Current
   - **Drift Risk** (Low/Medium/High): Consequence of not addressing
   - **Triangulation Delta**: One-sentence summary of codebase-claim vs market-need gap

**Output Artifact**: `phase-3-priority-alignment.md`
- Segment needs matrix (3 segments x 5 needs each)
- Triangulation table (need, codebase claim, market need, delta)
- Feature-to-need mapping table (with gap annotations)
- Top 10 priorities table with Current/Target/Gap/Drift/Delta columns
- Priority ranking by gap score (highest gap first)

**[GATE 3: Alignment Integrity]**

Exit criteria (defined before phase starts):
- [ ] Each of the 10 priorities traces back to ≥ 1 segment need AND ≥ 1 codebase feature (or documented absence)
- [ ] Every Current/Target score has a one-sentence evidence line — no score without evidence
- [ ] Triangulation table covers all 15 segment needs (3 segments × 5 needs)
- [ ] Adversarial review completed: The Skeptic, The Missing Perspective, and The Contrarian have each produced findings or falsification statements
- [ ] Load-bearing priorities identified (which priorities, if wrong, invalidate the most downstream work)
- [ ] Unstated assumptions surfaced and logged
- [ ] 360-degree coverage: Customer Lens, Codebase Lens, AND Financial Lens all produce findings
- [ ] Pre-gate self-assessment composite ≥ 15/25
- [ ] Inter-phase consistency: Phase 3 outputs trace to Phase 1 feature inventory AND Phase 2 segment needs

Gate decision: GO / CONDITIONAL GO / RECYCLE / STOP

---

## Phase 4: Positioning Strategy & 8-Lens Audit

**Goal**: Define positioning strategy using the 8-lens audit framework (1-10 scoring with evidence). Define outreach strategy and drift tracking cadence.

**Steps**:

### 4a: 8-Lens Positioning Audit

For each of the 3 segments, score positioning on **eight lenses** (1-10, with one-sentence evidence per score):

| Lens | What It Measures |
|------|-----------------|
| **Category Noun Clarity** | Is there a single, consistent category noun across all surfaces? |
| **Value Proposition Density** | Is the value prop specific, quantified, and defensible? |
| **Differentiation Sharpness** | Is the differentiation from nearest competitor clear and provable? |
| **Proof Density** | Are there named customer outcomes, case studies, quantified results? |
| **Message Consistency** | Is messaging consistent across homepage, pricing, deck, docs? |
| **Pricing-Signal Match** | Does pricing page align with positioning brief? |
| **Segment-Product Fit** | Does the product actually serve the segment's workflow? |
| **Update Cadence** | Is positioning reviewed on a calendar, not just during crises? |

Scoring rubric (same for all lenses):
- **1-3**: Failing — lens absent or actively working against you
- **4-6**: Present but soft — inconsistent, underproven, or contradicted
- **7-8**: Working — consistent, evidenced, defensible against a sharp competitor
- **9-10**: Canonical — shaping how the market talks about you

### 4b: Positioning Statement

Define positioning statement per segment using this template:
> For [target segment] who [need/pain], [product] is a [category] that [unique benefit]. Unlike [nearest competitor], we [differentiation].

### 4c: Outreach Strategy

Define outreach strategy per segment:
- Primary channel (where this segment is reachable)
- Secondary channel
- Messaging angle (tied to the #1 unmet need from Phase 2)
- First-touch to conversion path
- ICP scoring threshold for outreach trigger (70+ from Phase 2)

### 4d: Drift Risk Register & Quarterly Cadence

- Identify positioning drift risks and mitigation actions
- Define quarterly audit cadence: same 8 lenses, same rubric, same 4-page artifact
- Set calendar reminders for positioning brief review (PMM) and battle card refresh (head of sales)
- Define the comparison view: quarter-over-quarter scorecard for all 8 lenses

**Output Artifact**: `phase-4-positioning-strategy.md`
- 8-lens positioning scorecard (3 segments x 8 lenses, 1-10 scale, tabular, with evidence)
- Positioning statement per segment
- Outreach strategy table per segment
- Drift risk register with mitigations
- Recommended positioning priority order (which segment to pursue first, second, third)
- Quarterly audit calendar definition

**[GATE 4: Positioning Rigor]**

Exit criteria (defined before phase starts):
- [ ] Each of the 8 lens scores (× 3 segments = 24 scores) has a one-sentence evidence line
- [ ] No lens scores are all 7-8s (if they are, adversarial review must explain why this isn't self-flattery)
- [ ] Positioning statements follow the template exactly (all 5 blanks filled per segment)
- [ ] Adversarial review completed: The Contrarian has argued for an alternative positioning, and the argument is documented
- [ ] Quarterly audit calendar defined with specific dates and owners
- [ ] 360-degree coverage: Customer Lens, Competitor Lens, Market Lens, AND Financial Lens all produce findings
- [ ] Pre-gate self-assessment composite ≥ 15/25
- [ ] Inter-phase consistency: Positioning statements trace to Phase 3 priorities and Phase 2 segments
- [ ] Reversal cost assessed: if the #1 recommended segment is wrong, what is the cost of switching?

Gate decision: GO / CONDITIONAL GO / RECYCLE / STOP

---

## [APPROVAL GATE — User Decision]

**STOP. Present all four phase artifacts to the user. Do not proceed to Phase 5 until the user explicitly approves.**

Present:
1. Summary of top 3 beachhead segments (with ICP scores)
2. Summary of top 10 priorities (with gap scores)
3. Summary of 8-lens positioning audit (with scores)
4. The Phase 5 audit plan

Ask: "Do you approve proceeding to the codebase audit? Reply YES to proceed or provide adjustments."

---

## Phase 5: Codebase Audit Execution

**Goal**: Audit the codebase against the approved positioning strategy to identify concrete changes needed to minimize positioning drift. Every finding must be anchored to specific file paths and line numbers.

**Advisor Checkpoint**: If `ecc-advisor` is available, call advisor with the audit plan and Phase 4 summary before executing.

**Steps**:
1. For each of the top 10 priorities, audit the codebase:
   - Locate the relevant code modules/features (file:line citations required)
   - Assess current implementation against target state
   - Document specific gaps with file:line citations
   - Classify gap as: **Missing Feature**, **Partial Implementation**, **Misaligned Feature**, or **Drift Feature**
2. For each drift area (features no segment needs):
   - Document the feature and its code location
   - Recommend action: **Remove**, **Repurpose**, or **Retain-with-low-priority**
   - Estimate effort to remove/repurpose (S/M/L)
3. **Intent drift detection** — compare what the codebase actually does vs what the positioning claims:
   - Does the code support the positioning statement?
   - Are there features that contradict the positioning?
   - Are there missing features that the positioning implies?
4. **Feature-to-business alignment audit** — for each feature in the inventory:
   - Does it drive conversion, retention, upsell, or support reduction?
   - Features that serve none are confirmed bloat — recommend disposition
5. Produce a remediation roadmap (see Phase 6)

**Output Artifact**: `phase-5-codebase-audit.md`
- Audit findings table (priority, code location, gap type, severity, recommended action, evidence)
- Intent drift report (positioning claim vs codebase reality, with citations)
- Drift feature inventory with disposition recommendations
- Bloat confirmation list with removal/repurpose effort estimates

**[GATE 5: Audit Rigor]**

Exit criteria (defined before phase starts):
- [ ] Every finding cites specific file paths AND line numbers (no vague references)
- [ ] Every finding has a closure criterion (how we'll prove it's fixed)
- [ ] Every finding has a post-remediation test (scheduled, not aspirational)
- [ ] Intent drift report compares positioning claims vs codebase reality with citations
- [ ] Adversarial review completed: The Skeptic has challenged at least 3 findings with falsification tests
- [ ] Drift features have disposition recommendations (Remove/Repurpose/Retain) with effort estimates
- [ ] 360-degree coverage: Codebase Lens AND Technical Lens both produce findings
- [ ] Pre-gate self-assessment composite ≥ 15/25
- [ ] Inter-phase consistency: Every audit finding traces to a Phase 3 priority or a Phase 1 bloat candidate
- [ ] Load-bearing findings identified (which findings, if wrong, invalidate the remediation roadmap)

Gate decision: GO / CONDITIONAL GO / RECYCLE / STOP

---

## Phase 6: Remediation Roadmap & Drift Tracking Setup

**Goal**: Produce an actionable, time-boxed remediation roadmap and set up the quarterly drift tracking loop.

**Steps**:
1. **Remediation roadmap**:
   - Priority-ordered list of changes (by gap score x drift risk)
   - Effort estimate per change (S/M/L) with approximate hour ranges
   - Impact on positioning alignment per change (which lens score it improves)
   - Dependencies between changes
   - **Time-boxed due dates** (not vague "we should fix this")
2. **Pre/post drift assessment**:
   - Pre-audit drift score (average gap across 10 priorities, average 8-lens score)
   - Post-remediation projected drift score
   - Confidence level in the projection (with reasoning)
3. **Quarterly drift tracking setup**:
   - Define the re-audit calendar (quarterly, same 8 lenses, same rubric)
   - Create the comparison template (quarter-over-quarter scorecard)
   - Define trigger thresholds: if any lens drops 2+ points, trigger immediate review
   - Define ownership: PMM owns positioning brief, head of sales owns battle cards
4. **First 30-day action list**:
   - The top 3 changes to ship in the next 30 days
   - Each with: surface, owner, due date, expected lens score improvement

**Output Artifact**: `phase-6-remediation-roadmap.md`
- Remediation roadmap (ordered, with effort, impact, dependencies, due dates)
- Pre/post drift score comparison
- Quarterly drift tracking template and calendar
- 30-day action list (top 3 changes, time-boxed)

**[GATE 6: Roadmap Actionability]**

Exit criteria (defined before phase starts):
- [ ] Every remediation item has a due date (specific date, not "soon" or "Q3")
- [ ] Every remediation item has an owner (named role, not "team")
- [ ] Every remediation item has a closure criterion and post-remediation test
- [ ] 30-day action list has exactly 3 items, each with surface, owner, due date, and expected lens score improvement
- [ ] Pre/post drift scores are numeric and comparable (not narrative)
- [ ] Quarterly drift tracking template is defined and ready to use
- [ ] 360-degree coverage: Financial Lens AND Technical Lens both produce findings (cost estimates and effort)
- [ ] Pre-gate self-assessment composite ≥ 15/25
- [ ] Inter-phase consistency: Every roadmap item traces to a Phase 5 finding
- [ ] Reversal cost assessed for the top 3 remediation items

Gate decision: GO / CONDITIONAL GO / RECYCLE / STOP

---

## Dependency Gating

- Phase 0 requires: codebase access (file read tools) + web search capability
- Phase 1 requires: Phase 0 artifact (pre-execution protocol complete)
- Phase 2 requires: web search capability + Phase 1 artifact
- Phase 3 requires: Phase 1 + Phase 2 artifacts
- Phase 4 requires: Phase 3 artifact
- Phase 5 requires: Phase 4 artifact + explicit user approval
- Phase 6 requires: Phase 5 artifact

## Tool Truth

- This skill does NOT require any Claude-only slash commands
- Web research uses available search tools (firecrawl, search_web, or equivalent)
- Codebase analysis uses file read and grep tools
- No external MCP servers are required for the baseline path
- `ecc-advisor` integration is optional — if Grok CLI token is unavailable, skip advisor checkpoints and proceed
- If web search is unavailable, Phase 2 must be skipped and the user notified
- Every score in every phase requires a one-sentence evidence line — no exceptions
- Every gate produces a formal GO / CONDITIONAL GO / RECYCLE / STOP decision — no gate defaults to pass
- Pre-gate self-assessment composite must be ≥ 15/25 before requesting gate review
- Confidence score ≥ 95% required before gate review (improvisation loop if below; RECYCLE if below 60%)
- Adversarial review (3 hostile personas) is mandatory for Phases 3, 4, and 5 — no exceptions
- 360-degree coverage checklist must be satisfied for each phase's applicable perspectives
- Closure criteria and post-remediation tests are mandatory for all Phase 5 and 6 findings
- Phase 0 is mandatory — no phase execution begins without completing the pre-execution protocol
- Inter-phase skill re-evaluation is mandatory at every gate transition — skill selection is dynamic, not static
- Confidence log (composite + subscores + iterations) is mandatory on every artifact's Page 1
- Input parameters are accepted but auto-detected/defaulted when not provided — skill works zero-config
- Scope selection (quick/standard/deep) adjusts phase depth and gate thresholds — default is standard
- Stack auto-detection runs in Phase 0a — if detection fails, ask user; if monorepo, detect all stacks
- Pre-audit questionnaire calibrates the audit — unanswered questions are "unknown" not guessed
- Per-project extensions in `.positioning-audit/extras/*.md` are loaded if present — extends built-in dimensions
- Persistent state in `.positioning-audit/state.json` enables resumption and quarterly drift tracking
- Cross-codebase portfolio at `~/.positioning-audit-portfolio/portfolio.json` aggregates all audited codebases
- Evidence grading (HIGH/MEDIUM/LOW) is mandatory for every finding — LOW findings cannot be load-bearing
- Advisor checkpoints: call `ecc-advisor` before Phase 2 and Phase 5 if available; if unavailable, proceed with documented skip

## Upstream Source

- Created from user request: "Identification of top 3 niche customer segments and positioning strategy"
- Optimized via `ecc-prompt-optimize` workflow
- Revised via `@deep-research` with web research on best practices
- Methodology sources: MIT Disciplined Entrepreneurship, Stratridge 2026, ICP Scoring Rubric (Nimitai/Growleads/Hyperspect), N.I.C.H.E. Framework (NicheCheck), Product Maturity Assessment (KnowledgeLib), IntentGuard, PrismGrid, Stage Gate PM, Adversarial Review, Audit Readiness Framework, TriAdReview
- v3 additions: Phase 0 Pre-Execution Protocol, Confidence Threshold Mechanism (95% target), Inter-Phase Skill Re-Evaluation, dynamic per-phase skill selection
- v4 additions: Input Parameters, Scope Selection (quick/standard/deep), Stack Auto-Detection (6 ecosystems), Pre-Audit Questionnaire (8 questions), Per-Project Extensions, Persistent State (`.positioning-audit/`), Cross-Codebase Portfolio View, Evidence Grading (HIGH/MEDIUM/LOW), IMPACT Framework integration, advisor checkpoint verification
