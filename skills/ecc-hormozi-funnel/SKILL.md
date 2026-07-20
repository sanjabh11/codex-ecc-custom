---
name: ecc-hormozi-funnel
description: >-
  Build GTM execution assets from positioning audit outputs using Alex Hormozi's
  $100M Funnel methodology. Five-prompt workflow: content batching machine,
  value equation offer builder, hook generator, authority builder, and funnel
  audit. Consumes positioning audit segments, hypotheses, and evidence corpus.
  Every output cites evidence IDs from the upstream audit. Run in sequence for
  full funnel build, or individually for specific assets.
  TRIGGER when: "content calendar", "offer creation", "value equation",
  "hook generation", "authority building", "funnel audit", "Hormozi funnel",
  "Grand Slam offer", "content batching", "proof assets", or "lead magnet
  rewrite" — especially after a positioning audit has been completed.
  DO NOT TRIGGER when: no positioning audit or product context is available,
  or the task is pure strategic positioning research without GTM/content intent.
allow_implicit_invocation: true
---

# ecc-hormozi-funnel

Use this skill to convert positioning audit findings into distributable GTM
assets: content calendars, offers, hooks, proof libraries, and funnel audits.
The upstream `ecc-niche-positioning-audit` produces the strategic foundation;
this skill produces the tactical execution layer.

## Scope Modes

| Mode | Prompts run | Use case |
|---|---|---|
| **quick** | 1 prompt (user picks) | Need one asset fast (e.g., just offers or just hooks) |
| **standard** | 3 prompts (1, 2, 3) | Content + offers + hooks for a GTM push |
| **deep** | All 5 prompts in sequence | Full funnel build with audit |

Default mode is `standard` unless the user specifies otherwise.

## Operating Contract

1. Consume a `positioning-audit-export.json` from a completed positioning audit.
   Every output cites evidence IDs, segment IDs, and hypothesis IDs from that
   audit. No output makes claims unsupported by the audit evidence corpus.
2. Run the five prompts in sequence for a full funnel build, or individually
   for specific assets. Each prompt produces schema-valid artifacts.
3. Score offers and hooks using deterministic formulas, not subjective vibes.
   The Value Equation composite and hook ranking scores are computed, not
   guessed. Composite scores are capped at 100.
4. Enforce proof-loop injection: at least 50% of content calendar entries cite
   evidence from the positioning audit. Content without proof is flagged.
5. Persist all outputs in `.hormozi-funnel/` with canonical schemas. Run the
   validator at each prompt boundary.
6. Call `ecc-advisor` at decision points: before ranking offers, before
   rewriting top hooks, and before finalizing the funnel audit. If advisor is
   unavailable, document the skip in state.
7. Run adversarial review on all outputs: a skeptic pass checks for unsupported
   claims, a missing-perspective pass checks for blind spots, and a contrarian
   pass checks for claims that contradict the evidence corpus.
8. Produce a decision confidence score for all outputs based on evidence
   quality, source coverage, and adversarial review survival.

## Direct References

| Need | Reference |
|---|---|
| integration contract with positioning audit | [integration-contract.md](references/integration-contract.md) |
| methodology sources, dates, applicability, limitations | [methodology-provenance.md](references/methodology-provenance.md) |

## Inputs and Outputs

**Required input:** `positioning-audit-export.json` produced by
`ecc-niche-positioning-audit`. This file contains segments, hypotheses,
evidence corpus, gap table, and decision confidence from the upstream audit.

**Optional inputs:** `existing_content` (for funnel audit), `existing_offers`
(for comparison scoring), `platform_priorities` (default: all 5 platforms),
`output_dir` (default `.hormozi-funnel/`).

**Outputs:** content calendar (`content-calendar.json`), offers
(`offers.json`), hooks (`hooks.json`), proof library
(`proof-library.json`), funnel audit (`funnel-audit.json`). All outputs are
schema-valid and cite positioning audit evidence IDs.

## Integration with Positioning Audit

The positioning audit produces a `positioning-audit-export.json` with:

- `audit_id`, `scope`, `decision_confidence`, `gate_decision`
- `segments[]` — ranked segments with pain, urgency, WTP, evidence IDs
- `hypotheses[]` — positioning hypotheses with status and evidence bundles
- `evidence_corpus[]` — all evidence items with grades and citations
- `gap_table[]` — 8-type gap classification with evidence citations
- `experiments[]` — validation experiments with results (if executed)

This skill consumes that export and never re-researches market positioning.
If no export is available, direct the user to run `ecc-niche-positioning-audit`
first.

## Prompt 1: Content Batching Machine

### Step 1: Extract Core Pillars

Extract 5-7 core content pillars from the positioning audit's top-ranked
hypotheses. Each pillar maps to a hypothesis ID and represents a defensible
positioning angle. For each pillar, list 10 subtopics derived from the
hypothesis's evidence bundle and the segment's pain points.

Pillar extraction rules:
- Each pillar cites at least one hypothesis ID from the positioning audit
- Subtopics are derived from evidence corpus items, not invented
- Pillars cover different awareness levels (unaware through product-aware)
- At least one pillar addresses the primary gap type from the audit

### Step 2: Repurpose Long-Form into Short-Form

Take one long-form audit finding (e.g., the gap table, a hypothesis analysis,
or the evidence reconnaissance) and repurpose it into 20 short-form ideas:
hooks, one-liners, and mini-stories. Each idea cites the evidence ID that
supports it.

Repurposing rules:
- Every short-form idea cites at least one evidence ID
- Ideas span all 4 hook formulas (pain, desire, proof, curiosity)
- No idea makes a claim unsupported by the evidence corpus
- Ideas are platform-agnostic at this stage; formatting happens in Step 3

### Step 3: Format Per Platform

Format each short-form idea for its target platform:

| Platform | Format | Char limit | Key constraints |
|---|---|---:|---|
| Twitter | Thread (up to 8 tweets) | 280 per tweet | Hook in tweet 1, proof in tweet 3, CTA in tweet 8 |
| Instagram | Carousel (up to 10 slides) | 2200 per slide | Visual-first, hook on slide 1, swipe prompt on slide 9 |
| TikTok | Script (60 seconds) | ~150 spoken words | Hook in first 3 seconds, proof in middle, CTA in last 5 seconds |
| LinkedIn | Post | 3000 characters | Professional tone, proof-led, no clickbait hooks |
| YouTube | Short (60s) or long-form (10min) | 5000 title/description | Hook in thumbnail + first 5 seconds, proof in first third |

### Step 4: Proof-Loop Injection

Ensure at least 50% of all content pieces include proof: case studies, stats,
results, or evidence citations from the positioning audit. The proof density
metric is calculated as `entries_with_proof / total_entries` and must be
>= 0.50.

Proof injection rules:
- Proof means citing a specific evidence ID with a concrete data point
- "We help companies grow" is not proof; "Client X grew 3x in 60 days (evidence
  ID: E-012)" is proof
- LOW-grade evidence cannot be used as proof in content
- Content without proof is allowed but flagged in the calendar

### Step 5: Batch into 30-Day Calendar

Distribute all formatted content into a 30-day calendar across pillars and
platforms. Ensure:
- Each pillar gets coverage across the 30 days
- Platform rotation prevents same-platform fatigue
- Proof-heavy content is spaced throughout, not clustered
- Each entry has a day, pillar, platform, content type, title, body, and
  `has_proof` flag

Output: `content-calendar.json` validated against
`schemas/content-calendar.schema.json`.

## Prompt 2: Value Equation Offer Builder

### Step 1: Extract Top 10 Burning Pains

From the positioning audit's segments and hypotheses, extract the top 10
burning pains. For each pain, record:
- The exact customer quote or evidence ID where the pain is expressed
- The segment ID where this pain is most acute
- The pain intensity (derived from the audit's segment ranking urgency score)

Pain extraction rules:
- Every pain cites an evidence ID from the positioning audit corpus
- Pains are stated in the customer's own words where possible
- Pains must be specific and observable, not vague sentiments
- "Thighs chafing" beats "feeling unhealthy" — specificity wins

### Step 2: Flip Each Pain into a Vivid Dream Outcome

For each pain, construct a dream outcome that is:
- **Concrete**: Specific, measurable result, not a vague aspiration
- **Emotional**: Tied to identity, status, or a life event
- **Time-bound**: Has a clear timeframe for achievement
- **Observable**: An alien or court witness could verify it happened

Dream outcome formula: "From [current pain state] to [specific desired state]
in [timeframe] so you can [identity/emotional outcome]."

Example: From "thighs chafing on every walk" to "fitting into your college
jeans by summer" in 12 weeks so you "feel confident at your reunion."

### Step 3: Build 10 Offers via the Value Equation

For each dream outcome, construct an offer using:

```
Value = (Dream Outcome x Perceived Likelihood) / (Time Delay x Effort & Sacrifice)
```

Each offer includes:
- **Core offer**: The primary product/service delivering the dream outcome
- **Bonus 1** (speed): Fast-start guide, templates, or done-for-you assets
- **Bonus 2** (effort): Tools, checklists, or automation that reduces effort
- **Bonus 3** (likelihood): Community, accountability, or support system
- **Bonus 4** (adjacent): Solves a related problem the customer didn't expect
- **Guarantee**: Risk reversal mechanism (unconditional, conditional, or
  performance-based)
- **Scarcity/urgency**: Real, not fabricated, limiting factor

### Step 4: Score Each Offer 1-10

Score each offer on four Value Equation dimensions:

| Dimension | 1 (weak) | 10 (irresistible) |
|---|---|---|
| Dream Outcome | Vague, generic | Specific, emotional, identity-tied |
| Likelihood | No proof, no guarantee | Specific case studies + performance guarantee |
| Time Delay | Results in 6+ months | Results in days or weeks |
| Effort & Sacrifice | High effort, many steps | Done-for-you, minimal effort |

Composite score: `(Dream x Likelihood) / ((11 - Time) x (11 - Effort)) x 10`,
capped at 100.

**Advisor checkpoint**: Before ranking offers, call `ecc-advisor` with the
 top 5 offers and their scores. Ask: "Are these scores calibrated correctly?
Am I missing a higher-value offer angle?" If advisor is unavailable, document
 the skip in state.

### Step 5: Rank and Rewrite Top 3

Rank all 10 offers by composite score. Take the top 3 and rewrite them to be
irresistible:
- Make the dream outcome more specific and emotional
- Add or strengthen proof elements (citing evidence IDs)
- Reduce time delay with quick-win bonuses
- Reduce effort with done-for-you elements
- Strengthen the guarantee
- Ensure scarcity/urgency is real and compelling

Output: `offers.json` — array of offer objects validated against
`schemas/offer.schema.json`.

## Prompt 3: Hormozi Hook Generator

### Step 1: Extract Hook Formulas

From the positioning audit's evidence corpus, extract hook examples for each
of the 4 formulas:

| Formula | Source | What it triggers |
|---|---|---|
| **Pain** | Customer quotes, support tickets, pain evidence | "That's my problem" |
| **Desire** | Dream outcomes, segment aspirations | "I want that" |
| **Proof** | Case studies, analytics data, results evidence | "They can do it" |
| **Curiosity** | Gap table findings, contradictions, unmet needs | "What happens next?" |

For each formula, extract 10 examples from the evidence corpus. Each example
cites the evidence ID it was derived from.

### Step 2: Generate Niche Hooks

For each pain (from Prompt 2, Step 1), generate 5 hooks per formula style:
- 5 pain hooks, 5 desire hooks, 5 proof hooks, 5 curiosity hooks
- 20+ hooks per pain
- Each hook is 10-15 words
- Each hook cites the evidence ID it's derived from
- Each hook is tagged with an awareness level (unaware, problem-aware,
  solution-aware, product-aware)

Awareness-level targeting:
- **Unaware**: Curiosity hooks — pattern interrupt, bold statement, surprise
- **Problem-aware**: Pain hooks — name the pain, show understanding, cost of
  inaction
- **Solution-aware**: Desire hooks — fastest way, simplest method, unique angle
- **Product-aware**: Proof hooks — case studies, specific numbers, testimonials

### Step 3: Rank Top 25 and Rewrite Top 10

Score each hook on three dimensions (1-10 each):
- **Clarity**: Is the message immediately understandable?
- **Curiosity**: Does it create an open loop the brain needs to close?
- **Pull**: Does it make the target audience feel "this is about me"?

Composite = average of clarity, curiosity, and pull.

**Advisor checkpoint**: Before rewriting the top 10 hooks, call `ecc-advisor`
with the top 25 hooks. Ask: "Which hooks would stop your scroll? Which feel
generic?" If advisor is unavailable, document the skip in state.

Rank all hooks by composite score. Take the top 25 and then rewrite the top 10
in 3 formats:
1. **Video hook**: Spoken in first 3 seconds of a video
2. **Written hook**: First line of a post, thread, or email
3. **Thumbnail text**: 5-7 words for a visual thumbnail

Output: `hooks.json` — array of hook objects validated against
`schemas/hook.schema.json`.

## Prompt 4: Hormozi Authority Builder

### Step 1: Gather and Categorize Proof

From the positioning audit's evidence corpus, gather all proof assets and
categorize them into 4 types:

| Category | What it contains | Evidence types |
|---|---|---|
| **Quantitative** | Numbers, metrics, growth stats | `analytics_data`, `sales_data`, `pricing_signal` |
| **Qualitative** | Testimonials, quotes, feedback | `user_quote`, `support_ticket`, `stakeholder_input` |
| **Transformation** | Before/after, case studies, journeys | `customer_outcome`, `behavioral_observation` |
| **Authority** | Credentials, media, third-party validation | `competitor_intel`, `codebase_evidence` |

Each proof asset cites its evidence ID from the positioning audit.

### Step 2: Rewrite Each Proof in 3 Formats

For each proof asset, produce:
- **Short** (1 sentence): "Client X grew revenue 3x in 60 days."
- **Mid** (1 paragraph): "Client X came to us struggling with stagnant growth.
  After implementing our framework, they tripled revenue in 60 days — from
  $50K to $150K MRR."
- **Long** (1 page): Full case study with challenge, solution, implementation,
  results, and quote.

### Step 3: Fuse Proof with Stories

Create 20 sticky proof-stories that combine logic (data) with emotion
(narrative). Each story:
- Opens with a relatable pain or situation
- Introduces the proof element (data, result, transformation)
- Resolves with the emotional outcome (identity, status, relief)
- Cites the evidence ID(s) that support the factual claims
- Is 150-300 words

Sticky story rules:
- Specificity over sentiment: "12,847 brands" beats "thousands of customers"
- Observable reality: if an alien or court witness couldn't see it, don't
  write it
- Before-after-bridge structure for transformation stories
- No hollow blue words: "trust," "energy," "manifestation" — replace with
  observable behaviors

Output: `proof-library.json` — array of proof assets with categories, formats,
and stories.

## Prompt 5: Funnel Audit

### Step 1: Awareness Audit

Stress-test the current funnel's awareness layer:

1. **Hook audit**: Review all hooks currently in use (ads, landing pages,
   content). Score each on pain articulation, specificity, and attention-grab.
   Flag hooks that open with feature lists instead of pain.
2. **Messaging audit**: Review messaging across the funnel. Score on clarity,
   proof density, and Value Equation alignment. Flag messaging that uses
   hollow blue words.
3. **Proof upfront audit**: Check whether proof appears above the fold on
   landing pages and in the first 3 seconds of video content. Flag pages
   where proof is buried below the fold.
4. **Attention leak detection**: Identify where attention drops — long
   intros, feature lists, vague promises, missing CTAs. Each leak gets a
   severity score and location tag.
5. **10 fixes**: Produce 10 prioritized fixes for the awareness layer, each
   with an expected impact and evidence citation.

### Step 2: Lead Capture Audit

Score the current lead capture mechanism on the Value Equation:

1. **Opt-in score** (1-10): How compelling is the lead magnet?
2. **Value Equation scoring**: Score the opt-in on Dream Outcome, Likelihood,
   Time Delay, and Effort. A free checklist that delivers immediate value
   scores high; a vague "newsletter" scores low.
3. **Friction audit**: Identify every friction point in the opt-in flow:
   - Too many form fields
   - Slow page load
   - Unclear value proposition
   - Too many steps
   - No proof on the opt-in page
   - Weak or buried CTA
4. **Kill friction**: For each friction item, produce a specific fix.
5. **Rewrite weakest magnet**: Identify the weakest lead magnet and rewrite
   it using the Value Equation framework. The rewrite must cite evidence IDs
   from the positioning audit.

Output: `funnel-audit.json` validated against
`schemas/funnel-audit.schema.json`.

**Advisor checkpoint**: Before finalizing the funnel audit, call `ecc-advisor`
with the audit findings and fix list. Ask: "Am I missing any attention leaks?
Are these fixes prioritized correctly?" If advisor is unavailable, document
the skip in state.

## Adversarial Review

After all prompts complete, run three adversarial passes on every output:

1. **Skeptic pass**: For each offer, hook, content piece, and proof asset,
   challenge every claim. Does it cite a valid evidence ID? Is the evidence
   HIGH or MEDIUM grade? Is the claim observable and specific? Flag any
   unsupported claims for removal or revision.
2. **Missing-perspective pass**: What audience segment or pain point is not
   addressed by the current outputs? Are there evidence corpus items that
   were not used? Flag gaps for potential additional content.
3. **Contrarian pass**: Does any output contradict the positioning audit's
   findings or evidence corpus? Does any offer promise something the audit's
   evidence doesn't support? Flag contradictions for resolution.

Record adversarial review results in state. Unresolved contradictions block
the final output.

## Decision Confidence

Produce a decision confidence score for all outputs:

```text
composite = evidence_quality(0..30) + source_coverage(0..25)
          + adversarial_survival(0..25) + advisor_confirmed(0..20)
```

| Score | Band | Action |
|---|---|---|
| 80-100 | High | Ship outputs as-is |
| 60-79 | Moderate | Ship with flagged caveats |
| 40-59 | Low | Revise weak outputs before shipping |
| <40 | Critical | Do not ship — re-run affected prompts |

Advisor confirmation score: 20 if advisor was called at all decision points,
10 if called at some, 0 if never called or unavailable.

## Tool Truth

### Enforcement Rules

1. **Positioning audit export is required** — this skill does not re-research
   market positioning; it consumes upstream audit outputs
2. **Every output cites evidence IDs** — offers, hooks, content, and proof
   assets must cite positioning audit evidence corpus IDs
3. **Value Equation scores are computed, not guessed** — the composite formula
   is deterministic: `(Dream x Likelihood) / ((11 - Time) x (11 - Effort)) x 10`
4. **Hook ranking scores are computed, not guessed** — composite is the
   average of clarity, curiosity, and pull
5. **Proof density is enforced** — at least 50% of content calendar entries
   must cite evidence; the metric is calculated, not estimated
6. **Scarcity and urgency must be real** — fake scarcity destroys trust
   permanently; the `is_real` field must be true
7. **LOW-grade evidence cannot be used as proof** — only MEDIUM and HIGH
   evidence items qualify as proof in content and offers
8. **Content calendar is a plan, not an engagement guarantee** — producing a
   calendar does not guarantee views, clicks, or conversions
9. **Hooks are messaging hypotheses, not conversion guarantees** — hook
   performance requires testing with real audiences
10. **Offers are constructs, not market validation** — an offer scoring 10/10
    on the Value Equation is still unvalidated until tested with real buyers
11. **Proof stories fuse logic and emotion** — data without narrative is dry;
    narrative without data is hollow; both are required
12. **Specificity beats sentiment** — "12,847 brands" beats "thousands of
    customers"; observable reality beats hollow blue words
13. **Platform formatting is mandatory** — content must be formatted per
    platform constraints (char limits, format types, visual cues)
14. **Funnel audit fixes are prioritized** — P0 fixes address critical
    attention leaks; P1 fixes address major friction; P2 fixes are
    optimizations
15. **No output makes claims unsupported by the evidence corpus** — if the
    positioning audit didn't find evidence for a claim, this skill doesn't
    make that claim
16. **Run the validator at each prompt boundary** — use
    `scripts/validate_skill.py` to verify schema compliance and tool truth
    rules after each prompt
17. **Advisor checkpoints are mandatory at decision points** — before offer
    ranking, hook rewriting, and funnel audit finalization; if `ecc-advisor`
    is unavailable, document the skip in state
18. **Adversarial review is mandatory before shipping** — skeptic,
    missing-perspective, and contrarian passes must complete; unresolved
    contradictions block output
19. **Decision confidence is computed, not guessed** — the 4-subscore formula
    is deterministic; advisor confirmation is scored based on call coverage
20. **Composite scores are capped at 100** — the Value Equation formula can
    produce very high values when time and effort are both 10; cap prevents
    misleading scores

## Artifact and State Contract

All outputs are persisted in `.hormozi-funnel/` with canonical schemas:

| Artifact | Schema | Filename |
|---|---|---|
| Content calendar | `schemas/content-calendar.schema.json` | `content-calendar.json` |
| Offers | `schemas/offer.schema.json` | `offers.json` |
| Hooks | `schemas/hook.schema.json` | `hooks.json` |
| Proof library | `schemas/proof-library.schema.json` | `proof-library.json` |
| State | `schemas/state.schema.json` | `state.json` |
| Funnel audit | `schemas/funnel-audit.schema.json` | `funnel-audit.json` |

Use `scripts/validate_skill.py` to verify all artifacts. The validator checks
schema compliance, evidence citation presence, proof density thresholds, and
tool truth rule counts.

## Backing Skills

- `ecc-advisor` — for advisor checkpoints at decision points
- `ecc-content-quality-ops` — for content quality gating on calendar entries
- `ecc-niche-positioning-audit` — upstream skill producing the required input

## Platform Compatibility

Works across all harnesses:

- **Cascade / Claude Code** — full functionality with native advisor API
- **Codex** — full functionality with Codex-Orchestration advisor
- **Windsurf / Devin** — full functionality with Grok CLI advisor fallback
- **Anti-Gravity** — full functionality with Grok CLI advisor fallback

If no advisor backend is available, the skill proceeds with documented skips
and reduced decision confidence (advisor_confirmed = 0).

## Upstream Source

- Origin: user request to integrate Hormozi $100M Funnel methodology with
  positioning audit outputs.
- Methodology registry: [methodology-provenance.md](references/methodology-provenance.md).
- Integration contract: [integration-contract.md](references/integration-contract.md).
- v8.1 release: 6 schemas (added state, proof-library), 5-prompt workflow,
  advisor checkpoints, adversarial review, decision confidence, scope modes,
  validator, 3 behavioral scenarios, evidence traceability to positioning audit.
