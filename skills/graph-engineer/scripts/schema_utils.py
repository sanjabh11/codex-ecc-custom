"""Shared strict format checks for all Graph-engineer JSON boundaries."""

import datetime as dt

import jsonschema


def strict_format_checker():
    """Return a checker that enforces timezone-aware RFC3339 date-times."""
    checker = jsonschema.FormatChecker()

    @checker.checks("date-time", raises=(TypeError, ValueError))
    def is_rfc3339_datetime(value):
        if not isinstance(value, str) or not value or value != value.strip():
            return False
        normalized = value.replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(normalized)
        return parsed.tzinfo is not None

    return checker
