---
name: deep-research
description: Multi-round, multi-source deep research on any topic. Iteratively searches the web, digs into primary sources, follows leads across rounds, and produces a cited research report with findings, evidence quality assessment, and open questions. Use for questions that need thorough investigation beyond a single search.
argument-hint: 'question or topic to research in depth'
allowed-tools: Bash, Read, Write, WebSearch, WebFetch, Agent
---

# deep-research: Thorough, Multi-Round Research with Citations

Deep research on a topic or question. Unlike a quick search, this runs multiple
research rounds, follows leads, checks sources against each other, and delivers
a cited report the user can act on.

## When to Use

Load this skill when the user:
- Asks an open question that needs investigation ("What's the current state of X?", "Compare A vs B and tell me which is right for us")
- Explicitly says "research this", "dig into this", "do deep research on X"
- Needs a decision backed by evidence, not one search result

Do NOT use for simple factual lookups (one search answers it) or for
last-30-days social-media research (use the `last30days` skill instead).

## Critical: Parse Intent First

Before searching, extract and display:

```
Deep research on {TOPIC}.

- Core question: {the actual question to answer}
- Scope: {boundaries — time range, geography, product category, etc.}
- Success looks like: {what the user will do with the answer}

Planning {3} research rounds. Starting now.
```

If the topic is ambiguous, pick the most reasonable interpretation and state
your assumption — do not block on a clarifying question unless the topic is
genuinely unresolvable.

## Research Loop

Run up to 3 rounds. Each round: search, read, record findings, and identify
what is still unknown.

**Round 1 — Map the territory**
- Run 2-4 broad searches covering the core question
- Identify key terms, players, competing viewpoints, and primary sources
- List open questions the round did NOT answer

**Round 2 — Chase the gaps**
- Search specifically for the open questions from Round 1
- Prefer primary sources: official docs, filings, papers, changelogs, original posts
- Open and read the top pages in full — do not judge from search snippets alone

**Round 3 — Stress-test (only if the first two rounds left real uncertainty)**
- Search for counter-evidence and critiques of what you found
- Check dates: is each claim current or superseded?
- Resolve contradictions between sources or flag them honestly

Stop early if Rounds 1-2 answered the question with high confidence and no
contradictions remain. Do not pad rounds to look thorough.

## Evidence Rules

- **Cite every claim.** Track source name + URL for each finding as you go.
- **Prefer primary over secondary.** Official docs beat blog posts; the actual
  paper beats a summary of the paper.
- **Date everything.** A claim from 2023 about a fast-moving topic is weak.
- **Separate fact from opinion.** Label what is established vs. contested vs. speculation.
- **Note conflicts.** If two credible sources disagree, say so rather than picking a winner silently.

## Report Format

```
# Research Report: {Topic}

## Bottom Line
2-4 sentences answering the core question directly. This is the part the
user reads if they read nothing else.

## Key Findings
1. {Finding} — per {source}
2. {Finding} — per {source}
3. {Finding} — per {source}

## Details
{Expand on the findings where nuance matters. Use short subsections if the
topic has natural parts. Include specifics: numbers, dates, names, versions.}

## Confidence & Caveats
- What is well-established (multiple independent sources)
- What is single-source or uncertain
- What changed recently or may change soon

## Open Questions
{What could not be determined and what would answer it}

## Sources
{Numbered list of source names with URLs}
```

## After the Report

Offer 1-2 concrete next steps based on what you found (e.g., "Want a decision
matrix comparing the top options?" or "Want me to monitor how X develops?").
Then stop — do not keep researching unprompted.
