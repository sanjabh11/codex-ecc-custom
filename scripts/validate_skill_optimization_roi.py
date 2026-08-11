#!/usr/bin/env python3
"""Validate ROI pilot evidence without upgrading local metadata to host proof."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def _parse_time(value: str, name: str, errors: list[str]) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{name} is not a valid ISO-8601 timestamp")
        return None


def _validate_record(record: dict[str, Any], errors: list[str]) -> None:
    started = _parse_time(record["started_at_utc"], "started_at_utc", errors)
    finished = _parse_time(record["finished_at_utc"], "finished_at_utc", errors)
    if started is not None and finished is not None and finished < started:
        errors.append(f"{record['run_id']}: finished_at_utc precedes started_at_utc")

    status = record["status"]
    metrics = record["metrics"]
    outcome = record["outcome"]
    if status == "not_run":
        if not isinstance(record.get("not_run_reason"), str) or not record["not_run_reason"].strip():
            errors.append(f"{record['run_id']}: not_run requires not_run_reason")
        if any(value is not None for value in metrics.values()):
            errors.append(f"{record['run_id']}: not_run cannot claim runtime metrics")
        if any(record[key] is not None for key in ("output_sha256", "artifact_sha256")):
            errors.append(f"{record['run_id']}: not_run cannot claim output or artifact hashes")
        if outcome["success"] is not None or outcome["reviewer_decision"] != "not_run":
            errors.append(f"{record['run_id']}: not_run outcome must remain unverified")
    else:
        for key in ("input_sha256", "output_sha256", "artifact_sha256"):
            if not isinstance(record[key], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", record[key]):
                errors.append(f"{record['run_id']}: {key} is required for an observed result")
        if any(value is None for value in metrics.values()):
            errors.append(f"{record['run_id']}: observed results require latency, token, and cost metrics")
        if not isinstance(outcome["success"], bool):
            errors.append(f"{record['run_id']}: observed result requires boolean outcome.success")
        if outcome["reviewer_decision"] == "not_run":
            errors.append(f"{record['run_id']}: observed result cannot use not_run reviewer decision")

    if record["proof_level"] == "live" and not isinstance(record.get("external_attestation"), dict):
        errors.append(f"{record['run_id']}: live proof requires external_attestation")

    secret_like = re.compile(r"(?:sk-[A-Za-z0-9]{12,}|Bearer\s+[A-Za-z0-9._-]{12,})")
    if secret_like.search(record.get("notes", "")):
        errors.append(f"{record['run_id']}: notes appear to contain a credential")


def validate(path: Path, schema_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        import jsonschema

        payload = _load(path)
        schema = _load(schema_path)
        validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        errors.extend(error.message for error in validator.iter_errors(payload))
    except ImportError as exc:
        errors.append(f"jsonschema is required: {exc}")
        payload = {}
    except ValueError as exc:
        errors.append(str(exc))
        payload = {}

    if not errors and isinstance(payload, dict):
        records = payload["records"]
        lanes = [record["strictness"] for record in records]
        if len(set(lanes)) != len(lanes):
            errors.append("records must not duplicate strictness lanes")
        if set(lanes) != {"supportive", "neutral", "competing"}:
            errors.append("records must cover supportive, neutral, and competing lanes")
        for record in records:
            _validate_record(record, errors)

    return {
        "status": "valid" if not errors else "invalid",
        "pilot": str(path),
        "schema_version": payload.get("schema_version") if isinstance(payload, dict) else None,
        "records": len(payload.get("records", [])) if isinstance(payload, dict) and isinstance(payload.get("records"), list) else 0,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot", type=Path)
    parser.add_argument("--schema", type=Path, default=Path("schemas/skill-optimization-roi-pilot.schema.json"))
    args = parser.parse_args()
    try:
        result = validate(args.pilot, args.schema)
    except Exception as exc:  # CLI boundary must not leak a traceback.
        result = {"status": "invalid", "pilot": str(args.pilot), "records": 0, "errors": [f"internal validator error: {exc}"]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
