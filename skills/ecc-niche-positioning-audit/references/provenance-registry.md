# Provenance Registry

Every methodology source, framework, and rubric used by this skill must be registered here with URL, publication date, source tier, and limitations. Unverified sources cannot drive gates.

## Source Tiers

| Tier | Definition | Gate Eligibility |
|------|-----------|-----------------|
| **academic** | Peer-reviewed publication or established academic framework | Load-bearing eligible |
| **practitioner** | Widely adopted framework from recognized practitioner/consultancy | Load-bearing eligible with corroboration |
| **standard** | Industry standard or official specification (ISO, PRISMA, GRADE) | Load-bearing eligible |
| **internal** | User-provided data, codebase evidence, or first-party research | Load-bearing eligible for codebase findings only |
| **unverified** | Named framework without independent documentation or URL | NOT load-bearing — heuristic only |

## Registered Sources

### 1. MIT Disciplined Entrepreneurship
- **URL**: https://disciplinedentrepreneurship.com/
- **Date**: 2013 (book), continuously referenced 2024-2026
- **Tier**: academic
- **Load-bearing**: Yes (beachhead methodology, TAM/SAM narrowing)
- **Limitations**: Academic framework; real-world beachhead selection may require additional market validation beyond the 6 filters

### 2. PRISMA 2020 Statement
- **URL**: https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.1003583
- **Date**: 2021-03-29
- **Tier**: standard
- **Load-bearing**: Yes (evidence protocol, research ledger structure)
- **Limitations**: Designed for healthcare systematic reviews; adapted for market research — some items (meta-analysis, study protocol registration) are not applicable

### 3. GRADE / Certainty of Evidence
- **URL**: https://www.bmj.com/content/389/bmj-2024-083864
- **Date**: 2024-2025 (Core GRADE series)
- **Tier**: standard
- **Load-bearing**: Yes (evidence grading HIGH/MEDIUM/LOW, certainty assessment)
- **Limitations**: Healthcare-focused; adapted for market evidence — RCT vs observational distinction maps to "validated market data" vs "inferred signals"

### 4. ISO 19011:2026 — Auditing Management Systems
- **URL**: https://www.iso.org/standard/602c3cef-1d84-4d52-8d97-48d35b8d824e
- **Date**: 2026
- **Tier**: standard
- **Load-bearing**: Yes (audit governance principles, independence, risk-based approach)
- **Limitations**: Guidance, not requirements; designed for management system audits — adapted for codebase/market positioning audits

### 5. Strategyzer — Business Hypothesis Testing
- **URL**: https://www.strategyzer.com/library/mastering-business-testing-formulating-strong-hypotheses
- **Date**: 2024-2025
- **Tier**: practitioner
- **Load-bearing**: Yes (hypothesis formulation: testable, precise, discrete)
- **Limitations**: Practitioner framework; no peer-reviewed validation of the hypothesis ranking method itself

### 6. Teresa Torres — Continuous Discovery Habits
- **URL**: https://www.producttalk.org/glossary-discovery-continuous-discovery/
- **Date**: 2021 (book), referenced 2024-2026
- **Tier**: practitioner
- **Load-bearing**: Yes (weekly touchpoint cadence, assumption testing)
- **Limitations**: Product management practice guide; not empirically validated against control groups

### 7. OpenAI Evals Framework
- **URL**: https://developers.openai.com/api/docs/guides/evals
- **Date**: 2024-2025
- **Tier**: standard
- **Load-bearing**: Yes (eval harness pattern: data_source_config + testing_criteria + graders)
- **Limitations**: Designed for LLM evaluation; adapted for skill evaluation — grader types map to deterministic checks

### 8. Anthropic Claude Code Skills Documentation
- **URL**: https://code.claude.com/docs/en/skills.md
- **Date**: 2025-2026
- **Tier**: standard
- **Load-bearing**: Yes (progressive disclosure, SKILL.md structure, references/ pattern)
- **Limitations**: Platform-specific; may change with Claude Code version updates

### 9. Anthropic Skill Development Guide
- **URL**: https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/skill-development/SKILL.md
- **Date**: 2025
- **Tier**: standard
- **Load-bearing**: Yes (body target 1,500-2,000 words, references/ usage, scripts/ pattern)
- **Limitations**: Official guidance but not a formal specification

### 10. ICP Scoring Rubric (Nimitai/Growleads/Hyperspect)
- **URL**: Not independently verified — sources named in original skill creation
- **Date**: Unknown
- **Tier**: unverified
- **Load-bearing**: No — used as heuristic starting point only
- **Limitations**: Cannot be independently verified; weights (40/25/20/15) are treated as configurable hypotheses, not validated standards

### 11. N.I.C.H.E. Framework (NicheCheck)
- **URL**: Not independently verified
- **Date**: Unknown
- **Tier**: unverified
- **Load-bearing**: No — used as mnemonic heuristic for niche discovery
- **Limitations**: Cannot be independently verified; the 5-step process is a useful checklist but not a validated methodology

### 12. Product Maturity Assessment (KnowledgeLib)
- **URL**: Not independently verified
- **Date**: Unknown
- **Tier**: unverified
- **Load-bearing**: No — 6-dimension scoring is a heuristic
- **Limitations**: Dimensions (PMF, completeness, debt, scalability, security, UX) are reasonable but scoring criteria are not calibrated

### 13. IntentGuard
- **URL**: Not independently verified
- **Date**: Unknown
- **Tier**: unverified
- **Load-bearing**: No
- **Limitations**: Named in original skill; no independent documentation found

### 14. PrismGrid
- **URL**: Not independently verified
- **Date**: Unknown
- **Tier**: unverified
- **Load-bearing**: No
- **Limitations**: Named in original skill; no independent documentation found

### 15. Stage Gate PM
- **URL**: Not independently verified — concept relates to Stage-Gate process by Robert Cooper
- **Date**: Unknown
- **Tier**: unverified
- **Load-bearing**: No — gate framework is adapted from general stage-gate concepts
- **Limitations**: The specific implementation in this skill is custom, not a direct adoption of Cooper's Stage-Gate

### 16. Adversarial Review
- **URL**: General concept — no single authoritative source
- **Date**: N/A
- **Tier**: practitioner
- **Load-bearing**: Yes (3-persona adversarial review pattern)
- **Limitations**: The specific 3-persona design (Skeptic, Missing Perspective, Contrarian) is custom; adversarial review as a concept is widely practiced

### 17. Audit Readiness Framework
- **URL**: Not independently verified
- **Date**: Unknown
- **Tier**: unverified
- **Load-bearing**: No
- **Limitations**: Named in original skill; no independent documentation found

### 18. TriAdReview
- **URL**: Not independently verified
- **Date**: Unknown
- **Tier**: unverified
- **Load-bearing**: No
- **Limitations**: Named in original skill; no independent documentation found

## Inclusion/Exclusion Rules

- **Include**: Sources with verifiable URLs, publication dates, and independent documentation
- **Exclude**: Sources that cannot be independently verified after reasonable search — mark as `unverified` and demote to non-load-bearing
- **Re-verify**: Sources should be re-verified annually; if a URL becomes dead, attempt to find archived version or alternative source
- **Upgrade**: An `unverified` source can be upgraded to `practitioner` or `academic` if independent documentation is found during Phase 0c (live best practices scan)

## Source Quality Signals

| Signal | Positive Indicator | Negative Indicator |
|--------|-------------------|-------------------|
| **URL resolves** | Live page with content | 404 or redirect to unrelated content |
| **Date present** | Publication or last-updated date visible | No date — freshness unknown |
| **Independent citation** | Cited by other sources | Only self-referenced |
| **Peer review** | Academic publication | Vendor whitepaper only |
| **Adoption evidence** | Used by multiple organizations | Single-company internal tool |
