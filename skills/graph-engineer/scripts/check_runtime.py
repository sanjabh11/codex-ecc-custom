#!/usr/bin/env python3
"""Fail-closed pre-run gate for graph-engineer graphs.

This command validates the graph, runtime package, tools, manifest, and human
approval binding. It is a pre-run gate, not a graph executor or process
supervisor.
"""

import datetime as dt
import hashlib
import json
import os
import platform as host_platform
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import jsonschema
except ImportError:  # pragma: no cover - exercised with python -S
    jsonschema = None

try:
    from runtime_policy import classify_tool, executable_available, load_tool_policy, normalize_tool
except ImportError:  # pragma: no cover - supports package-style imports
    from scripts.runtime_policy import classify_tool, executable_available, load_tool_policy, normalize_tool

try:
    from schema_utils import strict_format_checker
except ImportError:  # pragma: no cover - supports package-style imports
    try:
        from scripts.schema_utils import strict_format_checker
    except ImportError:  # pragma: no cover - dependency-gate path
        strict_format_checker = None


SKILL_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_DIR / "scripts" / "validate_graph.py"
MANIFEST_SCHEMA = SKILL_DIR / "schemas" / "runtime-manifest.schema.json"
RULES_PATH = SKILL_DIR / "validation-rules.json"
REQUIRED_RUNTIME_FILES = (
    "SKILL.md",
    "activation-policy.json",
    "requirements.txt",
    "validation-rules.json",
    "scripts/validate_graph.py",
    "scripts/check_runtime.py",
    "scripts/record_evidence.py",
    "scripts/runtime_policy.py",
    "scripts/schema_utils.py",
    "schemas/activation-policy.schema.json",
    "schemas/evidence-record.schema.json",
    "schemas/graph-definition.schema.json",
    "schemas/node-definition.schema.json",
    "schemas/review-report.schema.json",
    "schemas/runtime-manifest.schema.json",
)


def runtime_package(runtime_root):
    if not runtime_root:
        return None
    root = Path(runtime_root).resolve()
    package = (root / "skills" / "graph-engineer").resolve()
    if not package.is_dir():
        return None
    try:
        package.relative_to(root)
    except ValueError:
        return None
    return package


def file_sha256(path):
    try:
        resolved = Path(path).resolve()
        if not resolved.is_file():
            return None
        return hashlib.sha256(resolved.read_bytes()).hexdigest()
    except (OSError, UnicodeError):
        return None


def decode_process_output(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value if isinstance(value, str) else ""


def runtime_identity(policy_path=None):
    policy_path = Path(policy_path) if policy_path else RULES_PATH
    return {
        "platform": sys.platform,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "executable": Path(sys.executable).name,
        "interpreter_path": str(Path(sys.executable).resolve()),
        "host_profile": f"{sys.platform}:{host_platform.machine()}",
        "hostname": os.uname().nodename if hasattr(os, 'uname') else 'unknown',
        "policy_sha256": file_sha256(policy_path),
    }


def canonical_json_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def graph_hash(graph):
    return canonical_json_hash(graph)


def runtime_hash(runtime_root):
    """Hash package paths and contents, excluding generated Python caches.

    G8: When runtime_root is missing or invalid, return None instead of a
    sentinel hash. Callers must check for None and fail closed.
    """
    if not runtime_root:
        return None
    package = runtime_package(runtime_root)
    if package is None:
        return None
    for relative in REQUIRED_RUNTIME_FILES:
        required = package / relative
        try:
            required.resolve().relative_to(package)
        except ValueError:
            return None
        if not required.is_file():
            return None
    digest = hashlib.sha256()
    for path in sorted(package.rglob("*")):
        relative_path = path.relative_to(package)
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc" or (relative_path.parts and relative_path.parts[0] == "evidence"):
            continue
        try:
            path.resolve().relative_to(package.resolve())
        except ValueError:
            return None  # G8: unsafe symlink — fail closed
        relative = relative_path.as_posix().encode("utf-8")
        digest.update(relative + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def load_graph(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return None, f"graph could not be parsed: {exc}"
    if not isinstance(value, dict):
        return None, f"graph root must be an object, got {type(value).__name__}"
    return value, None


def validate_graph(graph_path, runtime_root):
    validator = VALIDATOR
    if runtime_root:
        package = runtime_package(runtime_root)
        if package is None:
            return False, "runtime package is missing or incomplete"
        validator = package / "scripts" / "validate_graph.py"
    command = [sys.executable, str(validator)]
    if runtime_root:
        command.extend(["--runtime-root", str(runtime_root)])
    command.append(str(graph_path))
    try:
        result = subprocess.run(command, capture_output=True, text=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        return False, f"validator could not run: {exc}"
    try:
        output = decode_process_output(result.stdout) + decode_process_output(result.stderr)
    except UnicodeDecodeError as exc:
        return False, f"validator output was not valid UTF-8: {exc}"
    return result.returncode == 0, output[-3000:]


def parse_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty RFC3339 string")
    normalized = value.strip().replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def check_runtime_refs(graph, runtime_root):
    refs = graph.get("runtime_refs", [])
    if not refs:
        return {"status": "ok", "missing": [], "checked": 0, "targets": []}
    if not runtime_root:
        return {"status": "blocked", "missing": refs, "checked": 0, "reason": "runtime_refs require --runtime-root"}
    root = Path(runtime_root).resolve()
    skills_root = (root / "skills").resolve()
    missing = []
    targets = []
    for ref in refs:
        if not isinstance(ref, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", ref):
            missing.append(ref)
            continue
        path = (skills_root / ref / "SKILL.md").resolve()
        try:
            path.relative_to(skills_root)
        except ValueError:
            missing.append(ref)
            continue
        if not path.is_file():
            missing.append(ref)
        else:
            targets.append({"ref": ref, "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    if missing:
        return {"status": "blocked", "missing": missing, "checked": len(refs), "targets": targets}
    return {"status": "ok", "missing": [], "checked": len(refs), "targets": targets}


def run_health_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=False, timeout=10)
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        return False, str(exc)
    try:
        output = decode_process_output(result.stdout) + decode_process_output(result.stderr)
    except UnicodeDecodeError as exc:
        return False, f"health command output was not valid UTF-8: {exc}"
    return result.returncode == 0, output.strip()[-500:]


def version_tuple(value):
    match = re.search(r"\d+(?:\.\d+)+", value or "")
    return tuple(int(part) for part in match.group(0).split(".")) if match else None


def check_tools(graph, rules_path=None):
    # G14: load_tool_policy now raises ValueError on malformed/missing policy
    # instead of falling back to defaults. Catch and block.
    try:
        policy = load_tool_policy(str(rules_path or RULES_PATH))
    except ValueError as exc:
        return [], [{"node": None, "reason": f"tool policy load failed: {exc}"}], []
    checks = []
    blocked = []
    degraded = []
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            blocked.append({"node": None, "reason": "node is not an object"})
            continue
        tools = node.get("tools", [])
        if not isinstance(tools, list):
            blocked.append({"node": node.get("id"), "reason": "tools must be a list"})
            continue
        for raw_tool in tools:
            declaration = normalize_tool(raw_tool)
            if declaration is None:
                blocked.append({"node": node.get("id"), "reason": "malformed tool declaration"})
                continue
            name = declaration["name"]
            category = classify_tool(name, policy)
            available = executable_available(name)
            record = {"node": node.get("id"), "tool": name, "category": category, "available": available}
            # G9: Unknown tools are never accepted by this policy version —
            # they must first be added to the shared taxonomy and reviewed.
            if category == "unknown":
                record["status"] = "blocked"
                blocked.append({"node": node.get("id"), "tool": name, "reason": "unknown tool not in policy taxonomy — blocked by default"})
                checks.append(record)
                continue
            if not available:
                if category == "advisory" or not declaration["required"]:
                    record["status"] = "degraded"
                    degraded.append({"node": node.get("id"), "tool": name, "reason": "optional tool unavailable"})
                else:
                    record["status"] = "blocked"
                    blocked.append({"node": node.get("id"), "tool": name, "reason": "required tool unavailable"})
                checks.append(record)
                continue
            if declaration.get("health_command"):
                healthy, detail = run_health_command(declaration["health_command"])
                record["health"] = {"ok": healthy, "detail": detail}
                if not healthy:
                    if declaration["required"] and category != "advisory":
                        blocked.append({"node": node.get("id"), "tool": name, "reason": "health command failed"})
                    else:
                        degraded.append({"node": node.get("id"), "tool": name, "reason": "optional health command failed"})
            try:
                version_result = subprocess.run([name, "--version"], capture_output=True, text=False, timeout=10)
                try:
                    version_output = (
                        decode_process_output(version_result.stdout)
                        + decode_process_output(version_result.stderr)
                    )
                except UnicodeDecodeError as exc:
                    raise UnicodeDecodeError(exc.encoding, exc.object, exc.start, exc.end, str(exc)) from exc
                actual_version = version_tuple(version_output)
            except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
                actual_version = None
                record["version_error"] = str(exc)
            record["version"] = {"actual": list(actual_version) if actual_version else None}
            if declaration.get("min_version"):
                required = version_tuple(declaration["min_version"])
                record["version"]["required"] = list(required) if required else None
                if actual_version is None or required is None or actual_version < required:
                    blocked.append({"node": node.get("id"), "tool": name, "reason": "minimum version not satisfied"})
            record.setdefault("status", "available")
            checks.append(record)
    return checks, blocked, degraded


def tool_snapshot(checks):
    snapshot = {}
    for check in checks:
        name = check["tool"]
        snapshot[name] = {
            "category": check["category"],
            "available": bool(check["available"]),
            "version": check.get("version", {}).get("actual"),
        }
    return snapshot


def check_manifest(
    manifest_path,
    graph,
    graph_sha,
    runtime_sha,
    run_id,
    artifact_digest,
    tool_checks,
    runtime_root,
):
    if not manifest_path:
        return {"status": "blocked", "reason": "--manifest is required for a pre-run decision"}
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return {"status": "blocked", "reason": f"manifest could not be parsed: {exc}"}
    if jsonschema is None or strict_format_checker is None:
        return {"status": "blocked", "reason": "jsonschema and the strict format checker are required to validate the runtime manifest"}
    try:
        package = runtime_package(runtime_root)
        schema_path = package / "schemas" / "runtime-manifest.schema.json" if package else MANIFEST_SCHEMA
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(
            instance=manifest,
            schema=schema,
            format_checker=strict_format_checker(),
        )
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, jsonschema.ValidationError, jsonschema.SchemaError) as exc:
        return {"status": "blocked", "reason": f"manifest schema validation failed: {exc}"}
    try:
        issued_at = parse_timestamp(manifest["issued_at"])
        expires_at = parse_timestamp(manifest["expires_at"])
        approval_expires = parse_timestamp(manifest["approval_binding"]["expires_at"])
        approved_at = parse_timestamp(manifest["approval_binding"]["approved_at"])
    except ValueError as exc:
        return {"status": "blocked", "reason": str(exc)}
    now = dt.datetime.now(dt.timezone.utc)
    if issued_at > now + dt.timedelta(minutes=5):
        return {"status": "blocked", "reason": "manifest is issued in the future"}
    if expires_at <= now or approval_expires <= now:
        return {"status": "revoked", "reason": "manifest or approval has expired"}
    if approved_at > now + dt.timedelta(minutes=5):
        return {"status": "blocked", "reason": "approval is issued in the future"}
    if manifest["revoked"]:
        return {"status": "revoked", "reason": manifest.get("revocation_reason", "manifest is revoked")}
    if manifest["graph_sha256"] != graph_sha or manifest["approval_binding"]["graph_sha256"] != graph_sha:
        return {"status": "blocked", "reason": "manifest graph hash does not match graph"}
    if manifest["runtime_sha256"] != runtime_sha:
        return {"status": "blocked", "reason": "manifest runtime hash does not match runtime package"}
    policy_path = runtime_package(runtime_root) / "validation-rules.json"
    current_identity = runtime_identity(policy_path)
    if manifest["runtime_identity"] != current_identity:
        return {"status": "blocked", "reason": "manifest runtime identity does not match this host runtime"}
    if manifest["policy_sha256"] != current_identity["policy_sha256"]:
        return {"status": "blocked", "reason": "manifest policy hash does not match runtime policy"}
    validator_sha = file_sha256(runtime_package(runtime_root) / "scripts" / "validate_graph.py")
    if manifest["validator_sha256"] != validator_sha:
        return {"status": "blocked", "reason": "manifest validator hash does not match runtime validator"}
    if manifest["tool_snapshot"] != tool_snapshot(tool_checks):
        return {"status": "blocked", "reason": "manifest tool snapshot does not match current tool health/version results"}
    approval = manifest["approval_binding"]
    if run_id is None or artifact_digest is None:
        return {"status": "blocked", "reason": "--run-id and --artifact-digest are required for approval binding"}
    if approval["run_id"] != run_id or approval["artifact_digest"] != artifact_digest:
        return {"status": "blocked", "reason": "approval binding does not match requested run or artifact"}
    if approval["decision"] != "approved":
        return {"status": "blocked", "reason": f"approval decision is {approval['decision']}"}
    gates = graph.get("human_gates", [])
    if gates and not any(
        approval["action"] == gate.get("action") and approval["target"] == gate.get("position")
        for gate in gates
    ):
        return {"status": "blocked", "reason": "approval action or target does not match graph human gate"}
    return {"status": "ok", "manifest_version": manifest["manifest_version"], "approval": approval}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fail-closed graph-engineer pre-run gate")
    parser.add_argument("--graph", required=True)
    parser.add_argument("--runtime-root", default=None)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--artifact-digest", default=None)
    args = parser.parse_args()

    graph, graph_error = load_graph(args.graph)
    if graph_error:
        print(json.dumps({"decision": "blocked", "reason": graph_error}, indent=2))
        return 1
    valid, validator_output = validate_graph(args.graph, args.runtime_root)
    if not valid:
        print(json.dumps({"decision": "blocked", "reason": "graph validation failed", "validator_output": validator_output}, indent=2))
        return 1

    graph_sha = graph_hash(graph)
    runtime_sha = runtime_hash(args.runtime_root)
    # G8: If runtime_hash returned None, the runtime root is missing or unsafe.
    # Fail closed — do not report available.
    if runtime_sha is None:
        print(json.dumps({
            "decision": "blocked",
            "reason": "runtime root is missing, invalid, or contains unsafe symlinks — cannot produce a runtime hash",
            "graph_sha256": graph_sha,
        }, indent=2))
        return 1
    package = runtime_package(args.runtime_root)
    policy_path = package / "validation-rules.json" if package else None
    validator_sha = file_sha256(package / "scripts" / "validate_graph.py") if package else None
    policy_sha = file_sha256(policy_path) if policy_path else None
    if package is None or validator_sha is None or policy_sha is None:
        print(json.dumps({
            "decision": "blocked",
            "reason": "runtime package, validator, or policy digest is unavailable",
            "graph_sha256": graph_sha,
            "runtime_sha256": runtime_sha,
        }, indent=2))
        return 1
    tool_checks, blocked_tools, degraded_tools = check_tools(graph, rules_path=policy_path)
    refs_result = check_runtime_refs(graph, args.runtime_root)
    manifest_result = check_manifest(
        args.manifest,
        graph,
        graph_sha,
        runtime_sha,
        args.run_id,
        args.artifact_digest,
        tool_checks,
        args.runtime_root,
    )
    decision = "available"
    if blocked_tools or refs_result["status"] == "blocked" or manifest_result["status"] == "blocked":
        decision = "blocked"
    elif manifest_result["status"] == "revoked":
        decision = "revoked"
    elif degraded_tools:
        decision = "degraded"

    report = {
        "decision": decision,
        "graph_sha256": graph_sha,
        "runtime_sha256": runtime_sha,
        "runtime_identity": runtime_identity(policy_path),
        "validator_sha256": validator_sha,
        "policy_sha256": policy_sha,
        "tool_snapshot": tool_snapshot(tool_checks),
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "tool_checks": tool_checks,
        "blocked_tools": blocked_tools,
        "degraded_tools": degraded_tools,
        "runtime_refs_check": refs_result,
        "manifest_check": manifest_result,
        "limitations": [
            "This gate cannot terminate already-running processes or bypassed invocations.",
            "This gate is a pre-run decision boundary, not a graph executor or process supervisor.",
            "Host-specific loader execution remains unproven until a supported host smoke test runs.",
        ],
    }
    print(json.dumps(report, indent=2))
    return 0 if decision in ("available", "degraded") else 1


if __name__ == "__main__":
    sys.exit(main())
