---
name: perf-ratchet
description: "Measure performance before and after changes, then block regressions with a ratchet threshold."
origin: ECC
---

# Performance Ratchet Skill

Use this skill when the user asks to improve speed, prevent performance regressions, compare benchmarks, or make performance claims about a code path.

## Trigger Phrases

- "perf ratchet"
- "performance regression"
- "benchmark this"
- "make it faster"
- "latency budget"
- "throughput"
- "slow build"

## Workflow

1. Identify the metric that matters: latency, throughput, memory, bundle size, build time, training time, or query time.
2. Locate existing benchmark or performance tooling:
   ```bash
   rg -n "benchmark|perf|ratchet|bundle|lighthouse|criterion|pytest-benchmark" .
   ```
3. Capture a baseline before editing whenever possible.
4. Apply the smallest change that targets the measured bottleneck.
5. Re-run the exact same measurement after the change.
6. Decide with an explicit threshold:
   - `pass`: improved or within allowed regression budget.
   - `fail`: regression exceeds threshold.
   - `inconclusive`: measurement is noisy or environment changed.

## Useful Command Patterns

```bash
time <command>
npm run build
npm run test -- <perf-test>
cargo bench
pytest <benchmark-test>
du -sh dist build .next
```

When a repo provides `scripts/perf*`, `bench*`, or ratchet scripts, use those first and preserve their output.

## Output Contract

Return:
- `Metric`: the measured performance dimension.
- `Baseline`: command and result before the change.
- `After`: command and result after the change.
- `Threshold`: allowed regression or required improvement.
- `Decision`: pass, fail, or inconclusive.
- `Caveats`: hardware, runtime, cache warmth, sample size, or noisy measurements.

## Safety Rules

- Do not claim performance improvement without before/after evidence.
- Do not compare different commands, datasets, or environments as if equivalent.
- Do not optimize by removing correctness checks unless the user explicitly accepts the tradeoff.
- Prefer reproducible command output over subjective UI feel.
