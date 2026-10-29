---
name: ecc-multi-model-blindspot
description: >-
  Multi-model blindspot detection and adversarial cross-review. Dispatches a
  task to N independent models, collects their responses, then cross-reviews
  each model's output against the others to surface blind spots, disagreements,
  and risks before shipping. Use when stakes are high, multiple valid approaches
  exist, or a single model's output may miss critical edge cases. Triggers on
  "blindspot review", "cross-model check", "multi-model review", "what am I
  missing", "adversarial review", "second opinion from multiple models".
---

# Multi-Model Blindspot Review

Surface AI blindspots before shipping by putting multiple models on the same
task and cross-reviewing their outputs for disagreements, gaps, and risks.

## When to Use

- High-stakes decisions where a single model's blind spot could cause real damage
- Architecture choices with multiple valid approaches (monolith vs microservices, SQL vs NoSQL)
- Security reviews where one model may miss an attack vector
- Research synthesis where coverage breadth matters
- Pre-merge review of complex changes
- Any task where "what am I missing?" is the key question

## When NOT to Use

- Trivial one-liner fixes (use `ecc-build-fix` instead)
- Single-model code review (use `ecc-code-review` instead)
- Dual-model adversarial review (use `santa-method` instead)
- Four-voice structured disagreement (use `council` instead)

## Workflow

### Phase 1: Dispatch (Discover)

1. Identify the task, question, or artifact to review
2. Select N models (2-8) based on availability and task domain
3. Send the same prompt to each model independently
4. Collect all responses without cross-contamination

**Model Selection Guide:**

| Task Type | Recommended Models |
|-----------|-------------------|
| Code review | Claude, GPT, Gemini, Grok |
| Security audit | Claude, GPT, local model (privacy) |
| Architecture decision | Claude, Gemini, Qwen, Copilot |
| Research synthesis | Perplexity, Gemini, Claude, Copilot |
| Edge-case hunting | All available — diversity matters most |

### Phase 2: Cross-Review (Define)

1. Present each model's response to all other models
2. Ask each model: "What did [Model X] get right that you missed? What did they get wrong?"
3. Collect structured disagreement reports
4. Identify consensus points (all models agree) and blind spots (unique to one model)

### Phase 3: Synthesize (Develop)

1. Merge consensus points as high-confidence findings
2. Flag disagreements for human review
3. Surface unique insights from individual models as blind-spot candidates
4. Produce a blindspot report with confidence levels:
   - **Consensus** (all models agree): High confidence
   - **Majority** (>= 75% agree): Medium confidence
   - **Minority** (1-2 models only): Blindspot candidate — requires human judgment

### Phase 4: Deliver

1. Output the blindspot report with:
   - Consensus findings (safe to act on)
   - Majority findings (likely safe, verify)
   - Blindspot candidates (human must decide)
   - Model disagreement map (which models disagreed on what)
2. Include a go/no-go recommendation based on consensus threshold
3. Log the review for future reference

## Integration with Existing Skills

- **`ecc-multi-backend`**: Provides the multi-model dispatch infrastructure
- **`ecc-multi-execute`**: Handles parallel model execution
- **`ecc-multi-plan`**: Plans the multi-model workflow
- **`santa-method`**: Use for 2-model adversarial review (simpler, faster)
- **`council`**: Use for 4-voice structured disagreement (fixed panel)
- **`ecc-quality-gate`**: Can invoke this skill as a pre-merge quality gate
- **`ecc-verify`**: Can invoke this skill for high-stakes verification
- **`ecc-ml-engineering`**: Use for cross-model ML recipe and training review

## Use Case: Spec Review (Adversarial Spec Consensus)

This skill can be used for multi-model spec/PRD review — adapted from
[zscole/adversarial-spec](https://github.com/zscole/adversarial-spec) (1.2k+ stars).

### Workflow

1. **Dispatch**: Send the spec/PRD to N models with this prompt:
   ```
   Review this specification for: missing requirements, ambiguous
   definitions, untested edge cases, security gaps, and scope creep.
   For each finding: cite the specific section, explain the gap, and
   propose a fix.
   ```
2. **Cross-Review**: Share each model's findings with the others:
   ```
   Another model found these gaps in the spec: {findings}
   Do you agree? What did they miss? What is wrong?
   ```
3. **Synthesize**: Merge findings into consensus/majority/minority categories
4. **Deliver**: Produce a revised spec with all consensus fixes applied,
   majority fixes flagged, and minority findings listed for human review

### When to Use Spec Review Mode

- Before implementing a complex feature (catch gaps before coding)
- When reviewing a PRD or technical spec
- For conformance gate evidence (multi-model agreement on verdict)
- Before architecture decisions where "what am I missing?" matters

## Consensus Threshold

Default: **75% agreement** required to mark a finding as "majority confidence."
Below 75% = blindspot candidate requiring human judgment.
Unanimous agreement = consensus (high confidence, safe to act on).

## Dispatch Prompt Template

```
You are reviewing: {task_description}

Context/artifact under review:
{artifact_or_code}

Your task: Analyze this for {review_type} (security issues, architectural
risks, edge cases, missing requirements, performance problems).

Return your findings as a structured list:
- Finding: [concise description]
- Severity: [critical/high/medium/low]
- Evidence: [specific code reference or reasoning]
- Recommendation: [actionable fix]
```

### Cross-Review Prompt Template

```
You previously analyzed: {task_description}

Here is what another model found:
{other_model_findings}

Questions:
1. What did they get right that you missed?
2. What did they get wrong?
3. Are there any findings you disagree with? Why?
4. What additional blind spots do you see?
```

## Single-Model Fallback

If only 1 model is available (all others offline, API errors, or rate-limited):
1. Run the review with the single available model
2. Flag the result as "single-model — no cross-review"
3. Recommend human review of the output before acting on high-severity findings
4. Log the degraded state for audit trail
5. Do NOT claim consensus or majority confidence — mark all findings as "unverified"

## Cost Awareness

Each model invocation costs tokens. N models = N x prompt tokens + N x response
tokens + N x (N-1) cross-review tokens. For 4 models: ~4x prompt + 4x response +
12x cross-review. Use fewer models for lower-stakes tasks.

## Cross-IDE Compatibility

This skill is a pure workflow pattern — no runtime dependencies:
- **Windsurf**: SKILL.md auto-discovered, uses native multi-model dispatch
- **Devin**: SKILL.md injected as context, models dispatched via API calls
- **Autogravity**: SKILL.md read as agent capability, dispatches via available models
- **Codex**: `agents/openai.yaml` provides Codex agent definition, uses `ecc-multi-backend`

## Auto-Revocation

This skill depends on `ecc-multi-backend` / `ecc-multi-execute` for model
dispatch. These are **Advisory tools** — if multi-model infrastructure is
unavailable, the skill degrades gracefully.

### Tool Taxonomy

| Class | Tool | Gating Behavior |
|-------|------|----------------|
| **Core** | `grep`, `cat`, `diff` | Never gate — used for artifact comparison |
| **Advisory** | `ecc-multi-backend`, `ecc-multi-execute` | `command -v` or skill availability check. If absent: degrade to single-model fallback (see Single-Model Fallback section). Wrap with `2>/dev/null` and `\|\| true`. Never block. |
| **Advisory** | External model APIs (OpenAI, Gemini, Grok, etc.) | API key check. If absent: skip that model silently. Never block on any single provider. |

### Degradation Path

1. All models available → full N-model cross-review with consensus
2. Some models available → reduced cross-review, flag as "partial cross-review"
3. One model available → single-model fallback (see Single-Model Fallback section)
4. No models available → manual review guidance only, flag as "no model review"

## Upstream Source

Concept adapted from [Claude Octopus](https://github.com/nyldn/claude-octopus) (3.8k stars) — multi-provider blindspot detection with consensus gates. Original is a Claude Code plugin; this is a portable skill pattern.
