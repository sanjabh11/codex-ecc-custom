---
name: ecc-integrations-catalog
description: Inventory of ECC integrations, MCP servers, external runtimes, and service dependencies for the Codex adaptation layer.
---

# ecc-integrations-catalog

Use this skill when the user asks which integrations are required, optional, or unavailable for the ECC Codex adaptation layer.

## GitHub MCP

- Required for: repo inspection, PR review, ADR work, repo-scan, security-review
- Optional for: deep research cross-checking, skill-create validation
- Notes: Configure via @modelcontextprotocol/server-github and set GITHUB_PERSONAL_ACCESS_TOKEN.
## Context7 MCP

- Required for: docs lookup, API verification, search-first
- Optional for: framework planning, refactoring with live docs
- Notes: Configure via @upstash/context7-mcp@latest.
## Exa MCP

- Required for: broad research, market/investor workflows, many adapted commands
- Optional for: generic planning or review when local context is sufficient
- Notes: Configure EXA_API_KEY if you want the full research-oriented ECC surfaces.
## Playwright MCP

- Required for: e2e, browser-qa, e2e-runner
- Optional for: codebase onboarding, visual regression checks
- Notes: Configured in upstream .mcp.json and .codex/config.toml.
## Memory MCP

- Required for: None
- Optional for: persistent memory, long-running session continuity
- Notes: Useful but not required for the baseline adaptation.
## Sequential Thinking MCP

- Required for: None
- Optional for: structured planning, debugging, deep analysis
- Notes: Keep available for high-complexity work; not required for every flow.
## Firecrawl MCP

- Required for: None
- Optional for: deep-research, exa-search
- Notes: Improves crawl-heavy workflows when enabled.
## AgentShield

- Required for: None
- Optional for: security-scan, plankton-code-quality
- Notes: Install with npx ecc-agentshield or wire its GitHub Action for CI.
## ccg-workflow

- Required for: multi-plan, multi-execute, multi-backend, multi-frontend, multi-workflow
- Optional for: None
- Notes: Initialize with npx ccg-workflow; without it, multi-* wrappers must stay guidance-only.
## PM2

- Required for: None
- Optional for: pm2, enterprise-agent-ops, long-running loop supervision
- Notes: Needed only for process-management workflows.
## DevFleet

- Required for: None
- Optional for: parallel worktree orchestration
- Notes: Use when you want the devfleet workflow available beyond tmux/dmux guidance.
## VideoDB

- Required for: None
- Optional for: videodb, video-editing
- Notes: Required for the media-editing branch of ECC.
## fal.ai

- Required for: None
- Optional for: fal-ai-media, video-editing
- Notes: Backs AI image/video/audio generation workflows.
## Nutrient API

- Required for: None
- Optional for: nutrient-document-processing
- Notes: Commercial API; required only for document-processing flows.
## X API

- Required for: None
- Optional for: x-api, crosspost, content-engine, some learning signals
- Notes: Needed only for X/Twitter publishing and analysis flows.
## ClickHouse MCP

- Required for: None
- Optional for: clickhouse-io, analytics-heavy operational skills
- Notes: Enable when you need ClickHouse querying workflows.
## Browserbase

- Required for: None
- Optional for: cloud browser workflows beyond local Playwright
- Notes: Optional advanced browser automation.
## browser-use

- Required for: None
- Optional for: browser agent tasks beyond local Playwright
- Notes: Optional remote browser agent integration.
## Omega Memory

- Required for: None
- Optional for: semantic memory, multi-agent coordination
- Notes: Richer alternative to the basic memory server.
## Skill Creator GitHub App

- Required for: None
- Optional for: skill-create at large repo scale, team sharing, auto-PRs
- Notes: Advanced replacement for the local git-history flow.
