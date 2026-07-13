---
name: ecc-instinct-status
description: Codex adaptation of ECC `/instinct-status`. Show learned instincts (project + global) with confidence
---

# ecc-instinct-status

Use this skill when the user is asking for the ECC `/instinct-status` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/instinct-status` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `continuous-learning-v2`

## Workflow

1. Restate the user's goal in the language of the `/instinct-status` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

- None for the baseline guidance path.

## Upstream Source

- Command file: `instinct-status.md`
- Original description: Show learned instincts (project + global) with confidence
