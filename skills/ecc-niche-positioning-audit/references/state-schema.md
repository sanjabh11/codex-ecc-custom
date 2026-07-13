# State Schema & Privacy Safety

Data classification, redaction-before-storage, schema versioning, run IDs, atomic writes, retention, and portfolio opt-in.

## Data Classification

| Classification | Examples | Storage Rule |
|---------------|----------|-------------|
| **public** | Positioning scores, 8-lens scorecard, segment names | Store in artifacts freely |
| **internal** | Feature inventory, tech stack, codebase structure | Store in artifacts and state |
| **confidential** | Customer names, revenue data, user counts | Store only in artifacts with redaction; never in state.json |
| **restricted** | API keys, tokens, passwords, PII (emails, phone numbers) | NEVER store — redact before any persistence |

## Redaction-Before-Storage

Before writing any content to `state.json`, `portfolio.json`, or artifact files:

1. **Scan for secrets**: Match patterns for API keys (`sk-`, `pk_`, `AKIA`, `ghp_`, `xox`), tokens (`Bearer `, JWT patterns), passwords, connection strings
2. **Scan for PII**: Match email addresses, phone numbers, IP addresses, credit card numbers
3. **Replace with placeholders**: `REDACTED_API_KEY`, `REDACTED_EMAIL`, `REDACTED_PHONE`, `REDACTED_IP`
4. **Log redaction**: Record count of redacted items in state.json (not the content)

### Redaction Patterns

```
API keys:     r'(sk-[a-zA-Z0-9]{20,})' → REDACTED_API_KEY
AWS keys:     r'(AKIA[A-Z0-9]{16})' → REDACTED_AWS_KEY
GitHub tokens: r'(ghp_[a-zA-Z0-9]{36})' → REDACTED_GITHUB_TOKEN
Slack tokens: r'(xox[bpoa]-[a-zA-Z0-9-]+)' → REDACTED_SLACK_TOKEN
Emails:       r'[\w.+-]+@[\w-]+\.[\w.-]+' → REDACTED_EMAIL
Phone:        r'\+?[\d\s\-\(\)]{10,}' → REDACTED_PHONE
IP addresses: r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b' → REDACTED_IP
JWT:          r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+' → REDACTED_JWT
```

## State File Schema

### state.json

```json
{
  "schema_version": "1.0.0",
  "run_id": "audit-20250713-143000-a1b2",
  "codebase_path": "/path/to/codebase",
  "codebase_name": "my-app",
  "audit_started": "2025-07-13T14:30:00Z",
  "audit_completed": null,
  "current_phase": "phase-2",
  "scope": "standard",
  "stack_detected": "next",
  "domain_detected": "saas",
  "gate_decisions": {
    "gate-0": "GO",
    "gate-1": "GO",
    "gate-2": "CONDITIONAL_GO"
  },
  "confidence_scores": {
    "phase-0": 96,
    "phase-1": 92,
    "phase-2": 88
  },
  "pre_gate_self_assessment": {
    "phase-0": 22,
    "phase-1": 18,
    "phase-2": 15
  },
  "redaction_log": {
    "secrets_redacted": 3,
    "pii_redacted": 7
  },
  "portfolio_opt_in": false,
  "advisor_used": false,
  "extensions_loaded": []
}
```

### Schema Versioning

- `schema_version` field is mandatory
- Current version: `1.0.0`
- Migration rule: when schema changes, increment version and provide migration function
- Old state files with lower version: attempt migration; if migration fails, start fresh with warning

### Run IDs

- Format: `audit-YYYYMMDD-HHMMSS-XXXX` (XXXX = 4 random hex chars)
- Each audit run gets a unique run_id
- Previous run's state is archived to `history/{run_id}/` before overwriting
- state.json always reflects the current (latest) run

## Atomic Writes

To prevent corruption from interrupted writes:

1. Write to `state.json.tmp` first
2. Rename `state.json.tmp` → `state.json` (atomic on POSIX)
3. If `state.json.tmp` exists on resume: delete it (incomplete write) and recover from `state.json`

## Idempotency

- Re-running a phase with same inputs must produce same outputs
- Gate decisions are not re-evaluated unless the phase is re-run
- Confidence scores are recalculated on re-run (may change if new evidence is found)

## Retention Policy

| Data | Retention | Action |
|------|-----------|--------|
| `history/` run archives | 8 quarters (2 years) | Auto-archive older to `history/archive/` |
| `research-ledger.json` | Permanent | Never deleted — audit trail |
| `state.json` | Current run only | Overwritten on new run; previous archived |
| `portfolio.json` | Permanent | Updated, never deleted |
| Artifact `.md` files | Current run only | Overwritten on re-run; previous archived |

## Portfolio Opt-In

- Global portfolio at `~/.positioning-audit-portfolio/portfolio.json` requires **explicit user consent** per codebase
- `portfolio_opt_in: false` in state.json means portfolio is NOT updated
- User must be asked: "May I add this codebase to your cross-codebase portfolio? This stores positioning scores and segment names globally."
- If user declines: portfolio is not updated; no global data is written
- Portfolio file contains only public-classification data (scores, segment names, dates) — never confidential or restricted

## Corruption Recovery

If `state.json` is corrupt or unreadable:

1. Attempt to parse JSON — if fails, log warning
2. Check for `state.json.tmp` — if exists, attempt to recover
3. If recovery fails: start fresh run with warning "Previous state corrupted — starting new audit run"
4. Archive corrupt state to `history/corrupt-{timestamp}/` for debugging
5. Never silently overwrite corrupt state without archiving

## Multi-Run Isolation

- Each run has its own `run_id` and artifact set
- History directory isolates runs: `history/{run_id}/`
- No run reads another run's state (only reads history for drift comparison)
- Concurrent runs on same codebase: not supported — state.json is single-writer
