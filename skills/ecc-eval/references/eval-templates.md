# Eval Templates

## Capability Eval Template

```markdown
[CAPABILITY EVAL: <feature-name>]
Task: <description of what the agent should accomplish>
Success Criteria:
  - [ ] Criterion 1
  - [ ] Criterion 2
  - [ ] Criterion 3
Expected Output: <description of expected result>
Grader: code | model | human
```

## Regression Eval Template

```markdown
[REGRESSION EVAL: <feature-name>]
Baseline: <SHA or checkpoint name>
Tests:
  - <existing-test-1>: PASS/FAIL
  - <existing-test-2>: PASS/FAIL
  - <existing-test-3>: PASS/FAIL
Result: X/Y passed (previously Y/Y)
Grader: code
```

## Model-Grader Eval Template

```markdown
[MODEL GRADER PROMPT]
Evaluate the following output:
1. Does it solve the stated problem?
2. Is it well-structured?
3. Are edge cases handled?
4. Is error handling appropriate?

Score: 1-5 (1=poor, 5=excellent)
Reasoning: [explanation]

Output to evaluate:
---
<output content here>
---
```

## Skill Validation Eval Template

```markdown
[SKILL VALIDATION EVAL: <skill-name>]
Task: Validate this skill for completeness, portability, and correctness
Success Criteria:
  - [ ] SKILL.md has valid frontmatter (name, description, triggers)
  - [ ] SKILL.md has required sections (When to Use, How It Works, Dependency Gating)
  - [ ] agents/openai.yaml exists for Codex
  - [ ] .claude-plugin/plugin.json exists
  - [ ] scripts/ directory has at least one script
  - [ ] No hardcoded paths to $HOME
  - [ ] Platform compatibility section mentions all 4 IDEs
  - [ ] No $(git root) anti-pattern
Expected Output: JSON with pass/fail per criterion and overall status
Grader: model
```

## Prompt A/B Test Template

```markdown
[PROMPT A/B TEST: <test-name>]
Prompt: <the prompt text>
Models:
  - Model A: <model-1>
  - Model B: <model-2>
Success Criteria:
  - [ ] Both models produce valid output
  - [ ] Output diff is meaningful (not just whitespace)
  - [ ] At least one model meets the quality bar
Expected Output: Two response files for comparison
Grader: human | model
```

## MCP Config Audit Template

```markdown
[MCP AUDIT EVAL: mcp-config]
Task: Audit MCP server configuration for issues
Success Criteria:
  - [ ] No servers are unexpectedly disabled
  - [ ] No servers have missing required fields
  - [ ] No servers have security issues (exposed keys, overly permissive settings)
  - [ ] All enabled servers have valid command paths
Expected Output: JSON with per-server status and issues list
Grader: model
```
