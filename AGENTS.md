# AGENTS.md

Instructions for Grok Bot, Cursor cloud agents, Codex, and Claude-compatible agents working in this repository.

## Project mission

This repo is a library of **ECC custom skills** (`skills/<name>/SKILL.md` directories) for **Grok Bot**, **Codex**, and **Claude-compatible** agents.

Work here is about adding, fixing, or documenting individual skills. It is not an application product: do not implement product features unless a later task explicitly asks for them.

## How to work

- **Do not clone this repo onto a user laptop.** Work in the cloud agent environment against this checkout.
- **Ship changes as pull requests via the cloud agent.** Do not apply work only locally and leave it unpushed.
- **Branch off `main`.** Use a short, descriptive branch name. Keep the branch focused on one concern.

## Build, test, and lint

There is **no application test suite** and **no project lint/CI stack** that skill PRs must pass.

Do **not** add a fake CI pipeline, linter config, or generated test harness just to look complete.

For a **skill change**, the skill directory must include a `SKILL.md` that:

1. Starts with YAML frontmatter containing `name` and `description`.
2. Includes a **when-to-use** section (or equivalent opening guidance that states when the agent should load the skill).

That checklist is the validation bar for skill PRs. Do not invent extra build or test steps.

## Do not touch

- **Do not delete skill directories.**
- **Do not rewrite all 100+ skills in one PR.** Change only the skills (or files) needed for the current concern.
- **Leave `.phase-loop` and `.system` alone** (including `skills/.system`). Do not edit, move, or delete them unless a task is explicitly about those paths.

## Pull request workflow

- Prefer **small PRs** with **one concern** each.
- In the PR description, explain **why** the change is needed, not only what files moved.
- Keep diffs reviewable: one skill or one docs/agent-instruction change is better than a bulk rewrite.

## Safety

- **No secrets in skills.** Do not put API keys, tokens, passwords, or private credentials in `SKILL.md` or other skill files.
- **No force-push.**
- **No `git reset --hard`.**
