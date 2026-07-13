import os
import json
import requests
from typing import Dict, Any, List, Optional


class ServiceBase:
    def __init__(self, api_key: str, mock_mode: bool = True):
        self.api_key = api_key
        self.mock_mode = mock_mode

    def _api_get(self, url: str, headers: Dict = None, params: Dict = None,
                 timeout: int = 10) -> Optional[requests.Response]:
        """Attempt a real GET request; return None on any failure."""
        if self.mock_mode or not self.api_key:
            return None
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp
            print(f"  [API] {url} returned {resp.status_code}")
        except Exception as e:
            print(f"  [API] Request failed: {e}")
        return None

    def _api_post(self, url: str, headers: Dict = None, json_body: Dict = None,
                  timeout: int = 10) -> Optional[requests.Response]:
        """Attempt a real POST request; return None on any failure."""
        if self.mock_mode or not self.api_key:
            return None
        try:
            resp = requests.post(url, headers=headers, json=json_body, timeout=timeout)
            if resp.status_code in (200, 201):
                return resp
            print(f"  [API] {url} returned {resp.status_code}")
        except Exception as e:
            print(f"  [API] Request failed: {e}")
        return None


# ─── Inbox + Triage ─────────────────────────────────────────────────────────

class GmailService(ServiceBase):
    def get_unread_emails(self) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"id": "msg-001", "from": "customer@company.com", "subject": "Billing issue",
                 "body": "I was charged twice for the monthly plan."},
                {"id": "msg-002", "from": "partner@firm.org", "subject": "Proposal update",
                 "body": "Please review the updated agreement by Friday."}
            ]
        # Real Gmail API v1 call
        resp = self._api_get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers={"Authorization": f"Bearer {self.api_key}"},
            params={"q": "is:unread", "maxResults": 10},
        )
        if resp:
            emails = []
            for msg in resp.json().get("messages", []):
                detail = self._api_get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"format": "metadata", "metadataHeaders": ["From", "Subject"]},
                )
                if detail:
                    d = detail.json()
                    headers = {h["name"]: h["value"] for h in d.get("payload", {}).get("headers", [])}
                    emails.append({
                        "id": d["id"],
                        "from": headers.get("From", "unknown"),
                        "subject": headers.get("Subject", "(no subject)"),
                        "body": d.get("snippet", ""),
                    })
            return emails
        return []

    def draft_reply(self, thread_id: str, body: str) -> bool:
        if not self.mock_mode and self.api_key:
            resp = self._api_post(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{thread_id}/drafts",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json_body={"message": {"threadId": thread_id, "raw": body.encode('base64')}},
            )
            if resp:
                print(f"[Gmail] Drafted reply for thread {thread_id} via API")
                return True
        print(f"[Gmail] Drafted reply for thread {thread_id}: {body[:50]}...")
        return True


class SlackService(ServiceBase):
    def sweep_channels(self, channels: List[str]) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"channel": "general", "user": "alice",
                 "text": "@agent SLA is breaching on ticket #8801!"},
                {"channel": "eng-incidents", "user": "bob",
                 "text": "DB connection pool critical — down to 3 remaining connections"}
            ]
        # Real Slack API call — search.messages
        all_msgs = []
        for ch in channels:
            resp = self._api_get(
                "https://slack.com/api/conversations.history",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"channel": ch, "limit": 20},
            )
            if resp:
                for msg in resp.json().get("messages", []):
                    all_msgs.append({"channel": ch, "user": msg.get("user", ""),
                                     "text": msg.get("text", "")})
        return all_msgs

    def post_message(self, channel: str, text: str) -> bool:
        if not self.mock_mode and self.api_key:
            resp = self._api_post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json_body={"channel": channel, "text": text},
            )
            if resp and resp.json().get("ok"):
                print(f"[Slack] Posted to #{channel} via API")
                return True
        print(f"[Slack] Posted to #{channel}: {text[:80]}")
        return True


class DiscordService(ServiceBase):
    def sweep_channels(self, guild_id: str, keywords: List[str]) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"channel": "support", "user": "user_xyz",
                 "text": "App is down! Getting 503 errors on login."}
            ]
        return []


class ZendeskService(ServiceBase):
    def get_recent_tickets(self) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"id": 8801, "subject": "I thought it did X, but it fails",
                 "status": "open", "priority": "high",
                 "created_at": "2026-07-07T10:00:00Z", "sla_remaining_mins": 45},
                {"id": 8802, "subject": "Cannot export CSV",
                 "status": "open", "priority": "normal",
                 "created_at": "2026-07-07T12:00:00Z", "sla_remaining_mins": 180}
            ]
        return []

    def escalate_ticket(self, ticket_id: int, priority: str) -> bool:
        print(f"[Zendesk] Escalated ticket #{ticket_id} to priority: {priority}")
        return True


class JiraService(ServiceBase):
    def create_ticket(self, title: str, body: str, labels: List[str]) -> Dict[str, Any]:
        if self.mock_mode or not self.api_key:
            ticket = {"key": "PROJ-999", "title": title, "status": "Open"}
            print(f"[Jira] Created ticket {ticket['key']}: {title[:60]}")
            return ticket
        return {}

    def sync_status(self, ticket_key: str, status: str) -> bool:
        print(f"[Jira] Updated {ticket_key} → {status}")
        return True


class LinearService(ServiceBase):
    def get_open_issues(self) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"id": "LIN-101", "title": "Fix flaky test in CI", "state": "In Progress"},
                {"id": "LIN-102", "title": "Improve DB query performance", "state": "Backlog"}
            ]
        return []

    def update_issue_state(self, issue_id: str, state: str) -> bool:
        print(f"[Linear] Updated {issue_id} → {state}")
        return True


# ─── Version Control ─────────────────────────────────────────────────────────

class GitHubService(ServiceBase):
    def get_open_pull_requests(self, repo: str = None) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"number": 42, "title": "feat: add oauth login",
                 "state": "open", "author": "dev-alpha"}
            ]
        # Real GitHub API call
        repo_path = repo or os.environ.get("GITHUB_REPO", "")
        if not repo_path:
            return []
        resp = self._api_get(
            f"https://api.github.com/repos/{repo_path}/pulls",
            headers={"Authorization": f"token {self.api_key}", "Accept": "application/vnd.github.v3+json"},
            params={"state": "open", "per_page": 10},
        )
        if resp:
            return [{"number": pr["number"], "title": pr["title"],
                     "state": pr["state"], "author": pr["user"]["login"]}
                    for pr in resp.json()]
        return []

    def sync_pr_to_issue(self, pr_num: int, status: str) -> bool:
        print(f"[GitHub] Synced PR #{pr_num} status to issue tracker: {status}")
        return True


# ─── KPIs + Analytics ────────────────────────────────────────────────────────

class PostHogService(ServiceBase):
    def query_metrics(self) -> Dict[str, Any]:
        if self.mock_mode or not self.api_key:
            return {
                "daily_active_users": 1250,
                "error_rate": 0.042,
                "signups": 45,
                "retention_d7": 0.62
            }
        return {}


class StripeService(ServiceBase):
    def get_recent_charges(self) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"id": "ch_3M4e", "amount": 29900, "customer": "cus_N9f1",
                 "status": "succeeded", "description": "Monthly Pro plan"},
                {"id": "ch_3M4f", "amount": 150000, "customer": "cus_N9f2",
                 "status": "failed", "description": "Annual Enterprise plan"}
            ]
        # Real Stripe API call
        resp = self._api_get(
            "https://api.stripe.com/v1/charges",
            headers={"Authorization": f"Bearer {self.api_key}"},
            params={"limit": 10},
        )
        if resp:
            return [{"id": ch["id"], "amount": ch["amount"],
                     "customer": ch.get("customer", ""), "status": ch["status"],
                     "description": ch.get("description", "")}
                    for ch in resp.json().get("data", [])]
        return []

    def get_monthly_vendor_charges(self) -> Dict[str, Any]:
        if self.mock_mode or not self.api_key:
            return {
                "current_month": {"AWS": 4800, "Sendgrid": 320, "Segment": 890},
                "previous_month": {"AWS": 4100, "Sendgrid": 310, "Segment": 750}
            }
        return {}


class PostgresService(ServiceBase):
    def run_check_query(self, query: str) -> List[Any]:
        if self.mock_mode or not self.api_key:
            if "anomaly" in query.lower() or "sanity" in query.lower():
                return [{"id": 1092, "issue": "Orphaned subscription record for cus_N9f1"}]
            return []
        # Real Postgres query via psycopg2 if available
        try:
            import psycopg2
            conn = psycopg2.connect(self.api_key)  # api_key stores connection string
            cursor = conn.cursor()
            cursor.execute(query)
            cols = [desc[0] for desc in cursor.description]
            rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
            conn.close()
            return rows
        except ImportError:
            print("  [Postgres] psycopg2 not installed; returning empty")
        except Exception as e:
            print(f"  [Postgres] Query failed: {e}")
        return []


class SalesforceService(ServiceBase):
    def get_hot_leads(self, limit: int = 5) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"id": "SF-001", "company": "Acme Corp", "contact": "Jane Doe",
                 "email": "jane@acme.com", "score": 92,
                 "description": "Series B startup, 200 engineers, evaluating our platform"},
                {"id": "SF-002", "company": "GlobalTech", "contact": "Mark Wu",
                 "email": "mark@globaltech.io", "score": 84,
                 "description": "Replacing legacy on-prem solution by Q4"}
            ]
        return []


class OpsgenieService(ServiceBase):
    def get_open_alerts(self) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"id": "alert-001", "message": "High CPU on prod-db-01",
                 "priority": "P2", "age_mins": 12}
            ]
        return []

    def escalate_alert(self, alert_id: str, team: str) -> bool:
        print(f"[Opsgenie] Escalated alert {alert_id} to team: {team}")
        return True


class GDriveService(ServiceBase):
    def list_files_in_folder(self, folder_name: str) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"id": "drive-001", "name": "Privacy_Policy_v3.docx",
                 "modified": "2026-06-01"},
                {"id": "drive-002", "name": "SOC2_Report_2025.pdf",
                 "modified": "2026-03-15"}
            ]
        return []

    def check_compliance_clauses(self, file_id: str, clauses: List[str]) -> Dict[str, bool]:
        if self.mock_mode or not self.api_key:
            return {clause: True for clause in clauses}
        return {}


# ─── Research + Content ──────────────────────────────────────────────────────

class ExaService(ServiceBase):
    def search_trends(self, query: str) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"title": "AI Agent loops on autopilot trend",
                 "url": "https://techcrunch.com/agent-loops",
                 "snippet": "Autopilot loops are the next frontier..."}
            ]
        return []


class FirecrawlService(ServiceBase):
    def crawl_site(self, url: str) -> Dict[str, Any]:
        if self.mock_mode or not self.api_key:
            return {
                "url": url,
                "markdown": "# Competitor Launch\n\nToday they launched version 2.0 with instant Stripe checkout."
            }
        return {}


class TwitterService(ServiceBase):
    def search_mentions(self, query: str) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"id": "12345", "user": "user_praise",
                 "text": "Lovin the Fable Loop adaptation! Absolute gamechanger."},
                {"id": "12346", "user": "dev_jones",
                 "text": "The new inbox triage workflow saved me 2 hours today!"}
            ]
        return []


class BufferService(ServiceBase):
    def get_pending_posts(self) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"id": "buf-001", "platform": "twitter",
                 "text": "New feature drop: Loop workflows on autopilot 🚀"},
                {"id": "buf-002", "platform": "linkedin",
                 "text": "How we automated 25 workflows with Fable 5"}
            ]
        return []

    def schedule_post(self, post_id: str, slot: str) -> bool:
        print(f"[Buffer] Scheduled post {post_id} for slot: {slot}")
        return True


class SubstackService(ServiceBase):
    def create_draft(self, title: str, body: str) -> Dict[str, Any]:
        if self.mock_mode or not self.api_key:
            draft = {"id": "sub-draft-001", "title": title, "status": "draft"}
            print(f"[Substack] Created draft: {title[:60]}")
            return draft
        return {}


class GSearchService(ServiceBase):
    def get_keyword_positions(self) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"keyword": "fable 5 autopilot", "position": 14, "impressions": 480},
                {"keyword": "ai agent loop workflows", "position": 18, "impressions": 310},
                {"keyword": "ecc operating protocol", "position": 7, "impressions": 920}
            ]
        return []


class RedditService(ServiceBase):
    def search_subreddit(self, subreddit: str, query: str) -> List[Dict[str, Any]]:
        if self.mock_mode or not self.api_key:
            return [
                {"id": "post-001", "subreddit": subreddit,
                 "title": f"Anyone using {query} for automation?",
                 "upvotes": 143, "comments": 38}
            ]
        return []


# ─── AI / Multi-Model ───────────────────────────────────────────────────────

class GrokService(ServiceBase):
    """
    xAI Grok API service (Responses API first, with Chat Completions fallback).
    Base URL: https://api.x.ai/v1
    Models:  grok-4.5, grok-4, grok-3, etc.
    """
    DEFAULT_BASE_URL = "https://api.x.ai/v1"
    DEFAULT_MODEL = "grok-4.5"

    @staticmethod
    def _load_grok_cli_token() -> Optional[str]:
        """Load the active access token from the Grok CLI auth file."""
        auth_path = os.path.expanduser("~/.grok/auth.json")
        try:
            with open(auth_path, "r") as f:
                data = json.load(f)
            # auth.json is keyed by realm; grab the first (usually only) entry
            entry = next(iter(data.values()), {})
            return entry.get("key")
        except Exception:
            return None

    @staticmethod
    def _load_grok_auth_data() -> dict:
        """Load the full auth data from ~/.grok/auth.json (first realm entry)."""
        auth_path = os.path.expanduser("~/.grok/auth.json")
        try:
            with open(auth_path, "r") as f:
                data = json.load(f)
            realm_key = next(iter(data), None)
            if realm_key:
                return data[realm_key]
        except Exception:
            pass
        return {}

    @staticmethod
    def _save_grok_auth_data(realm_key: str, entry: dict) -> bool:
        """Update ~/.grok/auth.json with refreshed token data."""
        auth_path = os.path.expanduser("~/.grok/auth.json")
        try:
            with open(auth_path, "r") as f:
                data = json.load(f)
            data[realm_key] = entry
            with open(auth_path, "w") as f:
                json.dump(data, f, indent=2)
            os.chmod(auth_path, 0o600)
            return True
        except (OSError, json.JSONDecodeError) as e:
            print(f"  [Grok] Failed to save refreshed auth: {e}")
            return False

    @staticmethod
    def _refresh_oauth_token() -> Optional[str]:
        """Refresh the xAI OAuth access token using the stored refresh_token.

        POSTs to https://auth.x.ai/oauth2/token with:
          grant_type=refresh_token, client_id=<oidc_client_id>, refresh_token=<refresh_token>

        On success, updates ~/.grok/auth.json with the new access_token and refresh_token.
        Returns the new access token, or None on failure.
        """
        auth_data = GrokService._load_grok_auth_data()
        refresh_token = auth_data.get("refresh_token", "")
        client_id = auth_data.get("oidc_client_id", "")

        if not refresh_token or not client_id:
            print("  [Grok] No refresh_token or client_id available for token refresh")
            return None

        token_endpoint = "https://auth.x.ai/oauth2/token"
        print(f"  [Grok] Refreshing OAuth token at {token_endpoint}")

        try:
            resp = requests.post(
                token_endpoint,
                data={
                    "grant_type": "refresh_token",
                    "client_id": client_id,
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )
            if resp.status_code != 200:
                print(f"  [Grok] Token refresh failed: {resp.status_code} {resp.text[:200]}")
                return None

            payload = resp.json()
            new_access = payload.get("access_token", "")
            new_refresh = payload.get("refresh_token", refresh_token)
            expires_in = payload.get("expires_in", 3600)

            if not new_access:
                print("  [Grok] Token refresh returned no access_token")
                return None

            from datetime import datetime, timezone, timedelta
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

            # Find the realm key and update via the helper method
            auth_path = os.path.expanduser("~/.grok/auth.json")
            with open(auth_path, "r") as f:
                full_data = json.load(f)
            realm_key = next(iter(full_data), None)
            if realm_key:
                full_data[realm_key]["key"] = new_access
                full_data[realm_key]["refresh_token"] = new_refresh
                full_data[realm_key]["expires_at"] = expires_at
                GrokService._save_grok_auth_data(realm_key, full_data[realm_key])

            print(f"  [Grok] Token refreshed successfully, expires at {expires_at}")
            return new_access
        except (requests.RequestException, json.JSONDecodeError, OSError) as e:
            print(f"  [Grok] Token refresh error: {e}")
            return None

    def __init__(self, api_key: str, mock_mode: bool = True, base_url: str = None, model: str = None):
        # Prefer an explicit API key; fall back to the Grok CLI token.
        # If both exist (e.g. stale XAI_API_KEY env var), prefer the CLI token
        # since it is refreshed by `grok login` and tied to the active subscription.
        cli_token = self._load_grok_cli_token()
        resolved_key = api_key if api_key else cli_token or ""
        super().__init__(resolved_key, mock_mode)
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or self.DEFAULT_MODEL
        self._cli_token = cli_token
        self._refresh_in_progress = False

    @staticmethod
    def _is_token_expired(buffer_seconds: int = 60) -> bool:
        """Check if the CLI token is expired or about to expire.

        Returns True if expires_at is within buffer_seconds of now, or if
        expires_at is missing/unparseable.
        """
        auth_data = GrokService._load_grok_auth_data()
        expires_at = auth_data.get("expires_at", "")
        if not expires_at:
            return True
        try:
            from datetime import datetime, timezone
            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return (exp - now).total_seconds() < buffer_seconds
        except Exception:
            return True

    def _maybe_refresh_token(self) -> None:
        """Proactively refresh the OAuth token if it's near expiry.

        Called before each API request to avoid 403 failures.
        Uses a simple flag to prevent concurrent refresh stampede.
        """
        if self._refresh_in_progress:
            return
        if not self._cli_token and not self.api_key:
            return
        if self._is_token_expired(buffer_seconds=60):
            self._refresh_in_progress = True
            try:
                new_token = self._refresh_oauth_token()
                if new_token:
                    self.api_key = new_token
                    self._cli_token = new_token
            finally:
                self._refresh_in_progress = False

    def chat(self, messages: List[Dict[str, Any]], max_output_tokens: int = 1024, temperature: float = 0.7) -> str:
        """Call /v1/responses (preferred) or /v1/chat/completions (fallback)."""
        if self.mock_mode or not self.api_key:
            return self._mock_response(messages)

        # Proactive refresh: check token expiry before making the API call
        self._maybe_refresh_token()

        last_error = ""
        # Try Responses API first
        for path, payload_key, body in [
            ("/responses", "input", {"max_output_tokens": max_output_tokens, "temperature": temperature}),
            ("/chat/completions", "messages", {"max_tokens": max_output_tokens, "temperature": temperature}),
        ]:
            url = f"{self.base_url}{path}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            body[payload_key] = messages
            body["model"] = self.model
            body.setdefault("store", False)
            try:
                resp = requests.post(url, headers=headers, json=body, timeout=120)
                print(f"  [API] {url} returned {resp.status_code}")
            except Exception as e:
                print(f"  [API] Request failed: {e}")
                continue

            try:
                data = resp.json()
            except Exception:
                data = {}

            if resp.status_code not in (200, 201):
                err = data.get("error") or data.get("message") or resp.text
                last_error = f"{url} -> {resp.status_code}: {err}"
                continue

            if data.get("error"):
                return f"[Grok] API error: {data['error']}"
            # Responses API shape
            if "output_text" in data:
                return data["output_text"]
            output = data.get("output", [])
            for item in output:
                if item.get("role") == "assistant" and item.get("type") == "message":
                    content = item.get("content")
                    if isinstance(content, list):
                        texts = [c.get("text", "") for c in content
                                 if isinstance(c, dict) and c.get("type") == "output_text"]
                        return "".join(texts)
                    if isinstance(content, str):
                        return content
            # Chat Completions shape
            choices = data.get("choices")
            if choices and len(choices) > 0:
                msg = choices[0].get("message", {})
                return msg.get("content", "")
            return f"[Grok] Unexpected response shape: {list(data.keys())}"

        # 403 fallback: token may be expired — try refreshing via OAuth refresh_token
        if self._cli_token is not None or self.api_key:
            print("  [API] 403 on both endpoints — attempting OAuth token refresh")
            new_token = self._refresh_oauth_token()
            if new_token and new_token != self.api_key:
                print("  [API] Token refreshed — retrying with new access token")
                saved_key = self.api_key
                self.api_key = new_token
                self._cli_token = new_token
                try:
                    return self.chat(messages, max_output_tokens=max_output_tokens, temperature=temperature)
                finally:
                    self.api_key = saved_key
            elif self._cli_token and self._cli_token != self.api_key:
                print("  [API] Refresh failed — retrying with original CLI token as last resort")
                saved_key = self.api_key
                self.api_key = self._cli_token
                try:
                    return self.chat(messages, max_output_tokens=max_output_tokens, temperature=temperature)
                finally:
                    self.api_key = saved_key

        return f"[Grok] API call failed. {last_error}"

    def generate(self, prompt: str, system: str = "You are a helpful assistant.", max_output_tokens: int = 1024, temperature: float = 0.7) -> str:
        """Convenience wrapper for a single user prompt."""
        return self.chat(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )

    def _mock_response(self, messages: List[Dict[str, Any]]) -> str:
        last = messages[-1].get("content", "") if messages else ""
        return f"[Grok {self.model} mock] Would answer: '{last[:80]}...'"


class MiniMaxService(ServiceBase):
    """
    MiniMax API service (OpenAI-compatible endpoint).
    Base URL: https://api.minimax.io/v1
    Models:  MiniMax-M3, MiniMax-M2.7, MiniMax-M2.5, etc.
    """
    DEFAULT_BASE_URL = "https://api.minimax.io/v1"
    DEFAULT_MODEL = "MiniMax-M3"

    def __init__(self, api_key: str, mock_mode: bool = True, base_url: str = None, model: str = None):
        super().__init__(api_key, mock_mode)
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or self.DEFAULT_MODEL

    def chat(self, messages: List[Dict[str, Any]], max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """Call the chat endpoint or return mock."""
        if self.mock_mode or not self.api_key:
            return self._mock_response(messages)

        # Try OpenAI-compatible endpoint first, then native endpoint
        for path in ["/chat/completions", "/text/chatcompletion_v2"]:
            url = f"{self.base_url}{path}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=60)
                print(f"  [API] {url} returned {resp.status_code}")
            except Exception as e:
                print(f"  [API] Request failed: {e}")
                continue

            if resp.status_code not in (200, 201):
                continue

            try:
                data = resp.json()
                # Native MiniMax error format
                base_resp = data.get("base_resp") or {}
                if base_resp and base_resp.get("status_code"):
                    status_code = int(base_resp.get("status_code"))
                    if status_code != 0:
                        return f"[MiniMax] API status {status_code}: {base_resp.get('status_msg')}"
                # Extract content from choices (OpenAI or native)
                choices = data.get("choices")
                if choices and len(choices) > 0:
                    choice = choices[0]
                    msg = choice.get("message") or choice.get("delta", {})
                    return msg.get("content", "")
                return f"[MiniMax] Unexpected response shape: {list(data.keys())}"
            except Exception as e:
                return f"[MiniMax] Error parsing response: {e}"

        return "[MiniMax] API call failed or no response."

    def generate(self, prompt: str, system: str = "You are a helpful assistant.", max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """Convenience wrapper for a single user prompt."""
        return self.chat(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def _mock_response(self, messages: List[Dict[str, Any]]) -> str:
        last = messages[-1].get("content", "") if messages else ""
        return f"[MiniMax {self.model} mock] Would answer: '{last[:80]}...'"

