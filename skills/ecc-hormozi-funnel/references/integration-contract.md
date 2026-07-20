# Integration Contract: Positioning Audit to Hormozi Funnel

## Overview

The `ecc-niche-positioning-audit` skill produces a structured export file that
the `ecc-hormozi-funnel` skill consumes. This contract defines the exact format
and required fields.

## Export File

**Filename:** `positioning-audit-export.json`
**Location:** `.positioning-audit/positioning-audit-export.json`
**Produced by:** `ecc-niche-positioning-audit` (Phase 7 or terminal output)
**Consumed by:** `ecc-hormozi-funnel` (Prompt 1 input)

## Schema

```json
{
  "audit_id": "string — unique audit identifier",
  "scope": "string — quick|standard|deep",
  "gate_decision": "string — GO|CONDITIONAL_GO|RECYCLE|STOP",
  "decision_confidence": {
    "composite": "number — 0-100",
    "quality": "number — 0-30",
    "coverage": "number — 0-25",
    "consistency": "number — 0-20",
    "counter": "number — 0-15",
    "validation": "number — 0-10"
  },
  "segments": [
    {
      "segment_id": "string — e.g., SEG-001",
      "name": "string",
      "rank": "integer",
      "pain_score": "integer — 1-10",
      "urgency_score": "integer — 1-10",
      "wtp_score": "integer — 1-10",
      "competition_score": "integer — 1-10",
      "evidence_ids": ["string — evidence corpus IDs"]
    }
  ],
  "hypotheses": [
    {
      "hypothesis_id": "string — e.g., H-SEG1-001",
      "text": "string",
      "status": "string — supported|weakened|disproven|stale|unresolved",
      "evidence_bundle": ["string — evidence IDs"],
      "load_bearing": "boolean"
    }
  ],
  "evidence_corpus": [
    {
      "evidence_id": "string — e.g., E-001",
      "type": "string — one of 11 evidence types",
      "source": "string",
      "source_tier": "string",
      "grade": "string — HIGH|MEDIUM|LOW",
      "confidence": "number — 0-1",
      "is_customer_commercial": "boolean",
      "content_summary": "string",
      "authority_tier": "string",
      "checked_at": "string — ISO date",
      "expiry": "string — ISO date or null",
      "url_health": "string — ok|broken|unknown"
    }
  ],
  "gap_table": [
    {
      "gap_id": "string",
      "gap_type": "string — need|product|proof|positioning|pricing|distribution|adoption|evidence",
      "description": "string",
      "evidence_ids": ["string"]
    }
  ],
  "experiments": [
    {
      "experiment_id": "string",
      "hypothesis_id": "string",
      "status": "string — designed|executing|completed|failed",
      "result": "string — supported|weakened|disproven|inconclusive|null"
    }
  ]
}
```

## Required Fields

The Hormozi funnel skill requires at minimum:
- `segments` with at least 1 segment (3+ recommended)
- `evidence_corpus` with at least 3 evidence items
- `hypotheses` with at least 1 hypothesis
- `gap_table` may be empty but must be present

## Error Handling

If the export file is missing or invalid:
1. Direct the user to run `ecc-niche-positioning-audit` first
2. Do not attempt to re-research market positioning
3. Do not generate outputs without evidence citations

If the export has fewer than 3 evidence items:
1. Warn the user about limited evidence
2. Proceed with reduced output quality
3. Flag all outputs as evidence-limited
