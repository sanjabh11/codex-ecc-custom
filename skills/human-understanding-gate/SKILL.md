---
name: human-understanding-gate
description: "Use when a human must deeply understand a session, audit, implementation, bug fix, design decision, code path, phase handoff, or long-running agent outcome before work continues."
origin: ECC
---

# Human Understanding Gate

Use this skill to convert ECC work into an evidence-bound teach-back loop. The goal is not a longer explanation; the goal is verified human understanding of the problem, the solution, the tradeoffs, the edge cases, and the broader impact.

## Skill Pack Contract

This skill follows the skill-pack pattern:
- `SKILL.md` is the instruction layer: intent, judgment, collaboration rules, and teaching behavior.
- `scripts/human-understanding-gate.js` is the thin deterministic layer: resolver scoring, checklist scaffolding, skill-pack checks, and eval execution.
- `resolver.json` contains explicit auto-invocation rules that agents can inspect instead of guessing from vibes.
- `evals/skill-behavior-cases.json` is the LLM-eval scaffold for checking whether a model applying the skill includes the required gate behavior.
- `evals/resolver-cases.json` tests resolver behavior on positive and negative prompts.
- `tests/scripts/human-understanding-gate.test.js` unit-tests the deterministic layer and integration between markdown, resolver, evals, command, and manifest.

Do not put teaching judgment into code. Keep code limited to I/O, scoring, schema checks, and repeatable verification.

## When to Use

Activate this skill when the user asks for:
- "make sure I understand"
- "human-understanding-gate"
- "understanding gate"
- "teach-back"
- "quiz me"
- "ELI5", "ELI14", "ELII", or "explain like an intern"
- session handoff, phase handoff, or audit handoff where misunderstanding would cause bad next steps
- high-stakes decisions where the user must understand claim boundaries before approving work

Do not activate for Tier 0 answers, simple one-liners, or cases where the user clearly wants only direct execution.

When uncertain, run the resolver first:

```bash
node skills/human-understanding-gate/scripts/human-understanding-gate.js resolve --task "<task>" --json
```

## ECC Collaboration

This skill teaches from verified ECC evidence. Pair it with the smallest useful set of related skills:
- `agent-phase-ratchet`: use the phase baseline, checks, delta, reflection, and next adjustment as the teaching source.
- `verification-loop`: teach only after the relevant implementation evidence is known.
- `conformance-gate`: explain proof boundaries, correctness claims, live/local/artifact-only distinctions, and release-readiness limits.
- `perf-ratchet`: explain benchmark baselines, thresholds, before/after deltas, and why a performance claim is or is not valid.
- `fuzz-regression`: explain edge cases, adversarial inputs, parser boundaries, and regression fixtures.
- `browser-qa` or `e2e-testing`: explain UI/runtime behavior from real browser or test evidence.
- `deep-research`: explain external research findings, citations, confidence caps, and what remains unverified.
- `understand-*` or `codegraph`: use graph, dependency, caller/callee, and architecture evidence to teach how code pieces connect.
- `dynamic-workflow-backlog`: teach multi-workstream plans, worker boundaries, evidence gates, and why work should or should not be parallelized.

Do not claim any tool, MCP server, interactive quiz API, debugger, graph, hook, or runtime is available unless it is exposed or verified in the current session.

## Deterministic Checks

Use these commands when maintaining or validating this skill pack:

```bash
node skills/human-understanding-gate/scripts/human-understanding-gate.js check-pack --json
node skills/human-understanding-gate/scripts/human-understanding-gate.js eval-skill --json
node skills/human-understanding-gate/scripts/human-understanding-gate.js eval-resolver --json
node tests/scripts/human-understanding-gate.test.js
```

The deterministic layer must never claim that the human understood something. It can only classify prompts, create checklists, validate pack structure, validate eval scaffolds, and report whether the required gate mechanics exist.

## Operating Rules

1. Start from the human's current model when feasible: ask the user to restate their understanding before adding more explanation.
2. Teach incrementally. Do not dump the full explanation at the end of a long run.
3. Cover both high-level motivation and low-level mechanics: business logic, code path, edge cases, proof boundaries, and impact.
4. Drill into why, then what, then how. Understanding the problem and why it existed comes before the solution.
5. Use adaptive depth: `ELI5`, `ELI14`, `intern`, `practitioner`, `expert`, or `executive`.
6. Use worked examples, code references, debugger steps, browser evidence, or diagrams when the concept is easier to learn from an artifact.
7. Quiz with open-ended or multiple-choice prompts. Rotate answer order. Do not reveal the answer key until after the user responds.
8. If an interactive question tool is exposed, use it for concise checks. Otherwise ask plain-text questions.
9. Keep a checklist at response level by default. Persist a Markdown checklist only when the user asks for durable tracking, the task is long-running, or the active workflow already uses persistent artifacts.
10. Do not block forever. If the user is unavailable, mark understanding as `not verified yet` and provide the exact teach-back questions needed to verify later.

## Understanding Checklist

Track these items until each is `verified`, `partial`, `not verified yet`, or `not applicable`:
- Problem: what failed, why it mattered, and why it existed.
- Branches: alternatives considered and why they were accepted or rejected.
- Solution: what changed or what was decided.
- Design decisions: constraints, tradeoffs, and why this path was chosen.
- Edge cases: failure modes, adversarial inputs, regressions, and guardrails.
- Evidence: commands, tests, browser checks, runtime artifacts, citations, and proof gaps.
- Impact: what this affects, what it does not affect, and what must not be overclaimed.
- Next action: what the human should approve, review, test, or ask next.

## Workflow

1. Evidence intake:
   - Identify the current phase, artifact, code path, diff, audit section, or decision being taught.
   - Separate proven facts from assumptions and unresolved gaps.
2. Human baseline:
   - Ask for the user's restatement when the topic is complex, high-risk, or handoff-critical.
   - If the user asked for immediate explanation, provide a compact baseline and then ask one checkpoint question.
3. Teach-back module:
   - Explain one concept at a time.
   - Use the requested depth level or default to `intern`.
   - Include concrete references to files, commands, routes, tests, or research when available.
4. Probe:
   - Ask one to three questions that test problem, solution, and impact.
   - Use multiple choice only when quick validation is more useful than open-ended reasoning.
5. Refine:
   - Correct misunderstandings.
   - Add a smaller example, a diagram, a code walk, or a debugger/browser step when needed.
6. Decision:
   - `verified`: the user demonstrated understanding of every required checklist item.
   - `partial`: the user understood the core but missed one or more checklist items.
   - `not verified yet`: the user has not answered the probes.
   - `skipped`: the user explicitly asked to skip the gate.

## Output Contract

For a gate response, include:

| Field | Content |
|---|---|
| Topic | The exact session, phase, code path, audit, or decision being taught |
| Evidence basis | Files, commands, browser checks, runtime artifacts, or citations used |
| Depth | ELI5, ELI14, intern, practitioner, expert, or executive |
| Checklist | Understanding items with status |
| Teach-back prompt | What the user should restate |
| Quiz | One to three questions without answer key |
| Gate status | verified, partial, not verified yet, or skipped |
| Next adjustment | How to teach or verify the next concept better |

## Prompt Core

Use this compact prompt when invoking the skill directly:

```text
Use human-understanding-gate. Teach this session incrementally from verified evidence, maintain a checklist of what I must understand, ask me to restate my model, quiz me without revealing the answer key, fill gaps, and do not mark the gate verified until I demonstrate understanding of the problem, solution, tradeoffs, edge cases, evidence, impact, and next action.
```
