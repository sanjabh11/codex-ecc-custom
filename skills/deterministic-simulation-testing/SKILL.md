---
name: deterministic-simulation-testing
description: >-
  FoundationDB-class testing with virtual time, DPOR schedule exploration,
  chaos injection, and seed-replayable failures. Use when building concurrent,
  distributed, or stateful systems where concurrency bugs must be found before
  production. Covers the four DST ingredients (concurrency control, virtual time,
  seeded randomness, failure injection), Rust-specific DST tooling, state machine
  architecture, crashpacks, and CI meta-tests.
  TRIGGER when: "deterministic simulation", "DST", "simulation testing",
  "virtual time testing", "DPOR", "chaos testing", "seed replay",
  "FoundationDB testing", "concurrency bug finding", "distributed system testing".
  DO NOT TRIGGER when: task is a simple CRUD app with no concurrency,
  or when the system has no async/concurrent components.
---

# Deterministic Simulation Testing (DST)

## When to Use

- Building concurrent, distributed, or stateful systems (databases, queues, schedulers, replication protocols)
- Systems with async I/O, locks, shared state, or multi-threaded execution
- When concurrency bugs must be found before production, not after
- When you need replayable failure scenarios (crashpacks)
- When formal methods (TLA+/Lean) are too heavy but unit tests are too light

## The Four Ingredients

DST requires full control over four ingredients. Missing any one breaks determinism.

### 1. Concurrency (Task Scheduling)
- All task scheduling must be controlled by the simulator, not the OS
- In production: real scheduler drives state machines via network
- In testing: single thread drives event loop, routes messages via message bus
- **Rust:** async/await is actor-like; swappable runtime design enables DST by using a different runtime in tests

### 2. Time (Virtual Clocks)
- No physical clocks. All time comes from a virtual clock the simulator controls
- Simulated time advances in discrete steps synchronized across all components
- Typical ratio: ~10:1 real-to-simulated time (faster than real time)
- **Rust:** Override `clock_gettime` via turmoil's clock; scope with `SimClocksGuard` to avoid teardown issues

### 3. Randomness (Seeded RNG)
- All RNG must come from a PRNG you control and seed
- The seed becomes part of the input — same seed = same execution
- Override `getrandom`, `getentropy`, and platform-specific RNG calls
- **Rust:** MadSim overrides `getrandom`, `getentropy`, and (Mac) `CCRandomGenerateBytes`

### 4. Failure Injection
- Optional but where DST's real power lies
- Inject: torn writes, bit flips, ENOSPC, fsync lies, network partitions
- Simulate: connection failures, machine degradation, shutdowns, reboots, machines coming back from dead
- Stress-test: fail machines at very short intervals, severe loads, delayed communications

## Architecture Pattern

### State Machine Design
```
Production:
  State Machine A <--network--> State Machine B
       |                            |
    Driver A                     Driver B
       |                            |
    Local SM                     Local SM

Testing:
  Single Thread Event Loop
       |
  Message Bus
   /     \
  SM A   SM B
```

- Core components are single-threaded state machines
- Production: "driver" routes messages via network, handles local state outputs
- Testing: single thread drives event loop, routes messages via message bus
- This architecture is a powerful mental model for reasoning about system behavior

### Rust-Specific Implementation

**Turmoil** — Network simulation framework for Rust
- Controls time and entropy via `libc` symbol overrides
- Use with MadSim for full DST coverage

**MadSim** — Deterministic simulation testing library
- Overrides `getrandom`, `getentropy`, `CCRandomGenerateBytes`
- Overrides `clock_gettime` using turmoil's clock
- Statically initializes RNG with `set_rng()`

**mad-turmoil** — MadSim-derived crate (S2's approach)
- Combines turmoil's network simulation with MadSim's determinism
- Provides byte-level log conformity on CI

**Sled simulation guide** — Actor-based concurrency model
- All core components written as single-threaded state machines
- Inspired FoundationDB-style DST in Rust

## CI Integration

### Meta-Test Pattern
```rust
// CI reruns the same seed and compares TRACE-level logs
#[test]
fn deterministic_replay() {
    let seed = get_ci_seed(); // from failing run or fixed CI seed
    let run1 = simulate(seed);
    let run2 = simulate(seed);
    assert_eq!(run1.trace_logs(), run2.trace_logs());
    // "Down to the last bytes on the wire, we have conformity"
}
```

### Crashpacks
- Failing runs auto-attach crashpacks with replay commands
- A crashpack contains: seed, initial state, failure schedule, replay command
- `replay(crashpack)` reproduces the failure deterministically
- Share crashpacks across machines — same seed = same bug

### Failure Schedule
```
# Example test file (FoundationDB-style config blocks)
test_cluster:
  - clog_network: probability=0.01
  - kill_machine: interval=10s, reboot=true
  - degrade_performance: machine=3, factor=0.1
  - delay_communication: p50=100ms, p99=500ms
  - full_datacenter_failure: dc=1, duration=30s
```

## Testing Strategy

### What to Check
1. **Internal assertions** — Liberal assertions in mainline code; far better to crash loudly when ACID properties are violated
2. **External invariants** — Durability after crash, API semantics under concurrent operations
3. **State consistency** — All state machines reach consistent terminal states
4. **No leaks** — No tasks, pins, or resources left dangling

### Defense in Depth
- Check invariants as a client (external perspective)
- Check invariants granularly in mainline code (internal assertions)
- Both layers catch different bug classes

## When NOT to Use DST

- Simple CRUD apps with no concurrency
- Pure computation (no I/O, no shared state)
- Frontend-only applications
- When the system cannot be restructured as state machines
- When the team cannot afford the cognitive overhead (DST is intrusive)

## Cost and Effort

- **Initial investment:** Several months of engineering time for serious DST
- **Retrofitting:** Possible but harder than building DST in from day one
- **Ongoing cost:** Cognitive overhead during implementation (thinking about state transitions)
- **Payoff:** Discovers bugs that take weeks of production debugging in minutes of simulation
- **Track record:** FoundationDB rarely paged in production; Polar Signals found data loss + data duplication bugs

## Integration with ECC

- Use with `invariant-registry` to define what invariants DST should check
- Use with `reference-oracle-testing` for differential testing against a simple reference
- Use with `fuzz-regression` to convert DST-discovered bugs into regression tests
- Use with `conformance-gate` to prove DST coverage before shipping
- Use with `rust-testing` for Rust-specific test patterns

## Key References

- FoundationDB simulation guide (the canonical reference)
- S2: "Deterministic simulation testing for async Rust" (s2.dev/blog/dst)
- Polar Signals: "DST in Rust: A Theater Of State Machines"
- sled simulation guide (github.com/spacejam/sled)
- MadSim, Turmoil, mad-turmoil crates
- Amplify Partners: "A DST Primer for Unit Test Maxxers"
