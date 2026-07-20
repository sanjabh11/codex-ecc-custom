#!/usr/bin/env python3
"""Scenario: Context file loading — large context from file.

Tests that --context-file flag loads content from a file and combines
it with positional arguments.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


def main():
    cli_path = PROJECT_ROOT / "fable" / "advisor_cli.py"

    # Create a temporary context file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Task Context\n\nThis is a large context that would exceed shell arg limits.\n" * 50)
        context_file_path = f.name

    try:
        # Run with --dry-run to avoid API call, --context-file to load the file
        result = subprocess.run(
            [sys.executable, str(cli_path), "--dry-run", "--context-file", context_file_path, "Additional question"],
            capture_output=True, text=True,
            cwd=str(PROJECT_ROOT),
        )

        assert result.returncode == 0, f"CLI exited with {result.returncode}: {result.stderr}"

        # Dry run output should mention the context size
        output = result.stdout
        assert "Dry run" in output, f"Expected dry run message, got: {output[:100]}"
        # The context should be large (file content + "Additional question")
        # Dry run reports character count
        assert "chars" in output, f"Expected char count in dry run output, got: {output[:100]}"

        # Verify the context was loaded (should be > 2000 chars from the repeated lines)
        # Extract the number from "would call advisor with N chars"
        import re
        match = re.search(r'(\d+) chars', output)
        assert match, f"Could not find char count in output: {output}"
        char_count = int(match.group(1))
        assert char_count > 2000, f"Context file content should be >2000 chars, got {char_count}"

    finally:
        import os
        os.unlink(context_file_path)

    print("PASS: context_file_loading — large context loaded from file successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
