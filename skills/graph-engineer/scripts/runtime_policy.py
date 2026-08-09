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
    """Load the single taxonomy source, falling back only for diagnostics."""
    try:
        with open(rules_path, encoding="utf-8") as handle:
            policy = json.load(handle).get("rules", {}).get("tool_policy", {})
        result = {
            key: {str(value).strip().lower() for value in policy.get(key, [])}
            for key in DEFAULT_POLICY
        }
        if all(result.values()):
            return result
    except (OSError, ValueError, TypeError):
        pass
    return DEFAULT_POLICY


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
