---
name: agents-md-generator
description: >-
  Generate and maintain AGENTS.md files with engineering doctrine, verification
  ladder, safety rules, branch policy, and spec-first workflow guidelines for
  AI coding agents. Use when setting up a new repo for AI-assisted development
  or upgrading existing agent guidelines.
  TRIGGER when: "AGENTS.md", "agents.md generator", "agent guidelines",
  "AI coding agent rules", "engineering doctrine file", "agent guardrails",
  "repo agent setup", "agent safety rules".
  DO NOT TRIGGER when: task is unrelated to repo setup or agent guidelines.
---

# AGENTS.md Generator

## When to Use

- Setting up a new repo for AI-assisted development
- Upgrading existing agent guidelines (from CLAUDE.md to AGENTS.md or adding one)
- When engineering doctrine needs to be encoded for AI agents
- When safety rules, branch policy, or verification ladders need to be formalized

## AGENTS.md Template

```markdown
# AGENTS.md — [Project Name]

> Guidelines for AI coding agents working in this codebase.

---

## RULE 0 — THE FUNDAMENTAL OVERRIDE PREROGATIVE

If I tell you to do something, even if it goes against what follows below,
YOU MUST LISTEN TO ME. I AM IN CHARGE, NOT YOU.

---

## RULE 1 — NO FILE DELETION

**YOU ARE NEVER ALLOWED TO DELETE A FILE WITHOUT EXPRESS PERMISSION.**
Even a new file that you yourself created. You have permanently lost any
and all rights to determine that a file or folder should be deleted.

**YOU MUST ALWAYS ASK AND RECEIVE CLEAR, WRITTEN PERMISSION BEFORE EVER
DELETING A FILE OR FOLDER OF ANY KIND.**

---

## Irreversible Git & Filesystem Actions — DO NOT EVER BREAK GLASS

1. **Absolutely forbidden commands:** `git reset --hard`, `git clean -fd`,
   `rm -rf`, or any command that can delete or overwrite code/data must never
   be run unless the user explicitly provides the exact command and states
   they understand the irreversible consequences.
2. **No guessing:** If there is any uncertainty, stop and ask.
3. **Safer alternatives first:** Use non-destructive options (`git status`,
   `git diff`, `git stash`, backups) before considering destructive commands.
4. **Mandatory explicit plan:** Restate the command verbatim, list what will
   be affected, and wait for confirmation.
5. **Document the confirmation:** Record the exact user text that authorized it.

---

## Branch Policy

- Primary branch is `main`.
- Do not reference `master` in docs/scripts.
- Create feature branches from `main` with descriptive names.

---

## Project Mission

[One paragraph: what we're building and why]

---

## Spec-First Workflow

Implementation follows the plan, not ad-hoc invention. Read in this order:
1. [Link to comprehensive plan or architecture doc]
2. [Link to invariant registry or invariants.toml]
3. [Link to on-disk format specs, API contracts, protocol definitions]

**Hard rule: no subsystem ships against an unenforced invariant.**

---

## Engineering Doctrine

[List non-negotiable rules. Example:]

1. **The dependency universe is closed.** Allowed: [list]. Everything else
   is built in-house.
2. **Memory safety is structural.** [unsafe policy]
3. **Determinism by default.** Same input + same query + same policy = same output.
4. **Simulation-first.** The entire system runs under a lab runtime in testing.
5. **Spec-first.** Read the plan before writing code.

Violating any doctrine rule is a revert, memorialized in `docs/NEGATIVE_EVIDENCE.md`.

---

## Verification Ladder

1. **Simulation-first:** Virtual time, DPOR, chaos injection, seed-replayable failures.
2. **Reference oracle:** Deliberately simple, obviously-correct reference for
   differential testing.
3. **Consistency oracles:** SI/SSI history checking, Elle-class validation.
4. **Formal anchors (scoped, honest):** Lean proves invariants; TLA+/TLC
   models protocols. Every load-bearing invariant has a stable ID in
   `invariants.toml` with a live checker.
5. **Plan certificates:** Every result is an auditable, replayable artifact.
6. **Complexity witnesses:** Observed op-count vs. declared bound. Regression
   locks fail CI.

---

## Testing Requirements

- All PRs must pass: [list CI checks]
- Test coverage minimum: [percentage]%
- New features require: [unit tests, integration tests, property tests]
- Bug fixes require: [regression test that would have caught the bug]
```

## Generation Steps

1. **Analyze the repo:** Read existing docs, README, CI config, test structure
2. **Identify doctrine:** What are the non-negotiable rules for this project?
3. **Identify invariants:** What must always be true? (Use `invariant-registry` skill)
4. **Identify verification approach:** What testing strategies are used?
5. **Generate AGENTS.md** from the template above, filled with project-specific content
6. **Review with user:** Present the generated file for approval
7. **Write to repo root:** `AGENTS.md` at the repository root

## AGENTS.md vs. CLAUDE.md

| File | Purpose | Audience |
|---|---|---|
| `AGENTS.md` | Engineering doctrine, safety rules, verification ladder | All AI coding agents (Claude, Codex, Cursor, etc.) |
| `CLAUDE.md` | Claude-specific instructions, tool preferences | Claude Code specifically |
| `.cursorrules` | Cursor-specific rules | Cursor IDE |

**Recommendation:** Generate AGENTS.md as the universal doctrine file. Keep CLAUDE.md for Claude-specific tooling. AGENTS.md is the source of truth; CLAUDE.md references it.

## Integration with ECC

- Use with `codebase-onboarding` — AGENTS.md generation is part of repo onboarding
- Use with `invariant-registry` — invariants referenced in AGENTS.md come from the registry
- Use with `spec-first-doctrine` — the spec-first workflow section comes from this skill
- Use with `deterministic-simulation-testing` — the verification ladder references DST
- Use with `safety-guard` — safety rules in AGENTS.md enforce safety-guard behavior

## Maintenance

- **Update on doctrine changes:** When engineering rules change, update AGENTS.md
- **Version control:** AGENTS.md is committed and reviewed like any other file
- **Negative evidence:** When rules are violated, record in `docs/NEGATIVE_EVIDENCE.md`
- **Periodic audit:** Review AGENTS.md quarterly to ensure it matches actual practices
