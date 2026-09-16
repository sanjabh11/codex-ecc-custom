---
name: plugin-customizer
description: "Customize broad ECC skills or external plugin ideas into narrower, project-specific, evidence-gated skills and workflow packs."
origin: ECC
---

# Plugin Customizer

Use this skill to turn a broad plugin, skill, or marketplace idea into a scoped workflow that fits the user's actual repositories and tools.

## Activation

Use when the user asks to:
- customize a plugin for their workflow
- convert a marketplace idea into an ECC skill
- make a global workflow usable for Codex, Windsurf, Antigravity, or another platform
- narrow a broad skill for a specific repo, department, stack, or operating protocol

## Safety Rules

- Do not mutate global skills from reflection alone; require explicit user request.
- Inspect the existing skill or plugin before creating a derivative.
- Preserve source attribution when adapting concepts.
- Avoid copying large third-party text or code; rebuild the workflow contract in ECC style.
- Register only after validation passes.

## Workflow

1. Define customization target:
   - source plugin or skill
   - target platform
   - target repo or workflow
   - expected trigger phrases
2. Inspect current capabilities:
   - existing ECC skills
   - platform manifests
   - connector availability
   - current user operating protocol
3. Choose customization type:
   - `alias`: document a usage pattern for an existing skill
   - `wrapper`: compose existing skills with stricter routing
   - `narrow skill`: new `skills/<name>/SKILL.md`
   - `bundle`: install-module grouping or department route
4. Build contract:
   - activation
   - inputs
   - steps
   - tool-truth checks
   - verification gates
   - output template
5. Validate:
   - manifest registration
   - catalog counts
   - no personal absolute paths
   - runtime cache mirror when installed plugin behavior is needed

## Customization Template

```md
Name:
Source:
Target workflow:
Trigger phrases:
Existing skills reused:
New behavior:
Verification:
Install targets:
Rollback:
```

## Example Uses

| Request | Customization |
|---|---|
| "Make this design process global" | Narrow `interactive-design-ops` and register it in the global plugin |
| "Borrow this marketplace plugin safely" | `marketplace-scout` -> `safe-plugin-importer` -> `plugin-customizer` |
| "Make one skill work for Windsurf and Antigravity too" | Add platform-neutral wording and manifest target coverage |
| "Create a department bundle" | `department-plugin-bundles` -> install-module grouping |
