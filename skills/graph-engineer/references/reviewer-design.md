# Reviewer Design

How to design independent reviewers with separate questions.

## Core Principle

Per @VibeMarketer_: "Never let an agent grade its own homework. Use separate
reviewers with separate questions: is it correct? is it current? is the source
real? Overlapping reviewers just repeat the same blind spots."

## Reviewer Design Rules

1. **One question per reviewer.** A reviewer checks exactly one dimension.
2. **Different agent or prompt.** The reviewer must not be the same agent as
   the worker it reviews.
3. **No overlapping questions.** Two reviewers on the same node must ask
   different questions. If they ask the same thing, one is redundant.
4. **Structured feedback.** A failed review produces: what failed, where (file:line
   or section), and what to fix. Not just "this is wrong."

## Standard Reviewer Questions

### Content / Marketing

| Reviewer | Question | What it catches |
|---|---|---|
| Correctness | "Is every factual claim verifiable with a cited source?" | Hallucinated facts |
| Currency | "Is all time-sensitive information current within the last 30 days?" | Stale data |
| Source | "Is every cited source a real, accessible URL or document?" | Fake citations |

### Code / Technical

| Reviewer | Question | What it catches |
|---|---|---|
| Logic | "Does the code do what the spec says?" | Implementation gaps |
| Edge-case | "What input breaks this?" | Unhandled edge cases |
| Security | "What attack surface does this expose?" | Vulnerabilities |

### Design / Product

| Reviewer | Question | What it catches |
|---|---|---|
| Usability | "Can a new user complete the core task without help?" | UX friction |
| Accessibility | "Does this meet WCAG 2.2 AA standards?" | a11y violations |
| Consistency | "Does this match the existing design system?" | Design drift |

## Anti-Patterns

| Anti-pattern | Why it fails |
|---|---|
| One reviewer checks everything | Blind spots repeat — the reviewer has the same biases as the worker |
| Same agent reviews its own work | Self-grading — the agent can't catch its own mistakes |
| Two reviewers ask the same question | Redundant — one reviewer is wasted budget |
| Reviewer gives a "looks good" pass | No evidence — the reviewer didn't actually check anything |
| No structured feedback on fail | Worker can't fix what it doesn't understand |

## How Many Reviewers?

- **Minimum:** 2 (two independent dimensions)
- **Recommended:** 3 (correctness, currency, source for content; logic, edge-case, security for code)
- **Maximum:** 5 (more reviewers add cost without proportional quality gain)

The number of reviewers should match the number of independent quality
dimensions that matter for the output. Adding more reviewers for the same
dimension is waste.
