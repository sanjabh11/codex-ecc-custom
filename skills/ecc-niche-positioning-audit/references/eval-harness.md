# Evaluation Harness

OpenAI-eval-pattern test definitions for the ecc-niche-positioning-audit skill. Each scenario has a data source config, testing criteria, grader type, and pass threshold.

## Eval Framework

Pattern adapted from [OpenAI Evals](https://developers.openai.com/api/docs/guides/evals):

- **data_source_config**: JSON schema for test input
- **testing_criteria**: Grader that determines pass/fail
- **pass_threshold**: Minimum score for pass

## Eval Scenarios

### 1. Frontmatter Validation (deterministic)

```json
{
  "name": "frontmatter_validation",
  "data_source_config": {
    "type": "custom",
    "item_schema": {
      "type": "object",
      "properties": {
        "skill_file": {"type": "string"},
        "max_description_length": {"type": "integer"},
        "max_body_lines": {"type": "integer"}
      }
    }
  },
  "testing_criteria": [{
    "type": "python",
    "name": "frontmatter_checks",
    "pass_threshold": 1.0,
    "script": "validate_skill.py"
  }]
}
```
**Pass condition**: description ≤ 1024 chars, body ≤ 500 lines, all required sections present.

### 2. Scope DAG Path Validity (deterministic)

```json
{
  "name": "scope_dag_validity",
  "data_source_config": {
    "type": "custom",
    "item_schema": {
      "type": "object",
      "properties": {
        "scope": {"type": "string", "enum": ["quick", "standard", "deep"]},
        "expected_phases": {"type": "array", "items": {"type": "string"}}
      }
    }
  },
  "testing_criteria": [{
    "type": "string_check",
    "name": "scope_has_valid_path",
    "operation": "eq",
    "input": "{{scope_dag_result}}",
    "reference": "valid"
  }]
}
```
**Pass condition**: every scope has a valid start→terminal path in scope-dag.md.

### 3. Scoring Reproducibility (deterministic)

```json
{
  "name": "scoring_reproducibility",
  "data_source_config": {
    "type": "custom",
    "item_schema": {
      "type": "object",
      "properties": {
        "evidence_density": {"type": "number"},
        "adversarial_survival": {"type": "number"},
        "assumption_risk": {"type": "number"},
        "coverage_completeness": {"type": "number"},
        "triangulation_strength": {"type": "number"},
        "expected_composite": {"type": "number"}
      }
    }
  },
  "testing_criteria": [{
    "type": "string_check",
    "name": "composite_matches",
    "operation": "eq",
    "input": "{{computed_composite}}",
    "reference": "{{expected_composite}}"
  }]
}
```
**Pass condition**: composite = weighted average formula produces expected result.

### 4. Offline / Web-Unavailable (scenario)

```json
{
  "name": "offline_web_unavailable",
  "data_source_config": {
    "type": "custom",
    "item_schema": {
      "type": "object",
      "properties": {
        "web_search_available": {"type": "boolean"},
        "expected_outcome": {"type": "string"}
      }
    }
  },
  "testing_criteria": [{
    "type": "string_check",
    "name": "phase2_skip_on_no_web",
    "operation": "eq",
    "input": "{{actual_outcome}}",
    "reference": "skip_phase2_and_notify_user"
  }]
}
```
**Pass condition**: when web search is unavailable, Phase 2 is skipped and user is notified.

### 5. Unsupported Stack (scenario)

```json
{
  "name": "unsupported_stack",
  "data_source_config": {
    "type": "custom",
    "item_schema": {
      "type": "object",
      "properties": {
        "signal_files": {"type": "array", "items": {"type": "string"}},
        "expected_outcome": {"type": "string"}
      }
    }
  },
  "testing_criteria": [{
    "type": "string_check",
    "name": "ask_user_on_unknown_stack",
    "operation": "eq",
    "input": "{{actual_outcome}}",
    "reference": "ask_user_for_stack"
  }]
}
```
**Pass condition**: when no stack signal files match, skill asks user instead of crashing.

### 6. Missing Advisor (scenario)

```json
{
  "name": "missing_advisor",
  "data_source_config": {
    "type": "custom",
    "item_schema": {
      "type": "object",
      "properties": {
        "advisor_available": {"type": "boolean"},
        "expected_outcome": {"type": "string"}
      }
    }
  },
  "testing_criteria": [{
    "type": "string_check",
    "name": "skip_advisor_gracefully",
    "operation": "eq",
    "input": "{{actual_outcome}}",
    "reference": "documented_skip_proceed"
  }]
}
```
**Pass condition**: when ecc-advisor is unavailable, skill documents skip and proceeds.

### 7. Fewer Than Three Segments (scenario)

```json
{
  "name": "fewer_than_three_segments",
  "data_source_config": {
    "type": "custom",
    "item_schema": {
      "type": "object",
      "properties": {
        "viable_segments_found": {"type": "integer"},
        "expected_outcome": {"type": "string"}
      }
    }
  },
  "testing_criteria": [{
    "type": "string_check",
    "name": "insufficient_evidence_handling",
    "operation": "eq",
    "input": "{{actual_outcome}}",
    "reference": "insufficient_evidence_conditional_go"
  }]
}
```
**Pass condition**: when < 3 viable segments found, skill reports "insufficient evidence" with CONDITIONAL GO.

### 8. Resume / Corrupt State (scenario)

```json
{
  "name": "corrupt_state_recovery",
  "data_source_config": {
    "type": "custom",
    "item_schema": {
      "type": "object",
      "properties": {
        "state_json_valid": {"type": "boolean"},
        "expected_outcome": {"type": "string"}
      }
    }
  },
  "testing_criteria": [{
    "type": "string_check",
    "name": "fresh_start_on_corrupt",
    "operation": "eq",
    "input": "{{actual_outcome}}",
    "reference": "fresh_start_with_warning"
  }]
}
```
**Pass condition**: when state.json is corrupt, skill starts fresh with warning and archives corrupt state.

### 9. Privacy / Redaction (deterministic)

```json
{
  "name": "redaction_before_storage",
  "data_source_config": {
    "type": "custom",
    "item_schema": {
      "type": "object",
      "properties": {
        "input_text": {"type": "string"},
        "expected_redacted_patterns": {"type": "array", "items": {"type": "string"}}
      }
    }
  },
  "testing_criteria": [{
    "type": "string_check",
    "name": "no_secrets_in_output",
    "operation": "ne",
    "input": "{{redacted_output}}",
    "reference": "sk-.*|ghp_.*|xox.*|AKIA.*|eyJ.*"
  }]
}
```
**Pass condition**: no API keys, tokens, or PII patterns present in persisted output.

### 10. Artifact Schema Validation (deterministic)

```json
{
  "name": "artifact_schema_validation",
  "data_source_config": {
    "type": "custom",
    "item_schema": {
      "type": "object",
      "properties": {
        "artifact_json": {"type": "object"},
        "schema_path": {"type": "string"}
      }
    }
  },
  "testing_criteria": [{
    "type": "python",
    "name": "jsonschema_validation",
    "pass_threshold": 1.0,
    "script": "jsonschema.validate(artifact_json, schema)"
  }]
}
```
**Pass condition**: artifact JSON validates against artifact.schema.json.

## Pass Targets

| Eval | Type | Pass Target |
|------|------|-------------|
| frontmatter_validation | deterministic | 100% |
| scope_dag_validity | deterministic | 100% (all 3 scopes) |
| scoring_reproducibility | deterministic | 100% |
| offline_web_unavailable | scenario | pass@3 ≥ 90% |
| unsupported_stack | scenario | pass@3 ≥ 90% |
| missing_advisor | scenario | pass@3 ≥ 90% |
| fewer_than_three_segments | scenario | pass@3 ≥ 90% |
| corrupt_state_recovery | scenario | pass@3 ≥ 90% |
| redaction_before_storage | deterministic | 100% |
| artifact_schema_validation | deterministic | 100% |

**Release-critical regression checks** (frontmatter, scope DAG, scoring, redaction, artifact schema) must achieve pass^3 = 100% (3 consecutive runs all pass).
