---
name: department-plugin-bundles
description: "Package related ECC skills and connector checks into department-style bundles for design, launch, security, research, investor, and operations workflows."
origin: ECC
---

# Department Plugin Bundles

Use this skill when a user wants packaged workflow suites rather than isolated skills.

## Activation

Use when the user asks for:
- bundles, packs, departments, teams, or role-based workflows
- a design department, launch department, research department, security department, investor department, or operations department
- reusable workflow groupings for Codex, Windsurf, Antigravity, Cursor, or Claude-style environments

## Operating Rules

- Bundles are curated routes, not proof that every connector is installed.
- Each bundle must list required skills, optional connectors, verification gates, and output artifacts.
- Keep bundles small enough to execute. Avoid "everything" bundles that hide responsibility.
- Use `connector-skill-composer` when a connector is a core part of the bundle.

## Bundle Template

```md
Bundle:
- Name:
- Purpose:
- Trigger examples:
- Core skills:
- Optional connectors:
- Required proof:
- Stop gates:
- Output artifacts:
- Install module:
```

## Starter Bundles

| Bundle | Core route | Use |
|---|---|---|
| Design Ops | `interactive-design-ops`, `frontend-patterns`, `browser-qa` | UI redesign and visual QA |
| Release Proof | `conformance-gate`, `verification-loop`, `e2e-testing` | Release readiness and proof boundaries |
| Performance Lab | `perf-ratchet`, `benchmark`, `agent-phase-ratchet` | Before/after performance claims |
| Research Scout | `marketplace-scout`, `deep-research`, `safe-plugin-importer` | Plugin and external ecosystem research |
| Second Brain | `notion-style-second-brain`, `scheduled-briefing-pack`, `conformance-gate` | Durable project memory and recurring proof packs |
| Security Gate | `security-review`, `security-scan`, `safe-plugin-importer` | Supply-chain and code security checks |

## Handoff

Return a table with:
- bundle name
- included skills
- optional tools to verify
- example syntax
- proof command or artifact
- residual risk
