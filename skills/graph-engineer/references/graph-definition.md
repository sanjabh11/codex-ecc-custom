# Graph Definition Contract

The normative machine-readable contract is `schemas/graph-definition.schema.json`. Every graph declares `schema_version`: `v1` retains the legacy string contract; `v1.1` adds typed ports, reviewer ownership, state conditions, joins, canonical resources/locks, budgets, and evidence policy.

```json
{
  "schema_version": "v1.1",
  "name": "human-readable graph name",
  "description": "what this graph accomplishes",
  "diagram": "Mermaid or ASCII diagram",
  "entry_node": "optional explicit structural entry",
  "runtime_refs": ["optional local skill directory name"],
  "nodes": [
    {
      "id": "unique node ID",
      "type": "planner | worker | reviewer | synthesizer | human-gate",
      "responsibility": "one job",
      "inputs": ["upstream node IDs"],
      "outputs": ["artifact descriptions"],
      "input_ports": [{"name": "input", "from_node": "upstream", "from_port": "artifact", "schema": {"type": "object"}}],
      "output_ports": [{"name": "artifact", "schema": {"type": "object"}}],
      "review_questions": ["exactly one question for reviewer nodes"],
      "reviewed_node_id": "worker-id",
      "resources": {"reads": ["source:ledger"], "writes": ["artifact:report.json"], "locks": ["artifact:report.json"]},
      "loop_cap": 2,
      "human_gate_action": "action for human-gate nodes",
      "contract": {
        "preconditions": "optional string",
        "postconditions": "optional string",
        "failure_output": "optional string"
      }
    }
  ],
  "edges": [
    {
      "from": "node ID",
      "to": "node ID",
      "dependency_reason": "why the downstream job needs the output",
      "type": "data | control | failure | exhaustion",
      "condition": "review_passed | review_failed | retry_exhausted"
    }
  ],
  "objective": "v1.1 measurable objective",
  "success_criteria": [{"id": "quality", "metric": "review_pass_rate", "threshold": "pass", "evidence": ["review-report"]}],
  "budget": {"max_model_calls": 8, "max_spawned_agents": 2, "max_concurrency": 2, "max_tool_calls": 12, "max_wall_clock_seconds": 300, "max_tokens": 12000, "max_retries": 2, "max_graph_writes": 2},
  "evidence_policy": {"required_anchors": true, "required_sources": true, "required_evaluator_outputs": true, "min_evidence_count": 1},
  "joins": [{"node_id": "synthesizer", "expected_count": 2, "partial_failure": "block"}],
  "caps": {
    "max_review_rounds": 3,
    "max_spawned_agents": 8,
    "max_total_agents": 20
  },
  "human_gates": [{"position": "node ID", "action": "approval action"}]
}
```

## Contract rules

- Every `inputs` entry must be supplied by a data/control edge, and every data/control edge must be declared in the destination's inputs.
- In v1.1, data/control edges declare matching ports and conditions; reviewers bind `reviewed_node_id` and emit `schemas/review-report.schema.json`.
- Data/control flow must be reachable and acyclic. Recovery loops use failure edges only.
- Failure edges return reviewer feedback to bounded workers; exhaustion edges explicitly route `retry_exhausted` to a human gate.
- v1.1 fan-in nodes require a `joins` contract with expected count and partial-failure behavior. Writes use canonical resource IDs and locks; filenames alone are not writer protection.
- `runtime_refs` are checked against `skills/<name>/SKILL.md` only when `--runtime-root` is supplied; graphs with refs fail closed without it.
- `human-gates` must be connected terminal nodes immediately before the external irreversible action.

Validate before execution:

```bash
python3 scripts/validate_graph.py [--runtime-root /path/to/repository] graph.json
```
