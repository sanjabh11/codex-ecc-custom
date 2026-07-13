---
name: ecc-agent-reach
description: Search and read content across 17+ platforms (Reddit, Twitter/X, Bilibili, YouTube, GitHub) without API keys or costs using Agent-Reach.
---

# ECC Agent-Reach

Use this skill when the user asks to search or read content from X/Twitter, Reddit, YouTube, Bilibili, GitHub, or other social/developer platforms, especially for research tasks.

## Setup Requirements

Verify if `agent-reach` CLI is installed:
```bash
which agent-reach || pip install agent-reach && agent-reach install --env=auto
```

## CLI Usage Guidelines

Run the following commands inside the terminal to retrieve platform data:

1. **Read URL Content**: Use to fetch the main text/data from any supported URL (e.g., a tweet, a repo, or an article):
   ```bash
   agent-reach read "<url>"
   ```
2. **Search Twitter**: Search for posts on X without API limits:
   ```bash
   agent-reach search-twitter "<query>"
   ```
3. **Diagnostics**: Check connection and dependency status:
   ```bash
   agent-reach doctor
   ```

## Reference Link Requirements

Whenever you complete a search or read operation, you must output clickable Markdown reference links.

### CRITICAL: Zero Link Hallucination Rule
- **NEVER invent status IDs, video IDs, or thread IDs**. Do not generate fake segment/status numbers.
- **Use Tool-Returned Source Links**: Only output specific URLs that are explicitly provided in the search tool outputs or API responses.
- **Fallback to Search Query URLs**: If the exact ID or URL is not present in the tool results, you must use a search query URL which is guaranteed to resolve:
  - **Twitter/X Search Link**: `https://x.com/search?q=[URL-encoded-query]`
  - **YouTube Search Link**: `https://www.youtube.com/results?search_query=[URL-encoded-query]`
  - **Reddit Search Link**: `https://www.reddit.com/search/?q=[URL-encoded-query]`
  - **General Web Search**: Use the exact URL returned in the search citation.
- **Presentation**: Place references directly next to the findings or in a "References" section at the end.

## Best Practices
- Combine `agent-reach` search results with your WebSearch or local cache for research-heavy tasks like `/last30days`.
- Do not request expensive API keys when Agent-Reach is available.

