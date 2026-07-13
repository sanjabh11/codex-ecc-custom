---
name: ecc-fable-goal
description: Execute Fable 5 goal-driven agent workflows.
---

# ecc-fable-goal

Use this skill when running outcome-heavy, multi-step agent tasks requiring a verifiable result.

## Purpose

The Fable 5 goal architecture executes a task until it reaches a defined `finish line`, validates the outcome using a separate `judge` process, and outputs verification logs as `proof`.

## Core Concepts

1. **finish line**: A clear, semantic definition of what completion looks like.
2. **judge**: A separate evaluation check (using a model or script) to assess compliance and avoid author bias.
3. **proof pasted in chat**: Verification data (diffs, test logs, summaries) outputted as evidence of completion.

## Usage

Run a Fable goal using the local Python runner:

```bash
python3 fable/fable_runner.py --goal "<finish_line_description>" --judge "<criteria>" --mock
```
