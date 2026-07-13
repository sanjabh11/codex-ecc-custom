---
name: ecc-learn-eval
description: Codex adaptation of ECC `/learn-eval`. Extract reusable patterns from the session, self-evaluate quality before saving, and determine the right save location (Global vs Project).
---

# ecc-learn-eval

Use this skill when the user is asking for the ECC `/learn-eval` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/learn-eval` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `continuous-learning-v2`
- `skill-stocktake`

## Workflow

1. Restate the user's goal in the language of the `/learn-eval` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

- None for the baseline guidance path.

## Upstream Source

- Command file: `learn-eval.md`
- Original description: Extract reusable patterns from the session, self-evaluate quality before saving, and determine the right save location (Global vs Project).
