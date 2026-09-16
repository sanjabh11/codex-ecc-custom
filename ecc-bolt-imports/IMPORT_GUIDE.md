# ECC to Bolt Skills Library — Import Guide

One-time setup to make your ECC skills auto-invoke in every Bolt project.
Skills auto-trigger when your prompt matches their description, or force one
with `/skill-name` in the chatbox.

All 19 skills are packaged as ready-to-import `.zip` files in the `zips/`
subfolder (one skill per zip, each zip contains a single `SKILL.md` with
valid frontmatter, all well under the 2 MB limit). Import each zip in one
shot — no copy-pasting.

Steps per skill:
1. Bolt -> account dropdown -> Settings -> Skills library (or the project's
   gear icon -> Skills)
2. Add skill -> Import from file
3. Drag the `.zip` from `ecc-bolt-imports/zips/` into the drop zone -> Import

Full list (19 zips in `zips/`):
agent-architecture-audit, agent-phase-ratchet, benchmark,
benchmark-optimization-loop, browser-qa, codebase-onboarding, coding-judgment,
conformance-gate, deep-research, dynamic-workflow-backlog, e2e-testing,
ecc-advisor, ecc-guide, ecc-prompt-optimize, ecc-role-catalog, fuzz-regression,
prompt-optimizer, token-budget-advisor, workflow-audit-router

Sourcing note: 9 of these were downloaded today from the public
`affaan-m/ECC` repo; the other 9 were exported from this workspace because
they no longer exist upstream. Behavior is identical either way.
