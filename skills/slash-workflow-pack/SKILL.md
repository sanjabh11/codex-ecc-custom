---
name: slash-workflow-pack
description: "Convert repeated user workflows into slash-style reusable command recipes without claiming platform slash-command support unless verified."
origin: ECC
---

# Slash Workflow Pack

Use this skill to package repeated work into compact slash-style workflows such as `/release-gate`, `/design-qa`, `/proof-pack`, `/repo-audit`, or `/morning-brief`.

## Activation

Use when the user asks to:
- create a repeatable command, workflow, pack, or shortcut
- standardize a recurring Codex/ECC process
- port a Claude plugin command pattern into Codex, Windsurf, Antigravity, Cursor, or another agent surface
- reduce a long prompt into a reusable recipe

## Tool-Truth Rule

Slash-style names are portable labels unless the current platform exposes native slash-command registration. Do not claim a real slash command was installed unless the target runtime has a verified command manifest or equivalent hook.

## Workflow

1. Identify repeatability:
   - task trigger
   - required inputs
   - optional inputs
   - expected output artifact
   - proof commands
2. Choose packaging level:
   - `prompt recipe`: documented invocation only
   - `skill`: reusable `SKILL.md`
   - `command manifest`: only where the platform supports commands
   - `automation`: only when recurring execution is explicitly requested and tooling is exposed
3. Define the route:
   - selected ECC skills
   - connectors/tools that must be verified per session
   - stop gates and approval requirements
4. Add acceptance criteria:
   - what evidence proves completion
   - what failure requires stop-and-ask
   - what data must never be persisted
5. Install or document:
   - use `plugin-customizer` when narrowing an existing skill
   - use `connector-skill-composer` when connectors and skills are paired
   - use `safe-plugin-importer` before adopting external plugin code

## Slash-Style Recipe Template

```md
Name: /workflow-name
Purpose:
Inputs:
Route:
Tools to verify:
Steps:
Checks:
Stop gates:
Output:
```

## Starter Workflows

| Slash-style workflow | Purpose | Typical route |
|---|---|---|
| `/design-qa` | Verify a local UI change visually and functionally | `interactive-design-ops` + `browser-qa` |
| `/release-gate` | Build/test/proof-boundary gate before release | `conformance-gate` + `verification-loop` |
| `/perf-claim` | Prove a speed or memory claim | `perf-ratchet` + benchmark command |
| `/proof-pack` | Produce an evidence-backed status pack | `workflow-audit-router` + `conformance-gate` |
| `/plugin-scout` | Rank plugin candidates safely | `marketplace-scout` + `safe-plugin-importer` |
