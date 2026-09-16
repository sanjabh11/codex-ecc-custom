# Security And Launch Readiness Framework

Use this reference to keep commercial launch audits current, evidence-bound, and proof-honest.

## Primary Framework Links

- OWASP Top 10 2025: https://owasp.org/Top10/
- OWASP Top Ten project: https://owasp.org/www-project-top-ten/
- OWASP API Security Top 10 2023: https://owasp.org/API-Security/editions/2023/en/0x00-header/
- OWASP GenAI Security Project: https://genai.owasp.org/
- OWASP Application Security Verification Standard: https://owasp.org/www-project-application-security-verification-standard/
- NIST Secure Software Development Framework SP 800-218: https://csrc.nist.gov/pubs/sp/800/218/final
- CISA Secure by Design: https://www.cisa.gov/securebydesign
- CISA Secure-by-Design resources: https://www.cisa.gov/resources-tools/resources/secure-by-design
- NIST AI Risk Management Framework: https://airc.nist.gov/

## Proof Buckets

Use these buckets in every claim:

| Bucket | Meaning | Allowed Claim |
|---|---|---|
| Hosted/live | Verified against deployed production or staging URL with current credentials and runtime evidence. | Can support launch-facing runtime claims. |
| Local | Verified in local checkout with local env and commands. | Can support implementation readiness, not hosted readiness. |
| Repo artifact | Present in code, docs, tests, fixtures, or generated reports but not executed now. | Can support design intent or implementation evidence. |
| Candidate/shadow | Prototype, branch, disabled code, placeholder, mock, or unmerged path. | Can support roadmap or candidate language only. |
| Roadmap | Planned, recommended, or externally blocked. | Cannot support launch claims. |

## Severity Scale

| Severity | Meaning | Launch Effect |
|---|---|---|
| P0 | Exploitable security issue, data leak, auth bypass, payment risk, destructive data risk, or legal/compliance blocker. | Blocks launch. |
| P1 | Serious trust, reliability, onboarding, billing, privacy, or core workflow gap. | Blocks commercial-ready; may allow controlled pilot if contained. |
| P2 | Important quality, maintainability, observability, UX, or evidence gap. | Launch caveat; prioritize before scale. |
| P3 | Polish, copy, non-critical docs, minor DX, or future optimization. | Does not block pilot. |

## Security Checklist

Map each repo to the applicable items:

- Auth and session management: login, logout, token storage, password reset, MFA assumptions, session expiry.
- Access control: authorization checks, tenant boundaries, role checks, object-level access, admin routes.
- API security: input validation, output filtering, rate limits, pagination, CORS, error handling, idempotency.
- Database and RLS: policies, migrations, seed data, backups, least privilege, audit trails.
- Secrets and envs: no committed secrets, documented envs, safe defaults, rotation gates, secret-dependent tests separated.
- Data privacy: PII minimization, retention, export/delete flows, logging redaction, consent boundaries.
- Supply chain: lockfiles, dependency audit, package provenance, CI install behavior, build scripts.
- CI/CD and deployment: reproducible builds, protected deploy steps, environment separation, rollback path.
- Observability: structured logs, alerts, error reporting, health checks, audit events.
- AI/LLM risks: prompt injection, data exfiltration, unsafe tool use, excessive agency, model output trust boundaries.
- Abuse and fraud: rate limits, invite abuse, scraping, spam, payment abuse, account takeover.
- Licensing and third-party terms: dependency licenses, data-source rights, model/API usage terms.

## Readiness Checklist

- Build passes from a clean checkout or the failure is documented with exact blocker evidence.
- Tests and lint run where available; missing tests are treated as evidence gaps.
- Browser smoke verifies primary routes for frontend apps.
- API smoke verifies health and at least one core path for backend apps.
- Docs explain install, env setup, deploy, rollback, and known limitations.
- Demo path is short, credible, and does not need hidden manual setup.
- Pricing, onboarding, support, and privacy expectations are ready enough for the intended launch mode.

## Launch Decisions

| Decision | Criteria |
|---|---|
| blocked | Any unresolved P0, uncontrolled P1, missing core runtime proof, unsafe claims, or unavailable approval gate needed for launch. |
| pilot-only | No known P0; P1s are contained; launch requires guided onboarding, clear caveats, and controlled customer selection. |
| sellable-with-caveats | Core value is demonstrable and buyer pain is credible, but some scale, polish, compliance, evidence, or automation gaps remain. |
| commercial-ready | Security, readiness, sellability, evidence, support, and outreach claims are verified for the intended market and launch scope. |

## Score Guidance

Score each area from 1 to 5:

- 1: unproven or materially blocked.
- 2: partial implementation with serious gaps.
- 3: pilot-grade with clear caveats.
- 4: sellable for a defined segment with manageable gaps.
- 5: launch-grade with strong evidence and adversarial review passed.
