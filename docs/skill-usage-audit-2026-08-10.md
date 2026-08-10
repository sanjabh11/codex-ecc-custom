# Codex skill and action usage audit — 2026-08-10

## Executive decision

The local evidence supports a **verified-local usage instrument**, not a
complete account of host activation or successful skill execution.

- The strongest available skill signal is an explicit user selector, counted
  once per session (L1). It identifies the top 20 skills below.
- Recorded top-level tool calls are action evidence (L2), but `exec` is a
  wrapper action and does not prove that every nested call succeeded.
- Plain mentions and tool names embedded inside wrapper input are supporting
  evidence only (L3). They must not be promoted to invocation proof.
- The underutilized list is an opportunity hypothesis (L4), ranked from local
  skill metadata and observed task vocabulary. It is not evidence that the
  user needs, loaded, or benefited from a skill.

No existing skill implementation was changed in this audit. The bounded
architecture change is the offline analyzer and its regression test. Existing
modified and untracked skill packages remain outside the change scope.

## Frozen provenance and coverage snapshot

| Field | Value | Proof label |
|---|---|---|
| Repository | `/Users/sanjayb/codex-ecc-custom` | verified-local |
| Git HEAD at initial live snapshot | `1f7cac81653fc119fde928184838465af0cbdb67` | historical baseline |
| Authoritative clean-rerun commit | `1d28de3d35258884049ece8025db3f061e6d576e` | verified-local |
| Frozen manifest scan UTC | `2026-08-10T16:36:53Z` | verified-local |
| Final clean-input verification UTC | `2026-08-10T16:38:40Z` | verified-local |
| Final artifact commit | `9d3648ea2d1214743d1b6e0e656edec91e015fdc` | verified-local |
| Window | `2026-06-10T00:00:00Z` through `2026-08-10T23:59:59.999999Z` | verified-local |
| Full worktree status entries at initial snapshot | `472` | verified-local, dirty checkout |
| Main worktree status after selective commits | `470` | verified-local, unrelated user work |
| Frozen source manifest | `docs/audits/skill-usage-audit-source-manifest.json` with `41` SHA-256-bound JSONL files | verified-local |
| Frozen skill manifest | `docs/audits/skill-usage-audit-skill-manifest.json` with `102` SHA-256-bound `SKILL.md` files | verified-local |
| Inventory labels in frozen CSV | `111` distinct labels across `102` skill files | verified-local |
| Analyzer SHA-256 at clean rerun | `b75f9c542a3fadb5195943eb0273355946ebd3e5d9d899260e08d76a9b9f9809` | verified-local |
| Test SHA-256 at clean rerun | `504aacd2bba10abaf89152355a234ad7853f54d9308d92e99823cb88280a0955` | verified-local |
| Evidence SHA-256 at clean rerun | `2d975ca6e6b0767f9d95376333eb94a60d915c38e8b586eb70c725fcdd514ed4` | verified-local |
| Source-manifest SHA-256 at clean rerun | `c2b1ef7c66705a6abdcc89a6924c39a843e760911ec44768467aef29b7e7a830` | verified-local |
| Skill-manifest SHA-256 at clean rerun | `1e50568104f7bfa320fe30712cbce10031b4daccd6f306ec502bbf4731eecb87` | verified-local |
| Frozen summary SHA-256 at clean rerun | `d65239e9fc5d462ba00f8a276859d8465490be357a90c3bcf525ec8f51b7cc95` | verified-local |
| Canonical skill inventory | `102` local skill directories | verified-local |
| Candidate transcript files in live coverage scan | `100` | verified-local, live reference |
| Active transcript files in live coverage scan | `43` | verified-local, live reference |
| Stable files in authoritative manifest | `41` | verified-local |
| Distinct sessions in authoritative manifest | `33` | verified-local |
| In-window events in authoritative manifest | `218,936` | verified-local |
| Filtered user prompts in authoritative manifest | `931` | verified-local |
| Repeated context blocks excluded in authoritative manifest | `262` | verified-local |
| Malformed JSONL lines | `0` | verified-local |
| CASS | unhealthy/stale; not used as authoritative evidence | runtime-unverified |

The checkout is intentionally dirty. The 472-entry count includes unrelated
user work and must not be interpreted as changes made by this audit. The live
coverage scan included two files that were still changing; the authoritative
ranking therefore uses the 41-file hash-bound transcript manifest and the
102-file hash-bound skill/inventory manifest, excluding those two recently
modified transcript files. The exact run reproduced with clean analyzer code
in a pristine detached worktree while reading those frozen local inputs.

## Evidence model

| Tier | Evidence captured | What it proves | What it does not prove |
|---|---|---|---|
| L1 | `$skill`, `@skill`, or equivalent explicit selector in a user prompt; sessions deduplicated | The user explicitly selected/referenced the label in that session | Host loader activation, successful execution, output quality, or runtime availability |
| L2 | Top-level tool-call record in a session transcript | A tool call was recorded in an available local transcript | That an `exec` wrapper's nested command ran, succeeded, or was authorized |
| L3 | Plain skill mention or `tools.*` nested call-site in wrapper input | Supporting context for discovery and workflow shape | Invocation, execution, or host integration |
| L4 | Relevance × usage gap from local metadata and task vocabulary | A bounded candidate for an activation pilot | Need, value, adoption, or ROI |

The analyzer deliberately excludes repeated application-context blocks beginning
with `<recommended_plugins>`, `# AGENTS.md`, `<environment_context>`,
`<app-context>`, `<skills_instructions>`, `<permissions instructions>`, and
other known context markers. This reduces false counts but cannot recover
transcripts that are not present in the local session roots.

## Top 20 skills by strongest available usage evidence

Quality abbreviations: `FM` frontmatter, `OC` output contract, `SB` scope
boundary, `R` references, `S` scripts, `T` tests. A dash means the label was
supplied as an external/global label and its implementation was not audited in
the canonical 102-skill inventory.

| # | Skill | L1 selector prompts / sessions | L3 mention prompts / sessions | Source | Quality signals | Architect recommendation |
|---:|---|---:|---:|---|---|---|
| 1 | `deep-research` | 53 / 12 | 232 / 24 | external label | — | Keep as the default research route; add a mandatory source ledger, date window, and fact/inference split before treating a research result as complete. |
| 2 | `ecc-niche-positioning-audit` | 34 / 7 | 38 / 8 | canonical | FM, SB, R, S, T | Preserve as a high-use workflow; add an explicit output contract and a claim-to-evidence matrix to make repeated audits comparable. |
| 3 | `ecc-advisor` | 62 / 5 | 86 / 13 | canonical | FM, SB, R, S, T | Keep the advisor gate before edits and completion; add machine-readable decision/remaining-call-budget evidence to prevent advisory output from becoming process proof. |
| 4 | `prompt-optimizer` | 12 / 4 | 12 / 4 | external label | — | Use only when prompt quality is the bottleneck; require before/after scenarios and avoid optimizing prompts when the missing control is repository/runtime enforcement. |
| 5 | `conformance-gate` | 6 / 3 | 20 / 6 | external label | — | Make it the release-facing gate for contract work; require explicit pass/fail criteria, negative fixtures, and proof-layer labels. |
| 6 | `slides` | 4 / 2 | 9 / 5 | canonical | FM, SB, R, S, T | Add a render/open smoke check and a final artifact link/hash so deck generation is verified beyond source creation. |
| 7 | `last30days` | 4 / 2 | 4 / 2 | canonical | FM, SB, S, T | Reconcile the name/window mismatch with a single UTC window contract and source list; keep web freshness claims separate from local history evidence. |
| 8 | `agent-phase-ratchet` | 3 / 2 | 16 / 6 | external label | — | Require baseline, one focused lever, check output, reflection, and next ratchet in every Tier 2+ ledger. |
| 9 | `second-brain-ops` | 12 / 1 | 12 / 1 | canonical | FM, SB | Keep vault writes approval-bound; add a content-hash, target-path, and reversible-write contract before using it for durable memory. |
| 10 | `ecc-explain` | 6 / 1 | 8 / 2 | canonical | FM, SB | Require audience, evidence level, and limitations in every explanatory artifact; avoid turning a clear narrative into an unsupported readiness claim. |
| 11 | `ecc-ml-engineering` | 6 / 1 | 6 / 1 | canonical | FM, R | Add scope boundaries, dataset/model provenance, and reproducibility gates before using it for implementation claims. |
| 12 | `ecc-multi-execute` | 6 / 1 | 6 / 1 | canonical | FM | Treat as high-risk orchestration; require an explicit action budget, ownership map, approval gate, and rollback/stop condition. |
| 13 | `skill-optimizer` | 4 / 1 | 5 / 2 | external label | — | Use the evidence schema and 3–7 supportive/neutral/competing scenarios; do not promote a skill based on a metadata-only quality score. |
| 14 | `ecc-hormozi-funnel` | 1 / 1 | 24 / 6 | canonical | FM, SB, R, S, T | Separate copy generation from buyer validation; require claim provenance and a no-invention gate for market/customer statements. |
| 15 | `codebase-onboarding` | 1 / 1 | 16 / 6 | external label | — | Make it the first step for unfamiliar repositories; require HEAD, status, instruction files, dependency health, and test baseline. |
| 16 | `ecc-fable-loop` | 0 / 0 | 22 / 5 | canonical | FM | Add termination, budget, and durable-state output requirements; mentions do not establish that the loop was selected or run. |
| 17 | `ecc-model-route` | 0 / 0 | 22 / 5 | canonical | FM, SB | Require an auditable route decision, model/tool constraints, and fallback behavior; test that the route cannot be silently bypassed. |
| 18 | `ecc-verify` | 0 / 0 | 16 / 5 | canonical | FM | Add standard discovery tests and a structured failure taxonomy; a verification skill must report what it did not test. |
| 19 | `ecc-prompt-optimize` | 0 / 0 | 12 / 5 | canonical | FM | Distinguish this canonical package from the external `prompt-optimizer` label and add an explicit alias/namespace mapping. |
| 20 | `graph-engineer` | 0 / 0 | 26 / 4 | canonical | FM, SB, R, S, T | Keep its graph/schema validator as the core; separately track host loader, MCP, runtime, and human-gate proof rather than inferring them from local tests. |

### Top-20 cross-cutting gaps

1. Several high-ranked labels are global/external labels. They are usage
   signals, not local implementation audits.
2. The canonical skills mostly have frontmatter and scope signals, but output
   contracts are inconsistently detectable. This is a metadata quality flag,
   not a semantic verdict; the detector is intentionally heuristic.
3. A high mention count with zero selectors (`ecc-fable-loop`,
   `ecc-model-route`, `ecc-verify`, `graph-engineer`) is a discovery/routing question, not proof
   of underuse or failed activation.
4. `ecc-advisor` and `ecc-niche-positioning-audit` are the strongest local
   candidates for reusable output schemas because they have both repeated
   selector evidence and supporting package assets.

## Codex actions observed

These are recorded top-level tool-call records (L2), not inferred nested
commands.

| Action | Count | Sessions | Interpretation | Optimization |
|---|---:|---:|---|---|
| `exec` | 30,638 | 31 | Dominant wrapper/orchestration surface | Add a compact run summary and preserve the inner command's exit status; do not treat wrapper count as work count. |
| `wait` | 3,649 | 27 | Long-running/polling workflow | Add bounded wait budgets and terminal-state evidence to long loops. |
| `exec_command` | 99 | 1 | Direct command surface | Prefer a reproducible command manifest for audits; keep secrets and environment values redacted. |
| `request_user_input` | 54 | 20 | Human clarification/approval surface | Distinguish clarification from authorization and record the decision target/expiry when it is an approval. |
| `send_message` | 18 | 2 | Coordination surface | Use only with explicit ownership and handoff state. |
| `wait_agent` | 10 | 4 | Worker/agent coordination | Require worker result, failure, and timeout records. |
| `list_agents` | 5 | 2 | Discovery of available workers | Report availability separately from successful execution. |
| `write_stdin` | 4 | 1 | Interactive process continuation | Bound process lifetime and capture final exit status. |
| `spawn_agent` | 4 | 2 | Delegation surface | Require scope, artifact ownership, and no-overlap constraints before spawning. |
| `get_goal` / `create_goal` / `update_goal` | 1 each | 1 each | Goal lifecycle | Keep goal completion tied to acceptance evidence, not elapsed effort. |

The analyzer also records nested wrapper call-sites as L3. Those are useful for
understanding workflow shape but may include code examples inside an `exec`
input; they are not host-activation evidence.

## Top 10 underutilized candidates

All ten candidates had zero L1 selector sessions in this window. The score is
`relevance / (1 + mention sessions)` and is used only to prioritize a bounded
activation pilot.

| # | Skill | Relevance | Opportunity gap | L1 / L3 sessions | Quality signals | Audit and bounded next move |
|---:|---|---:|---:|---:|---|---|
| 1 | `ecc-graphify` | 0.7143 | 0.7143 | 0 / 0 | FM, SB, R, S, T | Pilot the clean-checkout core on one codebase; keep MCP, GraphML/SVG/wiki, remote DB, and multimodal gates separate. |
| 2 | `plan-certificates` | 0.7143 | 0.7143 | 0 / 0 | FM, SB | Pilot on one provenance-heavy release plan; require certificate inputs, expiry, and verification output before considering adoption. |
| 3 | `deterministic-simulation-testing` | 0.4286 | 0.4286 | 0 / 0 | FM, SB | Pilot against one boundary regression; require deterministic seed, fixture, replay command, and artifact hash. |
| 4 | `ecc-a11y-audit` | 0.4286 | 0.4286 | 0 / 0 | FM | Pilot on one user-facing document/app surface; add scope, tool availability, and manual-review fallback. |
| 5 | `ecc-buyer-pipeline` | 0.4286 | 0.4286 | 0 / 0 | FM, OC, SB, R | Pilot only for an evidence-backed buyer hypothesis; separate outreach copy from validated buyer evidence. |
| 6 | `ecc-conversion-audit` | 0.4286 | 0.4286 | 0 / 0 | FM, OC, SB, R | Pilot on one existing funnel artifact; require baseline metric source, variant boundary, and no unsupported conversion claim. |
| 7 | `spec-first-doctrine` | 0.4286 | 0.4286 | 0 / 0 | FM, SB | Use before one architecture change; require acceptance criteria and a refusal when the spec is incomplete. |
| 8 | `agents-md-generator` | 0.2857 | 0.2857 | 0 / 0 | FM, SB | Pilot on a temporary fixture repository; require instruction precedence, diff review, and no broad overwrite. |
| 9 | `ecc-content-quality-ops` | 0.2857 | 0.2857 | 0 / 0 | FM, OC, SB, R | Pilot on one customer-facing artifact; require source registry, claim scan, and final link/render check. |
| 10 | `ecc-cpp-review` | 0.2857 | 0.2857 | 0 / 0 | FM | Activate only for a real C/C++ change; require compiler/toolchain detection before claiming review coverage. |

These rankings should not trigger automatic installation or edits. The next
step is one scenario per candidate, then promote only candidates with repeatable
value and a clear output contract.

## Revised phase-wise implementation plan

### P0 — Freeze provenance and evidence boundary (complete for this snapshot)

- Keep the primary checkout untouched except for the new audit tool/test and
  report artifacts.
- Record HEAD, full dirty status count, scoped paths, UTC window, inventory
  size, and source hashes.
- Treat the initial live scan as a coverage reference and the 41-file
  SHA-256-bound manifest scan as the authoritative ranking.
- Fail closed when a manifest-listed transcript changes.

### P1 — Build the usage ledger (complete)

- Parse local Codex session and archive JSONL only.
- Exclude repeated application context.
- Deduplicate selector counts by session.
- Separate L1/L2/L3/L4 and expose source coverage.
- Support a hash-bound source manifest so live transcript growth cannot create
  false reproducibility.
- Support a hash-bound skill/inventory manifest so a Git clean tree does not
  silently omit user-owned untracked skill packages.
- Add regression tests for context exclusion, malformed lines, out-of-window
  sessions, wrapper contamination, quality-signal propagation, and manifest
  hash drift.

### P2 — Audit the top 20 (complete as architecture review)

- Keep external labels separate from canonical package audits.
- Add output-contract, scope, provenance, and testability recommendations per
  skill.
- Do not edit high-use skills automatically while the checkout is dirty.

### P3 — Run bounded underutilized pilots (next coding-agent batch)

For each candidate, create three short scenarios: supportive request, neutral
request, and competing/irrelevant request. Capture:

- whether the skill is selected;
- whether the expected artifact is produced;
- whether the skill declines or routes away when out of scope;
- command/test evidence and artifact hash;
- time/tool-call cost where available.

Start with `plan-certificates`, `deterministic-simulation-testing`,
`spec-first-doctrine`, and `ecc-eval`; they align most directly with the
observed planning, testing, and provenance workload.

### P4 — Make the shared contracts explicit (architectural fixes)

Implement in an isolated/clean worktree, in this order:

1. Add a shared skill alias/selector registry so aliases and canonical names
   are counted consistently.
2. Add a small machine-readable output-contract block to the highest-value
   local skills, beginning with `ecc-advisor` and
   `ecc-niche-positioning-audit`.
3. Add a reusable provenance block: input sources, evidence level, output
   paths, and stop conditions.
4. Add a standard scenario runner that emits skill-optimizer evidence JSON.
5. Add an action-result envelope distinguishing wrapper, nested command,
   exit status, and artifact status.

The coding agent may handle minor wording, fixtures, and per-skill tests after
these contracts are approved. Do not mass-edit all 102 skills.

### P5 — Validate and promote

- Validate evidence JSON with the skill-optimizer validator.
- Run a 3–7 scenario matrix per changed skill covering supportive, neutral,
  and competing prompts.
- Require before/after evidence for any skill implementation change.
- Run scoped unit tests, standard discovery, and `git diff --check`.
- Reject a promotion if the result relies only on prompt mentions, nested
  wrapper strings, or a stale/uncommitted artifact.

### P6 — Host/runtime/provenance gate

- Reproduce the analyzer in a clean checkout.
- Run one loader smoke test per logical host family; filesystem symlinks alone
  are insufficient.
- If host telemetry is available, reconcile local selector counts with the
  host's invocation/event counts.
- Keep optional MCP, remote database, rendering, and multimodal gates
  separately labeled and non-blocking until prerequisites and authority exist.

### P7 — Maintenance loop

- Generate one UTC snapshot per month from a fixed command manifest.
- Store the JSON evidence and report together with source hashes.
- Compare periods by distinct sessions and selector sessions, not raw prompt
  mentions alone.
- Re-audit the top five changes and top five emerging underutilized candidates;
  retire stale aliases and skills explicitly.

## Gap register and root causes

| ID | Gap | Evidence | Root cause | Severity | Fix phase |
|---|---|---|---|---|---|
| U1 | Host activation is unmeasured | Local transcripts expose prompts/tool records, not host loader telemetry | Selector evidence was treated as execution evidence in earlier audits | Critical | P6 |
| U2 | External/global labels lack source audits | `deep-research`, `prompt-optimizer`, `conformance-gate`, `agent-phase-ratchet`, `skill-optimizer`, and `codebase-onboarding` have null local quality fields | One ranking combined canonical and global labels | High | P2/P4 |
| U3 | Alias and renamed-skill usage may be split | Matching is canonical-name/token based | No shared selector registry | High | P4 |
| U4 | Outcomes are not measured | Counts show selection/mentions, not artifact quality, time, cost, or user success | Usage ledger was built before an outcome envelope | High | P3/P4 |
| U5 | Primary worktree remains dirty | 470 unrelated status entries remain after selective audit commits; the clean detached worktree is pristine | User changes must be preserved while audit artifacts are committed selectively | Medium | P0 complete; P6 only for future releases |
| U6 | Historical coverage may be incomplete | 100 live candidates, 41 hash-bound stable files; two recent files excluded; CASS was stale and skipped | Local transcript availability differs by host/archive | High | P0/P6 |
| U7 | Quality checks are heuristic | `has_output_contract` and related flags are phrase/directory signals | A cheap inventory signal was needed before semantic schema work | Medium | P4 |
| U8 | Per-skill scenario evidence is absent | Only analyzer regression scenarios exist | Top-20 audit was metadata/usage-first | High | P3/P5 |
| U9 | Wrapper actions overcount implementation work | `exec` dominates at 30,638 calls and nested strings may be code examples | Tool telemetry was not modeled as a typed action/result graph | Medium | P4 |
| U10 | Plugin mentions are not skill activation | `everything-claude-code` appears 242 times, but it is a plugin/container label | Plugin and skill namespaces were mixed in prior reasoning | Medium | P2 |
| U11 | Prompt matching can false-positive or miss aliases | L3 is text/token based by design | No host trigger engine or alias map is exposed in this audit | Medium | P4/P6 |
| U12 | Live reports can drift from the run | Source and skill manifests fail closed on input drift; a committed frozen summary now backs the human report | A frozen snapshot command/manifest was initially missing | Medium | P0 complete; P7 maintenance |
| U13 | External integration prerequisites remain separate | CASS, MCP client, host loaders, remote DBs, and multimodal rights are unavailable or unapproved | Optional gates were mixed with the core usage audit | High | P6 |
| U14 | Git clean tree omits user-owned untracked skills | The first clean run dropped `second-brain-ops`, `ecc-explain`, and related labels | Git commit contents are not the same as the active local skill inventory | High | Fixed with hash-bound skill/inventory manifest; host portability still open |

## Manual steps

1. No core-code manual step remains: the analyzer, regression test, report,
   evidence, and source manifest are selectively committed in `d29999f`. Keep
   unrelated worktree entries unstaged; do not use `git add .`.
2. If host-level activation proof is required, obtain the relevant Codex
   invocation/skill telemetry or run one authenticated loader smoke test per
   logical host family.
3. Approve a bounded pilot for the four P3 starter candidates and supply one
   real, non-sensitive scenario for each.
4. Refresh CASS only if cross-agent history is needed and index mutation is
   approved; its current stale/unhealthy state is not evidence of zero usage.
5. Keep MCP, remote database, SVG/GraphML/wiki, multimodal rights, vault
   writes, and production claims outside the core release gate until their
   prerequisites and authority are supplied.

## Best-practice alignment

OpenAI describes skills as reusable workflows containing instructions,
examples, and code, and distinguishes skill usage/invocation telemetry from
the skill package itself. The local L1/L2/L3 separation follows that principle
and avoids claiming activation from a text mention. See [Skills in ChatGPT and
Codex](https://help.openai.com/en/articles/20001066).

Plugins are containers for skills/apps/templates whose availability and
permissions vary by surface and workspace; therefore plugin mentions are kept
separate from canonical skill usage. See [Plugins in ChatGPT and
Codex](https://help.openai.com/en/articles/20001256).

OpenAI's Codex safety description emphasizes boundary controls, approvals, and
agent-native telemetry/audit trails. The P4/P6 plan applies the same separation
to action envelopes, approval records, and host proof. See [Running Codex safely
at OpenAI](https://openai.com/index/running-codex-safely/).

## Current proof-level decision

**Decision:** The usage analyzer and its focused regression suite are
`verified-local`. The ranked top 20 and underutilized top 10 are
`verified-local` as measurements of the 41-file hash-bound transcript corpus
against the 102-file/111-label hash-bound local skill inventory, with L4
opportunity claims explicitly marked as hypotheses. Clean analyzer
reproducibility is verified with code/input commit `1d28de3` and final artifact
commit `9d3648e`. Skill host loading, successful execution, cross-surface
coverage, and outcome/ROI remain unverified.

Do not use this artifact to claim “top 20 most executed skills” or “the top 10
skills the user needs.” The accurate wording is: “top 20 explicit selector
labels in the available 60-day local Codex transcript corpus, plus ten
metadata-ranked activation candidates.”
