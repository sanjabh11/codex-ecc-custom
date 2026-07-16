# Optional Codebase Reconnaissance

Codebase inspection is one evidence lane, not market validation. Use read-only,
bounded enumeration and record command, timestamp, coverage, and failure. If
access, stack detection, or coverage fails, mark the lane unavailable; do not
infer capability from a directory name.

| Stack signal | Bounded inventory |
|---|---|
| `package.json` with Next | `app/`, `pages/`, `api/`, `components/`, scripts, dependencies |
| `package.json` without Next | `src/`, `public/`, scripts, dependencies |
| `pyproject.toml`/`requirements.txt` | Python modules, entry points, tests, dependencies |
| `go.mod` | `cmd/`, `internal/`, `pkg/`, tests, modules |
| `Cargo.toml` | `src/`, binaries, tests, dependencies |
| `Gemfile` | `app/`, `config/`, tests, gems |
| `pom.xml`/`build.gradle` | `src/main`, `src/test`, build dependencies |

Compare validated positioning claims to implemented capabilities, proof
instrumentation, integrations, pricing surfaces, distribution readiness, and
technical debt. Report implementation gaps separately from need, proof, pricing,
distribution, and adoption gaps. Do not let a passing build turn a market
hypothesis into a supported hypothesis.
