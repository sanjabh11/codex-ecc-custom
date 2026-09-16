---
name: interactive-design-ops
description: "Run evidence-backed UI redesign work across repo inspection, design-system extraction, browser QA, and optional Figma or local visual tooling."
origin: ECC
---

# Interactive Design Ops

Use this skill for website, dashboard, portal, landing page, design-system, or UX improvement tasks where the result must be implemented and visually verified.

## Activation

Use when the user asks to:
- redesign, improve, polish, or modernize a web UI
- apply a design reference, design.md, Figma file, or visual direction
- verify a local web app with browser screenshots or interaction checks
- convert a one-off design pass into a reusable design workflow

## Operating Rules

- Start with `agent-phase-ratchet` for non-trivial redesign work.
- Use `workflow-audit-router` to pick the minimal skill set.
- Use `frontend-patterns`, `design-system`, `browser-qa`, or `e2e-testing` only when the repo evidence supports them.
- Use Figma, Browser, Chrome, or Computer tools only when exposed in the current session.
- Do not claim visual success from code diff alone; collect runtime or screenshot evidence when a local target is available.
- Preserve existing product information architecture unless the task explicitly includes restructuring.

## Workflow

1. Classify scope:
   - `light polish`: one component, typography, spacing, or color improvement
   - `screen redesign`: one route or dashboard surface
   - `system redesign`: tokens, shared components, navigation, and multiple routes
2. Baseline:
   - inspect repo stack, design tokens, component library, routes, and current browser target
   - capture current screenshots or runtime notes when possible
   - record constraints such as shadcn/ui, Tailwind, framework, accessibility rules, or brand assets
3. Design direction:
   - state visual thesis in 3 to 6 concrete attributes
   - map changes to one acceptance dimension, such as "noir control room dashboard" or "executive proof-pack portal"
   - identify reusable components/tokens before editing leaf screens
4. Implementation:
   - edit the smallest shared surface that produces the intended visual change
   - avoid disconnected one-off styles unless the repo has no reusable layer
   - keep data, auth, and business logic behavior unchanged unless explicitly requested
5. Verification:
   - run build/typecheck/lint where relevant
   - open the local URL with Browser/Chrome when available
   - check responsive behavior, key interactions, contrast risks, and console errors
6. Handoff:
   - include before/after proof, changed files, checks, residual visual risks, and next adjustment

## Output Template

```md
Design route:
- Scope:
- Visual thesis:
- Existing system reused:
- Tools verified:
- Stop gates:

Evidence:
- Baseline:
- Checks:
- Browser/runtime proof:
- Delta:
- Next adjustment:
```

## Routing Examples

| User intent | Route |
|---|---|
| "Improve this dashboard drastically" | `agent-phase-ratchet` -> `interactive-design-ops` -> `browser-qa` |
| "Apply this Figma design" | `interactive-design-ops` -> verified Figma tooling -> `frontend-patterns` |
| "Make it production ready visually" | `interactive-design-ops` -> `conformance-gate` -> `browser-qa` |
| "Use design.md from awesome-design-md" | `interactive-design-ops` -> local design skill or file -> runtime visual proof |
