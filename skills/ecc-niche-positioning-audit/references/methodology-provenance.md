# Methodology Provenance Registry

All 26 methodology sources with URLs, versions, dates, applicability, and limitations.

## Direct Methodology Sources

| # | Source | URL | Version/Date | Applicability | Limitations |
|---|--------|-----|-------------|---------------|-------------|
| 1 | MIT Disciplined Entrepreneurship | https://disciplinedentrepreneurship.com/ | Book, 2013 (24-step framework) | Beachhead segment selection, market segmentation | Academic framework; needs adaptation for B2B SaaS |
| 2 | Stratridge 2026 Positioning Framework | https://stratridge.com/ | 2026 | 8-lens positioning audit, claim verification | Proprietary; principles adapted, not directly licensed |
| 3 | ICP Scoring Rubric | https://www.gtmhub.com/blog/icp-scoring | 2024 | 4-dimension ICP model (firmographic, behavioral, intent, technographic) | Weights are heuristic, not empirically validated |
| 4 | N.I.C.H.E. Research Process | — (internal framework) | 2025 | Notice → Investigate → Compete → Hypothesize → Experiment | Internal; no external validation |
| 5 | Product Maturity Assessment | — (internal framework) | 2025 | 6-dimension product maturity scoring | Internal; dimensions adapted from various sources |
| 6 | IntentGuard Intent Drift Detection | — (internal framework) | 2025 | Specification vs implementation gap measurement | Internal; adapted from spec-driven development |
| 7 | PrismGrid Positioning Validation | — (internal framework) | 2025 | Claim verification before scaling | Internal; adapted from A/B testing principles |
| 8 | ecc-advisor pattern | https://github.com/sanjabh11/codex-ecc-custom | 2025 | Second-opinion checkpoint using Grok 4.5 advisor | Requires Grok CLI token; graceful fallback if unavailable |
| 9 | Stage Gate PM | https://www.stage-gate.com/ | Cooper, 2008 | Decision forcing functions, Go/Conditional Go/Recycle/Stop outcomes | Originally for product development; adapted for positioning |
| 10 | Adversarial Review | — (synthesized from multiple sources) | 2025 | Independent hostile personas, falsification tests | Synthesized; no single canonical source |
| 11 | Audit Readiness Framework | — (internal framework) | 2025 | 5-dimension pre-gate self-assessment | Internal; adapted from ISO 19011 |
| 12 | TriAdReview | — (internal framework) | 2025 | Triangular adversarial review architecture | Internal; no external validation |

## Adapted Methodology Sources

| # | Source | URL | Version/Date | Applicability | Limitations |
|---|--------|-----|-------------|---------------|-------------|
| 13 | IMPACT Framework | — (internal framework) | 2025 | Hypothesis-driven B2B positioning: Identify → Map → Pinpoint → Anchor → Craft → Translate | Internal; synthesized from multiple positioning frameworks |
| 14 | plugin-gtm | https://github.com/sanjabh11/codex-ecc-custom | 2025 | Codebase-to-GTM engine: analyze codebase → product profile → GTM plan | Internal ECC plugin; codebase-dependent |
| 15 | Lumen PM | — (internal framework) | 2025 | 18-agent PM orchestration with evidence-graded reports | Internal; agent orchestration pattern |
| 16 | code-repository-audit-skill | https://github.com/sanjabh11/codex-ecc-custom | 2025 | 13-dimension tech-DD framework with stack-aware extensions | Internal ECC skill; codebase-dependent |
| 17 | Codebase Pattern Extraction | — (internal framework) | 2025 | Collect → diff → abstract → parameterize → package | Internal; parameterization pattern |
| 18 | Auditor Skill | — (internal framework) | 2025 | Pre-audit questionnaire, scope selection, 1209-item checklist | Internal; adapted from ISO audit standards |

## External Research Sources (v5 additions)

| # | Source | URL | Version/Date | Applicability | Limitations |
|---|--------|-----|-------------|---------------|-------------|
| 19 | JTBD Framework | https://thrv.com/ | Christensen, 2003+ | Product-market alignment through job steps and customer outcomes, not features | Originally consumer-focused; adapted for B2B |
| 20 | NIST AI RMF Core | https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10 | AI RMF 1.0, 2023 | **Conditional evaluation/risk-governance source** — principles of documented test sets, metrics, uncertainty, repeatability, and independent review adapted for evidence evaluation | Designed for AI risk management, not product-market research; principles adapted, not directly applied |
| 21 | NIST AI 800-3 | https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.800-3.pdf | 2026 | **Statistical validity source** — principles of uncertainty quantification, construct validity, and proxies vs direct measurement adapted for decision confidence | Addresses AI benchmark evaluation, not market research; statistical models (GLMMs) not directly applicable; principles of uncertainty awareness adapted |
| 22 | Evidence Engine | https://github.com/sanjxksl/evidence-engine | 2025 | Evidence classification by type, bias mitigation, counter-evidence search, gap identification, assumption challenge | Open-source tool; designed for PM use cases; patterns adapted |
| 23 | Latent Spark / Iridae | https://iridae.com/product/latent-spark/ | 2025 | Living product-market context, belief states with confidence and provenance, drift and staleness tracking | Commercial product; conceptual model adapted, not the software |
| 24 | AHRQ Research Gap Framework | https://effectivehealthcare.ahrq.gov/sites/default/files/pdf/research-gaps_research.pdf | Robinson et al., 2011 (AHRQ Publication No. 11-EHC043-EF) | **Healthcare systematic review source — adapted for market gap analysis** — PICOS gap classification and 4 reasons for gaps (insufficient, biased, inconsistent, wrong information) adapted from healthcare to market research | Explicitly designed for healthcare systematic reviews; PICOS (Population, Intervention, Comparison, Outcomes, Setting) requires domain translation; gap reasons adapted but not directly applicable |
| 25 | Lean Startup Validated Learning | https://tryhamster.com/skills/designing-validated-learning-experiments | Ries, 2011+ | Cheapest experiment that can falsify hypothesis, WTP tests, fidelity ladder (low/medium/high) | Originally for startup product development; adapted for positioning validation |
| 26 | ParallelHQ Market Gap Guide | https://parallelhq.com/blog/how-to-find-market-gaps/ | 2025 | Segment by unmet needs, high pain + WTP + low competition, validate before building | Blog post; practical but not peer-reviewed |

## Adaptation Notes

### NIST AI RMF (Source 20)
The NIST AI RMF Core provides a GOVERN/MAP/MEASURE/MANAGE framework for AI risk management. The MEASURE function's emphasis on documented test sets, metrics, measures of uncertainty, comparisons to benchmarks, and formalized reporting is adapted as principles for evidence evaluation in this skill. The framework itself is not applied directly — it is a risk management framework for AI systems, not a market research methodology.

### NIST AI 800-3 (Source 21)
This 2026 NIST report addresses statistical validity of AI benchmark evaluations using generalized linear mixed models (GLMMs). The key adapted principles are: (1) distinguish benchmark accuracy from generalized accuracy, (2) quantify uncertainty explicitly, (3) recognize that proxy measurements may not capture the intended construct. These principles inform the "Decision Confidence" composite score and the distinction between decision confidence and statistical confidence. The GLMM methodology itself is not applicable to market research.

### AHRQ Research Gap Framework (Source 24)
The AHRQ framework was developed for healthcare systematic reviews using the PICOS (Population, Intervention, Comparison, Outcomes, Setting) structure. The 8-type gap classification in this skill adapts the AHRQ's 4-reason gap framework (insufficient information, biased information, inconsistency, wrong information) by translating it to market research contexts. The PICOS structure is replaced with the Alignment Chain (market need → customer outcome → product promise → actual capability → proof → positioning → experiment). The gap types (need, product, proof, positioning, pricing, distribution, adoption, evidence) are market-research-specific and do not map 1:1 to PICOS elements.
