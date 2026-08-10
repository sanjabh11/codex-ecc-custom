#!/usr/bin/env python3
"""Build a local, proof-tiered Codex skill and action usage audit.

The Codex desktop transcript format contains repeated application context and
tool-wrapper source code.  A raw grep over those files produces false usage
counts.  This module deliberately separates:

* L1: explicit skill/plugin selectors in user prompts, deduplicated by session;
* L2: recorded top-level tool-call records;
* L3: plain user-prompt mentions and nested wrapper call-site strings; and
* L4: opportunity estimates for skills that are relevant but underused.

It is intentionally offline and standard-library-only.  It does not claim
that a selector proves host activation, runtime loading, or successful skill
execution.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


SCHEMA_VERSION = "skill-usage-audit.v1"
DEFAULT_WINDOW_DAYS = 60
DEFAULT_CONTEXT_PREFIXES = (
    "<recommended_plugins>",
    "# AGENTS.md",
    "<environment_context>",
    "<app-context>",
    "<skills_instructions>",
    "<permissions instructions>",
    "<developer>",
    "<subagent_notification>",
    "<turn_aborted>",
)

TOPIC_TERMS = {
    "audit_review": ("audit", "review", "gap analysis", "forensic", "cross-verify"),
    "research_browser": ("research", "browse", "browser", "internet", "look up", "deep dive"),
    "implementation_fix": ("implement", "fix", "code", "build", "patch", "refactor"),
    "testing_verification": ("test", "pytest", "unittest", "regression", "validation", "verify"),
    "planning_orchestration": ("plan", "phase", "workflow", "orchestrat", "agent", "skill"),
    "docs_artifacts": ("document", "report", "artifact", "markdown", "pdf", "brief"),
    "security_provenance": ("security", "provenance", "hash", "manifest", "secret", "runtime", "production"),
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: Any) -> datetime | None:
    """Parse common Codex timestamps and return an aware UTC datetime."""

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        # Codex event timestamps are occasionally Unix seconds.
        try:
            return datetime.fromtimestamp(value, timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_boundary(value: str, *, end_of_day: bool = False) -> datetime:
    """Parse an ISO date or timestamp used by the CLI."""

    parsed = parse_timestamp(value)
    if parsed is None:
        raise ValueError(f"invalid ISO timestamp/date: {value!r}")
    if "T" not in value and "t" not in value and end_of_day:
        return parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
    return parsed


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_source_manifest(path: Path) -> list[Path]:
    """Load and verify a frozen JSONL source manifest.

    A live Codex session file can change while an audit is running.  Manifest
    mode makes that drift visible and fails closed instead of presenting a
    moving event count as a reproducible snapshot.
    """

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read source manifest {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "skill-usage-source-manifest.v1":
        raise ValueError("source manifest schema_version must be skill-usage-source-manifest.v1")
    entries = payload.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("source manifest files must be a non-empty list")

    resolved_paths: list[Path] = []
    seen: set[Path] = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"source manifest entry {index} must be an object")
        raw_path = entry.get("path")
        expected_hash = entry.get("sha256")
        if not isinstance(raw_path, str) or not raw_path.startswith("/"):
            raise ValueError(f"source manifest entry {index} path must be absolute")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
            raise ValueError(f"source manifest entry {index} sha256 must be 64 hexadecimal characters")
        source = Path(raw_path).resolve()
        if source in seen:
            raise ValueError(f"source manifest contains duplicate path: {source}")
        if source.suffix != ".jsonl" or not source.is_file():
            raise ValueError(f"source manifest path is not an existing JSONL file: {source}")
        actual_hash = sha256_file(source)
        if actual_hash != expected_hash.lower():
            raise ValueError(f"source manifest hash mismatch: {source}")
        seen.add(source)
        resolved_paths.append(source)
    return resolved_paths


def load_skill_manifest(path: Path, *, skill_root: Path, inventory_csv: Path) -> int:
    """Verify the canonical skill files and inventory used by a scan."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read skill manifest {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "skill-usage-skill-manifest.v1":
        raise ValueError("skill manifest schema_version must be skill-usage-skill-manifest.v1")
    expected_root = payload.get("skill_root")
    expected_inventory = payload.get("inventory_csv")
    resolved_root = skill_root.resolve()
    resolved_inventory = inventory_csv.resolve()
    if expected_root != str(resolved_root):
        raise ValueError("skill manifest skill_root does not match --skill-root")
    if expected_inventory != str(resolved_inventory):
        raise ValueError("skill manifest inventory_csv does not match --inventory-csv")
    inventory_hash = payload.get("inventory_sha256")
    if not isinstance(inventory_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", inventory_hash):
        raise ValueError("skill manifest inventory_sha256 must be 64 hexadecimal characters")
    if not resolved_inventory.is_file() or sha256_file(resolved_inventory) != inventory_hash.lower():
        raise ValueError("skill manifest inventory CSV hash mismatch")

    entries = payload.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("skill manifest files must be a non-empty list")
    expected_files: set[Path] = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"skill manifest entry {index} must be an object")
        raw_path = entry.get("path")
        expected_hash = entry.get("sha256")
        if not isinstance(raw_path, str) or not raw_path.startswith("/"):
            raise ValueError(f"skill manifest entry {index} path must be absolute")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
            raise ValueError(f"skill manifest entry {index} sha256 must be 64 hexadecimal characters")
        skill_path = Path(raw_path).resolve()
        try:
            skill_path.relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(f"skill manifest path escapes skill_root: {skill_path}") from exc
        if skill_path.name != "SKILL.md" or not skill_path.is_file():
            raise ValueError(f"skill manifest path is not an existing SKILL.md: {skill_path}")
        if sha256_file(skill_path) != expected_hash.lower():
            raise ValueError(f"skill manifest hash mismatch: {skill_path}")
        if skill_path in expected_files:
            raise ValueError(f"skill manifest contains duplicate path: {skill_path}")
        expected_files.add(skill_path)

    discovered_files = {path.resolve() for path in resolved_root.glob("*/SKILL.md")}
    if discovered_files != expected_files:
        raise ValueError("skill manifest does not exactly match the canonical skill directory")
    return len(expected_files)


def load_optimization_aliases(path: Path) -> dict[str, tuple[str, ...]]:
    """Load the shared canonical-skill selector registry.

    Aliases are attribution metadata only: they make a selector such as
    ``@advisor`` count for ``ecc-advisor`` without proving host activation.
    The loader validates the small structural contract locally so a malformed
    or colliding registry cannot silently change the ranking.
    """

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read optimization manifest {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "skill-optimization-manifest.v1":
        raise ValueError("optimization manifest schema_version must be skill-optimization-manifest.v1")
    rows = payload.get("skills")
    if not isinstance(rows, list) or not rows:
        raise ValueError("optimization manifest skills must be a non-empty list")

    result: dict[str, tuple[str, ...]] = {}
    skill_ids_casefold: set[str] = set()
    owner_by_alias: dict[str, str] = {}
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"optimization manifest skill row {index} must be an object")
        skill_id = row.get("id")
        aliases = row.get("aliases")
        if (
            not isinstance(skill_id, str)
            or not skill_id.strip()
            or skill_id != skill_id.strip()
            or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", skill_id)
        ):
            raise ValueError(f"optimization manifest skill row {index} id must be a non-empty string")
        if skill_id.casefold() in skill_ids_casefold:
            raise ValueError(f"optimization manifest contains duplicate skill id: {skill_id}")
        if not isinstance(aliases, list) or any(
            not isinstance(alias, str)
            or not alias.strip()
            or alias != alias.strip()
            or not re.fullmatch(r"[a-z0-9][a-z0-9._/@-]*", alias)
            for alias in aliases
        ):
            raise ValueError(f"optimization manifest aliases for {skill_id} must be non-empty strings")
        skill_ids_casefold.add(skill_id.casefold())
        row_terms: set[str] = set()
        terms = (skill_id, *aliases)
        for term in terms:
            key = term.casefold()
            if key in row_terms:
                raise ValueError(f"optimization manifest duplicate selector term in {skill_id}: {term}")
            row_terms.add(key)
            previous = owner_by_alias.get(key)
            if previous is not None and previous != skill_id:
                raise ValueError(f"optimization manifest selector collision: {term} maps to {previous} and {skill_id}")
            owner_by_alias[key] = skill_id
        result[skill_id] = tuple(aliases)
    return result


def normalize_tokens(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def extract_frontmatter(content: str) -> dict[str, str]:
    """Read the small name/description subset used by the local inventory."""

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    frontmatter = match.group(1)
    result: dict[str, str] = {}
    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    if name_match:
        result["name"] = name_match.group(1).strip().strip("'\"")
    description_match = re.search(
        r"^description:\s*(.*?)(?=\n\s*(?:TRIGGER|DO NOT|allow_|$))",
        frontmatter,
        re.DOTALL | re.MULTILINE,
    )
    if description_match:
        description = description_match.group(1).strip()
        description = description.lstrip(">-").strip()
        result["description"] = re.sub(r"\s+", " ", description).strip("'\"")
    return result


def load_inventory(skill_root: Path, inventory_csv: Path | None = None) -> dict[str, dict[str, Any]]:
    """Discover canonical skills without requiring the generated index."""

    categories: dict[str, list[str]] = defaultdict(list)
    if inventory_csv and inventory_csv.is_file():
        try:
            with inventory_csv.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    name = (row.get("name") or row.get("skill_dir") or "").strip().lower()
                    if name:
                        categories[name] = [item.strip() for item in (row.get("categories") or "").split(";") if item.strip()]
        except (OSError, UnicodeError, csv.Error):
            # The usage audit remains usable when a generated inventory is stale
            # or malformed; the source-of-truth is still the skill directory.
            categories = defaultdict(list)

    inventory: dict[str, dict[str, Any]] = {}
    if not skill_root.is_dir():
        return inventory
    for skill_md in sorted(skill_root.glob("*/SKILL.md")):
        try:
            content = skill_md.read_text(encoding="utf-8")
            file_hash = sha256_file(skill_md)
        except (OSError, UnicodeError):
            continue
        directory_name = skill_md.parent.name.lower()
        frontmatter = extract_frontmatter(content)
        name = (frontmatter.get("name") or directory_name).lower()
        lowered_content = content.lower()
        inventory[name] = {
            "name": name,
            "skill_dir": directory_name,
            "canonical_path": str(skill_md),
            "description": frontmatter.get("description", ""),
            "categories": categories.get(name, categories.get(directory_name, [])),
            "sha256": file_hash,
            "has_references": (skill_md.parent / "references").is_dir(),
            "has_scripts": (skill_md.parent / "scripts").is_dir(),
            "has_tests": any((skill_md.parent / candidate).exists() for candidate in ("tests", "test", "fixtures")),
            "has_frontmatter": content.startswith("---\n") and "\n---" in content[4:],
            "has_output_contract": any(
                term in lowered_content for term in ("output contract", "required outputs", "response format", "return:")
            ),
            "has_scope_boundary": any(
                term in lowered_content for term in ("out of scope", "do not", "stop and ask", "proof")
            ),
        }
    return inventory


def iter_jsonl_files(roots: Iterable[Path]) -> Iterator[Path]:
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.suffix == ".jsonl":
            candidates = (root,)
        else:
            candidates = root.rglob("*.jsonl")
        for path in candidates:
            resolved = path.resolve()
            if resolved in seen or not resolved.is_file():
                continue
            seen.add(resolved)
            yield resolved


def content_text(content: Any, context_prefixes: tuple[str, ...]) -> tuple[str, int]:
    """Return user text while excluding repeated Codex application context."""

    if not isinstance(content, list):
        return (content if isinstance(content, str) else "", 0)
    parts: list[str] = []
    excluded = 0
    for block in content:
        if not isinstance(block, dict) or block.get("type") not in {"input_text", "output_text", "text"}:
            continue
        text = block.get("text")
        if not isinstance(text, str):
            continue
        if text.lstrip().startswith(context_prefixes):
            excluded += 1
            continue
        parts.append(text)
    return ("\n".join(parts), excluded)


def explicit_selector(text: str, name: str, aliases: Iterable[str] = ()) -> bool:
    """Recognize a user selector without treating prose as activation."""

    low = text.lower()
    for term in (name, *aliases):
        term_low = term.lower()
        if any(
            marker in low
            for marker in (
                f"${term_low}",
                f"@{term_low}",
                f"/skills/{term_low}/skill.md",
                f"plugin://{term_low}",
            )
        ):
            return True
    return False


def nested_tool_names(raw: Any) -> list[str]:
    """Find wrapper call-site names; these are explicitly lower-confidence."""

    if not isinstance(raw, str):
        return []
    result: list[str] = []
    for fragment in raw.split("tools.")[1:]:
        name_chars: list[str] = []
        for char in fragment:
            if char.isalnum() or char == "_":
                name_chars.append(char)
            else:
                break
        if name_chars:
            result.append("".join(name_chars))
    return result


def _session_in_window(session_started: datetime | None, event_time: datetime | None, start: datetime, end: datetime) -> bool:
    candidate = session_started or event_time
    return candidate is not None and start <= candidate <= end


def audit_usage(
    *,
    session_roots: Iterable[Path],
    skill_root: Path,
    inventory_csv: Path | None,
    start: datetime,
    end: datetime,
    extra_skills: Iterable[str] = (),
    source_manifest: Path | None = None,
    skill_manifest: Path | None = None,
    skill_manifest_file_count: int | None = None,
    optimization_manifest: Path | None = None,
) -> dict[str, Any]:
    """Collect usage evidence from Codex JSONL sessions."""

    inventory = load_inventory(skill_root, inventory_csv)
    aliases_by_skill = load_optimization_aliases(optimization_manifest) if optimization_manifest else {}
    for extra in extra_skills:
        name = extra.strip().lower()
        if name and name not in inventory:
            inventory[name] = {
                "name": name,
                "skill_dir": None,
                "canonical_path": None,
                "description": "external/plugin label supplied by the caller",
                "categories": [],
                "sha256": None,
                "has_references": None,
                "has_scripts": None,
                "has_tests": None,
            }

    skill_stats: dict[str, dict[str, Any]] = {
        name: {
            "name": name,
            "selector_prompt_count": 0,
            "selector_session_count": 0,
            "mention_prompt_count": 0,
            "mention_session_count": 0,
            "_selector_sessions": set(),
            "_mention_sessions": set(),
        }
        for name in inventory
    }
    plugin_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"prompt_count": 0, "session_ids": set()})
    direct_actions: Counter[str] = Counter()
    action_sessions: dict[str, set[str]] = defaultdict(set)
    nested_actions: Counter[str] = Counter()
    nested_action_sessions: dict[str, set[str]] = defaultdict(set)
    topics: Counter[str] = Counter()
    scanned_source_files: list[str] = []
    active_source_files: set[str] = set()
    sessions: set[str] = set()
    user_prompt_count = 0
    excluded_context_blocks = 0
    malformed_lines = 0
    events_in_window = 0

    for path in iter_jsonl_files(session_roots):
        scanned_source_files.append(str(path))
        current_session_id: str | None = None
        session_started: datetime | None = None
        try:
            handle = path.open(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        with handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except (json.JSONDecodeError, UnicodeError):
                    malformed_lines += 1
                    continue
                if not isinstance(event, dict):
                    malformed_lines += 1
                    continue
                payload = event.get("payload")
                payload = payload if isinstance(payload, dict) else {}
                event_time = parse_timestamp(event.get("timestamp") or payload.get("timestamp"))
                if event.get("type") == "session_meta":
                    current_session_id = payload.get("session_id") or payload.get("id")
                    session_started = event_time
                if not _session_in_window(session_started, event_time, start, end):
                    continue
                events_in_window += 1
                active_source_files.add(str(path))
                session_key = str(current_session_id or path)
                sessions.add(session_key)

                if event.get("type") != "response_item":
                    continue
                response_type = payload.get("type")
                if response_type in {"function_call", "custom_tool_call"}:
                    action_name = payload.get("name")
                    if isinstance(action_name, str) and action_name:
                        direct_actions[action_name] += 1
                        action_sessions[action_name].add(session_key)
                    raw = payload.get("input") or payload.get("arguments")
                    for nested_name in nested_tool_names(raw):
                        nested_actions[nested_name] += 1
                        nested_action_sessions[nested_name].add(session_key)

                if payload.get("role") != "user":
                    continue
                text, excluded = content_text(payload.get("content"), DEFAULT_CONTEXT_PREFIXES)
                excluded_context_blocks += excluded
                if not text.strip():
                    continue
                user_prompt_count += 1
                normalized = f" {normalize_tokens(text)} "
                low = text.lower()
                for topic, terms in TOPIC_TERMS.items():
                    if any(term in low for term in terms):
                        topics[topic] += 1
                for name, stat in skill_stats.items():
                    aliases = aliases_by_skill.get(name, ())
                    tokens = tuple(normalize_tokens(term) for term in (name, *aliases))
                    if not any(token and f" {token} " in normalized for token in tokens):
                        continue
                    stat["mention_prompt_count"] += 1
                    stat["_mention_sessions"].add(session_key)
                    if explicit_selector(text, name, aliases):
                        stat["selector_prompt_count"] += 1
                        stat["_selector_sessions"].add(session_key)
                for match in re.finditer(r"plugin://([^\s)\]]+)", low):
                    plugin_name = match.group(1).split("@")[0].split(":")[0]
                    if plugin_name:
                        plugin_stats[plugin_name]["prompt_count"] += 1
                        plugin_stats[plugin_name]["session_ids"].add(session_key)

    for stat in skill_stats.values():
        stat["selector_session_count"] = len(stat.pop("_selector_sessions"))
        stat["mention_session_count"] = len(stat.pop("_mention_sessions"))

    ranked_skills = sorted(
        skill_stats.values(),
        key=lambda item: (
            -item["selector_session_count"],
            -item["selector_prompt_count"],
            -item["mention_session_count"],
            -item["mention_prompt_count"],
            item["name"],
        ),
    )

    # Opportunity is intentionally conservative: it ranks local skills that
    # overlap observed task vocabulary but have no selector/session proof.  It
    # is a hypothesis for audit, not evidence that the user needs the skill.
    observed_topic_text = " ".join(topic for topic, count in topics.items() if count)
    candidates: list[dict[str, Any]] = []
    for stat in skill_stats.values():
        metadata = inventory[stat["name"]]
        if metadata.get("canonical_path") is None:
            continue
        corpus = " ".join(
            [
                metadata.get("name", ""),
                metadata.get("description", ""),
                " ".join(metadata.get("categories", [])),
            ]
        ).lower()
        matched_topics = [topic for topic, terms in TOPIC_TERMS.items() if any(term in corpus for term in terms)]
        relevance = len(matched_topics) / len(TOPIC_TERMS)
        if stat["selector_session_count"] == 0 and relevance > 0:
            gap = relevance / (1 + stat["mention_session_count"])
            candidates.append(
                {
                    **stat,
                    "relevance_score": round(relevance, 4),
                    "opportunity_gap_score": round(gap, 4),
                    "matched_observed_topics": matched_topics,
                    "quality_signals": {
                        "has_frontmatter": metadata.get("has_frontmatter"),
                        "has_output_contract": metadata.get("has_output_contract"),
                        "has_scope_boundary": metadata.get("has_scope_boundary"),
                        "has_references": metadata.get("has_references"),
                        "has_scripts": metadata.get("has_scripts"),
                        "has_tests": metadata.get("has_tests"),
                    },
                }
            )
    candidates.sort(key=lambda item: (-item["opportunity_gap_score"], -item["relevance_score"], item["name"]))

    for stat in ranked_skills:
        metadata = inventory[stat["name"]]
        stat.update(
            {
                "canonical_path": metadata.get("canonical_path"),
                "canonical_sha256": metadata.get("sha256"),
                "inventory_source": "canonical" if metadata.get("canonical_path") else "caller-supplied-external-label",
                "quality_signals": {
                    "has_frontmatter": metadata.get("has_frontmatter"),
                    "has_output_contract": metadata.get("has_output_contract"),
                    "has_scope_boundary": metadata.get("has_scope_boundary"),
                    "has_references": metadata.get("has_references"),
                    "has_scripts": metadata.get("has_scripts"),
                    "has_tests": metadata.get("has_tests"),
                },
            }
        )

    action_rows = [
        {
            "action": name,
            "count": count,
            "session_count": len(action_sessions[name]),
            "proof_level": "L2-top-level-tool-record",
        }
        for name, count in direct_actions.most_common()
    ]
    nested_action_rows = [
        {
            "action": name,
            "count": count,
            "session_count": len(nested_action_sessions[name]),
            "proof_level": "L3-wrapper-call-site",
            "warning": "May include source-code examples inside exec inputs; not host-activation proof.",
        }
        for name, count in nested_actions.most_common()
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now().isoformat(),
        "window": {"start": start.isoformat(), "end": end.isoformat(), "timezone": "UTC"},
        "proof_levels": {
            "L1": "explicit user selector, deduplicated by session",
            "L2": "top-level tool-call record in a session transcript",
            "L3": "plain prompt mention or nested wrapper call-site; supporting evidence only",
            "L4": "opportunity hypothesis derived from observed task vocabulary",
        },
        "source_coverage": {
            "session_roots": [str(Path(root).resolve()) for root in session_roots],
            "source_manifest": str(source_manifest.resolve()) if source_manifest else None,
            "source_manifest_file_count": len(scanned_source_files) if source_manifest else None,
            "skill_manifest": str(skill_manifest.resolve()) if skill_manifest else None,
            "skill_manifest_file_count": skill_manifest_file_count if skill_manifest else None,
            "optimization_manifest": str(optimization_manifest.resolve()) if optimization_manifest else None,
            "optimization_alias_count": sum(len(aliases) for aliases in aliases_by_skill.values()),
            "candidate_source_file_count": len(scanned_source_files),
            "active_source_file_count": len(active_source_files),
            "source_files": sorted(active_source_files),
            "session_count": len(sessions),
            "events_in_window": events_in_window,
            "user_prompt_count": user_prompt_count,
            "excluded_context_blocks": excluded_context_blocks,
            "malformed_jsonl_lines": malformed_lines,
            "caveat": "Transcript availability is local and may not cover every Codex host or archived session.",
        },
        "observed_topics": dict(topics),
        "skills": ranked_skills,
        "plugin_mentions": [
            {"plugin": name, "prompt_count": value["prompt_count"], "session_count": len(value["session_ids"])}
            for name, value in sorted(plugin_stats.items(), key=lambda item: (-item[1]["prompt_count"], item[0]))
        ],
        "actions": {"top_level": action_rows, "nested_call_sites": nested_action_rows},
        "ranked_top_skills": ranked_skills[:20],
        "underutilized_candidates": candidates[:10],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions-root", action="append", type=Path, dest="session_roots", help="JSONL file or directory; repeatable")
    parser.add_argument("--skill-root", type=Path, default=None, help="Canonical skill directory (default: repo/skills)")
    parser.add_argument("--inventory-csv", type=Path, default=None, help="Optional generated skill inventory CSV")
    parser.add_argument("--start", help="UTC ISO date/timestamp; default is 60 days before now")
    parser.add_argument("--end", help="UTC ISO date/timestamp; default is now")
    parser.add_argument(
        "--source-manifest",
        type=Path,
        help="Verified JSON source manifest; fails closed if any listed JSONL hash changes",
    )
    parser.add_argument(
        "--skill-manifest",
        type=Path,
        help="Verified skill/inventory manifest; fails closed if canonical skill inputs change",
    )
    parser.add_argument(
        "--optimization-manifest",
        type=Path,
        help="Shared canonical-skill alias registry; fails closed on malformed or colliding aliases",
    )
    parser.add_argument("--extra-skill", action="append", default=[], help="External/plugin skill label; repeatable")
    parser.add_argument("--output", type=Path, help="Write JSON to this path instead of stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    now = _utc_now()
    try:
        start = parse_boundary(args.start) if args.start else now - timedelta(days=DEFAULT_WINDOW_DAYS)
        end = parse_boundary(args.end, end_of_day=True) if args.end else now
    except ValueError as exc:
        parser.error(str(exc))
    repo_root = Path(__file__).resolve().parent.parent
    source_manifest = args.source_manifest
    if source_manifest:
        try:
            session_roots = load_source_manifest(source_manifest)
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"ERROR: invalid source manifest: {exc}", file=sys.stderr)
            return 2
    else:
        session_roots = args.session_roots or [Path.home() / ".codex" / "sessions", Path.home() / ".codex" / "archived_sessions"]
    skill_root = args.skill_root or repo_root / "skills"
    inventory_csv = args.inventory_csv or repo_root / "docs" / "skill-inventory.csv"
    skill_manifest = args.skill_manifest
    skill_manifest_file_count = None
    if skill_manifest:
        try:
            skill_manifest_file_count = load_skill_manifest(
                skill_manifest, skill_root=skill_root, inventory_csv=inventory_csv
            )
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"ERROR: invalid skill manifest: {exc}", file=sys.stderr)
            return 2
    optimization_manifest = args.optimization_manifest
    if optimization_manifest:
        try:
            load_optimization_aliases(optimization_manifest)
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"ERROR: invalid optimization manifest: {exc}", file=sys.stderr)
            return 2
    result = audit_usage(
        session_roots=session_roots,
        skill_root=skill_root,
        inventory_csv=inventory_csv,
        start=start,
        end=end,
        extra_skills=args.extra_skill,
        source_manifest=source_manifest,
        skill_manifest=skill_manifest,
        skill_manifest_file_count=skill_manifest_file_count,
        optimization_manifest=optimization_manifest,
    )
    output = json.dumps(result, indent=2, sort_keys=False) + "\n"
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            print(f"ERROR: cannot write {args.output}: {exc}", file=sys.stderr)
            return 2
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
