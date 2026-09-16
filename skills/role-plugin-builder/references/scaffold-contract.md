# Role Plugin Scaffold Contract

Use this contract before generating or modifying a Codex plugin from a role or workflow brief.

## Contract Template

| Field | Value |
|---|---|
| Role or workflow |  |
| Plugin name |  |
| Target audience |  |
| Primary outcome |  |
| Scope boundary |  |
| Customization type | `wrapper` / `narrow skill` / `bundle` / `full plugin` |
| Source inspiration |  |
| Attribution needed | `yes` / `no` |

## Workflow Package

| Workflow | Trigger phrases | Inputs | Outputs | Verification |
|---|---|---|---|---|
|  |  |  |  |  |

## Skill Stack

| Skill | Required? | Use | Evidence |
|---|---|---|---|
| workflow-audit-router | yes | route the request and proof plan | installed ECC skill or fallback noted |
| plugin-customizer | yes | choose alias, wrapper, narrow skill, bundle, or plugin | installed ECC skill or fallback noted |
| connector-skill-composer | conditional | compose verified tools/connectors | only when connectors are part of the role |
| department-plugin-bundles | conditional | package department-style bundles | only for department or role-family bundles |
| safe-plugin-importer | conditional | inspect external templates before adaptation | only for external sources |
| plugin-creator | conditional | generate the filesystem scaffold | only when files should be created |

## Connector Truth Table

Allowed statuses:

- `installed`: plugin or dependency exists in this Codex session.
- `exposed`: callable tools are visible to the current agent.
- `healthy`: a non-mutating smoke check succeeded.
- `planned`: useful but not currently callable or not yet configured.
- `unavailable`: missing or unsuitable for this scaffold.

| Surface | Status | Evidence | Scaffold decision |
|---|---|---|---|
|  |  |  | include / planned / omit |

Rules:

- Include `.app.json` only for verified app surfaces.
- Include `.mcp.json` only for verified or explicitly planned MCP servers.
- Do not claim health from documentation, templates, or memory alone.
- Never put secrets, tokens, placeholder IDs, or personal absolute paths in generated plugin files.

## Proposed Plugin Files

| Path | Include? | Purpose | Validation |
|---|---|---|---|
| `.codex-plugin/plugin.json` | yes | required plugin manifest | `validate_plugin.py` |
| `skills/<skill-name>/SKILL.md` | usually | role workflow instructions | `quick_validate.py` if extracted as standalone skill |
| `assets/` | optional | templates or examples copied into output | file existence and source attribution |
| `.app.json` | conditional | app connector metadata | connector truth table |
| `.mcp.json` | conditional | MCP server config | connector truth table and no secrets |
| `scripts/` | avoid by default | deterministic helpers only when needed | targeted smoke test |
| `hooks/` | avoid by default | only after explicit approval | manual review and stop gate |

## Scaffold Commands

Use the existing plugin creator instead of writing new scaffolding scripts:

```bash
cd /Users/sanjayb/.codex/skills/.system/plugin-creator
python3 scripts/create_basic_plugin.py <plugin-name> --with-skills --with-assets
python3 scripts/validate_plugin.py <plugin-path>
```

Add optional flags only when justified:

- `--with-apps`: app connector file is verified and needed.
- `--with-mcp`: MCP config is verified or explicitly planned.
- `--with-marketplace`: user explicitly wants personal marketplace listing.
- `--with-scripts`: deterministic helper is needed and has a smoke test.

## Adversarial Checklist

| Risk | Required handling |
|---|---|
| Overbroad role | narrow to one role, department, or workflow family |
| Fake connector availability | mark as `planned` or `unavailable` until verified |
| External template copying | adapt behavior and preserve attribution |
| Secret exposure | reject files containing credentials or token-shaped values |
| Unsafe hooks or automation | stop for explicit approval |
| Duplicate ECC behavior | prefer alias or wrapper over new plugin |
| Plugin cache mutation | avoid in v1 unless user explicitly requests ECC release packaging |

## Final Handoff

Return:

- plugin name and path
- completed connector truth table
- included files and omitted files
- validation commands run
- proof boundaries
- next packaging step, if any
