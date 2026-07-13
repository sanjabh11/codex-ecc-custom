# Fable Autopilot Playbook

This playbook contains strategies and rules generated dynamically by the model reflecting on past session execution history and failures.

## Active Rules
- **[R-101]** For tricky reasoning or repetitive errors, decompose before answering: If a command fails or code errors, break the problem into smaller sub-problems. Do not repeat the same fix/attempt.
- **[R-102]** When uncertain, verify intermediate steps and check assumptions: Double-check key assumptions, file existence, and return types before running modifying commands.
- **[R-103]** Explicitly enumerate items step by step before implementing changes: Match target structures exactly and list expected elements to prevent structure/type drift.

## Rule Revision History
- `[2026-07-10]`: Created Rule ID [R-101] to prevent failure mode: For tricky reasoning or repetitive errors, decompose before answering
- `[2026-07-10]`: Created Rule ID [R-102] to prevent failure mode: When uncertain, verify intermediate steps and check assumptions
- `[2026-07-10]`: Created Rule ID [R-103] to prevent failure mode: Explicitly enumerate items step by step before implementing changes
