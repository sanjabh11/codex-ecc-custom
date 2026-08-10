#!/usr/bin/env python3
"""Schema-validated, node-bound, atomic JSONL evidence recorder."""

import argparse
import contextlib
import datetime as dt
import hashlib
import hmac
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX fallback
    msvcrt = None

try:
    import jsonschema
except ImportError:  # pragma: no cover - exercised with python -S
    jsonschema = None

try:
    from schema_utils import strict_format_checker
except ImportError:  # pragma: no cover - supports package-style imports
    try:
        from scripts.schema_utils import strict_format_checker
    except ImportError:  # pragma: no cover - dependency-gate path
        strict_format_checker = None


SKILL_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_DIR / "scripts" / "validate_graph.py"
EVIDENCE_SCHEMA = SKILL_DIR / "schemas" / "evidence-record.schema.json"
DEFAULT_ROOT = SKILL_DIR / "evidence"
DEFAULT_OUTPUT = DEFAULT_ROOT / "evidence.jsonl"


def canonical_graph_hash(graph):
    payload = json.dumps(graph, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def redact(value):
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if re.search(r"(?i)(api[_-]?key|token|secret|password|credential)", str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if not isinstance(value, str):
        return value
    return re.sub(
        r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+",
        r"\1=[REDACTED]",
        value,
    )


def parse_timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def parse_bound_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("approval timestamps must be non-empty RFC3339 strings")
    normalized = value.strip().replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("approval timestamps must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def validate_graph(graph_path, runtime_root, review_report=None):
    validator = VALIDATOR
    if runtime_root:
        package = (Path(runtime_root).resolve() / "skills" / "graph-engineer").resolve()
        try:
            package.relative_to(Path(runtime_root).resolve())
        except ValueError:
            return False, "runtime package escapes the supplied runtime root"
        validator = package / "scripts" / "validate_graph.py"
        if not validator.is_file():
            return False, "runtime validator is missing"
    command = [sys.executable, str(validator)]
    if runtime_root:
        command.extend(["--runtime-root", str(runtime_root)])
    if review_report:
        command.extend(["--review-report", str(review_report)])
    command.append(str(graph_path))
    try:
        result = subprocess.run(command, capture_output=True, text=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        return False, f"validator could not run: {exc}"
    try:
        output = result.stdout.decode("utf-8") + result.stderr.decode("utf-8")
    except UnicodeDecodeError as exc:
        return False, f"validator output was not valid UTF-8: {exc}"
    return result.returncode == 0, output[-2000:]


def existing_records(output, run_id, graph_sha256):
    if not output.exists():
        return []
    records = []
    try:
        schema = json.loads(EVIDENCE_SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"evidence schema could not be loaded: {exc}") from exc
    for line in output.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"existing evidence file contains invalid JSONL: {exc}") from exc
        if jsonschema is None:
            raise ValueError("jsonschema is required to validate existing evidence")
        try:
            jsonschema.validate(
                instance=value,
                schema=schema,
                format_checker=strict_format_checker(),
            )
        except (jsonschema.ValidationError, jsonschema.SchemaError) as exc:
            raise ValueError(f"existing evidence record is not schema-valid: {exc}") from exc
        if value.get("run_id") == run_id:
            if value.get("graph_sha256") != graph_sha256:
                raise ValueError(
                    f"evidence stream for run '{run_id}' contains mixed graph hashes"
                )
            records.append(value)
    return records


def _node_by_id(graph, node_id):
    return next(
        (node for node in graph.get("nodes", [])
         if isinstance(node, dict) and node.get("id") == node_id),
        None,
    )


def _has_successful_node_attempt(run_records, node_id):
    return any(
        record.get("event_type") == "node_attempt"
        and record.get("node_id") == node_id
        and record.get("status") in {"pass", "skip"}
        for record in run_records
    )


def _has_passing_review(run_records, node_id):
    return any(
        record.get("event_type") == "review"
        and record.get("node_id") == node_id
        and record.get("status") == "pass"
        for record in run_records
    )


def _has_failed_review_for_attempt(run_records, node_id, attempt):
    return any(
        record.get("event_type") == "review"
        and record.get("status") in {"fail", "retry"}
        and record.get("reviewed_node_id") == node_id
        and record.get("reviewed_attempt") == attempt
        for record in run_records
    )


def _reviewed_node_id(graph, reviewer_id):
    reviewer = _node_by_id(graph, reviewer_id)
    if reviewer is None or reviewer.get("type") != "reviewer":
        return None
    if isinstance(reviewer.get("reviewed_node_id"), str):
        return reviewer["reviewed_node_id"]
    incoming_workers = [
        edge.get("from")
        for edge in graph.get("edges", [])
        if isinstance(edge, dict)
        and edge.get("to") == reviewer_id
        and edge.get("type") in ("data", "control")
        and _node_by_id(graph, edge.get("from"))
        and _node_by_id(graph, edge.get("from")).get("type") == "worker"
    ]
    return incoming_workers[0] if len(incoming_workers) == 1 else None


def _resolve_evidence_file(raw_value, evidence_root):
    if not isinstance(raw_value, str) or not raw_value or raw_value != raw_value.strip():
        raise ValueError("review artifact path must be a non-empty string without surrounding whitespace")
    candidate = Path(raw_value)
    if not candidate.is_absolute():
        candidate = evidence_root / candidate
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(evidence_root)
    except ValueError as exc:
        raise ValueError("review artifact must remain inside --evidence-root") from exc
    if not resolved.is_file():
        raise ValueError("review artifact must be an existing regular file")
    return resolved, relative.as_posix()


def prepare_review_artifact(artifact, artifact_digest, evidence_root, reviewer_id):
    """Require a local, content-bound review report before recording a review."""
    if not artifact or not artifact_digest:
        raise ValueError("review events require --artifact and --artifact-digest")
    if not isinstance(artifact_digest, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", artifact_digest):
        raise ValueError("review artifact digest must be a full SHA-256 hex string")
    resolved, relative = _resolve_evidence_file(artifact, evidence_root)
    actual_digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    if not hmac.compare_digest(actual_digest.lower(), artifact_digest.lower()):
        raise ValueError("review artifact digest does not match file contents")
    try:
        report = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"review artifact is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(report, dict) or report.get("reviewer_id") != reviewer_id:
        raise ValueError("review artifact reviewer_id does not match --node")
    return resolved, relative, actual_digest.lower(), report


def _completion_errors(graph, run_records):
    errors = []
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_id = node.get("id")
        node_type = node.get("type")
        if node_type in ("planner", "worker", "synthesizer") and not _has_successful_node_attempt(run_records, node_id):
            errors.append(f"node '{node_id}' has no successful node_attempt")
        elif node_type == "reviewer" and not _has_passing_review(run_records, node_id):
            errors.append(f"reviewer '{node_id}' has no passing review")
        elif node_type == "human-gate":
            if not any(
                record.get("event_type") == "gate_decision"
                and record.get("node_id") == node_id
                and record.get("status") == "pass"
                for record in run_records
            ):
                errors.append(f"human gate '{node_id}' has no passing gate_decision")
    return errors


def ensure_lifecycle(event_type, run_records, node_id, attempt, graph):
    terminal = any(record.get("event_type") in ("run_finished", "run_aborted") for record in run_records)
    if terminal:
        raise ValueError("run has already reached a terminal state")
    if event_type == "run_started" and run_records:
        raise ValueError("run_started cannot be recorded twice for the same run")
    if event_type != "run_started" and not any(record.get("event_type") == "run_started" for record in run_records):
        raise ValueError("a run_started record is required before execution evidence")
    if event_type == "node_attempt":
        prior_attempts = [
            record.get("attempt", 0)
            for record in run_records
            if record.get("event_type") == "node_attempt" and record.get("node_id") == node_id
        ]
        if prior_attempts:
            latest = max(
                (
                    record for record in run_records
                    if record.get("event_type") == "node_attempt" and record.get("node_id") == node_id
                ),
                key=lambda record: record.get("attempt", 0),
            )
            if latest.get("status") in {"pass", "skip"} and not _has_failed_review_for_attempt(
                run_records,
                node_id,
                latest.get("attempt", 0),
            ):
                raise ValueError(f"node '{node_id}' cannot start another attempt after {latest.get('status')}")
            if attempt != max(prior_attempts) + 1:
                raise ValueError(f"node '{node_id}' attempt must be {max(prior_attempts) + 1}")
    review_attempt = None
    # G12: Enforce lifecycle ordering — review events require prior node_attempt
    if event_type == "review":
        reviewed_node_id = _reviewed_node_id(graph, node_id)
        if reviewed_node_id is None:
            raise ValueError(f"reviewer '{node_id}' has no reviewed_node_id binding")
        worker_attempts = [
            record for record in run_records
            if record.get("event_type") == "node_attempt"
            and record.get("node_id") == reviewed_node_id
            and record.get("status") in {"pass", "skip"}
        ]
        if not worker_attempts:
            raise ValueError(
                f"review on reviewer '{node_id}' requires a prior successful node_attempt "
                f"on reviewed node '{reviewed_node_id}'"
            )
        review_attempt = max(record.get("attempt", 0) for record in worker_attempts)
        prior_reviews = [
            record for record in run_records
            if record.get("event_type") == "review" and record.get("node_id") == node_id
        ]
        if prior_reviews:
            latest_review = max(prior_reviews, key=lambda record: record.get("attempt", 0))
            if latest_review.get("status") == "pass":
                raise ValueError(f"reviewer '{node_id}' cannot review again after pass")
            if attempt != latest_review.get("attempt", 0) + 1:
                raise ValueError(f"reviewer '{node_id}' attempt must be {latest_review.get('attempt', 0) + 1}")
            if review_attempt <= latest_review.get("reviewed_attempt", 0):
                raise ValueError(
                    f"reviewer '{node_id}' must review a newer worker attempt after a failed review"
                )
    # G12: Enforce lifecycle ordering — gate_decision requires prior work
    # (either a node_attempt or a review must exist before gating)
    if event_type == "gate_decision":
        gate = _node_by_id(graph, node_id)
        predecessors = {
            edge.get("from")
            for edge in graph.get("edges", [])
            if isinstance(edge, dict)
            and edge.get("to") == node_id
            and edge.get("type") in ("data", "control")
        }
        if not predecessors:
            raise ValueError(f"gate_decision target '{node_id}' has no data/control predecessor")
        if not all(
            _has_successful_node_attempt(run_records, predecessor)
            or _has_passing_review(run_records, predecessor)
            for predecessor in predecessors
        ):
            raise ValueError(
                f"gate_decision on '{node_id}' requires terminal evidence for every direct predecessor"
            )
    # G12: Enforce completion check before run_finished
    if event_type == "run_finished":
        errors = _completion_errors(graph, run_records)
        if errors:
            raise ValueError("run_finished requires complete graph evidence: " + "; ".join(errors))
    return review_attempt


def check_node_type_compatibility(event_type, node_id, graph):
    """G11: Enforce event-type/node-type compatibility.

    - review events only on reviewer nodes
    - node_attempt events only on worker/planner/synthesizer nodes
    - gate_decision events only on human-gate nodes
    """
    if event_type in ("run_started", "run_finished", "run_aborted"):
        if node_id is not None:
            raise ValueError(f"{event_type} events must not be bound to a node")
        return
    if node_id is None:
        return
    nodes = graph.get("nodes", [])
    node = next((n for n in nodes if isinstance(n, dict) and n.get("id") == node_id), None)
    if node is None:
        raise ValueError(f"node '{node_id}' is not declared by the graph")
    node_type = node.get("type", "")
    if event_type == "review" and node_type != "reviewer":
        raise ValueError(f"review events can only be recorded on reviewer nodes, got type '{node_type}'")
    if event_type == "node_attempt" and node_type not in ("worker", "planner", "synthesizer"):
        raise ValueError(f"node_attempt events can only be recorded on executable nodes (worker/planner/synthesizer), got type '{node_type}'")
    if event_type == "gate_decision" and node_type != "human-gate":
        raise ValueError(f"gate_decision events can only be recorded on human-gate nodes, got type '{node_type}'")


@contextlib.contextmanager
def exclusive_append_lock(output):
    """Serialize read/validate/append across processes without a third-party dependency."""
    lock_path = Path(f"{output}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        elif msvcrt is not None:  # pragma: no cover - Windows-only branch
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:  # pragma: no cover - unsupported platform
            raise OSError("no supported file-locking primitive is available")
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            elif msvcrt is not None:  # pragma: no cover - Windows-only branch
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def main():
    parser = argparse.ArgumentParser(description="Record schema-validated graph execution evidence")
    parser.add_argument("--graph", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--event-type", choices=["run_started", "node_attempt", "review", "gate_decision", "run_finished", "run_aborted"], default="node_attempt")
    parser.add_argument("--node", default=None)
    parser.add_argument("--status", choices=["started", "pass", "fail", "retry", "skip", "finished", "aborted"], default=None)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--artifact", default=None)
    parser.add_argument("--artifact-digest", default=None)
    parser.add_argument("--source", action="append", default=None)
    parser.add_argument("--evaluator", default=None)
    parser.add_argument("--runtime-decision", choices=["available", "degraded", "blocked", "revoked"], default=None)
    parser.add_argument("--latency-ms", type=int, default=None)
    parser.add_argument("--tokens", type=int, default=None)
    parser.add_argument("--cost-usd", type=float, default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--approval-binding", default=None, help="JSON object binding the gate decision to a run and artifact")
    parser.add_argument("--manifest", default=None, help="Use the manifest's approval_binding for a gate decision")
    parser.add_argument("--note", default=None)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--evidence-root", default=str(DEFAULT_ROOT))
    parser.add_argument("--runtime-root", default=None)
    args = parser.parse_args()

    if not isinstance(args.run_id, str) or not args.run_id or args.run_id != args.run_id.strip():
        print("ERROR: --run-id must be a non-empty string without surrounding whitespace", file=sys.stderr)
        return 1
    if args.event_type in ("node_attempt", "review", "gate_decision") and not args.node:
        print("ERROR: --node is required for execution, review, and gate events", file=sys.stderr)
        return 1
    if args.event_type == "run_started":
        args.status = args.status or "started"
    elif args.event_type == "run_finished":
        args.status = args.status or "finished"
    elif args.event_type == "run_aborted":
        args.status = args.status or "aborted"
    elif args.status is None:
        print("ERROR: --status is required for this event type", file=sys.stderr)
        return 1
    if args.attempt < 1 or any(value is not None and (value < 0 or not math.isfinite(value)) for value in (args.latency_ms, args.tokens, args.cost_usd)):
        print("ERROR: attempt and resource measurements must be non-negative, with attempt >= 1", file=sys.stderr)
        return 1

    try:
        graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"ERROR: graph could not be parsed: {exc}", file=sys.stderr)
        return 1
    if not isinstance(graph, dict):
        print("ERROR: graph root must be an object", file=sys.stderr)
        return 1
    try:
        check_node_type_compatibility(args.event_type, args.node, graph)
    except ValueError as exc:
        print(f"ERROR: evidence event is invalid: {exc}", file=sys.stderr)
        return 1
    if jsonschema is None or strict_format_checker is None:
        print("ERROR: jsonschema is required to record evidence", file=sys.stderr)
        return 1

    output = Path(args.output).resolve()
    evidence_root = Path(args.evidence_root).resolve()
    try:
        output.relative_to(evidence_root)
    except ValueError:
        print("ERROR: evidence output must be inside --evidence-root", file=sys.stderr)
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)

    review_artifact_path = None
    recorded_artifact = args.artifact
    recorded_artifact_digest = args.artifact_digest
    if args.event_type == "review":
        try:
            review_artifact_path, recorded_artifact, recorded_artifact_digest, report = prepare_review_artifact(
                args.artifact,
                args.artifact_digest,
                evidence_root,
                args.node,
            )
        except (OSError, ValueError) as exc:
            print(f"ERROR: review artifact is invalid: {exc}", file=sys.stderr)
            return 1
        expected_result = "pass" if args.status == "pass" else "fail" if args.status in ("fail", "retry") else None
        if expected_result is None or report.get("result") != expected_result:
            print("ERROR: review event status does not match review artifact result", file=sys.stderr)
            return 1

    valid, validation_output = validate_graph(args.graph, args.runtime_root, review_artifact_path)
    if not valid:
        print(f"ERROR: graph validation failed before evidence recording:\n{validation_output}", file=sys.stderr)
        return 1
    try:
        approval_binding = json.loads(args.approval_binding) if args.approval_binding else None
        if args.manifest:
            manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
            manifest_binding = manifest.get("approval_binding")
            if not isinstance(manifest_binding, dict):
                raise ValueError("manifest approval_binding must be an object")
            if approval_binding is not None and approval_binding != manifest_binding:
                raise ValueError("--approval-binding does not match --manifest approval_binding")
            approval_binding = manifest_binding
        if approval_binding is not None and not isinstance(approval_binding, dict):
            raise ValueError("--approval-binding must be a JSON object")
    except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: approval binding is invalid: {exc}", file=sys.stderr)
        return 1

    graph_sha256 = canonical_graph_hash(graph)
    if args.event_type == "gate_decision":
        if approval_binding is None:
            print("ERROR: gate_decision requires --approval-binding", file=sys.stderr)
            return 1
        required_binding = {
            "run_id", "graph_sha256", "artifact_digest", "action", "target",
            "approver", "decision", "approved_at", "expires_at",
        }
        missing_binding = sorted(required_binding - set(approval_binding))
        if missing_binding:
            print(f"ERROR: approval binding is missing: {', '.join(missing_binding)}", file=sys.stderr)
            return 1
        try:
            parse_bound_timestamp(approval_binding["approved_at"])
            parse_bound_timestamp(approval_binding["expires_at"])
        except ValueError as exc:
            print(f"ERROR: approval binding is invalid: {exc}", file=sys.stderr)
            return 1
        if approval_binding["run_id"] != args.run_id or approval_binding["graph_sha256"] != graph_sha256:
            print("ERROR: approval binding does not match this run or graph", file=sys.stderr)
            return 1
        if not args.artifact_digest or approval_binding["artifact_digest"] != args.artifact_digest:
            print("ERROR: gate_decision requires an artifact digest matching the approval binding", file=sys.stderr)
            return 1
        gate = next((gate for gate in graph.get("human_gates", []) if gate.get("position") == args.node), None)
        if gate is None or approval_binding["target"] != args.node or approval_binding["action"] != gate.get("action"):
            print("ERROR: approval binding target or action does not match the graph human gate", file=sys.stderr)
            return 1

    try:
        with exclusive_append_lock(output):
            records = existing_records(output, args.run_id, graph_sha256)
            node_ids = {node.get("id") for node in graph.get("nodes", []) if isinstance(node, dict)}
            if args.node and args.node not in node_ids:
                raise ValueError(f"node '{args.node}' is not declared by the graph")
            if review_artifact_path is not None:
                current_artifact_path = review_artifact_path.resolve()
                try:
                    current_artifact_path.relative_to(evidence_root)
                except ValueError as exc:
                    raise ValueError("review artifact moved outside --evidence-root before append") from exc
                if current_artifact_path != review_artifact_path or not current_artifact_path.is_file():
                    raise ValueError("review artifact changed before append")
                current_digest = hashlib.sha256(current_artifact_path.read_bytes()).hexdigest()
                if not hmac.compare_digest(current_digest, recorded_artifact_digest):
                    raise ValueError("review artifact changed after validation")
            reviewed_node_id = _reviewed_node_id(graph, args.node) if args.event_type == "review" else None
            reviewed_attempt = ensure_lifecycle(args.event_type, records, args.node, args.attempt, graph)
            record = {
                "run_id": args.run_id,
                "graph_sha256": graph_sha256,
                "timestamp": parse_timestamp(),
                "event_type": args.event_type,
                "node_id": args.node,
                "reviewed_node_id": reviewed_node_id,
                "reviewed_attempt": reviewed_attempt,
                "status": args.status,
                "attempt": args.attempt,
                "artifact": redact(recorded_artifact),
                "artifact_digest": redact(recorded_artifact_digest),
                "source": [redact(item) for item in args.source] if args.source else None,
                "evaluator": redact(args.evaluator),
                "runtime_decision": args.runtime_decision,
                "latency_ms": args.latency_ms,
                "tokens": args.tokens,
                "cost_usd": args.cost_usd,
                "model": redact(args.model),
                "approval_binding": redact(approval_binding),
                "note": redact(args.note),
            }
            schema = json.loads(EVIDENCE_SCHEMA.read_text(encoding="utf-8"))
            jsonschema.validate(
                instance=record,
                schema=schema,
                format_checker=strict_format_checker(),
            )
            line = json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n"
            with output.open("a", encoding="utf-8") as handle:
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())
    except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError, jsonschema.ValidationError, jsonschema.SchemaError) as exc:
        print(f"ERROR: evidence lifecycle, schema, or append is invalid: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
