---
name: manager-loop
description: >
  Run Matt Shumer's Manager Loop — a two-session multi-agent pattern for
  long-horizon goals (hours to days+). A Manager session interviews the human,
  builds a massive phased checklist, then assigns phases one at a time to a
  completely separate Implementer session (never a sub-agent), reviews evidence,
  and advances the project until every phase is done. Use when a goal is too big
  for one pass and a single agent would asymptote into details: large builds,
  world-building, multi-component systems, content pipelines, research programs.
  Triggers: "manager loop", "manager-loop", "coordinator implementer",
  "two-agent setup", "run a project with agents", "keep an agent working for
  days", "phased autonomous build", "/manager-loop", "$manager-loop". DO NOT
  trigger for single-session tasks, or when only an iterative quality/critic
  loop against a reference bar is needed — that is gauntlet-loop.
metadata:
  source: "Matt Shumer — Manager Loop, GPT-6 Astra review (somethingbig.ai/astra-review, Sep 2026) + accompanying implementation doc"
  version: 1.0.0
---

# Manager Loop

Separate planning/oversight from execution so a project keeps making forward
progress instead of asymptoting into details. One agent runs the project;
another agent does the work.

## Boundary (read first — prevents router confusion)

| If the user wants… | Use |
|---|---|
| Phased execution governance across two sessions | **this skill** |
| Iterative quality ratchet against an external reference bar | `gauntlet-loop` |
| A one-line goal turned into a written multi-session construction plan | `blueprint` |
| Generic decomposition + verification supervision | `multi-agent-swarm` |
| Long-running Codex `/goal` governance and drift control | `long-goal-governor` |
| Designing or reviewing a loop for failure modes | `loop-design-check` |
| The ECC `/orchestrate` workflow inside Codex | `ecc-orchestrate` |

Skill names in this table come from the user's wider ECC catalog. If a named
skill is not loaded on the current host, do not route to it — treat the task as
"not this skill" or ask the human, rather than inventing an invocation.

## Purpose

Turn one high-level request into sustained multi-phase progress. The Manager
owns the plan; the Implementer owns the current phase; a shared progress page
owns the audit trail.

## When to Use

- Ambitious multi-day or multi-hour builds a single agent would plateau on
- World-building, large refactors, multi-component systems, content pipelines
- Goals that decompose into substantial sequential or semi-parallel phases
- The human wants to supervise by exception — check a progress page, not steer
- The Implementer may need to fan out sub-agents inside a phase

## When NOT to Use

- Ordinary day-to-day tasks — use a single agent or a simple loop instead
- Work that cannot be decomposed into verifiable phases
- Tasks where the real problem is output quality vs a reference bar
  (`gauntlet-loop`), not phase coordination
- Environments where a second independent session is impossible AND degraded
  single-session mode (below) is unacceptable

## Prerequisites (harness capability check — do this first)

The pattern is harness-agnostic. Before starting, map each primitive to what
the current host actually exposes; never claim a mechanism the host lacks.

| Pattern primitive | What to check for | Degraded fallback |
|---|---|---|
| Second independent session | Host can spawn/run another full agent session (Devin sessions, Codex sessions/threads, Antigravity agents). Must NOT be a sub-agent of the Manager. | Degraded single-session mode (protocol below). Weaker but functional — say so to the human. |
| Inter-agent messaging | Host session-linking, shared workbench doc, or a shared file both sessions read/write. | The checklist/progress file IS the channel. |
| Persistent goal mode | Codex `/goal`, Devin goal mode, or equivalent "keep working until done" directive. | Restate the phase goal + stop conditions in each assignment message; enforce via the checklist. |
| Sub-agent fan-out | Implementer can spawn its own helpers for parallel scoped work. | Serial fresh-context passes inside the phase. |
| Shared progress artifact | Live HTML page, workbench.md doc, or a Markdown checklist both sides can update. | Non-negotiable — if nothing writable+readable is shared, do not start. |
| Reasoning effort | Raise effort/concurrency limits where the host allows (Shumer ran 16–96 sub-agents; start small). | Default limits; encourage delegation explicitly. |

### Degraded single-session protocol (only when no second session is possible)

Announce to the human that the run is degraded, then enforce separation
inside one agent:

1. Maintain two named roles in the checklist file header: `MANAGER:` and
   `IMPLEMENTER:`. The file is the ONLY channel — no role may "remember" for
   the other; each reads the file at turn start and appends at turn end.
2. Take strict alternating turns. A Manager turn may only: read the file,
   write/approve checklist or phase changes, and write the next assignment.
   An Implementer turn may only: read the file, work the current phase, and
   append results + evidence links. Never blend planning and execution in
   one turn.
3. Between role switches, compact or start a fresh context if the host
   allows; if not, explicitly re-read the checklist file as the Implementer
   and ignore Manager-side reasoning.
4. All phase gates still apply: no advancement without evidence written to
   the file first.

## Full Workflow / Instructions

### Phase 0 — Setup & goal alignment (human + Manager)

1. Launch the **Manager** (coordinator) in its own session.
2. The Manager interviews the human: overall goal, constraints, success
   criteria, house rules, tools/credentials available, non-negotiables. It asks
   the clarifying questions a good project manager would ask before planning.
   For interfaces, have it produce mockups and refine those before building.
3. Instruct the Manager: *"Build a massive, detailed checklist of every to-do
   required to fully achieve the goal. Then break that checklist into clear
   sequential or semi-parallel phases. Make phases substantial but
   completable."*
4. Human reviews and approves the checklist + phases. This is the living plan.
   A misunderstanding here becomes a lot of unwanted work — do not rush it.

**Exit gate:** a written, approved phased checklist both agents can reference.

### Phase 1 — Spawn the Implementer

1. Start a second, completely separate session: the **Implementer**. It is not
   a sub-agent of the Manager — independence is the point.
2. Establish the messaging channel (host messaging, or the shared artifact).
3. Give the Implementer the same tools, files, and the shared checklist.
4. Optionally raise the Implementer's sub-agent limit so it can fan out inside
   a phase — and explicitly encourage delegation; raising the limit alone does
   not mean it will be used.

**Exit gate:** two independent sessions running, able to communicate, both
holding the checklist.

### Phase 2 — Activate the loop

1. Put the Manager into goal/persistent mode where the host supports it.
2. Give the Manager its standing job: *"Run the project by assigning one phase
   at a time to the Implementer. For each phase, send a clear goal directive,
   wait for completion plus evidence, review it, then advance. Keep the project
   moving until every phase is done."*
3. Assignment language that works: *"Complete phase one completely, extremely
   well."* — "extremely well" outperforms "perfectly" (it permits forward
   motion once quality is high enough).
4. The Implementer works the assigned phase only. It does not stop until that
   phase's checklist items are done and verified, and it reports completion
   plus evidence back.
5. The Implementer maintains the **live progress page**: full checklist, ticked
   boxes, a progress counter or graph, and links to evidence (screenshots, test
   results, diffs). The Manager and the human inspect this independently.
6. Keep Manager→Implementer handoff prompts minimal. The phase goal plus where
   to find the checklist is enough — over-detailed instructions steer the work
   somewhere unintended.

**Exit gate:** Manager is actively assigning; phase one is underway; the
progress page is live and updating.

### Phase 3 — Autonomous execution & monitoring

1. Let the agents run. The Manager assigns the next phase only after receiving
   completion evidence for the current one — evidence, not vibes.
2. Inside a phase, the Implementer may spawn sub-agents for parallel scoped
   work.
3. The human watches the progress page and intervenes only when truly blocked
   or to adjust direction.
4. Optional hardening:
   - Fresh Implementer per phase + a written handoff (fights context growth).
   - Let the Implementer propose plan changes; the Manager decides whether to
     accept. The checklist stays the plan of record.
   - Inject a `gauntlet-loop` critic inside phases that need a quality bar.
5. Anti-stall rule: *"If you have not ticked a box in the window the human
   set (default 20 minutes of wall time — confirm it in Phase 0), reassess
   and move forward or escalate."*

**Exit gate:** all phases complete and final evidence reviewed, or the human
stops the loop.

### Runtime shape

```
Human ↔ Manager session (planning + oversight)
          │  phase assignment + goal directive
          ▼
Implementer session (execution) ──► sub-agents (optional)
          │  completion + evidence + updated progress page
          ▼
Manager reviews → advances or requests fixes → next phase
```

## Key Phrases & Commands

- Plan request: *"Build a massive, detailed checklist of every to-do required
  to fully achieve the goal. Then break that checklist into clear sequential or
  semi-parallel phases. Make phases substantial but completable."*
- Phase assignment: *"Complete phase N completely, extremely well."* (delivered
  via goal mode where the host has it — e.g. Codex `/goal` — or as the standing
  directive otherwise)
- Standing Manager job: *"Assign one phase at a time. Wait for completion plus
  evidence. Review. Advance. Keep the project moving."*
- Progress page instruction: *"Maintain and update a live HTML checklist page
  showing every item, completion status, and supporting evidence."*
- Anti-stall: *"If you have not ticked a box in X amount of time, reassess and
  move forward or escalate."*

## Progress & Audit Requirements

- A shared live page (HTML, workbench.md doc, or Markdown checklist) showing:
  every checklist item, its status, a progress counter/graph, and evidence.
- Evidence = something inspectable: test output, screenshots, rendered
  artifacts, file diffs — never a summary paragraph alone.
- The progress page is non-negotiable. It is how the human supervises without
  interrupting, and how the Manager reviews without trusting the Implementer's
  self-report.
- Never write secrets, credentials, tokens, or private session data into the
  progress page or checklist. Use the host's secret/credential mechanism; the
  page holds only non-sensitive status, links, and evidence.
- Staleness check: each Manager review confirms the page's last-updated time
  is recent. A page that stopped updating while work claims to continue is a
  red flag, not proof.
- Clear credentials, budgets, and routine permissions up front (as a stated
  dollar/token ceiling and an approval policy, not stored secrets) so agents
  do not stall asking for routine approvals — and so the loop stops when the
  ceiling is hit, not when it is exceeded silently.

## Quality Gates & Verification

- Do not advance past Phase 0 without an approved written checklist.
- Do not advance a phase without completion evidence the Manager independently
  reviewed on the progress page or in the artifacts.
- The Implementer never self-certifies a phase "done" without verification
  artifacts attached.
- If a phase cannot be completed after reasonable effort, the Manager
  escalates to the human with the current evidence — it never advances on a
  fabricated or partial "done," and never silently re-scopes the checklist.
- Do not finish the loop until every checklist item is ticked with linked
  evidence, or the human explicitly stops it.

## Common Failure Modes & Mitigations

| Failure | Mitigation |
|---|---|
| Plan goes stale as reality diverges | Implementer may propose changes; Manager decides; checklist updated in writing |
| Implementer context bloat over long phases | Fresh Implementer per phase + written handoff; or aggressive compaction of prior traces |
| Manager or Implementer drift | Strict phase isolation; the shared progress page both sides read; restate the phase goal |
| Over-detailed Manager handoffs | Tell the Manager to keep assignment prompts minimal — phase goal + checklist pointer |
| Asymptoting inside a phase | "Completely, extremely well" language + time-boxed stall rule; optional gauntlet-loop critic inside the phase |
| Implementer spawned as a sub-agent | It loses independence and context — always a separate session |
| Cost explosion | Start with few sub-agents and medium effort; reserve high concurrency/max effort for critical phases; state a dollar/token ceiling up front and check it against the progress page at each phase gate |
| No visibility into a long run | The live progress page — without it the pattern has no audit trail |
| Implementer reports "done" with no artifacts | Reject the report; evidence (test output, render, diff) is the gate — a summary is not evidence |
| Progress page stops updating mid-phase | Treat as a stall: apply the anti-stall rule or pause and ask the human before continuing |
| Two phases edit the same files (semi-parallel work) | Give each phase file/module ownership, or serialize the colliding phases — do not let two workers race on one file |
| Session crashes mid-phase | The checklist file + progress page is the resume point; a fresh Implementer (or Manager) picks up from written state, never from memory |
| Human is absent when a decision is needed | Stop and wait on genuinely blocking choices; do not guess on direction or scope |

## Example Invocation

- `$manager-loop` (or `/manager-loop` on hosts with slash syntax)
- Natural language: "Use the manager-loop skill. Run a coordinator + separate
  implementer to build a full New York City simulation — interview me first,
  produce the phased checklist, then run it phase by phase."

## Notes

- Pattern credit: Matt Shumer (@mattshumer_) — described in the GPT-6 Astra
  review (somethingbig.ai/astra-review) and X posts, September 2026.
- Shumer used this to build a simulated civilization and a GTA-style New York
  build in Unreal; large experiments consumed enormous token volume — warn the
  human about cost before high-concurrency runs.
- The two skills compose: `manager-loop` governs *when* work happens;
  `gauntlet-loop` governs *how good* a piece must get. A Manager may assign a
  gauntlet loop inside a phase.
- For visual/creative pieces inside a phase, recommend the host's strongest
  model and highest reasoning effort ("ultracode" where it exists).
- Primary-source detail behind this skill: `references/source-notes.md`.

## Cross-IDE Compatibility

Pure markdown skill — no runtime dependencies:

- **Devin**: discovered via `~/.config/devin/skills` symlink; sessions and
  goal mode map to the two-session pattern.
- **Antigravity**: discovered via `~/.agents/skills` symlink; agent
  sessions map to the two-session pattern.
- **Codex**: discovered via `~/.codex/skills` symlink; `agents/openai.yaml`
  supplies implicit invocation and `$manager-loop`; sessions/threads map to
  the two-session pattern.
- **Claude Code**: discovered via `~/.claude/skills` symlink; separate
  sessions map to the pattern.
- **Windsurf / Codeium**: discovered via `~/.windsurf/skills` and
  `~/.codeium/windsurf/skills` symlinks.
- Any host lacking multi-session support falls back to the degraded
  single-session protocol above — degraded, never silent.

## Auto-Revocation

- Revocation = remove the discovery symlinks; the canonical copy here is
  version-controlled and is never auto-deleted.
- `~/bin/skill-revoke.sh` removes the symlinks automatically; the repo
  directory is reported as canonical and skipped, not deleted.
- Do not `rm -rf` the canonical directory.

## How to Install

Canonical copy lives in this repository (`skills/manager-loop/`). Link it
onto each host's skill surface — run from the repository root:

```bash
REPO=$(git rev-parse --show-toplevel)
for d in ~/.config/devin/skills ~/.agents/skills ~/.codex/skills \
         ~/.claude/skills ~/.windsurf/skills ~/.codeium/windsurf/skills; do
  [ -d "$d" ] && ln -sfn "$REPO/skills/manager-loop" "$d/manager-loop"
done
```

Uninstall (remove links on every surface, keep the canonical copy):

```bash
for d in ~/.config/devin/skills ~/.agents/skills ~/.codex/skills \
         ~/.claude/skills ~/.windsurf/skills ~/.codeium/windsurf/skills; do
  rm -f "$d/manager-loop"
done
```

`~/bin/skill-revoke.sh manager-loop` does the same thing and is the
preferred path. Do not `rm -rf` the canonical directory.
