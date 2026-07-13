---
name: ecc-docs
description: Codex adaptation of ECC `/docs`. Look up current documentation for a library or topic via Context7.
---

# ecc-docs

Use this skill when the user is asking for the ECC `/docs` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/docs` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `documentation-lookup`
- `search-first`

## Workflow

1. Restate the user's goal in the language of the `/docs` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

- `Context7`: If Context7 MCP is unavailable, answer from local knowledge and mark API/library details as potentially stale.

## Upstream Source

- Command file: `docs.md`
- Original description: Look up current documentation for a library or topic via Context7.
