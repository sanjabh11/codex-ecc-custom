---
name: ecc-resume-session
description: Codex adaptation of ECC `/resume-session`. Load the most recent session file from ~/.claude/session-data/ and resume work with full context from where the last session ended.
---

# ecc-resume-session

Use this skill when the user is asking for the ECC `/resume-session` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/resume-session` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `iterative-retrieval`
- `strategic-compact`

## Workflow

1. Restate the user's goal in the language of the `/resume-session` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

- None for the baseline guidance path.

## Upstream Source

- Command file: `resume-session.md`
- Original description: Load the most recent session file from ~/.claude/session-data/ and resume work with full context from where the last session ended.
