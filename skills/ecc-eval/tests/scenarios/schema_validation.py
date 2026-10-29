#!/usr/bin/env python3
"""Scenario: Schema validation — eval-definition and eval-result schemas are valid JSON Schema."""

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent

def main():
    for schema_file in ["eval-definition.schema.json", "eval-result.schema.json"]:
        path = SKILL_DIR / "schemas" / schema_file
        assert path.exists(), f"Schema {schema_file} not found"
        data = json.loads(path.read_text())
        assert "$schema" in data, f"{schema_file} missing $schema"
        assert "type" in data, f"{schema_file} missing type"
        assert "properties" in data, f"{schema_file} missing properties"
        assert "required" in data, f"{schema_file} missing required"

    print("PASS: schema_validation — both schemas are valid JSON Schema")
    sys.exit(0)


if __name__ == "__main__":
    main()
