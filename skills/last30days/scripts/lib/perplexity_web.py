"""Perplexity web search integration for last30days."""

import json
import re
from typing import Any, Dict, List
from urllib.parse import urlparse

from . import http

PERPLEXITY_CHAT_URL = "https://api.perplexity.ai/chat/completions"


def _extract_json_array(text: str) -> List[Dict[str, Any]]:
    """Extract a JSON array from model output text."""
    if not text:
        return []

    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\n?", "", stripped)
        stripped = re.sub(r"\n?```$", "", stripped)

    # Direct parse first
    try:
        data = json.loads(stripped)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except Exception:
        pass

    # Fallback: locate first JSON array chunk in the response
    match = re.search(r"\[[\s\S]*\]", stripped)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except Exception:
        return []
    return []


def _domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def search_web(
    api_key: str,
    topic: str,
    from_date: str,
    to_date: str,
    max_results: int = 12,
    model: str = "sonar",
) -> Dict[str, Any]:
    """Search the web with Perplexity and return the raw response."""
    prompt = (
        f"Find recent web pages about: {topic}\n"
        f"Focus on content published between {from_date} and {to_date}.\n"
        f"Exclude Reddit, X, and Twitter URLs.\n"
        f"Return ONLY a JSON array with up to {max_results} items.\n"
        f"Each item must include: title, url, snippet, why_relevant, relevance (0-1), date (YYYY-MM-DD if known)."
    )

    payload = {
        "model": model,
        "temperature": 0.0,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise web research assistant. Return strictly valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    return http.post(PERPLEXITY_CHAT_URL, payload, headers=headers)


def parse_perplexity_response(
    raw: Dict[str, Any],
    max_results: int = 12,
) -> List[Dict[str, Any]]:
    """Convert Perplexity response into generic websearch result dicts."""
    items: List[Dict[str, Any]] = []
    seen_urls = set()

    # 1) Prefer structured results if returned by API
    for r in raw.get("search_results", []) or []:
        if not isinstance(r, dict):
            continue
        url = str(r.get("url", "")).strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        items.append(
            {
                "title": str(r.get("title", "")).strip() or _domain(url),
                "url": url,
                "snippet": str(r.get("snippet", r.get("description", ""))).strip(),
                "date": str(r.get("date", r.get("published_date", ""))).strip() or None,
                "relevance": 0.6,
                "why_relevant": "Found via Perplexity web search",
            }
        )
        if len(items) >= max_results:
            return items

    # 2) Parse assistant JSON content if available
    content = ""
    choices = raw.get("choices") or []
    if choices and isinstance(choices[0], dict):
        content = str((choices[0].get("message") or {}).get("content", "")).strip()

    for r in _extract_json_array(content):
        url = str(r.get("url", "")).strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        items.append(
            {
                "title": str(r.get("title", "")).strip() or _domain(url),
                "url": url,
                "snippet": str(r.get("snippet", r.get("description", ""))).strip(),
                "date": str(r.get("date", "")).strip() or None,
                "relevance": r.get("relevance", 0.6),
                "why_relevant": str(r.get("why_relevant", "")).strip(),
            }
        )
        if len(items) >= max_results:
            return items

    # 3) Fallback to citations list if present
    for url in raw.get("citations", []) or []:
        if not isinstance(url, str):
            continue
        url = url.strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        items.append(
            {
                "title": _domain(url),
                "url": url,
                "snippet": "",
                "date": None,
                "relevance": 0.5,
                "why_relevant": "Cited by Perplexity response",
            }
        )
        if len(items) >= max_results:
            break

    return items
