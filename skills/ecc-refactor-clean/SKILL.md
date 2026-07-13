---
name: ecc-refactor-clean
description: Codex adaptation of ECC `/refactor-clean`. Codex adaptation of ECC /refactor-clean.
---

# ecc-refactor-clean

Use this skill when the user is asking for the ECC `/refactor-clean` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/refactor-clean` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `repo-scan`
- `verification-loop`
- `coding-standards`

## Workflow

1. Restate the user's goal in the language of the `/refactor-clean` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

- `npx package`: This flow may rely on an external package; confirm the runtime/tool exists before execution.

## Upstream Source

- Command file: `refactor-clean.md`
- Original description: Codex adaptation of ECC /refactor-clean.
