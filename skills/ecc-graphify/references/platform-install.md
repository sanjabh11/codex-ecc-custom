# Platform Installation and Symlink Management

## ECC Wrapper vs Native Install

The ECC `ecc-graphify` skill wraps the graphify CLI. It does NOT use graphify's native `graphify install` command. Instead, it follows the ECC symlink pattern:

1. **Canonical source:** `/Users/sanjayb/codex-ecc-custom/skills/ecc-graphify/`
2. **Symlinked to:** Five physical discovery paths (not five proven host integrations)
3. **CLI dependency:** `~/.local/bin/graphify` (installed via `uv tool install graphifyy`)

This approach ensures:
- Single source of truth (the repo)
- No drift between platforms
- Easy updates (edit once, all platforms see the change)
- Clean uninstall (remove symlinks, not copies)

## Install to All Platforms

```bash
bash /Users/sanjayb/codex-ecc-custom/skills/ecc-graphify/scripts/graphify-platform-install.sh
```

An unexpected existing symlink is never replaced automatically. Review it and
rerun with `--force` only when replacement is intentional:

```bash
bash /Users/sanjayb/codex-ecc-custom/skills/ecc-graphify/scripts/graphify-platform-install.sh --force
```

This creates symlinks in:

| Platform | Symlink Path | Notes |
|----------|-------------|-------|
| Windsurf | `~/.codeium/windsurf/skills/ecc-graphify` | Canonical source location |
| Claude Code | `~/.claude/skills/ecc-graphify` | Symlink to windsurf |
| Generic Agents | `~/.agents/skills/ecc-graphify` | Agent-Skills spec location |
| Devin | `~/.devin/skills/ecc-graphify` | Devin CLI global skills |
| Codex | `~/.codex/skills/ecc-graphify` | Codex global skills |

## Uninstall from All Platforms

```bash
bash /Users/sanjayb/codex-ecc-custom/skills/ecc-graphify/scripts/graphify-platform-install.sh --uninstall
```

This removes only symlinks that point to this canonical skill. Unexpected
symlinks and real directories are preserved unless `--force` is explicitly
provided. Real directories are never removed by the normal path.

## Native Graphify Install (Alternative)

If you prefer graphify's native installer instead of the ECC wrapper:

```bash
# Claude Code (macOS/Linux)
graphify install

# Codex
graphify install --platform codex

# Devin
graphify devin install

# Antigravity
graphify antigravity install

# Generic Agent-Skills
graphify install --platform agents
```

**Warning:** Native install creates separate copies that drift from the repo. The ECC symlink approach is preferred for this environment.

## Platform-Specific Notes

The following notes describe Graphify's **native installer**, not the ECC
wrapper. The wrapper only installs the shared skill symlink; it does not create
host hooks or always-on files.

### Claude Code

- **Skill file:** `skill.md` (progressive disclosure with references/)
- **Always-on:** Appends a section to `~/.claude/CLAUDE.md`
- **Hooks:** PreToolUse hook for graph-first queries
- **Parallel:** Uses Claude subagents for multimodal extraction

### Codex

- **Skill file:** `skill-codex.md` (Codex-specific format)
- **Always-on:** Appends a section to `AGENTS.md`
- **Hooks:** PreToolUse hook in `.codex/hooks.json`
- **Parallel:** Requires `multi_agent = true` in `~/.codex/config.toml`
- **Config check:**
  ```bash
  grep -q "multi_agent = true" ~/.codex/config.toml && echo "PARALLEL_OK" || echo "NEEDS_CONFIG"
  ```

### Devin

- **Skill file:** `skill-devin.md` (monolith — full skill inline, no references/ sidecar)
- **Always-on:** `.windsurf/rules/graphify.md` (Devin reads Windsurf-format rules)
- **Hooks:** None
- **Parallel:** Uses Devin subagents

### Antigravity

- **Skill file:** `skill.md` (rides claude's bundle)
- **Always-on:** `.agents/rules/graphify.md` + `.agents/workflows/graphify.md`
- **Hooks:** None
- **YAML frontmatter:** Injected for native Antigravity tool discovery
- **MCP:** Add to `~/.gemini/antigravity/mcp_config.json` for full architecture navigation

### Windsurf

- **Skill file:** `skill.md` (same as Claude Code)
- **Always-on:** Windsurf rules
- **Hooks:** None
- **Parallel:** Uses Windsurf's agent system

## Graphify CLI Installation

The graphify CLI itself is installed separately from the skill:

```bash
# Recommended (uv)
uv tool install graphifyy

# Alternative (pipx)
pipx install graphifyy

# Alternative (pip)
pip install graphifyy
```

**Note:** The PyPI package is `graphifyy` (double y) while the CLI command is `graphify`. This is temporary while the `graphify` name is being reclaimed on PyPI.

### Verify Installation

```bash
bash /Users/sanjayb/codex-ecc-custom/skills/ecc-graphify/scripts/graphify-health.sh
```

### Update Graphify

```bash
uv tool install --upgrade graphifyy
# or
pipx upgrade graphifyy
```

### Uninstall Graphify CLI

```bash
uv tool uninstall graphifyy
# or
pipx uninstall graphifyy
```
