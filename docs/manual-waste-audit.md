# Manual-Waste Audit

## High-Leverage Marketing Tasks with Skill Coverage

These are weekly tasks where a skill already covers the work but may not be triggered.

| Task | Skill(s) | Manual waste if not triggered |
|---|---|---|
| Measure impact of marketing changes | ecc-closed-loop-analytics | High |
| Track buyer pipeline stages | ecc-buyer-pipeline | High |
| Review code changes for quality and security | ecc-code-review, ecc-cpp-review, ecc-go-review, ecc-kotlin-review, ecc-python-review, ecc-rust-review | Medium |
| Plan 7-day content calendar | ecc-hormozi-funnel | High |
| Review content for claims and quality | ecc-content-quality-ops | High |
| Audit landing pages for conversion friction | ecc-conversion-audit | High |
| Deploy or verify deployment readiness | ecc-quality-gate, ecc-verify | Medium |
| Write or update documentation | agents-md-generator, ecc-update-docs | Medium |
| Design and register a growth experiment | ecc-growth-experiment-loop | High |
| Audit funnel for friction points | ecc-conversion-audit, ecc-hormozi-funnel | Medium |
| Write and rank hooks for content | ecc-hormozi-funnel | High |
| Research target accounts and build dossiers | ecc-lead-dossier | High |
| Create or refine an evidence-backed offer | ecc-hormozi-funnel, ecc-value-pricing | Medium |
| Draft outreach messages (email, LinkedIn, X) | ecc-buyer-pipeline, ecc-outbound-campaign | Medium |
| Run positioning audit for a repo segment | ecc-niche-positioning-audit | High |
| Prepare pricing briefs and value hypotheses | ecc-value-pricing | High |
| Trace revenue to marketing activities | ecc-revenue-attribution | High |
| Prioritize SEO opportunities and technical fixes | ecc-seo-opportunity-loop | High |
| Maintain and validate ECC skills | ecc-skill-create, ecc-skill-health | Medium |
| Write or run tests | ecc-tdd, ecc-test-coverage | Medium |

## Gaps — High-Leverage Marketing Work with No Skill Coverage

No gaps detected — all weekly tasks have at least one skill covering them.

## Top 3 Chained Skills for Immediate Impact

| Rank | Skill | Why |
|---|---|---|
| 1 | ecc-niche-positioning-audit | Produces the evidence foundation all other marketing skills consume |
| 2 | ecc-hormozi-funnel | Converts positioning into distributable GTM assets (offers, hooks, content, proof) |
| 3 | ecc-growth-experiment-loop | Registers falsifiable experiments to test the assets produced by stage 2 |

**Chain:** positioning-audit → hormozi-funnel (weekly mode) → growth-experiment-loop

**Following week:** Pass `experiment-registration.json` to `ecc-closed-loop-analytics` for readback.
