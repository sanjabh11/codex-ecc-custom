---
name: ecc-build-fix
description: "Use when the user asks for the ECC /build-fix workflow inside Codex; adapts the upstream Claude command using verification-loop and search-first, with an npx dependency check."
---

# ecc-build-fix

Use this skill when the user is asking for the ECC `/build-fix` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/build-fix` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `verification-loop`
- `search-first`

## Workflow

1. Restate the user's goal in the language of the `/build-fix` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

### Workflow tools (required — fail loud if missing):
- `npx`: `command -v npx >/dev/null 2>&1 || { echo 'npx not found — cannot complete. Install: npm install -g npx'; return 1; }`

If a workflow tool is missing, report the limitation — do NOT silently succeed.

## Upstream Source

- Command file: `build-fix.md`
- Original description: Codex adaptation of ECC /build-fix.
