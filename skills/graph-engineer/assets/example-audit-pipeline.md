# Example: Codebase Audit Pipeline

A codebase audit graph using the diamond pattern for parallel dimension
reviewers, independent review questions, and a human gate before deploying
fixes.

## Diagram

```
                    ┌── Audit-Security ────────┐
                    │                          │
Plan-Audit ────────┤── Audit-Architecture ────├── Synthesize-Findings ── Human-Gate ── Deploy-Fixes
                    │                          │
                    └── Audit-Performance ─────┘
```

## Graph Definition

```json
{
  "name": "codebase-audit-pipeline",
  "description": "Parallel audit of security, architecture, and performance dimensions with independent reviewers and a human gate before deploying fixes",
  "diagram": "Plan-Audit → [Audit-Security, Audit-Architecture, Audit-Performance] → Synthesize-Findings → Human-Gate → Deploy-Fixes",
  "nodes": [
    {
      "id": "plan-audit",
      "type": "planner",
      "responsibility": "Map the repository structure and define audit scope for each dimension",
      "inputs": [],
      "outputs": ["repo-map.json", "audit-scope.json"]
    },
    {
      "id": "audit-security",
      "type": "worker",
      "responsibility": "Audit the codebase for security vulnerabilities and hardcoded secrets",
      "inputs": ["plan-audit"],
      "outputs": ["security-findings.json"],
      "loop_cap": 2
    },
    {
      "id": "audit-architecture",
      "type": "worker",
      "responsibility": "Audit the codebase for architecture smells and layering violations",
      "inputs": ["plan-audit"],
      "outputs": ["architecture-findings.json"],
      "loop_cap": 2
    },
    {
      "id": "audit-performance",
      "type": "worker",
      "responsibility": "Audit the codebase for performance bottlenecks and unbounded growth patterns",
      "inputs": ["plan-audit"],
      "outputs": ["performance-findings.json"],
      "loop_cap": 2
    },
    {
      "id": "synthesize-findings",
      "type": "synthesizer",
      "responsibility": "Merge the three audit dimension findings into one prioritized report",
      "inputs": ["audit-security", "audit-architecture", "audit-performance"],
      "outputs": ["audit-report-merged.json"]
    },
    {
      "id": "human-gate-deploy",
      "type": "human-gate",
      "responsibility": "Human reviews the merged audit report and approves which fixes to deploy",
      "inputs": ["synthesize-findings"],
      "outputs": ["approval-decision.json"],
      "human_gate_action": "deploy"
    }
  ],
  "edges": [
    {"from": "plan-audit", "to": "audit-security", "dependency_reason": "Security auditor needs the repo map and scope to know what to audit", "type": "data"},
    {"from": "plan-audit", "to": "audit-architecture", "dependency_reason": "Architecture auditor needs the repo map and scope to know what to audit", "type": "data"},
    {"from": "plan-audit", "to": "audit-performance", "dependency_reason": "Performance auditor needs the repo map and scope to know what to audit", "type": "data"},
    {"from": "audit-security", "to": "synthesize-findings", "dependency_reason": "Synthesizer needs all three dimension findings to produce a merged report", "type": "data"},
    {"from": "audit-architecture", "to": "synthesize-findings", "dependency_reason": "Synthesizer needs all three dimension findings to produce a merged report", "type": "data"},
    {"from": "audit-performance", "to": "synthesize-findings", "dependency_reason": "Synthesizer needs all three dimension findings to produce a merged report", "type": "data"},
    {"from": "synthesize-findings", "to": "human-gate-deploy", "dependency_reason": "Human needs the merged report to decide which fixes to approve for deployment", "type": "data"}
  ],
  "caps": {
    "max_review_rounds": 2,
    "max_spawned_agents": 5,
    "max_total_agents": 10
  },
  "human_gates": [
    {"position": "human-gate-deploy", "action": "deploy"}
  ]
}
```

## Key Design Notes

- **Diamond pattern**: Three audit dimensions run in parallel — security,
  architecture, performance. Each is independent and doesn't need the others'
  output.
- **No reviewers in this graph**: The audit workers ARE the reviewers. Each
  audits a different dimension, which is the spirit of "separate reviewers with
  separate questions." The synthesizer merges their findings.
- **Human gate**: Placed before deploy — deploying fixes is expensive to undo.
  The human decides which findings to act on.
- **Low caps**: Audit is read-only, so loop caps are low (2). No need for
  extensive retry loops on analysis tasks.
