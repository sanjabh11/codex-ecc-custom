---
name: ecc-fable-loop
description: Run Fable 5 agentic loops on autopilot.
---

# ecc-fable-loop

Use this skill when running repetitive agentic loop tasks on autopilot.

## Purpose

The Fable 5 loop architecture executes a task iteratively, maintaining progress across runs in a dedicated `state file` and stopping when a `stop rule` is met.

## Core Concepts

1. **schedule**: The frequency/cadence when the loop executes (e.g. `weekly`, `daily`, `hourly`).
2. **one change**: The smallest atomic modification or API call made during a single iteration.
3. **state file**: A JSON log storing conversation and run history, preventing context pollution.
4. **stop rule**: The specific evaluation logic (iteration limit, empty check, success token) that terminates the loop.

## Usage

Run a Fable loop using the local Python runner:

```bash
python3 fable/fable_runner.py --loop <workflow_name> --iterations <max_iterations> --mock
```

Available workflows:
- `high-agency-inbox-triage` (Gmail MCP)
- `pr-to-ticket-sync` (GitHub MCP)
- `daily-runbook-execution` (Terminal MCP)
- `database-sanity-check` (Postgres MCP)
- `kpi-anomaly-watch` (PostHog/Stripe)
- (and 20 other workflows defined in `fable/workflows.json`)
