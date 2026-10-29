#!/usr/bin/env python3
"""Contract tests for the locally audited Graphify CLI surface.

These tests deliberately pin the evidence to the installed Graphify version.
An upgrade must rerun this contract audit before the skill documentation can be
treated as current.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
CONTRACT_PATH = SKILL_DIR / "schemas" / "cli-contract.json"
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
AUDITED_VERSION = CONTRACT["audited_version"]
GRAPHIFY_BIN = shutil.which("graphify")
DOC_PATHS = [SKILL_DIR / "SKILL.md", *sorted((SKILL_DIR / "references").glob("*.md"))]


def _graphify_python() -> str:
    if not GRAPHIFY_BIN:
        return ""
    first_line = Path(GRAPHIFY_BIN).read_text(encoding="utf-8").splitlines()[0]
    return first_line.removeprefix("#!")


@unittest.skipUnless(GRAPHIFY_BIN, "Graphify CLI is not installed; local CLI contract is unavailable")
class GraphifyCliContractTests(unittest.TestCase):
    def run_cli(self, *args: str, cwd: Path | None = None, timeout: int = 20) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [GRAPHIFY_BIN, *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    def test_version_matches_audited_install(self) -> None:
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), f"graphify {AUDITED_VERSION}")

    def test_capability_contract_is_structured(self) -> None:
        self.assertEqual(CONTRACT["tool"], "graphify")
        self.assertEqual(CONTRACT["contract_version"], "1")
        self.assertTrue(CONTRACT["core_commands"])
        self.assertIn("obsidian", CONTRACT["exports"])
        self.assertFalse(CONTRACT["mcp"]["top_level_flag"])

    def test_help_exposes_core_commands(self) -> None:
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in ("extract", "query", "path", "explain", "update", "export"):
            self.assertIn(command, result.stdout)
        self.assertNotIn("--mcp", result.stdout)

    def test_export_subcommands_are_explicit(self) -> None:
        result = self.run_cli("export")
        self.assertNotEqual(result.returncode, 0)
        for export_name in ("obsidian", "wiki", "neo4j", "falkordb", "graphml", "svg"):
            self.assertIn(export_name, result.stdout + result.stderr)

    def test_mcp_is_a_module_entrypoint(self) -> None:
        python = _graphify_python()
        self.assertTrue(python)
        result = subprocess.run(
            [python, "-m", "graphify.serve", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("graphify", result.stdout.lower())
        self.assertIn("transport", result.stdout)

    def test_docs_do_not_use_unverified_legacy_invocations(self) -> None:
        docs = "\n".join(path.read_text(encoding="utf-8") for path in DOC_PATHS)
        forbidden = (
            r"graphify\s+--mcp",
            r"graphify\s+\.\s+--obsidian",
            r"graphify\s+\.\s+--wiki",
            r"graphify\s+\.\s+--neo4j(?:-push)?",
            r"graphify\s+\.\s+--falkordb(?:-push)?",
            r"graphify\s+\.\s+--graphml",
            r"graphify\s+\.\s+--svg",
        )
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, docs), pattern)

    def test_local_code_only_round_trip_and_offline_exports(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecc-graphify-contract-") as raw_root:
            root = Path(raw_root)
            source = root / "src"
            source.mkdir()
            (source / "alpha.py").write_text(
                "class Alpha:\n    def run(self):\n        return helper()\n\ndef helper():\n    return 1\n",
                encoding="utf-8",
            )

            built = self.run_cli(
                "extract",
                str(source),
                "--code-only",
                "--no-cluster",
                "--out",
                str(root),
                cwd=root,
            )
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            graph = root / "graphify-out" / "graph.json"
            self.assertTrue(graph.is_file())
            graph_data = json.loads(graph.read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(graph_data.get("nodes", [])), 2)

            for args in (
                ("query", "Alpha"),
                ("explain", "Alpha"),
            ):
                result = self.run_cli(*args, "--graph", str(graph), cwd=root)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            path_result = self.run_cli(
                "path",
                "alpha.py",
                "Alpha",
                "--graph",
                str(graph),
                cwd=root,
            )
            self.assertEqual(path_result.returncode, 0, path_result.stdout + path_result.stderr)

            obsidian_dir = root / "obsidian"
            obsidian = self.run_cli(
                "export",
                "obsidian",
                "--graph",
                str(graph),
                "--dir",
                str(obsidian_dir),
                cwd=root,
            )
            self.assertEqual(obsidian.returncode, 0, obsidian.stdout + obsidian.stderr)
            self.assertTrue((obsidian_dir / "graph.canvas").is_file())
            self.assertTrue(any(obsidian_dir.glob("*.md")))

            for export_name in ("neo4j", "falkordb"):
                exported = self.run_cli(
                    "export",
                    export_name,
                    "--graph",
                    str(graph),
                    cwd=root,
                )
                self.assertEqual(exported.returncode, 0, exported.stdout + exported.stderr)
                self.assertTrue((root / "graphify-out" / "cypher.txt").is_file())


if __name__ == "__main__":
    unittest.main()
