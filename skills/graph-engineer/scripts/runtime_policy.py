#!/usr/bin/env python3
"""Shared runtime tool policy for graph validation and pre-run gating."""

import json
import os
import shutil


DEFAULT_POLICY = {
    "core": {"python3", "python", "cat", "git", "ls", "grep", "find", "head", "tail", "wc", "sort", "diff", "test", "mkdir", "cp", "mv", "echo"},
    "workflow": {"pytest", "cargo", "npm", "docker", "go", "gradle", "dotnet", "ruby"},
    "advisory": {"cass", "cm", "dcg", "ubs", "gh", "br", "bv", "graphify"},
}


def load_tool_policy(rules_path):
    """Load the single taxonomy source.

    G14: Fail closed when the policy file is missing, malformed, or incomplete.
    Previously, this function fell back to DEFAULT_POLICY silently, which is
    fail-open. Now it raises a ValueError so callers can block execution.
    """
    try:
        with open(rules_path, encoding="utf-8") as handle:
            document = json.load(handle)
        if not isinstance(document, dict):
            raise ValueError("policy root must be an object")
        rules = document.get("rules")
        if not isinstance(rules, dict):
            raise ValueError("policy rules must be an object")
        policy = rules.get("tool_policy")
        if not isinstance(policy, dict):
            raise ValueError("rules.tool_policy must be an object")
        unexpected = set(policy) - set(DEFAULT_POLICY)
        if unexpected:
            raise ValueError(
                "rules.tool_policy contains unsupported categories: "
                + ", ".join(sorted(unexpected))
            )

        result = {}
        for key in DEFAULT_POLICY:
            values = policy.get(key)
            if (
                not isinstance(values, list)
                or not values
                or not all(type(value) is str and value.strip() for value in values)
            ):
                raise ValueError(
                    f"rules.tool_policy.{key} must be a non-empty list of strings"
                )
            result[key] = {value.strip().lower() for value in values}
        return result
    except (OSError, UnicodeDecodeError) as exc:
        # G14: File missing or invalid UTF-8 — fail closed.
        raise ValueError(
            f"tool policy at {rules_path} could not be loaded: {exc}. "
            f"refusing to fall back to defaults."
        ) from exc
    except (json.JSONDecodeError, TypeError) as exc:
        # G14: Malformed JSON — fail closed.
        raise ValueError(
            f"tool policy at {rules_path} is malformed: {exc}. "
            f"refusing to fall back to defaults."
        ) from exc


def normalize_tool(value):
    """Return a normalized declaration or None for malformed input."""
    if isinstance(value, str) and value.strip():
        return {"name": value.strip().lower(), "required": True, "health_command": None, "min_version": None}
    if isinstance(value, dict):
        name = value.get("name")
        required = value.get("required")
        if not isinstance(name, str) or not name.strip() or not isinstance(required, bool):
            return None
        health_command = value.get("health_command")
        if health_command is not None and (
            not isinstance(health_command, list)
            or not health_command
            or not all(isinstance(item, str) and item.strip() for item in health_command)
        ):
            return None
        min_version = value.get("min_version")
        if min_version is not None and (not isinstance(min_version, str) or not min_version.strip()):
            return None
        return {
            "name": name.strip().lower(),
            "required": required,
            "health_command": health_command,
            "min_version": min_version,
        }
    return None


def classify_tool(name, policy):
    for category, names in policy.items():
        if name in names:
            return category
    return "unknown"


def executable_available(name):
    return shutil.which(name) is not None
