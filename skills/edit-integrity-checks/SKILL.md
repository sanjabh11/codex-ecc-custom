---
name: edit-integrity-checks
description: Verify every structural file edit landed correctly before continuing — edit tools can report success on garbled mid-stream payloads. Use when making multi-line edits, extracting functions, or after any non-trivial edit in a long session.
---

# Edit Integrity Checks

Lessons promoted from LEARNINGS.md (R9–R11 rounds, Sep 2026).

## Rules

- After every structural edit, immediately `ast.parse` the file (or re-read the edited region) before continuing — `edit`/`write` calls have reported "made 1 replacement" on garbled mid-stream payloads (merged bullets, corrupted indentation).
- Never trust the success line alone; the verification is the parse/read, not the tool's report.
- For indentation surgery, prefer a scripted rewrite of the whole function over partial old_string/new_string edits.
