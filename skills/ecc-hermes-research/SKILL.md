---
name: ecc-hermes-research
description: >-
  Personal research assistant skill for the Hermes workflow. Runs vault-first
  research across financial, administrative, and project domains using exa,
  firecrawl, and search-console MCPs. Enforces output contracts, dedup checks,
  cost caps, and failure policies. Writes results to HermesBrain vault with
  provenance and frontmatter.
---

# ecc-hermes-research — Hermes Personal Research Assistant

## Activation Hints

Use this skill for requests containing terms such as `hermes research`,
`research ticker`, `financial review`, `flag bills`, `scan subscriptions`,
`monday review`, `personal research assistant`, or `hermes sweep`.

## When to Use

- Researching tickers, entry points, or fundamentals for personal investing
- Scanning bills/subscriptions for increases or unused services
- Running the Monday 8am financial review
- Any personal research task that should write to HermesBrain vault
- Tasks requiring the personal profile at `~/second-brain/Contract/personal-profile.md`

## Explicit Research Domains

This skill is **not** a generic search wrapper. It handles exactly these domains:

| Domain | Example Tasks | Primary MCP |
|---|---|---|
| **Financial research** | Ticker entry points, fundamentals, filings | exa + firecrawl |
| **Bill/subscription audit** | Flag increases, find unused services | firecrawl (email/bank portals) |
| **Project research** | Support ongoing projects with web evidence | exa |
| **Market scanning** | Sector trends, competitor moves | exa + search-console |

Out of scope: code research, academic paper search (use `deep-research`), lead generation (use `ecc-lead-dossier`).

## Workflow — Vault-First Gate (MANDATORY)

Every research task follows this order. No exceptions.

### Step 1: Vault-First Gate
Before any web/MCP call, search HermesBrain for existing coverage using the enforcement wrapper (structured frontmatter scan, not grep):

```bash
# Check for existing research notes matching this query (structured dedup)
python3 /Users/sanjayb/codex-ecc-custom/skills/ecc-hermes-research/scripts/hermes_research_wrapper.py --task --domain financial --desc "<your query>"

# Also grep HermesBrain for prior coverage (quote paths with spaces!)
grep -rl "<topic keywords>" "/Users/sanjayb/Documents/Obsidian Vault/HermesBrain/" 2>/dev/null
grep -rl "<topic keywords>" ~/second-brain/Vault\ Structure/wiki-pages/ 2>/dev/null
```

**If existing coverage found:**
- Read it first
- Note what's already covered
- Only fetch new/updated data — do not re-research what the vault already has

### Step 2: Load Personal Profile
```bash
cat ~/second-brain/Contract/personal-profile.md
```
Extract: risk tolerance, tickers of interest, research goals, output preferences. Every output must be filtered through this profile.

### Step 3: Dedup Check
Before fetching, check if the vault already has a note covering this exact query:
```bash
find "/Users/sanjayb/Documents/Obsidian Vault/HermesBrain/" -name "*.md" -newer ~/second-brain/Contract/personal-profile.md -exec grep -l "<query>" {} \;
```
If found and recent (< 7 days for financial, < 30 days for admin), surface it and ask whether to refresh.

### Step 4: Execute Research (with cost caps)
Use MCP tools in this priority order:
1. **exa** — web search for qualitative research (cap: 10 searches/task)
2. **firecrawl** — crawl specific pages for structured data (cap: 5 crawls/task)
3. **search-console** — Google Search Console data (cap: 3 queries/task)

**Cost caps are hard limits.** If you hit a cap, stop and report what you have. Do not silently exceed.

### Step 5: Failure Policy
If an MCP is down or returns errors:
1. Try the next MCP in the priority order
2. If all MCPs fail, report "MCP degradation — using vault-only knowledge" and surface what the vault already has
3. Never fabricate data to fill gaps — mark gaps explicitly with `[GAP: no live data]`

### Step 6: Output Contract
Every research output must be written to HermesBrain with this structure:

**Path:** `/Users/sanjayb/Documents/Obsidian Vault/HermesBrain/raw/research/YYYY-MM-DD-<slug>.md`

**Frontmatter (required):**
```yaml
---
date: YYYY-MM-DD
domain: financial | admin | project | market
query: "<original question>"
sources:
  - url: "<source URL>"
    title: "<source title>"
    accessed: YYYY-MM-DD
provenance:
  vault_checked: true
  prior_notes: ["<list of prior notes found>", "none"]
  mcp_used: ["exa", "firecrawl"]
  cost:
    searches: N
    crawls: N
profile_filters:
  risk_tolerance: "<from profile>"
  tickers: ["<from profile>"]
status: draft | reviewed | actioned
sensitivity: high | medium | low
---
```

**Body structure:**
1. **Question** — the original query
2. **Vault context** — what was already known
3. **Findings** — new data with inline citations `[1]`, `[2]`
4. **Sources** — numbered list with URL, title, date accessed
5. **Gaps** — explicit `[GAP: ...]` markers for missing data
6. **Recommendation** — filtered through personal profile
7. **Next actions** — concrete, optional

### Step 7: Link-Back
Add a wikilink from the research note to the relevant HermesBrain concept/entity page:
```markdown
Related: [[concepts/<topic>]], [[entities/<ticker>]]
```

## Monday 8am Financial Review

Triggered by `~/second-brain/Triggers/schedule`. Executes:

1. Load personal profile
2. For each ticker in profile:
   - Vault-first: check last research note
   - If > 7 days old: refresh via exa
   - Summarize: current price, recent news, upcoming earnings
3. Scan bills/subscriptions (if data source available)
4. Flag anything matching the "proactive flags" list in profile
5. Write summary to `HermesBrain/Daily Notes/YYYY-MM-DD.md`
6. Post summary to messaging gateway (if configured)

## Commands

### `ecc-hermes-research ticker <SYMBOL>`
Research entry points for a specific ticker.

### `ecc-hermes-research bills`
Scan for bill increases and unused subscriptions.

### `ecc-hermes-research monday`
Run the full Monday 8am financial review.

### `ecc-hermes-research project <name>`
Research supporting an ongoing project from the profile.

## Non-Goals

- Not a generic search wrapper — use `deep-research` for that
- Not a code research tool — use `codegraph` or `grep`
- Not a lead generation tool — use `ecc-lead-dossier`
- Does not execute trades or move money
- Does not store credentials or PII

## Auto-Revocation

If exa, firecrawl, and search-console are all unavailable:
- Skill degrades to vault-only mode
- Reports "MCP degradation" in output
- Still writes a note with vault-existing knowledge and explicit gap markers

**Enforcement:** The wrapper script at `scripts/hermes_research_wrapper.py` actually enforces:
- **Cost caps** — hard-stops when limit reached (logs to `~/second-brain/log/hermes-research-cost.jsonl`)
- **Output contract** — `--check-output <path>` refuses notes missing required frontmatter
- **Dedup** — structured frontmatter scan, not grep
- **Domain allowlist** — rejects out-of-scope domains
- **Revocation** — honors `~/second-brain/Contract/hermes-research-revoked.flag`

To revoke: `touch ~/second-brain/Contract/hermes-research-revoked.flag`
To re-enable: `rm ~/second-brain/Contract/hermes-research-revoked.flag`

## Proof Boundaries

- A research note without `vault_checked: true` in frontmatter is not valid
- A note with `sources: []` and no `[GAP:]` markers is fabricated — reject it
- Cost caps exceeded = task stops, not silently continues
- "MCP degradation" must be stated explicitly, not hidden
