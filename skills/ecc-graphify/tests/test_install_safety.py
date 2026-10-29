#!/usr/bin/env python3
"""Regression tests for non-destructive platform-link installation."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
INSTALLER = SKILL_DIR / "scripts" / "graphify-platform-install.sh"
CANONICAL = SKILL_DIR


class GraphifyInstallSafetyTests(unittest.TestCase):
    def _home_with_wrong_links(self) -> tuple[Path, list[Path]]:
        temp = Path(tempfile.mkdtemp(prefix="ecc-graphify-install-"))
        platform_dirs = [
            temp / ".codeium" / "windsurf" / "skills",
            temp / ".claude" / "skills",
            temp / ".agents" / "skills",
            temp / ".devin" / "skills",
            temp / ".codex" / "skills",
        ]
        links = []
        for directory in platform_dirs:
            directory.mkdir(parents=True)
            link = directory / "ecc-graphify"
            link.symlink_to("/tmp/unexpected-graphify-source")
            links.append(link)
        return temp, links

    def test_unexpected_symlinks_are_preserved_without_force(self) -> None:
        home, links = self._home_with_wrong_links()
        result = subprocess.run(
            ["bash", str(INSTALLER)],
            env={**os.environ, "HOME": str(home)},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        for link in links:
            self.assertTrue(link.is_symlink())
            self.assertEqual(os.readlink(link), "/tmp/unexpected-graphify-source")

    def test_force_replaces_only_symlinks(self) -> None:
        home, links = self._home_with_wrong_links()
        result = subprocess.run(
            ["bash", str(INSTALLER), "--force"],
            env={**os.environ, "HOME": str(home)},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for link in links:
            self.assertTrue(link.is_symlink())
            self.assertEqual(os.readlink(link), str(CANONICAL))


if __name__ == "__main__":
    unittest.main()
