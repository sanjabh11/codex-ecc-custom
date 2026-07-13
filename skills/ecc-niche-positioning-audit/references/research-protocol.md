# Research Protocol

PRISMA-aligned evidence protocol for market research, codebase findings, and all claims that drive gate decisions.

## Research Ledger

Every research query and finding must be logged in the research ledger. The ledger is stored at `.positioning-audit/research-ledger.json` and updated in real-time during Phases 0, 1, and 2.

### Ledger Entry Schema

```json
{
  "entry_id": "RL-001",
  "phase": "phase-2",
  "query": "B2B SaaS mid-market ICP pain points 2025",
  "search_tool": "firecrawl",
  "timestamp": "2025-07-13T14:30:00Z",
  "sources": [
    {
      "url": "https://example.com/article",
      "title": "Article title",
      "author": "Author name",
      "publication_date": "2025-03-15",
      "source_tier": "practitioner",
      "evidence_type": "survey",
      "population": "500 B2B SaaS decision-makers",
      "geography": "US",
      "bias_notes": "Vendor-sponsored survey; may overstate willingness to pay",
      "contradiction_status": "none",
      "decision_impact": "Supports ICP weight for firmographic dimension"
    }
  ],
  "negative_evidence": [
    {
      "query": "B2B SaaS mid-market churn rates",
      "finding": "Churn rates higher than industry average for mid-market segment",
      "source_url": "https://example.com/churn-data",
      "impact": "Reduces confidence in mid-market segment viability"
    }
  ],
  "synthesis": "Mid-market B2B SaaS shows strong pain signals but elevated churn risk — segment viable with retention-focused positioning",
  "contradictions_resolved": true
}
```

### Required Fields Per Source

| Field | Required | Description |
|-------|----------|-------------|
| `url` | Yes | Direct link to source |
| `title` | Yes | Title of the source document |
| `publication_date` | Yes | Date of publication (ISO 8601); "unknown" if not found |
| `source_tier` | Yes | academic / practitioner / standard / internal / unverified |
| `evidence_type` | Yes | survey / interview / case_study / data_analysis / opinion / codebase_signal |
| `population` | No | Sample size or population studied (if applicable) |
| `geography` | Yes | Geographic scope: US, EU, APAC, global, or specific country |
| `bias_notes` | Yes | Known biases: vendor-sponsored, self-reported, small sample, selection bias |
| `contradiction_status` | Yes | none / found / resolved — whether contradicting evidence was found and handled |
| `decision_impact` | Yes | How this source affects a gate decision or finding |

## Evidence Quality Rules

### Source Duplication Detection

- Two sources citing the same underlying study count as **one** source, not two
- Check for shared data, shared authors, or shared funding before counting as independent
- If duplication is suspected, note it in `bias_notes` and count as one source

### Freshness Requirements

| Evidence Type | Max Age | Action if Stale |
|---------------|---------|-----------------|
| Market data (market size, growth rates) | 12 months | Flag as stale; seek newer source |
| Competitor analysis | 6 months | Flag as stale; re-verify competitor status |
| Methodology/framework | 24 months | Acceptable if framework is foundational |
| Customer feedback/signals | 3 months | Flag as stale; seek recent signals |
| Codebase evidence | Current | Always current (from live codebase) |

### Negative Evidence Protocol

- Every research query must include a **negative evidence search**: actively search for evidence that contradicts the hypothesis
- If negative evidence is found, it must be logged in `negative_evidence` array
- Contradictions must be resolved before the finding can be load-bearing
- Unresolved contradictions downgrade evidence grade by one level (HIGH → MEDIUM, MEDIUM → LOW)

### Certainty Assessment (GRADE-aligned)

| Certainty Level | Criteria | Gate Impact |
|----------------|----------|-------------|
| **High** | ≥ 2 independent sources, no bias concerns, no contradictions, current | Load-bearing eligible |
| **Moderate** | 1 strong source or 2+ weak sources, minor bias, no unresolved contradictions | Load-bearing with documented caveat |
| **Low** | Single source, significant bias, or unresolved contradictions | NOT load-bearing |
| **Very Low** | Unverified source, opinion-only, or stale evidence | NOT load-bearing; heuristic only |

### Bias Assessment Checklist

For each source, assess:

1. **Funding bias**: Is the research funded by a vendor with a stake in the outcome?
2. **Selection bias**: Is the sample representative of the target population?
3. **Publication bias**: Are negative results likely to be published?
4. **Self-report bias**: Are respondents self-reporting (may overstate positive behaviors)?
5. **Geographic bias**: Does the evidence apply to the target geography?
6. **Temporal bias**: Is the evidence from a different market condition or time period?

### PRISMA-Aligned Reporting

The research ledger must satisfy these PRISMA 2020 items (adapted for market research):

| PRISMA Item | How Satisfied |
|-------------|---------------|
| Item 11 (risk of bias) | `bias_notes` field per source |
| Item 14 (reporting bias) | `negative_evidence` array — actively searched for contradicting evidence |
| Item 15 (certainty) | Certainty level assigned per finding |
| Item 18 (risk of bias results) | Bias assessment documented in ledger |
| Item 21 (reporting bias results) | Negative evidence findings documented |
| Item 22 (certainty of evidence) | Certainty level recorded with each finding |

## Unavailable Web Search Protocol

If web search is unavailable during execution:

1. **Phase 0**: Skip 0c (live best practices scan); note in artifact
2. **Phase 2**: Cannot complete market research — STOP and notify user
3. **Phase 4**: Use existing Phase 2 research; cannot refresh competitive data
4. **All phases**: Codebase-based findings (Phase 1, 3, 5) are unaffected — they use internal evidence only
5. **Resume**: When web search becomes available, re-run Phase 2 if it was skipped

## Source Classification Decision Tree

```
Is the source a peer-reviewed academic publication?
  YES → academic
  NO → Is it an industry standard (ISO, PRISMA, etc.)?
    YES → standard
    NO → Is it from a recognized consultancy/practitioner with independent adoption?
      YES → practitioner
      NO → Is it from the user's codebase or first-party data?
        YES → internal
        NO → unverified
```
