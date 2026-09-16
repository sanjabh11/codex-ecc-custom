---
name: scheduled-briefing-pack
description: "Design and verify recurring status, repo, market, or proof-pack briefings for Codex automation-capable environments."
origin: ECC
---

# Scheduled Briefing Pack

Use this skill when a user wants recurring briefings, scheduled checks, monitors, weekly reports, daily digests, or repeated proof-pack refreshes.

## Activation

Use when the user asks for:
- daily or weekly briefings
- recurring repo health checks
- scheduled market or plugin scouting
- automated status packs
- reminders that include evidence gathering

## Tool-Truth Rule

Only create or update an automation when the current environment exposes an automation tool and the user explicitly asks for recurring execution. Otherwise produce a copy-ready briefing spec.

## Workflow

1. Classify the briefing:
   - `status`: repo, project, milestone, or workstream status
   - `proof`: build/test/deploy/runtime evidence
   - `research`: market, plugin, competitor, or standards watch
   - `ops`: disk, job health, logs, alerts, or queue health
2. Define schedule and destination:
   - cadence
   - timezone
   - output channel
   - workspace or repo roots
   - retention needs
3. Define evidence sources:
   - local commands
   - repo files
   - browser/runtime targets
   - external sources that require current web research
   - connector health checks
4. Define gates:
   - when to warn
   - when to stop and ask
   - what counts as a material regression
5. Produce one of:
   - automation card using the exposed automation tool
   - portable briefing spec
   - repo-local runbook or skill prompt

## Briefing Spec Template

```md
Briefing:
- Name:
- Cadence:
- Timezone:
- Scope:
- Evidence sources:
- Commands:
- Connectors to verify:
- Alert thresholds:
- Output format:
- Retention:
```

## Common Briefings

| Briefing | Use | Evidence |
|---|---|---|
| Daily repo pulse | Morning status of dirty work, tests, blocked work | `git status`, focused tests, issue/task state |
| Weekly proof pack | Evidence-backed product/demo readiness | build/test/browser/deploy proof |
| Plugin marketplace scout | Rank new plugin candidates | current marketplace scan + ECC inventory diff |
| Agent phase audit | Identify unchecked execution drift | `.phase-loop` ledgers + failed checks + next adjustments |
