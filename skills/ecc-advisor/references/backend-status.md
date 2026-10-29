# Backend Implementation Status

## Fully Implemented

### jev_gateway
- **Status:** Production-ready (Primary cross-harness backend)
- **Implementation:** `fable/advisor_cli.py` → `fable/services.py::JevGatewayService`
- **Auth:** API key (`vck_...`) via `AI_GATEWAY_API_KEY` or config discovery in `~/.cline/plugins/`, `~/.codex/plugins/`, `~/.devin/plugins/`, or `~/.gemini/config/`
- **API:** Vercel AI Gateway Chat Completions (`https://ai-gateway.vercel.sh/v1/chat/completions`)
- **Model:** `typesafe-ai/jev` (configurable, supports OpenAI/Anthropic/Google models on Vercel AI Gateway)
- **Cost control:** Call cap, timeout, retry, dry-run
- **Harness support:** Cline, Codex, Devin, Antigravity

### grok_cli
- **Status:** Production-ready (Legacy fallback)
- **Implementation:** `fable/advisor_cli.py` → `fable/services.py::GrokService`
- **Auth:** OAuth token from `~/.grok/auth.json` (Super Grok CLI)
- **Token refresh:** Automatic via `_refresh_oauth_token()` when token expires
- **API:** xAI Responses API (`/v1/responses`) with Chat Completions fallback (`/v1/chat/completions`)
- **Model:** `grok-4.6` (configurable)
- **Cost control:** Call cap, timeout, retry, dry-run
- **Tested:** 67/67 tests pass including live integration test

## Detected but Not Yet Implemented in CLI

### claude_native
- **Status:** Detection only — returns informative fallback
- **Detection:** `CLAUDE_ADVISOR_ENABLED=true` env var
- **Implementation needed:** Call `advisor_20260301` server-side tool
- **Note:** In Claude Code, the advisor tool is called directly by the harness,
  not via this CLI. The CLI detection is for reporting purposes only.

### codex_orchestration
- **Status:** Detection only — returns informative fallback
- **Detection:** `~/.codex/plugins/codex-orchestration/` directory exists
- **Implementation needed:** Call MCP plugin seats (planner, advisor, executor)
- **Protocol:** PLAN_APPROVED/PLAN_REVISE with up to 5 review rounds

### fallback
- **Status:** Graceful degradation
- **Behavior:** Returns message advising to install Grok CLI or enable Claude advisor
- **No crash, no error exit** — executor proceeds without advisor
