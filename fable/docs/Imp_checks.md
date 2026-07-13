Current verified state & gaps
You  created useful snapshots, a dashboard, a registry, and 697 Codex/Claude projections. It is not yet safe to call the corpus fully refined:
Registry/dashboard/projections cover 697 skills, while the live corpus has 734.
695/697 Codex projections fail the real Codex validator, chiefly because the generator emits malformed YAML delimiters.
Projections are staged under .skill-hardening; they are not installed into the native Codex skill root.
Dashboard “health” is heuristic, not behavioral proof.
Existing routers contain stale counts and unavailable tool instructions, so they must not auto-route work yet.
Field	Decision
Tier	2 — corpus-wide, multi-runtime refinement
Primary skill	skill-optimizer
Subskills	conformance-gate, eval-harness, fuzz-regression, perf-ratchet
Auto-routing state	Disabled until P3 passes
Global publication	Requires P5 approval gate

Phase 0 — Freeze, reconcile, and block unsafe publication
Freeze current projections and dashboard as an audit snapshot; preserve live skills unchanged.
Rebuild the canonical manifest recursively from the live Windsurf corpus, excluding .skill-hardening.
Require exactly one record per logical skill, including path, canonical hash, runtime status, dependency declarations, risk tier, and prior projection hashes.
Reconcile all 734 live skills against the 697 baseline entries; classify the 37 omitted router/superpowers skills explicitly.
Mark every current projection blocked until it passes the actual bundled Codex quick_validate.py.
Exit criteria
Manifest count equals 734 exactly.
Every source skill has a hash and one lifecycle state.
No missing/extra projection is silently ignored.
Publication command refuses to run while any projection is invalid.
Phase 1 — Repair portability and validate real artifacts
Replace regex-based frontmatter rewriting with YAML parsing plus deterministic serialization.
Generate projections with a valid closing delimiter and newline; preserve body bytes after frontmatter.
For Codex projections, allow only Codex-supported keys: name, description, optional license, allowed-tools, and metadata.
Preserve Windsurf-specific fields only in the canonical source or runtime-override registry, never in Codex output.
Validate every projection with the actual Codex validator, not the custom heuristic validator.
Require projection cardinality, canonical hash, runtime hash, and validator result in the dashboard.
Exit criteria
734/734 Codex projections pass quick_validate.py.
No malformed YAML, name/path mismatch, invalid description, or unsupported field remains.
A source-to-projection hash manifest proves every projection came from the current canonical source.
No projection is installed yet.
Phase 2 — Replace heuristic health with behavioral certification
Create an evidence record per skill with these mandatory checks:
Schema and projection validity.
Trigger precision: direct, implicit, and competing prompts.
Scope control and safe failure on missing context.
Runtime/tool truth: no nonexistent tool, API, connector, or credential claim.
Security and secret handling.
Regression/boundary behavior for malformed or partial inputs.
Context efficiency: core instructions remain concise; conditional detail moves to references.
Dependency/script checks, where the skill includes executable assets.
Use five development scenarios and two held-out scenarios per applicable skill. not_applicable must include a reason; not_run fails promotion.
Certification gate
No P0/P1 safety issue.
All static checks pass.
≥97% weighted scenario pass rate.
No baseline scenario regression.
Skills below 8.5/10 improve by at least 1.5 points; higher-scoring skills require no regression.
High-risk skills require an independent reviewer or human approval before promotion.
Phase 3 — Build the auto-selection control plane
Replace fixed keyword routers with a registry-driven router. Each skill/plugin record must include:
{
  "id": "skill-name",
  "kind": "skill|plugin",
  "state": "candidate|canary|enabled|degraded|quarantined|disabled",
  "canonical_hash": "...",
  "domains": ["security", "testing"],
  "triggers": ["audit auth", "secret exposure"],
  "runtime_preconditions": ["tool:rg", "runtime:codex"],
  "risk_tier": "low|medium|high",
  "eval_pass_rate": 0.0,
  "fresh_until": "ISO-8601",
  "rollback_hash": "..."
}
Routing order:
Honor an explicit skill request only when that skill is enabled and runtime-ready.

Detect high-risk terms first: deploy, production, delete, migration, secret, credential, security, medical, financial.

Route high-risk work through the relevant safety/router skill; never auto-execute destructive or external-write actions.

Score eligible candidates:
0.45 intent match + 0.20 exact trigger + 0.15 runtime readiness + 0.10 eval reliability + 0.10 context efficiency

Auto-select one primary skill only if score ≥0.80 and leads the next candidate by ≥0.15.

At 0.55–0.79, invoke the domain router or ask one targeted clarification.

Below 0.55, use no specialized skill.

Add proof skills only when conditions demand them:

Condition / keywords	Required guard
skill, prompt, harden, plugin, evaluate	skill-optimizer
route, workflow, automation, connector	workflow-audit-router
security, auth, secret, permission	security review + conformance gate
latency, performance, benchmark, slow	perf-ratchet
malformed, edge case, regression, fuzz	fuzz-regression

Plugins may auto-activate only when the required tool is exposed, healthy, authorized, non-destructive, and fresh. Otherwise mark the plugin degraded and route to a safe fallback.
Exit criteria
Router tests cover all domain routers plus 100 adversarial/ambiguous prompts.
≥97% routing-fixture pass rate.
Zero unsafe auto-activation in high-risk fixtures.
Every decision emits a concise routing receipt: selected item, score, readiness, and fallback—never chain-of-thought.
Phase 4 — Automatic revocation and safe recovery
Use registry-state changes, not deletion, for automatic control.
Trigger	Automatic action
P0: secret leak, unguarded destructive action, privilege bypass	disabled; withdraw from routing; restore previous approved projection; incident record
P1: invalid schema, false tool claim, two failures in seven runs, three consecutive failures	quarantined; no auto-selection; create remediation task
Pass rate below 97% over latest 30 applicable scenarios	quarantined
Runtime dependency unavailable or evidence expired	degraded; manual use only with limitation notice
High-risk reference older than 7 days; other external integration older than 30 days	degraded pending refresh
Successful remediation, full eval, and canary proof	candidate → canary → enabled

Canary requires at least 30 applicable checks, no safety failure, and passed rollback drill.
External-write plugins never auto-promote beyond canary without explicit approval.
Never auto-delete a skill; preserve the last known-good hash and projection.
Exit criteria
Fault-injection tests prove disable, quarantine, degrade, rollback, and re-enable transitions.
Every enabled item has a verified rollback target.
Dashboard shows current state, reason, timestamp, expiry, and remediation owner.
Phase 5 — Runtime publication proof
Publish only validated projections through staging and atomic replacement.
Install into Codex only after its projection passes all P1/P2 gates.
Confirm actual runtime discovery in Codex, Windsurf, Hermes, Antigravity, and Devin; artifact presence alone is insufficient.
Keep unavailable targets deferred rather than fabricating installation claims.
Rewrite stale ecc-router instructions to use only currently exposed read/search tools and dynamic registry counts.
Exit criteria
Each enabled runtime shows the expected skill/plugin in its own discovery surface.
Installed hash equals the approved projection hash.
Runtime smoke test passes for activation, unavailable-tool fallback, and rollback.
Deferred runtimes are visibly marked unverified, not ready.
Phase 6 — Continuous refinement
On each skill change: run changed-only static checks, relevant scenarios, projection validation, and routing regression tests.
On runtime/version change: re-probe tools and mark dependent skills degraded until refreshed.
Maintain dashboard fields: baseline/current score, pass rate, routing precision, runtime state, expiry, P0/P1 count, canonical/projection hashes, and rollback availability.
Use SkillOpt-style bounded edits; retain rejected edits to prevent repeated failed “improvements.”
Do not create scheduled automation until separately approved; the initial trigger is manual change detection.
Final corpus exit criteria
100% canonical coverage.
100% valid projections for every enabled runtime.
≥97% behavioral pass rate with no unreviewed P0/P1 issue.
Zero stale or unavailable router/plugin auto-activations.
Every enabled skill/plugin is reversible by registry state and last-known-good hash.