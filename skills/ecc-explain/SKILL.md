---
name: ecc-explain
description: 'Explain any codebase, system, feature, or technical decision like an experienced product manager presenting to executives. Clear, concise, answers the "so what", makes complex topics super easy to understand, and drives toward a decision. Triggers: ''explain'', ''explain like a PM'', ''executive summary'', ''what does this do'', ''why does this matter'', ''so what'', ''summarize for leadership''.'
allowed-tools: Read, Bash
---

# ecc-explain — PM-Style Executive Explanation

> **Usage hint:** `explain X, explain like a PM, executive summary of X, what does this do, why does this matter`

Explain any codebase, system, feature, technical decision, or audit result in the style of an experienced product manager presenting to executives. Clear, concise, answers the "so what", makes complex topics super easy to understand, and drives toward a decision.

---

## Trigger Phrases

- "explain X", "explain like a PM", "executive summary of X"
- "what does this do", "why does this matter", "so what"
- "help me understand X for a stakeholder"
- "summarize this for leadership"

## When to Activate

- User asks for an explanation of a system, feature, codebase, or decision
- User needs to communicate technical work to non-technical stakeholders
- User wants a concise "so what" framing of complex work
- User is preparing for a review, demo, or executive update

## When NOT to Activate

- User asks for a deep-dive code-level explanation → use `understand-explain`
- User asks for an interactive visual explainer → use `poloclub-concept-explainer`
- User asks for a teach-back verification gate → use `human-understanding-gate`
- User asks for developer onboarding → use `codebase-onboarding`
- User asks for a research report with citations (not an explanation) → use `deep-research`
- User asks for a code audit (not an explanation of findings) → use `ecc-code-review` or `ecc-harness-audit`
- Note: If research or audit was already done, this skill CAN explain those findings for executives

## Evidence Gathering (Before Explaining)

Before writing the explanation, gather facts:
1. Read key files (README, AGENTS.md, plans, specs) to understand the system
2. Run `git log --oneline -20` to see recent activity
3. Check test status: `git status` and any test commands available
4. If `cass` is available, search for prior session context on the topic
5. If `gh` is available, check open PRs/issues for status context

Do NOT explain from memory alone — ground every claim in evidence.

## The PM Framework (BLUF — Bottom Line Up Front)

Every explanation follows the Pyramid Principle: **recommendation first, supporting detail second**. Executives decide in 60 seconds — give them what they need upfront, not buried at the end.

### 1. The Recommendation (Lead With the Ask)

State the conclusion and what you need from the audience in the first 2 lines. This is the most important section.

**Format:** "We have the opportunity to [business outcome] by [specific action]. I need [decision/approval/resource]."

If there is no decision to make (pure explanation), say so: "This is an informational briefing — no decision needed today."

### 2. The "So What" (Why It Matters)

Answer the executive's real question: "Why should I care?" Cover:
- **Business impact:** What changes if this works? What breaks if it doesn't?
- **Risk reduction:** What failure mode does this prevent?
- **Efficiency gain:** What time/cost/revenue impact does this have?
- **Strategic alignment:** How does this connect to broader goals?

Keep to 2-3 sentences maximum. Cut anything that doesn't change a decision.

### 3. The Status Table (Where We Stand)

A compact table showing current state — no more than 5-7 rows:

| Item | Status | Evidence |
|------|--------|----------|
| Component A | ✅ Working | Test passing, deployed to staging |
| Component B | ⚠️ Partial | 3 of 5 endpoints implemented |
| Component C | ❌ Missing | Not started, blocked on dependency X |

### 4. Key Decisions (3 Maximum)

State the most important decisions made. **Limit to 3** — cognitive load research shows executives retain 3 points, not 5. Format:
- **[Decision]:** [One-sentence why] (Alternative was: [alternative], rejected because: [reason])

### 5. What's Next (The Ask)

What needs to happen next, and what you need from the audience:
- Immediate next steps (next 1-2 weeks)
- Any decisions, approvals, or resources needed
- Risks or blockers that need attention

**Be explicit about the ask:** "I need budget approval by Friday" beats "We'd appreciate your input."

## Bad News Protocol

When delivering bad news, always include all 4 elements:
1. **What happened:** State the facts without spin
2. **Why it happened:** Root cause in one sentence
3. **What we're doing about it:** Corrective action with owner and timeline
4. **What we need from leadership:** Specific ask (resources, decision, timeline adjustment)

Never hide bad news. Executives respect PMs who surface problems early with a plan. Hiding bad news until it becomes a crisis destroys trust.

## Audience-Specific Reordering

The framework stays the same, but **reorder sections** based on who's reading:

| Audience | Lead With | Skip | Emphasis |
|----------|-----------|------|----------|
| **C-suite / Investors** | So What (revenue/cost/strategy) | Technical details | Business outcome, competitive position |
| **CTO / Engineering leadership** | Key Decisions + Status | So What (they already know) | Architecture risk, technical debt, velocity |
| **Product stakeholders** | What's Next + So What | Deep technical decisions | User impact, timeline, dependencies |
| **Cross-functional team** | Status Table | Key Decisions (unless cross-team) | "What this means for you" per team |

When audience is unspecified, default to C-suite ordering.

## Output Format

```
## [Topic Name] — Executive Summary

**Recommendation:** [One-sentence conclusion + what you need]

**So what:** [2-3 sentences on business impact]

### Status

| Item | Status | Evidence |
|------|--------|----------|
| ... | ... | ... |

### Key Decisions (3 max)

- **[Decision 1]:** [Why] (Alternative: [alt], rejected: [reason])
- **[Decision 2]:** [Why] (Alternative: [alt], rejected: [reason])

### What's Next

1. [Next step 1]
2. [Next step 2]

**Ask:** [Specific decision/approval needed, with deadline]
```

## Good vs Bad Example

**Good:**
> ## Auto-Revocation System — Executive Summary
>
> **Recommendation:** Approve the auto-revocation rollout — it prevents agent failures from missing CLI tools. No budget needed; implementation is complete.
>
> **So what:** Agents were silently failing when external tools (pytest, cargo, docker) were missing. This system detects gaps before execution and either fails loudly (required tools) or skips silently (optional tools). Eliminates a class of silent failures across 722 skills.
>
> **Ask:** No decision needed — informational briefing.

**Bad:**
> ## Auto-Revocation System
>
> We implemented a comprehensive auto-revocation mechanism across the ECC ecosystem. The system uses a three-class tool taxonomy (Core, Workflow, Advisory) to determine gating behavior. Core tools like git, ls, and cat are never gated. Workflow tools like pytest and cargo are checked with `command -v` and fail loud if missing. Advisory tools like cass and gh are wrapped with `2>/dev/null` and `|| true`...

*(Bad because: leads with implementation detail, no "so what", no ask, jargon without translation, no decision framing.)*

## Tone Rules

- **No jargon without translation.** If you must use a technical term, follow it with a plain-English equivalent in parentheses.
- **No "we" without context.** Executives don't know who "we" is. Use role names: "The engineering team...", "The agent system...".
- **No process descriptions.** Executives don't care HOW you built it. They care WHAT it does and WHY it matters.
- **No hedging.** Pick a clear position. "It might work" → "It works for X. It doesn't handle Y yet."
- **Evidence over assertion.** Every status claim needs evidence (test result, file, command output, deployment URL).
- **Brevity over completeness.** A 1-page summary beats a 5-page report. Cut anything that doesn't change a decision.
- **Numbers over adjectives.** "23% efficiency gain" beats "significant improvement." "722 skills" beats "many skills."

## Escalation (When This Skill Is Not Enough)

This skill explains findings; it does not generate them. Use these when you need deeper analysis first:
- `understand-explain` / `understand-chat` — when the user needs code-level architecture detail before you can explain
- `deep-research` — when the topic requires market/competitive data with citations
- `ecc-code-review` — when you need a quality audit before explaining project health
- `ecc-harness-audit` — when you need agent system health data
- `ecc-verify` — when you need verification evidence before explaining status

Flow: run the analysis skill → collect findings → use this skill to present them for executives.

## Dependency Gating

### Core tools (never gate):
- `git`, `cat`, `grep`, `find`, `head`, `tail` — used to read codebase and gather evidence

### Advisory tools (optional — silent skip if missing):
- `cass`: `command -v cass >/dev/null 2>&1 && cass search "<topic>" --robot --limit 5 --fields minimal 2>/dev/null || true` — use for cross-session context if available
- `gh`: `command -v gh >/dev/null 2>&1 && gh <args> 2>/dev/null || true` — use for PR/issue status if available

If an advisory tool is missing, skip the enrichment and proceed with local evidence only.

## Integration with Other Skills

This skill is a **presentation layer**, not a discovery layer. It consumes output from:
- `understand` / `understand-explain` — for codebase architecture facts
- `ecc-verify` / `verification-loop` — for status evidence
- `ecc-code-review` — for quality assessments
- `ecc-harness-audit` — for agent system health
- `deep-research` — for market/competitive context

It does NOT duplicate their analysis — it reformats their findings for executive consumption.

## Upstream Source

- Original concept: User request for PM-to-executive explanation style
- Framework enhanced with: BLUF/Pyramid Principle (Barbara Minto, McKinsey), 4-part executive summary formula, bad news protocol, audience-specific reordering, evidence-gathering workflow
