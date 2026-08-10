---
name: graph-engineer
description: >-
  Implements reliable AI agent graphs by drawing job-based nodes, diamond
  parallelism, independent reviews, explicit failure paths, and human gates.
  Follows VibeMarketer_/@steipete principles for marketing/content workflows
  and generalizes to any multi-agent pipeline. Enforces "draw first, code
  second" — a graph diagram must exist before implementation begins.
  TRIGGER when: "agent graph", "graph engineer", "diamond pattern",
  "agent pipeline design", "multi-agent workflow", "parallel agents",
  "agent review graph", "job-based nodes", "graph validation",
  "design an agent graph", or "build a reliable agent pipeline".
  DO NOT TRIGGER when: the task is a single-agent prompt with no graph
  structure needed, or the user explicitly asks for a linear chain with
  no parallelism or review gates.
---

# graph-engineer

Design and validate reliable AI agent graphs. Every graph starts with a
diagram, uses single-responsibility nodes, diamond parallelism where
breadth helps, independent reviewers with separate questions, explicit
failure paths, capped loops, and human gates before expensive-to-undo
actions.

## Source Attribution

Codified from [@VibeMarketer_](https://x.com/VibeMarketer_/status/2080880030993785102)
and @steipete's graph-engineer thread; these are design principles, not
runtime or production proof.

## Core Principle: Draw First, Code Second

Before writing any agent code, prompt definitions, or tool calls, you
MUST produce a graph diagram. This is not optional.

1. Ask the user what workflow they want to build.
2. Draw the graph as a Mermaid diagram or ASCII art.
3. Show the diagram to the user and confirm it captures the workflow.
4. Only then proceed to implementation.

If the user provides a graph definition JSON or markdown spec that
already contains a `diagram` field, you may skip step 2 but must still
confirm the diagram before coding.

The validator (`scripts/validate_graph.py`) will exit 1 if no diagram
is present in the graph definition.

## Preflight: Decide Whether a Graph Is Justified

Before drafting nodes, answer these questions:

1. Are there at least two genuinely independent jobs, or separate review dimensions?
2. Does each proposed edge carry data or control that the downstream job actually needs?
3. Will fan-out reduce wall-clock time or improve independent verification enough to justify orchestration cost?
4. Is there a clear structured artifact contract at every join, review, and failure boundary?
5. What is the single expensive-to-undo action, and where is its human gate?

If the first or third answer is no, use one agent or a linear workflow. Do not manufacture a diamond. Numeric token/dollar estimates require pricing and telemetry; otherwise use caps and qualitative budget tiers.

## The 8 Principles

### 1. Draw the Jobs, Not the Agents

Each node represents one clear task — not one AI agent. A node's
responsibility is a job: plan, research, write, review, merge, approve.
The arrows show which jobs genuinely depend on each other.

**Node taxonomy (single-responsibility):**

| Node type | Responsibility | Example |
|---|---|---|
| `planner` | Decompose the objective into sub-tasks | "Break 'write blog post' into research, outline, draft, edit" |
| `worker` | Execute one sub-task independently | "Research competitor pricing" |
| `reviewer` | Check one dimension of a worker's output | "Is the data current?" |
| `synthesizer` | Merge multiple worker outputs into one | "Combine 3 research angles into one report" |
| `human-gate` | Human approval before irreversible action | "Approve before publish" |

A node MUST have exactly one responsibility. If a node does two things,
split it into two nodes.

### Node Contracts

Treat every node's `inputs` and `outputs` as a normative artifact contract:

- `inputs` names the upstream node IDs whose outputs are required; every input must have a matching data/control edge.
- `outputs` describes the structured artifact the node produces; a downstream node must consume it through an explicit edge.
- Use an optional `contract` object for `preconditions`, `postconditions`, and `failure_output` when prose alone is ambiguous.
- Keep failure feedback separate from normal data flow. Failure edges return structured reviewer feedback to a bounded worker.
- Use `runtime_refs` for local skill dependencies and validate them with `--runtime-root`; file existence is not proof that a connector is healthy.

### 2. Delete Fake Edges

Before adding an edge between two nodes, ask: **does the next job
genuinely need the previous job's output?** If not, they should not wait
on each other. Run them in parallel.

**Edge rules:**
- Every edge must have a `dependency_reason` field stating WHY the
  downstream node needs the upstream output.
- If the reason is "they're related" or "it flows naturally," delete
  the edge. That is a fake edge.
- Independent jobs run in parallel. The graph should make parallelism
  visible, not hide it behind a linear chain.

### 3. Use the Diamond Pattern

When a problem can be split into independent angles, use the diamond:

```
        ┌── Worker A ──┐
Planner ──┤── Worker B ──├── Synthesizer
        └── Worker C ──┘
```

**Diamond rules:**
- Split one problem into 2-5 independent angles.
- Each worker attacks its angle without seeing the others' work.
- Check each worker's output SEPARATELY (see principle 4).
- Merge the survivors (outputs that passed review) into one result.
- Drop outputs that failed review — do not merge broken work.

**When to use diamond:** The angles are genuinely independent. If worker
B needs worker A's output, that is a linear chain, not a diamond.

### 4. Never Let an Agent Grade Its Own Homework

Use separate reviewers with separate questions. A reviewer checks ONE
dimension and asks ONE question. Overlapping reviewers repeat the same
blind spots.

**Reviewer design:**
- Each reviewer has exactly one question.
- Reviewers must be different agents (or different prompts) from the
  worker they review.
- Standard reviewer questions for content/marketing:
  - **Correctness reviewer:** "Is every factual claim verifiable?"
  - **Currency reviewer:** "Is the information current (last 30 days)?"
  - **Source reviewer:** "Is every cited source real and accessible?"
- Standard reviewer questions for code/technical:
  - **Logic reviewer:** "Does the code do what the spec says?"
  - **Edge-case reviewer:** "What input breaks this?"
  - **Security reviewer:** "What attack surface does this expose?"

A worker NEVER reviews its own output. A reviewer NEVER reviews the
same dimension as another reviewer on the same node.

### 5. Know When NOT to Use a Graph

Graphs buy breadth, not better judgment. If every step needs the full
context from the step before it, one agent will usually be cheaper and
better.

**Use a graph when:**
- The problem splits into independent angles (diamond applies).
- Multiple dimensions need separate review (correctness + currency +
  source).
- Parallelism reduces wall-clock time meaningfully.

**Do NOT use a graph when:**
- Each step depends on the full output of the previous step.
- The task is a single coherent reasoning chain.
- The cost of orchestration exceeds the cost of one good agent doing
  it linearly.

If in doubt, start with one agent. Add a graph only when you identify
independent angles or review dimensions that a single agent misses.

### 6. Turn Failures Into Explicit Paths

A failed check must NOT end the run or disappear inside a prompt.
Route the feedback back to the worker, retry, then check again.

**Failure routing pattern:**

```
Worker → Reviewer → [PASS] → Synthesizer
                   → [FAIL] → Worker (with feedback) → Reviewer → ...
                                                    → [FAIL after cap] → Human-gate
```

**Failure routing rules:**
- A failed review produces structured feedback (what failed, where,
  what to fix).
- The feedback routes back to the original worker as a new input.
- The worker retries with the feedback.
- The reviewer checks again.
- If the loop hits the cap (see principle 7), route to a human-gate
  instead of looping forever.
- Never silently swallow a failure. Never end the run on a failure
  without routing.

### 7. Cap Every Loop

Every loop in the graph must have a maximum. Without caps, a useful
workflow becomes an expensive recursion machine.

**Mandatory caps (configurable in validation-rules.json):**

| Cap | Default | Description |
|---|---|---|
| `max_review_rounds` | 3 | Maximum times a worker can be sent back for revision |
| `max_spawned_agents` | 8 | Maximum parallel workers spawned at any point |
| `max_total_agents` | 20 | Maximum agents across the entire graph run |
| `one_writer_per_file` | 1 | Only one node may write to any given output file |

If a loop hits its cap, route to a human-gate (see principle 8). Do not
silently continue. Do not increase the cap mid-run.

### 8. Put the Human Gate Before Expensive-to-Undo Actions

Approval on every node makes the human the bottleneck. Approval nowhere
lets the graph ship confident mistakes. Place the human gate immediately
before anything expensive to undo.

**Actions that require a human gate:**

| Action | Why it's expensive to undo |
|---|---|
| Publish | Content is public; retraction is visible |
| Send (email/message) | Recipient has it; recall is unreliable |
| Refund | Money leaves; reversal requires new transaction |
| Invoice | Financial record created; correction is messy |
| Deploy | Code is live; rollback is disruptive |
| Delete | Data is gone; recovery may be impossible |

**Actions that do NOT require a human gate:**
- Drafting content (editable)
- Running research (read-only)
- Internal review passes (revisable)
- Generating variants (choosable later)

Place exactly one human gate before each expensive-to-undo action. Not
zero, not multiple. The gate asks: "Review this output. Approve, reject
with feedback, or abort the run."

## Graph Definition and Validation

The complete machine-readable contract lives in `references/graph-definition.md` and `schemas/graph-definition.schema.json`. Every graph declares `schema_version`: `v1` preserves the legacy string contract; `v1.1` requires objective, structured success criteria, an execution budget, an evidence policy, typed ports, reviewer ownership, explicit state conditions, and canonical resource locks. Reviewer artifacts can be checked with `--review-report` against `schemas/review-report.schema.json`; `record_evidence.py` requires each recorded review to carry an evidence-root-contained report and matching full SHA-256 digest.

Run the validator before implementing any graph:

```bash
python3 "${SKILL_DIR:-$(dirname $(dirname $0))}/scripts/validate_graph.py" \
  [--runtime-root /path/to/repository] <graph-definition.json>
```

The validator is local and deterministic. It fails on malformed or dangling contracts, unreachable nodes, data/control cycles, unbounded failure targets, missing reviewers or reviewer questions, unknown runtime references, missing dependency reasons, missing human gates, and cap violations. Graphs with `runtime_refs` fail closed unless `--runtime-root` is supplied. See `references/graph-to-runtime.md` for the runtime selection and proof-boundary guide.

## Anti-Patterns

See `references/graph-definition.md` for the full anti-pattern catalog. The
most critical: agent-persona nodes, linear chains for independent tasks, one
reviewer checks everything, no failure path, uncapped loops, no human gate,
self-grading workers, fake edges, and graphs for sequential reasoning.

## When to Use This Skill

- Building a content creation pipeline (research → draft → review → publish)
- Designing a codebase audit with parallel dimension reviewers
- Creating an A/B testing workflow with independent variant generation
- Any multi-agent workflow where reliability matters more than speed
- Marketing/content workflows per @VibeMarketer_ principles

## When NOT to Use This Skill

- Single-agent prompt with no graph structure
- Linear chain with no parallelism or review gates
- Quick one-off task that doesn't warrant orchestration
- Every step depends on full prior context (use one agent instead)

## Cross-IDE Compatibility

This skill is designed to work across Codex, Claude Code, Devin, Windsurf,
Agents, and Gemini. The SKILL.md body contains no IDE-specific instructions.
Activation metadata and discovery are handled by:

- `agents/openai.yaml` — Codex/OpenAI agent integration
- `.claude-plugin/` — Claude Code plugin metadata
- Standard YAML frontmatter — readable by all IDEs that support skills
- `activation-policy.json` — shared trigger, anti-trigger, host-family, and discovery policy

**Proof boundary:** 7 physical discovery paths map to 6 logical host families:
Codex, Claude Code, Devin, Agents, Windsurf, and Gemini. The two Windsurf
paths and the generic `.agents` path are not automatically independent IDEs.
All seven currently point to this package, but authenticated host-loader and
runtime smoke proof remains unverified. Discovery is not execution proof.

Trigger tests are `metadata-only`; host trigger-engine execution remains unproven.

## Auto-Revocation and Runtime Gating

Nodes may declare a `tools` array. The design-time validator and strict
pre-run gate use the same taxonomy from `validation-rules.json`:

| Class | Examples | Gating Behavior |
|-------|---------|----------------|
| **Core** | python3, git, cat, grep, find, and basic shell tools | Validator does not revoke; runtime still records resolution. |
| **Workflow** | pytest, cargo, npm, docker, go, gradle, dotnet, ruby | Missing or unhealthy required tools block. |
| **Advisory** | cass, cm, dcg, ubs, gh, br, bv, graphify | Missing tools may produce `degraded` only when optional. |
| **Unknown** | Anything else | Always blocked in v1. Add the executable to the shared policy taxonomy and regenerate the manifest; there is no `allow_unknown` escape hatch. |

If a workflow tool is missing, the validator exits 1 with a message naming
the tool and node. Install the tool or remove the node dependency; never
silently skip a workflow tool the graph depends on. Advisory tools degrade
gracefully — the graph remains valid without them.

For a deterministic pre-run decision, use `scripts/check_runtime.py` with a
strict `schemas/runtime-manifest.schema.json` manifest. It revalidates the
graph, binds full graph/runtime SHA-256 values, checks RFC3339 expiry and
revocation, binds runtime identity and tool versions, and requires an exact
run/artifact/action/target approval record. Decisions are
`available | degraded | blocked | revoked`.

This is a pre-run gate, not an executor, process supervisor, or host trigger
engine; it cannot terminate running or bypassed processes. The manifest and
approval binding are content-validated but unsigned caller-supplied JSON, so
they are not cryptographic authorization against an actor who can rewrite both
the manifest and runtime. Install JSON Schema from `requirements.txt`; missing
`jsonschema` fails closed.

## Advisor Integration

If `ecc-advisor` is available, consult it before graph structure, reviewer
questions, and human gates; otherwise use these graph principles.
