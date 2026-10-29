---
name: ecc-verify
description: "Use when the user asks for the ECC /verify workflow inside Codex; adapts the upstream Claude command using verification-loop, security-review, and eval-harness as advisory tools."
---

# ecc-verify

Use this skill when the user is asking for the ECC `/verify` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/verify` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

- `verification-loop`
- `security-review`
- `eval-harness`

## Workflow

1. Restate the user's goal in the language of the `/verify` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

- None for the baseline guidance path.

## Auto-Revocation

Backing skills (`verification-loop`, `security-review`, `eval-harness`) are
**Advisory tools** — if unavailable, the skill degrades to baseline guidance.

### Tool Taxonomy

| Class | Tool | Gating Behavior |
|-------|------|----------------|
| **Core** | `git`, `cat`, `grep`, `diff` | Never gate — used for artifact inspection |
| **Advisory** | `verification-loop` | Skill availability check. If absent: skip silently, fall back to manual verification checklist. Wrap with `2>/dev/null` and `\|\| true`. |
| **Advisory** | `security-review` | Skill availability check. If absent: skip silently, fall back to `ecc-owasp-security` or manual security checklist. |
| **Advisory** | `eval-harness` | Skill availability check. If absent: skip silently, fall back to manual eval guidance. |
| **Advisory** | `pytest`, `cargo`, `npm test` | `command -v <tool>` check. If absent: report limitation, offer manual command. |

### Degradation Path

1. All backing skills available → full verification workflow with automated checks
2. Some backing skills available → partial verification, flag which phases were automated vs manual
3. No backing skills available → baseline guidance path only (manual checklist)
4. Never claim verification passed without command evidence

## Cross-IDE Compatibility

Pure markdown skill — no runtime dependencies:
- **Windsurf**: SKILL.md auto-discovered, uses native verification workflow
- **Devin**: SKILL.md injected as context, manual verification steps
- **Autogravity**: SKILL.md read as agent capability
- **Codex**: `agents/openai.yaml` provides agent definition

## Upstream Source

- Command file: `verify.md`
- Original description: Codex adaptation of ECC /verify.
