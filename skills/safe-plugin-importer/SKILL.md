---
name: safe-plugin-importer
description: "Safely evaluate external Claude/ECC plugins or marketplace skills before adoption. Prefer rebuilding trusted ECC-native equivalents over blindly installing remote code."
origin: ECC
---

# Safe Plugin Importer

Use this skill whenever the user wants to borrow, import, install, or adapt an external plugin, marketplace skill, GitHub plugin repo, or shared agent workflow.

## Safety Principle

Do not blindly install marketplace plugins. Inspect, threat-model, compare with ECC, then rebuild the useful behavior as a compact ECC-native skill or workflow when possible.

## When to Activate

- User provides a plugin marketplace URL, GitHub repo, ZIP, or copied plugin bundle.
- User asks to "borrow", "import", "install", "add to ECC", or "copy this plugin".
- User asks whether a third-party plugin is safe, useful, or redundant.
- A plugin could introduce commands, hooks, MCP servers, global rules, credentials, or automation.

## Intake Workflow

1. Capture source and provenance:
   - URL, repo owner, commit/tag if available, license, maintainer signal.
   - Whether it is official, curated, community, or unknown.
2. Inventory contents without executing code:
   - Skills/prompts/rules.
   - Commands/hooks/scripts.
   - MCP servers/connectors.
   - Network, filesystem, credential, or destructive operations.
3. Threat model:
   - Secret exposure.
   - Destructive commands.
   - Background automation.
   - Supply-chain or dependency install risk.
   - Prompt injection and overbroad authority.
4. Compare with ECC:
   - Existing equivalent skill.
   - Gaps worth adopting.
   - Redundant or lower-quality content to skip.
5. Decide:
   - `reject`
   - `document only`
   - `adapt into existing skill`
   - `create new ECC skill`
   - `install only after explicit approval`
6. Verify:
   - Run manifest/skill validators.
   - Smoke the installed runtime cache when ECC plugin files change.
   - Report proof boundaries and remaining risk.

## Output Contract

```markdown
| Check | Result |
|---|---|
| Source/provenance | ... |
| Code execution risk | ... |
| Secret risk | ... |
| Destructive risk | ... |
| Existing ECC overlap | ... |
| Recommended action | reject / document / adapt / create / install-with-approval |
| Verification plan | ... |
```

## Usage Examples

```text
Use safe-plugin-importer on this Claude marketplace plugin before adding it to ECC.
Audit this GitHub plugin repo and rebuild only the useful parts as ECC skills.
Compare this plugin with our existing workflow-quality skills and tell me what to skip.
```

## Related Skills

- `workflow-audit-router` for deciding whether import is warranted.
- `connector-skill-composer` for packaging safe patterns into workflows.
- `security-review` and `security-scan` for higher-risk code.
- `skill-comply` and `skill-stocktake` for post-import quality checks.
