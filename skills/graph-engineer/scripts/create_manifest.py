#!/usr/bin/env python3
"""Create a content-bound runtime manifest from an already validated graph.

This records the caller-supplied approval decision; it is not an approval UI.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - dependency gate
    jsonschema = None

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_runtime import (  # noqa: E402
    check_tools,
    file_sha256,
    graph_hash,
    runtime_package,
    runtime_hash,
    runtime_identity,
    tool_snapshot,
    validate_graph,
)
try:
    from schema_utils import strict_format_checker  # noqa: E402
except ImportError:  # pragma: no cover - dependency-gate path
    strict_format_checker = None


def timestamp(value):
    return value.isoformat().replace("+00:00", "Z")


def main():
    parser = argparse.ArgumentParser(description="Create a strict graph-engineer runtime manifest")
    parser.add_argument("--graph", required=True)
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--approver", required=True)
    parser.add_argument("--decision", choices=["approved", "rejected", "aborted"], required=True)
    parser.add_argument("--runtime-profile", default="local")
    parser.add_argument("--expires-in-seconds", type=int, default=3600)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if (
        args.expires_in_seconds <= 0
        or not isinstance(args.run_id, str)
        or not args.run_id
        or args.run_id != args.run_id.strip()
        or not isinstance(args.approver, str)
        or not args.approver
        or args.approver != args.approver.strip()
    ):
        print("ERROR: run ID, approver, and positive expiry are required", file=sys.stderr)
        return 1
    valid, detail = validate_graph(args.graph, args.runtime_root)
    if not valid:
        print(f"ERROR: graph validation failed before manifest creation:\n{detail}", file=sys.stderr)
        return 1
    try:
        graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"ERROR: graph could not be parsed: {exc}", file=sys.stderr)
        return 1
    package = runtime_package(args.runtime_root)
    runtime_sha = runtime_hash(args.runtime_root)
    policy_path = package / "validation-rules.json" if package else None
    validator_sha = file_sha256(package / "scripts" / "validate_graph.py") if package else None
    policy_sha = file_sha256(policy_path) if policy_path else None
    if package is None or runtime_sha is None or validator_sha is None or policy_sha is None:
        print("ERROR: runtime package is incomplete or cannot be content-bound", file=sys.stderr)
        return 1
    tool_checks, blocked_tools, _ = check_tools(graph, rules_path=policy_path)
    if blocked_tools:
        print(f"ERROR: required tools are unavailable; manifest not created: {blocked_tools}", file=sys.stderr)
        return 1

    now = dt.datetime.now(dt.timezone.utc)
    expires = now + dt.timedelta(seconds=args.expires_in_seconds)
    graph_sha = graph_hash(graph)
    manifest = {
        "manifest_version": "v1",
        "graph_sha256": graph_sha,
        "runtime_sha256": runtime_sha,
        "validator_sha256": validator_sha,
        "policy_sha256": policy_sha,
        "issued_at": timestamp(now),
        "expires_at": timestamp(expires),
        "revoked": False,
        "runtime_profile": args.runtime_profile,
        "runtime_identity": runtime_identity(policy_path),
        "tool_snapshot": tool_snapshot(tool_checks),
        "approval_binding": {
            "run_id": args.run_id,
            "graph_sha256": graph_sha,
            "artifact_digest": args.artifact_digest,
            "action": args.action,
            "target": args.target,
            "approver": args.approver,
            "decision": args.decision,
            "approved_at": timestamp(now),
            "expires_at": timestamp(expires),
        },
    }
    if jsonschema is None or strict_format_checker is None:
        print("ERROR: jsonschema is required to create a schema-valid manifest", file=sys.stderr)
        return 1
    try:
        schema = json.loads((package / "schemas" / "runtime-manifest.schema.json").read_text(encoding="utf-8"))
        jsonschema.validate(
            instance=manifest,
            schema=schema,
            format_checker=strict_format_checker(),
        )
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, jsonschema.ValidationError, jsonschema.SchemaError) as exc:
        print(f"ERROR: generated manifest is not schema-valid: {exc}", file=sys.stderr)
        return 1
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    try:
        temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        temporary.replace(output)
    except OSError as exc:
        print(f"ERROR: manifest could not be written: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
