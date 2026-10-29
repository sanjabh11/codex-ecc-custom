---
name: ecc-model-route
description: "Use when the user asks for the ECC /model-route workflow inside Codex; adapts the upstream Claude command using token-budget-advisor and search-first, with truthful route-state reporting."
---

# ecc-model-route

Use this skill when the user is asking for the ECC `/model-route` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/model-route` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `token-budget-advisor`
- `search-first`

## Workflow

1. Restate the user's goal in the language of the `/model-route` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

- None for the baseline guidance path.

## Truthful Route States

Use precise language when describing model routing status. Never claim a route is active without evidence.

| State | Meaning | Evidence Required |
|---|---|---|
| `native policy installed` | Managed user policy exists; activation depends on root model and workspace config | Config file inspection |
| `policy effective` | Managed fields win in current workspace; still not a live spawn | Config layering check |
| `pinned custom agent available` | Matching role loaded, not yet used | Agent file exists + loaded |
| `route accepted` | Exact controls accepted and validated by current tool | Tool confirmation |
| `unverified prompt preference` | No exact control available | User text only |
| `used and confirmed` | Client explicitly exposes effective runtime model/provider/effort metadata | Runtime metadata |
| `inherited root` | Requested child model was not used; root model handled it | Runtime metadata shows root model |
| `unavailable` | Provider/model/selector cannot run | Provider check failed |

Requested text, a config file, or child prose alone is **not** proof that a model ran.

## Model Effort Normalization

Normalize effort labels across providers to a canonical set:

| User Label | Canonical | Claude Code | Codex/OpenAI |
|---|---|---|---|
| `low` | `low` | `low` | `low` |
| `medium` | `medium` | `medium` | `medium` |
| `high` | `high` | `high` | `high` |
| `xhigh` / `extra high` | `xhigh` | `xhigh` | `xhigh` |
| `max` | `max` | `max` | - |
| `ultra` | `max` | `max` (alias) | - |
| `auto` / omitted | `high` (default) | `high` | `high` |

- `Ultra` is a user-facing alias for `max` because Claude Code has no separate Ultra setting
- `Extra High` normalizes to `xhigh`
- Omission or `Auto` defaults to `High`
- Validate effort against the installed CLI's advertised choices before persisting
- The bridge reads only the normalized saved value — tool callers cannot raise effort at review time

## Integration with Codex-Orchestration

When the `codex-orchestration` plugin is installed, this skill's routing guidance complements it:
- `ecc-model-route` handles complexity-based routing recommendations (which model for which task)
- `codex-orchestration` handles explicit seat assignment (Planner/Advisor/Executor)
- Use truthful route states when reporting either system's status

## Upstream Source

- Command file: `model-route.md`
- Original description: Codex adaptation of ECC /model-route.
- Enhanced with truthful route states and effort normalization from Codex-Orchestration v0.5.1 patterns.
