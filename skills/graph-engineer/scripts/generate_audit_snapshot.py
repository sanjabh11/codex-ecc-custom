#!/usr/bin/env python3
"""Generate one reproducible Graph-engineer provenance and verification snapshot."""

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = REPO_ROOT / "skills" / "graph-engineer"
CANONICAL_GRAPH = REPO_ROOT / ".phase-loop" / "graph-engineer-pilots" / "pir-panjal-repair-graph-v1.1.json"
OUTPUT = REPO_ROOT / ".phase-loop" / "graph-engineer-pilots" / "graph-engineer-audit-snapshot.json"


def run(command):
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": stdout,
        "stderr": stderr,
    }


def count_status(status_output):
    lines = [line for line in status_output.splitlines() if line]
    return {
        "total_entries": len(lines),
        "tracked_or_staged": sum(not line.startswith("?? ") for line in lines),
        "untracked_collapsed": sum(line.startswith("?? ") for line in lines),
    }


def sha256(path):
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def inventory():
    files = {}
    if PACKAGE_ROOT.is_dir():
        for path in sorted(PACKAGE_ROOT.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            files[str(path.relative_to(REPO_ROOT))] = sha256(path)
    if CANONICAL_GRAPH.is_file():
        files[str(CANONICAL_GRAPH.relative_to(REPO_ROOT))] = sha256(CANONICAL_GRAPH)
    return files


def extract_counts(result):
    text = result["stdout"] + result["stderr"]
    passed = [int(value) for value in re.findall(r"(\d+) passed", text)]
    failed = [int(value) for value in re.findall(r"(\d+) failed", text)]
    checks = re.search(r"Checks passed: (\d+).*?Checks failed: (\d+)", text, re.S)
    parsed = {}
    if passed:
        parsed["passed_mentions"] = passed
    if failed:
        parsed["failed_mentions"] = failed
    if checks:
        parsed["checks_passed"] = int(checks.group(1))
        parsed["checks_failed"] = int(checks.group(2))
    return parsed


def main():
    captured_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    head = run(["git", "rev-parse", "HEAD"])
    status_collapsed = run(["git", "status", "--short", "--untracked-files=normal"])
    status_full = run(["git", "status", "--short", "--untracked-files=all"])
    disk = run(["df", "-k", str(REPO_ROOT)])
    commands = [
        ["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "skills/graph-engineer/tests"],
        ["python3", "-m", "unittest", "discover", "-s", "skills/graph-engineer/tests", "-p", "test*.py"],
        ["python3", "skills/graph-engineer/tests/test_validate.py"],
        ["python3", "skills/graph-engineer/tests/test_triggers.py"],
        ["python3", "skills/graph-engineer/scripts/validate_graph.py", str(CANONICAL_GRAPH.relative_to(REPO_ROOT)), "--runtime-root", str(REPO_ROOT)],
        ["git", "diff", "--check", "--", "skills/graph-engineer"],
    ]
    command_results = []
    for command in commands:
        result = run(command)
        result["parsed_counts"] = extract_counts(result)
        command_results.append(result)

    snapshot = {
        "snapshot_version": "v1",
        "captured_at_utc": captured_at,
        "repo_root": str(REPO_ROOT),
        "git": {
            "head": head["stdout"].strip(),
            "head_command": head,
            "status_collapsed": status_collapsed,
            "status_collapsed_counts": count_status(status_collapsed["stdout"]),
            "status_full": status_full,
            "status_full_counts": count_status(status_full["stdout"]),
        },
        "runtime": {
            "python": sys.version,
            "executable": str(Path(sys.executable).resolve()),
            "platform": sys.platform,
            "disk": disk,
        },
        "inventory_sha256": inventory(),
        "canonical_graph": str(CANONICAL_GRAPH.relative_to(REPO_ROOT)),
        "commands": command_results,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    temporary.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(OUTPUT)
    print(json.dumps({
        "snapshot": str(OUTPUT),
        "captured_at_utc": captured_at,
        "head": snapshot["git"]["head"],
        "collapsed_untracked": snapshot["git"]["status_collapsed_counts"]["untracked_collapsed"],
        "full_untracked": snapshot["git"]["status_full_counts"]["untracked_collapsed"],
        "inventory_files": len(snapshot["inventory_sha256"]),
        "commands": [result["returncode"] for result in command_results],
    }, indent=2))
    return 0 if all(result["returncode"] == 0 for result in command_results) else 1


if __name__ == "__main__":
    sys.exit(main())
