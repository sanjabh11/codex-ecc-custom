# Launch Evidence Schema

Use this schema for the final evidence JSON produced by a one-repo commercial launch readiness run. The schema is intentionally plain JSON so it can be reviewed, diffed, and compared without extra dependencies.

Validate completed evidence with:

```bash
python3 /Users/sanjayb/.codex/skills/commercial-launch-readiness-orchestrator/scripts/validate_launch_evidence.py launch-evidence.json
```

## Required Top-Level Shape

```json
{
  "schema_version": 1,
  "repo": {
    "name": "example-app",
    "path": "/absolute/path/to/repo",
    "profile": "saas",
    "commit": "optional git commit"
  },
  "run": {
    "name": "launch-readiness-audit",
    "mode": "audit-only",
    "research_depth": "deep",
    "worker_mode": "dry-run",
    "duration_hours": 1.5,
    "generated_at": "2026-06-04T00:00:00Z"
  },
  "launch_decision": "pilot-only",
  "scores": {
    "security": 3,
    "readiness": 3,
    "sellability": 4,
    "evidence": 3,
    "overall": 3
  },
  "proof_buckets": {
    "hosted_live": [],
    "local": [],
    "repo_artifact": [],
    "candidate_shadow": [],
    "roadmap": []
  },
  "gaps": [],
  "pain_points": [],
  "target_customers": [],
  "outreach_plan": {},
  "fix_report": {},
  "implementation_decisions": [],
  "rejected_variants": [],
  "code_optimization_reviews": [],
  "adversarial_reviews": [],
  "progress_updates": [],
  "bottleneck_log": [],
  "market_evidence_mode": "real",
  "synthetic_data_points": [],
  "ecc_ledger": {}
}
```

## Gap Item

```json
{
  "gap": "Missing object-level authorization check",
  "severity": "P1",
  "evidence": "src/api/projects.ts:42",
  "framework_mapping": ["OWASP API1:2023 Broken Object Level Authorization"],
  "buyer_impact": "Enterprise buyers will block deployment without tenant isolation proof.",
  "fix": "Add ownership check and regression test.",
  "status": "open"
}
```

## Pain Point Item

```json
{
  "rank": 1,
  "pain_point": "Manual compliance evidence collection slows procurement.",
  "affected_buyer": "B2B SaaS security and sales teams",
  "source_evidence": ["https://example.com/source"],
  "willingness_to_pay_signal": "Existing paid compliance tooling and SOC2 deadlines.",
  "repo_proof_fit": "Verified proof-pack export.",
  "confidence": 4
}
```

## Target Customer Item

```json
{
  "rank": 1,
  "account_or_segment": "Series A B2B SaaS with SOC2 pressure",
  "pain": "Security review slows deals.",
  "trigger": "Enterprise procurement or SOC2 audit.",
  "decision_maker": "VP Engineering or Head of Security",
  "outreach_angle": "Reduce evidence gathering time for security reviews.",
  "proof_to_show": "Local proof-pack demo and security checklist.",
  "confidence": 4
}
```

## Progress Update Item

```json
{
  "phase": "research",
  "created_at": "2026-06-04T12:00:00Z",
  "accomplished": ["Mapped 7 competitor substitutes", "Collected 6 pain-point sources"],
  "target_matrix": [
    {
      "lane": "Market Pain Research",
      "target_percent": 20,
      "current_percent": 55,
      "status": "running",
      "evidence": ["results.jsonl: market-researcher partial handoff"],
      "confidence": 3
    }
  ],
  "pending": ["4 more source-backed pain points", "target account ranking"],
  "bottleneck": "Market source expansion is slow because real customer feedback is unavailable."
}
```

## Bottleneck Log Item

```json
{
  "phase": "research",
  "task_or_subtask": "T005 market-researcher",
  "elapsed_minutes": 145,
  "last_update": "2026-06-04T12:00:00Z",
  "root_cause": "search/exploration",
  "top_unblock_options": [
    "Limit research to top 5 sources per pain point.",
    "Use narrow ICP segments instead of named accounts.",
    "Create labeled synthetic hypotheses for missing feedback."
  ]
}
```

## Synthetic Data Point

```json
{
  "hypothesis": "Series A B2B SaaS teams with SOC2 pressure may pay for security evidence automation.",
  "reason": "No direct buyer feedback is available yet; public procurement and compliance workflows indicate likely pain.",
  "validation_source_needed": "Buyer interview, pilot feedback, RFP, or paid pilot."
}
```

## Implementation Decision Item

Use when a repo-side code change is made.

```json
{
  "task_id": "T007",
  "decision": "Add missing server-side tenant ownership check",
  "acceptance_check": "Unauthorized tenant access test fails before fix and passes after fix.",
  "chosen_variant": "minimal code patch",
  "repo_pattern_reused": "Existing requireTenantAccess helper",
  "files_changed": ["src/api/projects.ts", "tests/projects-auth.test.ts"],
  "tests_run": ["npm test -- projects-auth"],
  "proof": "Local test passed and code path maps to OWASP API1.",
  "reason": "Config-only and doc-only variants did not enforce authorization."
}
```

## Rejected Variant Item

```json
{
  "task_id": "T007",
  "variant": "Introduce a new authorization middleware framework",
  "reason_rejected": "Broader dependency and architecture change were unnecessary for the scoped P1 gap.",
  "tradeoff": "Minimal helper reuse is narrower and easier to verify.",
  "evidence": "Existing helper already covers tenant access pattern."
}
```

## Code Optimization Review Item

```json
{
  "target_task": "T007",
  "policy": "strict",
  "verdict": "pass",
  "minimality_score": 4,
  "evidence": "Changed two files, reused existing helper, no new dependency, focused test passed.",
  "tests_or_checks": ["npm test -- projects-auth"],
  "remaining_risk": "Hosted proof still not verified."
}
```

## Valid Values

- `repo.profile`: `saas`, `ai-app`, `data-app`, `devtool`, `marketplace`, `internal-tool`, or `unknown`.
- `run.mode`: `audit-only`, `fix-safe`, or `full`.
- `run.research_depth`: `light`, `standard`, or `deep`.
- `launch_decision`: `blocked`, `pilot-only`, `sellable-with-caveats`, or `commercial-ready`.
- `gap.severity`: `P0`, `P1`, `P2`, or `P3`.
- `market_evidence_mode`: `real`, `mixed`, `synthetic-only`, or `unknown`.
- `bottleneck_log.root_cause`: `context overload`, `ambiguous requirements`, `dependency issue`, `testing loop`, `search/exploration`, `decision paralysis`, `tool/execution delay`, `worker failure`, or `evidence gap`.
- `code_optimization_reviews.policy`: `safe`, `strict`, or `measured`.
- `code_optimization_reviews.verdict`: `pass`, `fail`, or `needs-retry`.
- Scores are integers from 1 to 5.

## Hard Validation Gates

- Completed evidence must include at least 10 `pain_points` and 10 `target_customers`.
- Each pain point must include at least one `http` or `https` source URL.
- Unresolved `P0` gaps require `launch_decision: "blocked"`.
- `commercial-ready` is not allowed with unresolved `P1` gaps.
- `commercial-ready` requires security, readiness, sellability, and evidence scores of at least 4.
- `commercial-ready` requires at least one `proof_buckets.hosted_live` item.
- `commercial-ready` is rejected when `market_evidence_mode` is `synthetic-only`.
- Any run with `run.duration_hours >= 20`, equivalent duration fields, or start/end timestamps totaling 20 hours or more must include at least one `bottleneck_log` entry.
- Proof bucket keys must be present even when the list is empty: `hosted_live`, `local`, `repo_artifact`, `candidate_shadow`, and `roadmap`.
- Progress keys must be present even when empty: `progress_updates`, `bottleneck_log`, `market_evidence_mode`, and `synthetic_data_points`.
- Code optimization keys must be present even when empty: `implementation_decisions`, `rejected_variants`, and `code_optimization_reviews`.
- If `fix_report.files_changed` is non-empty, evidence must include at least one `implementation_decisions` item, one `code_optimization_reviews` item, and at least one test/check in `fix_report.tests_run` or in the implementation decision.
- Code changes cannot pass final evidence validation when every code optimization review has verdict `fail` or `needs-retry`.
