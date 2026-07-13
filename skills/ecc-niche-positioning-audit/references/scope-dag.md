# Scope DAG — Phase Dependency Matrix

Explicit scope-to-phase dependency graph resolving all contradictions between scope rules and gate requirements.

## Scope Definitions

| Scope | Target Time | Use Case |
|-------|------------|----------|
| **quick** | 15-30 min | "Just tell me who my top 3 segments are and how my positioning scores" |
| **standard** | 1-3 hours | First audit on a codebase, or quarterly re-audit |
| **deep** | 3-6 hours | Pre-pivot, pre-fundraise, or post-major-feature-launch reassessment |

## Phase Dependency DAG

### Quick Mode

```
P0 (0a, 0b, 0d, 0g only — skip 0c, 0e, 0f)
  → [GATE 0-quick: threshold 12/25]
P1 (feature inventory + maturity scores — no bloat scan)
  → [GATE 1-quick: coverage = "known routes only"]
P2 (light: 10-15 candidates, no landing page test, no negative ICP)
  → [GATE 2-quick: ≥ 1 source per claim, ≥ 10 candidates]
P4 (8-lens scoring only — no outreach strategy, no drift register)
  → [GATE 4-quick: scores + positioning statements only]
  → TERMINAL (no Phase 5/6 in quick mode)
```

**Contradiction resolved**: Quick mode skips Phase 3, but Phase 4 originally required Phase 3 input. In quick mode, Phase 4 uses Phase 2 segment needs directly as input instead of Phase 3 triangulated priorities. This is documented in the Phase 4 input contract.

### Standard Mode

```
P0 (all sub-steps: 0a through 0g)
  → [GATE 0: threshold 15/25]
P1 (full recon: feature inventory, maturity, bloat, audience signals)
  → [GATE 1: coverage = "all enumerated routes"]
P2 (full: 20-30 candidates, P.R.O.F.I.T., ICP scoring, beachhead, negative ICP)
  → [GATE 2: ≥ 1 URL per claim, ≥ 20 candidates, ≥ 5 disqualifiers]
P3 (triangulation: 3 segments × 5 needs, top 10 priorities, gap scores)
  → [GATE 3: all 15 needs covered, adversarial review]
P4 (8-lens audit, positioning statements, outreach, drift register, quarterly cadence)
  → [APPROVAL GATE — User Decision]
P5 (codebase audit: top 10 priorities, file:line citations, intent drift)
  → [GATE 5: all findings cited, closure criteria]
P6 (remediation roadmap: 30-day action list, pre/post drift scores, quarterly setup)
  → [GATE 6: all items have due dates, owners, closure criteria]
  → TERMINAL
```

### Deep Mode

```
P0 (all sub-steps + extended research scan)
  → [GATE 0: threshold 15/25]
P1 (full recon + per-feature code quality assessment)
  → [GATE 1: coverage = "all enumerated routes" + quality scores]
P2 (extended: 30-40 candidates, competitor feature-by-feature matrix, landing page test)
  → [GATE 2: ≥ 2 URLs per load-bearing claim, ≥ 30 candidates]
P3 (full triangulation + per-feature alignment analysis)
  → [GATE 3: all 15 needs + per-feature alignment]
P4 (8-lens audit + competitor deep-dive lens + 90/180-day cadence)
  → [APPROVAL GATE — User Decision]
P5 (audit ALL features, not just top 10 — full codebase audit)
  → [GATE 5: all features audited, all cited]
P6 (30/90/180-day action lists + pre/post drift + quarterly + monthly drift signals)
  → [GATE 6: all time horizons covered]
  → TERMINAL
```

## Phase I/O Contracts

### Phase 0
- **Input**: codebase path, web search capability, optional input parameters
- **Output**: `phase-0-pre-execution-protocol.md` (dual-source research, deep think, skill selection, visualization, confidence scorecard)
- **Guarantees**: codebase surveyed, best practices scanned (standard/deep), skill selection documented

### Phase 1
- **Input**: Phase 0 artifact
- **Output**: `phase-1-codebase-recon.md` (feature inventory, maturity scores, audience signals, bloat candidates)
- **Guarantees**: all enumerated routes inventoried (or "unknown coverage" flagged)

### Phase 2
- **Input**: Phase 1 artifact + web search
- **Output**: `phase-2-market-research.md` (niche discovery log, ICP scores, beachhead segments, negative ICP)
- **Guarantees**: every market claim has cited source; ICP scores reproducible

### Phase 3
- **Input**: Phase 1 artifact + Phase 2 artifact
- **Output**: `phase-3-priority-alignment.md` (segment needs matrix, triangulation table, top 10 priorities)
- **Guarantees**: all 15 needs triangulated; adversarial review completed
- **Not in quick mode**: skipped entirely

### Phase 4
- **Input (standard/deep)**: Phase 3 artifact
- **Input (quick)**: Phase 2 artifact (segment needs used directly — no triangulation)
- **Output**: `phase-4-positioning-strategy.md` (8-lens scorecard, positioning statements, outreach [standard/deep], drift register [standard/deep])
- **Guarantees**: 24 lens scores with evidence (standard/deep); 24 lens scores (quick — no outreach/drift)

### Phase 5
- **Input**: Phase 4 artifact + explicit user approval
- **Output**: `phase-5-codebase-audit.md` (audit findings, intent drift, disposition recommendations)
- **Guarantees**: every finding cites file:line; closure criteria defined
- **Not in quick mode**: skipped entirely

### Phase 6
- **Input**: Phase 5 artifact
- **Output**: `phase-6-remediation-roadmap.md` (remediation roadmap, pre/post drift, 30-day list [standard], 30/90/180-day lists [deep])
- **Guarantees**: all items have due dates, owners, closure criteria
- **Not in quick mode**: skipped entirely

## Gate Decision Table

| Gate | Scope | Pre-gate Threshold | Key Exit Criteria |
|------|-------|-------------------|-------------------|
| Gate 0 | quick | 12/25 | Codebase surveyed, skill selection done, confidence ≥ 80% |
| Gate 0 | standard/deep | 15/25 | All 0a-0g complete, confidence ≥ 95% |
| Gate 1 | quick | 12/25 | Known routes inventoried, maturity scored |
| Gate 1 | standard/deep | 15/25 | All routes inventoried (or unknown flagged), maturity + bloat + audience signals |
| Gate 2 | quick | 12/25 | ≥ 10 candidates, ≥ 1 source per claim |
| Gate 2 | standard/deep | 15/25 | ≥ 20 candidates, ≥ 1 URL per claim, ≥ 5 disqualifiers, 4 perspectives |
| Gate 3 | standard/deep | 15/25 | 15 needs triangulated, adversarial review, load-bearing identified |
| Gate 4 | quick | 12/25 | 24 lens scores with evidence, positioning statements |
| Gate 4 | standard/deep | 15/25 | 24 lens scores, positioning statements, outreach, drift register, reversal cost |
| Approval | standard/deep | N/A | User explicitly approves proceeding |
| Gate 5 | standard/deep | 15/25 | All findings cited file:line, closure criteria, adversarial review |
| Gate 6 | standard/deep | 15/25 | All items have dates/owners/closure, pre/post drift numeric |

## Stop/Recycle Conditions

| Condition | Action |
|-----------|--------|
| Web search unavailable + Phase 2 needed | STOP — notify user |
| < 3 viable segments found in Phase 2 | STOP — "insufficient evidence" outcome (see scoring-rubric.md) |
| Confidence < 60% after 3 iterations | RECYCLE — restart phase with different approach |
| Stack cannot be detected and user cannot help | STOP — ask user for stack info |
| Advisor unavailable | Proceed with documented skip (not a stop condition) |
| Corrupt state.json | Fresh start with warning logged (not a stop condition) |
