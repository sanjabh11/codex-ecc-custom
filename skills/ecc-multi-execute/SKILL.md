---
name: ecc-multi-execute
description: Codex adaptation of ECC `/multi-execute`. Codex adaptation of ECC /multi-execute.
---

# ecc-multi-execute

Use this skill when the user is asking for the ECC `/multi-execute` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/multi-execute` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `dmux-workflows`
- `autonomous-loops`

## Workflow

1. Restate the user's goal in the language of the `/multi-execute` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

- `codeagent-wrapper`: This upstream workflow expects the Claude-side wrapper; in Codex, use only the conceptual workflow unless a compatible wrapper is installed.
- `ccg prompts`: These prompts are part of the ccg-workflow runtime; mention that requirement explicitly.

## Upstream Source

- Command file: `multi-execute.md`
- Original description: Codex adaptation of ECC /multi-execute.
