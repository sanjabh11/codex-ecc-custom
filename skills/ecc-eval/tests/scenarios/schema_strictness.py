#!/usr/bin/env python3
"""Scenario: Schema strictness — additionalProperties: false rejects unknown fields."""

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent

def main():
    try:
        import jsonschema
    except ImportError:
        print("SKIP: jsonschema not installed")
        sys.exit(0)

    # eval-definition schema
    def_schema = json.loads((SKILL_DIR / "schemas" / "eval-definition.schema.json").read_text())
    assert def_schema.get("additionalProperties") is False, "eval-definition schema missing additionalProperties: false"

    # Try validating with an unknown field
    bad_data = {"eval_type": "capability", "name": "test", "task": "test task here", "success_criteria": ["c1"], "unknown_field": "bad"}
    errors = list(jsonschema.Draft202012Validator(def_schema).iter_errors(bad_data))
    assert len(errors) > 0, "Schema should reject unknown fields"

    # eval-result schema
    res_schema = json.loads((SKILL_DIR / "schemas" / "eval-result.schema.json").read_text())
    assert res_schema.get("additionalProperties") is False, "eval-result schema missing additionalProperties: false"

    bad_result = {"eval_name": "test", "status": "pass", "criteria_results": [], "unknown_field": "bad"}
    errors = list(jsonschema.Draft202012Validator(res_schema).iter_errors(bad_result))
    assert len(errors) > 0, "Result schema should reject unknown fields"

    print("PASS: schema_strictness — additionalProperties: false rejects unknown fields")
    sys.exit(0)


if __name__ == "__main__":
    main()
