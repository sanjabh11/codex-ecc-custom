---
name: role-plugin-builder
description: Turn a role, job, department, or repeated workflow brief into a narrow Codex plugin scaffold contract, using ECC routing, connector truth checks, and plugin-creator for any actual scaffold generation.
---

# Role Plugin Builder

Use this skill to convert a role or workflow brief into a Codex plugin plan or scaffold. It is a wrapper, not a replacement for `plugin-creator`: first define the role contract and proof gates, then delegate filesystem scaffolding to the existing system plugin creator only when the user explicitly wants files created.

## When To Activate

- User asks to turn a role, job, department, workflow, or operating process into a Codex plugin.
- User asks for a role plugin scaffold, OpenAI-style plugin scaffold, or plugin package for Codex workflows.
- User wants a reusable plugin from existing ECC skills, connectors, prompts, hooks, or templates.
- User provides an external role-plugin idea and asks whether or how to adapt it.

## Core Route

1. Route first with `workflow-audit-router`.
   - Classify the request and keep the smallest effective workflow.
   - Use normal PhaseLoop unless the dynamic workflow dry-run recommends a backlog.
2. Decide the customization type with `plugin-customizer`.
   - Prefer `wrapper` or `narrow skill` over a large plugin.
   - Use a full plugin only when the user needs installable Codex plugin packaging.
3. Compose role capabilities with `connector-skill-composer`.
   - List required skills and optional connectors.
   - Verify every connector/tool as `installed`, `exposed`, `healthy`, `planned`, or `unavailable`.
4. Use `department-plugin-bundles` only when the role is really a department bundle.
   - Keep the bundle small enough to execute.
   - Reject vague "everything" bundles by narrowing to one role, department, or workflow family.
5. Use `safe-plugin-importer` for external templates or marketplace ideas.
   - Inspect provenance and risk without executing remote code.
   - Adapt useful behavior; do not copy third-party plugin text wholesale.
6. Use `plugin-creator` only for actual scaffold generation.
   - System skill path: `/Users/sanjayb/.codex/skills/.system/plugin-creator/`.
   - Do not recreate scaffold scripts inside this skill.

## Operating Rules

- Produce a scaffold contract before writing plugin files unless the user already gave an explicit implementation request.
- Do not claim `.app.json`, `.mcp.json`, hooks, MCP servers, or connectors are usable unless verified in the current session.
- Do not create hooks, background automation, destructive commands, MCP servers, or credential-bearing configs by default.
- Do not leave placeholder app IDs, fake connector names, secrets, tokens, or personal absolute paths in generated plugin output.
- Mark unavailable connectors as `planned` or remove them from the scaffold.
- Do not mutate the Everything Claude Code plugin cache in v1; create global user skills or personal plugin scaffolds unless the user explicitly asks for ECC packaging.
- Preserve source attribution when adapting official or third-party role templates.

## Output Contract

For contract-only work, read `references/scaffold-contract.md` and return the completed scaffold contract.

For scaffold-generation work:

1. Complete the scaffold contract first.
2. Normalize the plugin name to lower-case hyphen-case, at most 64 characters.
3. Run `plugin-creator` from its system skill root:

```bash
cd /Users/sanjayb/.codex/skills/.system/plugin-creator
python3 scripts/create_basic_plugin.py <plugin-name> --with-skills --with-assets
```

Add `--with-mcp` or `--with-apps` only when the connector truth table proves those files are warranted. Add `--with-marketplace` only when the user explicitly wants the plugin listed in the personal marketplace.

4. Edit only the generated plugin metadata and skill files needed by the contract.
5. Validate the plugin:

```bash
cd /Users/sanjayb/.codex/skills/.system/plugin-creator
python3 scripts/validate_plugin.py <plugin-path>
```

## Stop Gates

- Stop before installing third-party plugins, global CLIs, hooks, MCP servers, or background automations.
- Stop before storing secrets or credentials in plugin files.
- Stop before destructive commands, force overwrites, or broad marketplace changes.
- Stop if connector verification fails but the scaffold depends on that connector.

## Handoff

Report:

- role plugin name
- generated or proposed path
- included skills and optional connectors
- connector truth table
- validation commands and results
- proof boundaries and residual risks
