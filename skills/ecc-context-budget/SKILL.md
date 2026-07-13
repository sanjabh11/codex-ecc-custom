---
name: ecc-context-budget
description: Codex adaptation of ECC `/context-budget`. Analyze context window usage across agents, skills, MCP servers, and rules to find optimization opportunities. Helps reduce token overhead and avoid performance warnings.
---

# ecc-context-budget

Use this skill when the user is asking for the ECC `/context-budget` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/context-budget` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `context-budget`
- `token-budget-advisor`
- `strategic-compact`

## Workflow

1. Restate the user's goal in the language of the `/context-budget` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

- None for the baseline guidance path.

## Upstream Source

- Command file: `context-budget.md`
- Original description: Analyze context window usage across agents, skills, MCP servers, and rules to find optimization opportunities. Helps reduce token overhead and avoid performance warnings.
