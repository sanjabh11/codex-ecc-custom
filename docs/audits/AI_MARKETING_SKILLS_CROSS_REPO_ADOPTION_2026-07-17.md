# AI Marketing Skills Cross-Repository Adoption Audit

**Audit date:** 2026-07-17
**Upstream source:** [ericosiu/ai-marketing-skills](https://github.com/ericosiu/ai-marketing-skills) pinned to [a9f11007](https://github.com/ericosiu/ai-marketing-skills/commit/a9f11007aca31cc85f231698e22b64412f847b76)
**Canonical implementation:** `/Users/sanjayb/codex-ecc-custom`
**Decision:** adapt ten capabilities into ECC-native, evidence-gated skills; do not install the upstream package.

## Executive Finding

The upstream snapshot contains 22 skill directories, 57 Python files, no test files, lower-bounded dependencies, optional telemetry, live API/CRM/campaign paths, and Claude-specific assumptions. Basic Codex frontmatter screening passed 11 of 22 SKILL.md files and failed 11. The retained patterns are useful as a workflow library, but unsafe as a direct package import.

The five audited repositories have strong repository-side proof systems but limited first-party validation. The highest-value additions are therefore measurement, buyer-evidence, and claim-governance loops—not additional media-production volume.

## Current-Truth Fingerprints

| Repository | Implementation surface | Current product/evidence boundary |
|---|---|---|
| Career Automation Insights Engine | 2,083 tracked / 343 source / 98 test-spec / 67 edge functions / 128 scripts | Decision-support APO dashboard; evidence-limited, validation pending (confidence 68). No scientific-validation, broad-traction, or live-payment claims. |
| Canada Energy Intelligence Platform | 1,550 tracked / 408 source / 224 test-spec / 21 workflows / 110 edge functions / 118 scripts | Canadian utility/TIER proof packs; evidence-limited, validation pending (confidence 74). Accepted hash-verified buyer evidence controls confidence; no guaranteed savings or certification claims. |
| codex-ecc-custom | 300 tracked / 75 skills / 32 test-spec files | Canonical ECC corpus and Fable workflows; skill value must be shown by scenarios and runtime parity. Do not treat cache presence or installs as adoption proof. |
| Strategic Intelligence Platform | 432 tracked / 122 source / 54 test-spec / 69 edge functions / 97 scripts | Governed strategic-intelligence pilot; implementation-only confidence 76, hosted/market validation 0. No live-feed, calibrated-accuracy, procurement, or revenue claims without evidence. |
| Avalanche Insight Hub | 1,489 tracked / 194 source / 12 workflows / 12 edge functions | DRDO/DGRE-aligned pre-production research prototype with scientific safety gates. Use governed ML augmentation/comparative validation; no official-warning, replacement, or broad-rollout claims. |

## Scoring

Each repository relevance score is out of 5.0: product/buyer fit (30%), commercial or operational impact (25%), integration readiness (20%), measurability (15%), and safety/maintenance (10%). Portfolio rank is the five-repository mean, with tie-breaks for more scores at or above 4.0, lower risk, and less redundant behavior.

## Top-10 Matrix

| Rank | Upstream | ECC-native skill | Career | CEIP | ECC | Strategic | Avalanche | Avg | Existing overlap | Action | Principal risk |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| 1 | closed-loop-analytics-upgrade | `ecc-closed-loop-analytics` | 4.8 | 4.9 | 5.0 | 4.8 | 4.8 | 4.9 | agent-phase-ratchet, skill-optimizer, marketing-campaign | Create | Analytics availability and attribution quality |
| 2 | growth-engine | `ecc-growth-experiment-loop` | 4.5 | 4.7 | 4.8 | 4.6 | 4.4 | 4.6 | agent-phase-ratchet, ecc-niche-positioning-audit | Create | Low traffic or premature winner calls |
| 3 | revenue-intelligence | `ecc-revenue-attribution` | 4.6 | 4.9 | 4.0 | 4.8 | 4.6 | 4.6 | commercial-launch-readiness-orchestrator, customer-billing-ops | Create | Sparse joins and causal overclaim |
| 4 | lead-dossier | `ecc-lead-dossier` | 4.5 | 4.9 | 3.8 | 4.8 | 4.9 | 4.6 | lead-intelligence, ecc-niche-positioning-audit | Create | PII, scraped data, invented intent |
| 5 | outbound-engine | `ecc-outbound-campaign` | 4.4 | 5.0 | 3.6 | 4.8 | 4.8 | 4.5 | lead-intelligence, marketing-campaign | Create | Consent, suppression, accidental sending |
| 6 | content-ops | `ecc-content-quality-ops` | 4.4 | 4.6 | 4.3 | 4.5 | 4.5 | 4.5 | content-engine, brand-voice | Create | Simulated scores mistaken for proof |
| 7 | sales-playbook | `ecc-value-pricing` | 4.5 | 4.8 | 3.8 | 4.7 | 4.7 | 4.5 | commercial-launch-readiness-orchestrator, ecc-niche-positioning-audit | Create | Invented ROI or willingness-to-pay |
| 8 | sales-pipeline | `ecc-buyer-pipeline` | 4.3 | 4.8 | 3.7 | 4.7 | 4.6 | 4.4 | lead-intelligence, commercial-launch-readiness-orchestrator | Create | CRM writes and false qualification |
| 9 | conversion-ops | `ecc-conversion-audit` | 4.4 | 4.7 | 3.5 | 4.5 | 4.3 | 4.3 | landing-page-conversion-auditor, accessibility | Create | Heuristic scores presented as uplift |
| 10 | seo-ops | `ecc-seo-opportunity-loop` | 4.0 | 4.4 | 3.4 | 4.2 | 4.1 | 4.0 | seo, content-engine, ecc-closed-loop-analytics | Create | Credential gaps and unsupported content |

## Threat Model and Import Decisions

| Surface | Finding | Decision |
|---|---|---|
| Provenance | Public MIT repository, pinned to one commit, no release artifact | Record URL, commit, source skill, and license in each manifest |
| Skill contract | 11/22 fail basic frontmatter placement or required-field screening | Rebuild Codex frontmatter and triggers |
| Tests | No upstream test files; eval runner does not cover all scripts | Add a dependency-free validator and 70 deterministic scenarios |
| Dependencies | All requirements are lower-bounded; media/analytics lanes are heavy or credentialed | Add no v1 runtime dependencies |
| Telemetry | Relative version/opt-in telemetry preambles appear across skills | Remove all telemetry and background behavior |
| Credentials | GSC, Ahrefs, HubSpot, Instantly, RB2B, Google, Anthropic, OpenAI, and YouTube paths appear | Return `unavailable` when absent; never print or persist secrets |
| External writes | CRM tasks, campaign enrollment, uploads, webhooks, publishing, and messaging are possible | Draft/dry-run by default; explicit approval for every mutation |
| Process execution | Media skills invoke ffmpeg, yt-dlp, Whisper, subprocesses, and deletion | Defer media skills; import no scripts |
| Claims | Simulated panels and scores can be mistaken for proof | Label heuristics; real analytics, buyer evidence, and scientific gates remain authoritative |

## Complete 22-Skill Disposition

| Upstream skill | Score | Decision | Reason |
|---|---:|---|---|
| closed-loop-analytics-upgrade | 4.9 | Adopt as `ecc-closed-loop-analytics` | Retain bounded behavior; remove vendor/runtime assumptions. |
| growth-engine | 4.6 | Adopt as `ecc-growth-experiment-loop` | Retain bounded behavior; remove vendor/runtime assumptions. |
| revenue-intelligence | 4.6 | Adopt as `ecc-revenue-attribution` | Retain bounded behavior; remove vendor/runtime assumptions. |
| lead-dossier | 4.6 | Adopt as `ecc-lead-dossier` | Retain bounded behavior; remove vendor/runtime assumptions. |
| outbound-engine | 4.5 | Adopt as `ecc-outbound-campaign` | Retain bounded behavior; remove vendor/runtime assumptions. |
| content-ops | 4.5 | Adopt as `ecc-content-quality-ops` | Retain bounded behavior; remove vendor/runtime assumptions. |
| sales-playbook | 4.5 | Adopt as `ecc-value-pricing` | Retain bounded behavior; remove vendor/runtime assumptions. |
| sales-pipeline | 4.4 | Adopt as `ecc-buyer-pipeline` | Retain bounded behavior; remove vendor/runtime assumptions. |
| conversion-ops | 4.3 | Adopt as `ecc-conversion-audit` | Retain bounded behavior; remove vendor/runtime assumptions. |
| seo-ops | 4.0 | Adopt as `ecc-seo-opportunity-loop` | Retain bounded behavior; remove vendor/runtime assumptions. |
| content-eval | 3.9 | Defer | Mostly overlaps content-quality-ops; prompt-only and no independent evidence gate. |
| deck-generator | 3.9 | Defer | Existing Slides skill is stronger; requires Gemini and Google Slides credentials. |
| finance-ops | 3.8 | Document | Useful but outside the marketing-first objective and sensitive finance data. |
| autoresearch | 3.7 | Reject direct adoption | Simulated panel may optimize to the evaluator and be mistaken for validation. |
| x-longform-post | 3.6 | Defer | Narrow channel behavior overlaps Content Engine and forces style rules. |
| yt-competitive-analysis | 3.4 | Defer | No YouTube-led acquisition lane evidenced across the five repos. |
| short-form-pipeline | 3.3 | Defer | Heavy media dependency and no recurring source pipeline evidenced. |
| video-clip-pipeline | 3.2 | Defer | Duplicates short-form behavior and adds subprocess/upload risk. |
| podcast-ops | 3.1 | Defer | No active podcast corpus or publishing cadence evidenced. |
| video-caption-generator | 3.0 | Defer | Drive and transcription tooling not verified in current workflow. |
| team-ops | 2.7 | Reject | Low solo-operator fit and disproportionate HR/privacy risk. |
| clone-site | 2.0 | Reject | Copyright/trade-dress risk and Claude Chrome/worker assumptions. |

## Implementation and Verification

- Ten packages were created under `skills/`; each has SKILL.md, `agents/openai.yaml`, five-repository profiles, and upstream adoption evidence.
- All workflows are dependency-free and preserve proof buckets: hosted/live, local, repository artifact, candidate/shadow, and roadmap.
- Every workflow defaults to draft/dry-run and uses `unavailable` for missing credentials, consent, data, or tools.
- A shared validator and 70-scenario evidence suite enforce seven scenarios per skill: supportive, neutral, competing, five-repository claim-boundary coverage, and unavailable-state behavior.
- Projection is gated on canonical validation; global copies are derived artifacts and will not be mutated until the canonical source passes.

## Residual Risks

- Scores are evidence-backed judgments, not market validation.
- Live analytics, CRM, GSC, payment, and outreach checks remain unverified without user-authorized credentials.
- Scenario evidence validates contracts and safety defaults, not downstream commercial outcomes.
- Four repositories had dirty worktrees; only `codex-ecc-custom` is modified.
