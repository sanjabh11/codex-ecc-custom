---
name: connector-skill-composer
description: "Compose ECC skills and verified connectors into reusable workflow packages with inputs, outputs, guardrails, and proof gates. Use for launch reviews, design ops, daily briefs, and multi-connector workflows."
origin: ECC
---

# Connector Skill Composer

Use this skill to turn a repeated workflow into a compact ECC-native package instead of a one-off prompt. A composed workflow may reference connectors, MCP tools, browser/runtime checks, documents, and existing ECC skills, but it must not claim a connector exists unless verified in the current session.

## When to Activate

- User asks to combine connectors and skills into one workflow.
- User wants a reusable daily brief, release gate, launch review, design review, or proof pack.
- User mentions Claude plugins as "connectors + skills + role" and wants an ECC equivalent.
- A workflow needs more than one external surface, such as GitHub + Browser + Vercel + Figma + Documents.

## Workflow

1. Run `workflow-audit-router` first for classification and minimal routing.
2. Verify each connector/tool surface:
   - `installed`: plugin exists in this session.
   - `exposed`: callable tools are actually available.
   - `healthy`: a smoke call or non-mutating read works.
   - `planned`: useful but not currently callable.
3. Define the workflow package:
   - `name`
   - `trigger phrases`
   - `inputs`
   - `skill stack`
   - `connector/tool stack`
   - `outputs`
   - `verification gates`
   - `stop-and-ask gates`
4. Prefer composing existing ECC skills before creating a new skill.
5. If the workflow will recur across projects, create or update a compact `SKILL.md`.
6. If the workflow is project-specific, create a repo-local doc or checklist instead of global behavior.

## Template

```markdown
# <workflow-name>

## Triggers
- ...

## Inputs
- ...

## Skill Stack
- Primary: ...
- Subskills: ...

## Connectors And Tools
| Surface | Status | Use |
|---|---|---|
| GitHub | exposed | PR/issues/CI evidence |

## Outputs
- ...

## Verification Gates
- ...

## Stop Gates
- ...
```

## Usage Examples

```text
Use connector-skill-composer to create a launch-review workflow using GitHub, Browser, and conformance-gate.
Compose a daily briefing workflow for this repo using git status, open tasks, and deployment checks.
Build a design-review workflow using Figma, Browser QA, and frontend-patterns.
```

## Related Skills

- `workflow-audit-router` for route selection.
- `safe-plugin-importer` when the workflow is inspired by an external marketplace plugin.
- `agent-phase-ratchet` for persistent evidence on Tier 2+ workflows.
- `verification-loop` for final handoff checks.
