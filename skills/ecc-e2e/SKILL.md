---
name: ecc-e2e
description: Codex adaptation of ECC `/e2e`. Generate and run end-to-end tests with Playwright. Creates test journeys, runs tests, captures screenshots/videos/traces, and uploads artifacts.
---

# ecc-e2e

Use this skill when the user is asking for the ECC `/e2e` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/e2e` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `e2e-testing`
- `browser-qa`
- `tdd-workflow`

## Workflow

1. Restate the user's goal in the language of the `/e2e` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

- `playwright`: If Playwright MCP or local Playwright tooling is unavailable, stop at test design and explain what runtime is missing.
- `npx package`: This flow may rely on an external package; confirm the runtime/tool exists before execution.

## Upstream Source

- Command file: `e2e.md`
- Original description: Generate and run end-to-end tests with Playwright. Creates test journeys, runs tests, captures screenshots/videos/traces, and uploads artifacts.
