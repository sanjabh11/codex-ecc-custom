---
name: notion-style-second-brain
description: "Maintain project memory, source packs, decision logs, and proof boundaries with optional Notion-style export when a connector is verified."
origin: ECC
---

# Notion-Style Second Brain

Use this skill to turn scattered project knowledge into durable, evidence-backed source packs. It supports Notion-style organization without requiring the Notion connector.

## Activation

Use when the user asks to:
- build or refresh a second brain, knowledge base, or project memory
- organize research, decisions, proofs, and roadmap claims
- preserve source-pack truth across long-running projects
- separate live proof, local proof, artifact-only proof, and roadmap items

## Tool-Truth Rule

Prefer repo-local Markdown/JSON artifacts. Use Notion, Google Docs, or other document connectors only when the connector is exposed and authenticated in the current session.

## Workflow

1. Define knowledge boundary:
   - project or repo
   - time range
   - proof categories
   - target audience
2. Gather evidence:
   - local files and docs
   - commits and issue/task state
   - runtime/deploy checks where relevant
   - current external sources when claims may drift
3. Normalize:
   - decisions
   - assumptions
   - source links
   - proof status
   - risks
   - next actions
4. Store:
   - `docs/source-packs/` or existing repo docs when appropriate
   - memory update note only when the user explicitly asks
   - external document only with verified connector/tooling
5. Handoff:
   - report what is proven, what is inferred, what is stale, and what remains to verify

## Source Pack Schema

```md
# Source Pack: <name>

## Scope
## Current Proof
## Local-Only Proof
## Artifact-Only Claims
## Roadmap Claims
## Decisions
## Risks
## Open Questions
## Verification Commands
## Next Refresh Trigger
```

## Useful Pairings

| Pair with | Why |
|---|---|
| `conformance-gate` | Keeps proof boundaries honest |
| `scheduled-briefing-pack` | Refreshes packs on cadence |
| `marketplace-scout` | Stores ranked plugin/research candidates |
| `connector-skill-composer` | Exports to verified document connectors |
