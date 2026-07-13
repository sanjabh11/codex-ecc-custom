Corpus-Wide Skill Hardening suhhested byr GPT‑5.6 for GLM‑5.2 imeplementaions

Baseline and design decisions
Canonical source: /Users/sanjayb/.codeium/windsurf/skills (733 skills).
Current portability gaps: only 14/733 pass Codex’s native validator; 718 fail on nonportable frontmatter and one lacks name. Of 283 shared Windsurf/.agent skills, all 283 have content drift.
Do not bulk-rewrite live skills. Preserve Windsurf’s ECC extensions; generate filtered, runtime-specific projections from a registry.
GPT‑5.6 optimization will use capability probing, private reasoning, concise decision records, and eval evidence—not requests for visible chain-of-thought. GPT‑5.6 rollout/version availability remains a preflight check. OpenAI GPT‑5.6 guidance
Use progressive disclosure: concise SKILL.md, references for conditional detail, scripts only for deterministic repeated actions. OpenAI skills architecture, Anthropic skill design
Use SkillOpt-style bounded add/delete/replace edits, rejected-edit history, and held-out promotion gates; do not accept self-reported improvement. Microsoft SkillOpt research
Hardening prompt contract
Create skill-hardener-v2 as a single target-at-a-time prompt for GLM‑5.2. It must require:
Inputs: target path, runtime profile, mutation mode (audit|plan|apply|review), safety policy, baseline evidence, and scenario suite.
Mandatory order: probe runtime → read target and adjacent overlaps → establish baseline → propose bounded edits → run required checks → score → promote/hold.
Tool truth: use only discovered tools, model interfaces, credentials, and runtime paths. Unknown or stale capability claims become blockers, never invented instructions.
Portable skill structure: precise name and description; imperative workflow; explicit inputs/outputs; safety and stop gates; verification commands; references/scripts only where they reduce repeated work.
Output: machine-readable JSON plus concise Markdown containing baseline, changes, P0/P1 findings, scorecard, scenario evidence, promotion decision, rollback path, and next action.
Explicitly prohibit: exposed chain-of-thought, fabricated benchmarks/citations/tool calls, global mutations without a passed promotion gate, secrets in artifacts, and unrelated refactors.
Remove irrelevant inherited clauses such as graphics/instancing guidance unless the target skill demonstrably needs them.
Score each skill on a 0–10 rubric:
Dimension	Points
Trigger precision	1.0
Contract and scope control	1.0
Runtime and tool truth	1.2
Safety and failure handling	1.2
Workflow fidelity	1.0
Tests and evidence	1.2
Token/work efficiency	0.8
Maintainability and progressive disclosure	1.0
Uniqueness and adapter fit	0.6

Execution phases for GLM‑5.2
Phase	GLM action	Exit criteria
P0 — Preflight	Create an immutable hash-and-copy snapshot; inventory every source and target copy; detect duplicate names, drift, large skills, invalid frontmatter, scripts, references, and runtime availability.	Registry reconciles exactly 733 canonical skills; every target status is ready, deferred, or blocked with evidence.
P1 — Corpus control plane	Add /Users/sanjayb/.codeium/windsurf/.skill-hardening/ with registry, runtime profiles, hashes, run evidence, rejected edits, CSV dashboard, and rollback manifests. Implement only four stdlib utilities: scan, adapter-aware validation, projection dry-run/publish, and dashboard rendering.	Full dry-run produces no skill changes; Codex projection rules strip unsupported fields while preserving Windsurf extensions.
P2 — Prompt and eval calibration	Build the hardened prompt and select a stratified 24-skill pilot: simple, code, integration, security, workflow, research; include long files, invalid metadata, and drifted copies.	Every pilot skill has a baseline, five development scenarios, two held-out scenarios, and an evidence manifest accepted by existing skill-optimizer validators.
P3 — Pilot hardening	GLM makes one bounded edit set per skill; use deterministic checks first, then independent/fresh-context review. Security-sensitive or P0/P1 work requires a second reviewer or human gate.	No P0/P1 findings; all baseline scenarios retained; ≥97% weighted scenario pass rate; baseline <8.5 improves by at least 1.5 or reaches 10; higher-baseline skills show no regression.
P4 — Controlled rollout	Process remaining skills in sequential batches of 25, prioritized by schema failure, drift, safety risk, usage evidence, and overlap. Hold failed candidates in the rejected-edit ledger.	Each batch passes P3 gates; corpus target is a +1.5 weighted uplift among eligible skills, with no promoted regression.
P5 — Publish and prove	Generate adapter projections only after promotion: Codex-safe frontmatter, Windsurf-preserving source, and .agent projection. Antigravity, Devin, and Hermes remain deferred until their actual discovery paths are confirmed.	All Codex projections validate; target hashes match intended transformations; runtime discovery smoke checks pass or are explicitly marked unverified.
P6 — Sustain	Re-run changed-only inventory/evals, refresh stale runtime claims, and regenerate CSV/HTML dashboard. Do not schedule automation without separate approval.	Dashboard shows per-skill baseline/current score, delta, pass rate, drift, runtime status, P0/P1 count, promotion state, and rollback reference.

Evaluation and promotion
Use seven scenarios per applicable skill:
Direct request  
Implicit activation  
Competing/adjacent request  
Missing tool, credential, or runtime  
Stale/conflicting documentation  
Malformed, oversized, or boundary input  
Resume from partial state
Use five for development and freeze two as held-out validation. A scenario may be not_applicable, but never silently not_run. Require deterministic validators where possible, model judging only for open-ended quality, and human review for security or ambiguous promotions.
Reuse the installed skill-optimizer evidence schema and comparison scripts. Apply strict-improve to genuine hardening and no-regression only to metadata or maintenance changes. Do not install the external SkillOpt package unless a later benchmark proves the local harness insufficient.
Runtime safeguards
Codex CLI currently reports 0.144.0-alpha.4; probe its actual skill support before treating it as equivalent to the published minimum.
Hermes is installed but reports 581 commits behind. Do not update it automatically; mark Hermes runtime proof as blocked until separately approved and revalidated.
Antigravity has no confirmed managed skill publication target in the inspected surface; Devin has plans but no skill corpus. Produce packages/manifests only until their runtime discovery contracts are proven.
Preserve existing agents/openai.yaml files; do not add UI metadata to every skill without evidence that the target runtime consumes it.
ECC phase ledger
Route: ecc-prompt-optimize + skill-optimizer + agent-phase-ratchet.
Tier/mode: Tier 2, normal PhaseLoop; the installed dynamic-workflow classifier recommended no worker backlog.
Baseline: 733 canonical skills; 719 Codex-native validation failures; 283/283 shared copies drifted.
Checks: runtime inventory, native validator, cross-runtime hashes, installed optimizer/eval tooling, current primary-source research.
Decision: build the control plane and pilot before any global mutation.
Next adjustment: introduce parallel execution only after P2 proves disjoint batch ownership and the user explicitly authorizes worker execution.