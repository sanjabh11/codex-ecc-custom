---
name: ecc-cpp-test
description: Codex adaptation of ECC `/cpp-test`. Enforce TDD workflow for C++. Write GoogleTest tests first, then implement. Verify coverage with gcov/lcov.
---

# ecc-cpp-test

Use this skill when the user is asking for the ECC `/cpp-test` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/cpp-test` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `cpp-testing`
- `tdd-workflow`

## Workflow

1. Restate the user's goal in the language of the `/cpp-test` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

### Workflow tools (required — fail loud if missing):
- `gcov`: `command -v gcov >/dev/null 2>&1 || { echo 'gcov not found — cannot complete. Install: brew install gcov lcov'; return 1; }`
- `lcov`: `command -v lcov >/dev/null 2>&1 || { echo 'lcov not found — cannot complete. Install: brew install gcov lcov'; return 1; }`

If a workflow tool is missing, report the limitation — do NOT silently succeed.

## Upstream Source

- Command file: `cpp-test.md`
- Original description: Enforce TDD workflow for C++. Write GoogleTest tests first, then implement. Verify coverage with gcov/lcov.
