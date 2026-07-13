---
name: ecc-cpp-build
description: Codex adaptation of ECC `/cpp-build`. Fix C++ build errors, CMake issues, and linker problems incrementally. Invokes the cpp-build-resolver agent for minimal, surgical fixes.
---

# ecc-cpp-build

Use this skill when the user is asking for the ECC `/cpp-build` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/cpp-build` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `cpp-coding-standards`
- `cpp-testing`
- `verification-loop`

## Workflow

1. Restate the user's goal in the language of the `/cpp-build` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

- None for the baseline guidance path.

## Upstream Source

- Command file: `cpp-build.md`
- Original description: Fix C++ build errors, CMake issues, and linker problems incrementally. Invokes the cpp-build-resolver agent for minimal, surgical fixes.
