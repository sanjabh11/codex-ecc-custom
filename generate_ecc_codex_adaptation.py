#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


REPO_ROOT = Path("/tmp/everything-claude-code")
WORK_ROOT = Path("/Users/sanjayb/Documents/New project")
STAGING_ROOT = WORK_ROOT / "tmp" / "ecc_codex_adapt_staging"

AGENT_MODEL_MAP = {
    "opus": ("gpt-5.4", "high"),
    "sonnet": ("gpt-5.4", "medium"),
    "haiku": ("gpt-5.4-mini", "medium"),
}

AGENT_SANDBOX_MAP = {
    "docs-lookup": "read-only",
    "planner": "read-only",
    "architect": "read-only",
    "code-reviewer": "read-only",
    "security-reviewer": "read-only",
    "database-reviewer": "read-only",
    "harness-optimizer": "read-only",
    "healthcare-reviewer": "read-only",
    "performance-optimizer": "read-only",
}

COMMAND_BACKING_SKILLS = {
    "aside": ["iterative-retrieval", "strategic-compact"],
    "build-fix": ["verification-loop", "search-first"],
    "checkpoint": ["strategic-compact", "continuous-learning-v2"],
    "claw": ["nanoclaw-repl", "token-budget-advisor"],
    "code-review": ["security-review", "verification-loop", "coding-standards"],
    "context-budget": ["context-budget", "token-budget-advisor", "strategic-compact"],
    "cpp-build": ["cpp-coding-standards", "cpp-testing", "verification-loop"],
    "cpp-review": ["cpp-coding-standards", "security-review"],
    "cpp-test": ["cpp-testing", "tdd-workflow"],
    "devfleet": ["autonomous-loops", "dmux-workflows", "enterprise-agent-ops"],
    "docs": ["documentation-lookup", "search-first"],
    "e2e": ["e2e-testing", "browser-qa", "tdd-workflow"],
    "eval": ["eval-harness", "verification-loop"],
    "evolve": ["continuous-learning-v2", "skill-stocktake"],
    "fable-goal": ["ecc-fable-goal"],
    "fable-loop": ["autonomous-loops", "ecc-fable-loop"],
    "go-build": ["golang-patterns", "golang-testing", "verification-loop"],
    "go-review": ["golang-patterns", "security-review"],
    "go-test": ["golang-testing", "tdd-workflow"],
    "gradle-build": ["kotlin-patterns", "verification-loop"],
    "harness-audit": ["agent-harness-construction", "token-budget-advisor"],
    "instinct-export": ["continuous-learning-v2"],
    "instinct-import": ["continuous-learning-v2"],
    "instinct-status": ["continuous-learning-v2"],
    "kotlin-build": ["kotlin-patterns", "kotlin-testing", "verification-loop"],
    "kotlin-review": ["kotlin-patterns", "security-review"],
    "kotlin-test": ["kotlin-testing", "tdd-workflow"],
    "learn-eval": ["continuous-learning-v2", "skill-stocktake"],
    "learn": ["continuous-learning", "continuous-learning-v2"],
    "loop-start": ["autonomous-loops", "enterprise-agent-ops"],
    "loop-status": ["autonomous-loops", "enterprise-agent-ops"],
    "model-route": ["token-budget-advisor", "search-first"],
    "multi-backend": ["dmux-workflows", "autonomous-loops"],
    "multi-execute": ["dmux-workflows", "autonomous-loops"],
    "multi-frontend": ["dmux-workflows", "autonomous-loops"],
    "multi-plan": ["dmux-workflows", "autonomous-loops"],
    "multi-workflow": ["dmux-workflows", "autonomous-loops"],
    "orchestrate": ["dmux-workflows", "autonomous-loops"],
    "plan": ["api-design", "backend-patterns", "frontend-patterns", "search-first"],
    "pm2": ["enterprise-agent-ops", "deployment-patterns"],
    "projects": ["continuous-learning-v2"],
    "promote": ["continuous-learning-v2"],
    "prompt-optimize": ["prompt-optimizer"],
    "prune": ["continuous-learning-v2"],
    "python-review": ["python-patterns", "security-review"],
    "quality-gate": ["verification-loop", "security-review", "coding-standards"],
    "refactor-clean": ["repo-scan", "verification-loop", "coding-standards"],
    "resume-session": ["iterative-retrieval", "strategic-compact"],
    "rules-distill": ["rules-distill", "skill-stocktake"],
    "rust-build": ["rust-patterns", "rust-testing", "verification-loop"],
    "rust-review": ["rust-patterns", "security-review"],
    "rust-test": ["rust-testing", "tdd-workflow"],
    "save-session": ["iterative-retrieval", "strategic-compact"],
    "sessions": ["iterative-retrieval", "strategic-compact"],
    "advisor": ["ecc-advisor"],
    "setup-pm": ["configure-ecc", "agent-harness-construction"],
    "skill-create": ["skill-stocktake", "continuous-learning-v2"],
    "skill-health": ["skill-stocktake"],
    "tdd": ["tdd-workflow", "verification-loop", "coding-standards"],
    "test-coverage": ["verification-loop", "tdd-workflow"],
    "update-codemaps": ["repo-scan", "codebase-onboarding"],
    "update-docs": ["documentation-lookup", "codebase-onboarding"],
    "verify": ["verification-loop", "security-review", "eval-harness"],
}

INTEGRATION_INFO = {
    "GitHub MCP": {
        "required_for": ["repo inspection", "PR review", "ADR work", "repo-scan", "security-review"],
        "optional_for": ["deep research cross-checking", "skill-create validation"],
        "notes": "Configure via @modelcontextprotocol/server-github and set GITHUB_PERSONAL_ACCESS_TOKEN.",
    },
    "Context7 MCP": {
        "required_for": ["docs lookup", "API verification", "search-first"],
        "optional_for": ["framework planning", "refactoring with live docs"],
        "notes": "Configure via @upstash/context7-mcp@latest.",
    },
    "Exa MCP": {
        "required_for": ["broad research", "market/investor workflows", "many adapted commands"],
        "optional_for": ["generic planning or review when local context is sufficient"],
        "notes": "Configure EXA_API_KEY if you want the full research-oriented ECC surfaces.",
    },
    "Playwright MCP": {
        "required_for": ["e2e", "browser-qa", "e2e-runner"],
        "optional_for": ["codebase onboarding", "visual regression checks"],
        "notes": "Configured in upstream .mcp.json and .codex/config.toml.",
    },
    "Memory MCP": {
        "required_for": [],
        "optional_for": ["persistent memory", "long-running session continuity"],
        "notes": "Useful but not required for the baseline adaptation.",
    },
    "Sequential Thinking MCP": {
        "required_for": [],
        "optional_for": ["structured planning", "debugging", "deep analysis"],
        "notes": "Keep available for high-complexity work; not required for every flow.",
    },
    "Firecrawl MCP": {
        "required_for": [],
        "optional_for": ["deep-research", "exa-search"],
        "notes": "Improves crawl-heavy workflows when enabled.",
    },
    "AgentShield": {
        "required_for": [],
        "optional_for": ["security-scan", "plankton-code-quality"],
        "notes": "Install with npx ecc-agentshield or wire its GitHub Action for CI.",
    },
    "ccg-workflow": {
        "required_for": ["multi-plan", "multi-execute", "multi-backend", "multi-frontend", "multi-workflow"],
        "optional_for": [],
        "notes": "Initialize with npx ccg-workflow; without it, multi-* wrappers must stay guidance-only.",
    },
    "PM2": {
        "required_for": [],
        "optional_for": ["pm2", "enterprise-agent-ops", "long-running loop supervision"],
        "notes": "Needed only for process-management workflows.",
    },
    "DevFleet": {
        "required_for": [],
        "optional_for": ["parallel worktree orchestration"],
        "notes": "Use when you want the devfleet workflow available beyond tmux/dmux guidance.",
    },
    "VideoDB": {
        "required_for": [],
        "optional_for": ["videodb", "video-editing"],
        "notes": "Required for the media-editing branch of ECC.",
    },
    "fal.ai": {
        "required_for": [],
        "optional_for": ["fal-ai-media", "video-editing"],
        "notes": "Backs AI image/video/audio generation workflows.",
    },
    "Nutrient API": {
        "required_for": [],
        "optional_for": ["nutrient-document-processing"],
        "notes": "Commercial API; required only for document-processing flows.",
    },
    "X API": {
        "required_for": [],
        "optional_for": ["x-api", "crosspost", "content-engine", "some learning signals"],
        "notes": "Needed only for X/Twitter publishing and analysis flows.",
    },
    "ClickHouse MCP": {
        "required_for": [],
        "optional_for": ["clickhouse-io", "analytics-heavy operational skills"],
        "notes": "Enable when you need ClickHouse querying workflows.",
    },
    "Browserbase": {
        "required_for": [],
        "optional_for": ["cloud browser workflows beyond local Playwright"],
        "notes": "Optional advanced browser automation.",
    },
    "browser-use": {
        "required_for": [],
        "optional_for": ["browser agent tasks beyond local Playwright"],
        "notes": "Optional remote browser agent integration.",
    },
    "Omega Memory": {
        "required_for": [],
        "optional_for": ["semantic memory", "multi-agent coordination"],
        "notes": "Richer alternative to the basic memory server.",
    },
    "Skill Creator GitHub App": {
        "required_for": [],
        "optional_for": ["skill-create at large repo scale", "team sharing", "auto-PRs"],
        "notes": "Advanced replacement for the local git-history flow.",
    },
}

COMMAND_DEP_HINTS = {
    "Exa": "If Exa MCP is unavailable, fall back to local context and state explicitly that broad web research is unavailable.",
    "Context7": "If Context7 MCP is unavailable, answer from local knowledge and mark API/library details as potentially stale.",
    "playwright": "If Playwright MCP or local Playwright tooling is unavailable, stop at test design and explain what runtime is missing.",
    "ccg-workflow": "Without ccg-workflow, keep this as planning/guidance only and do not pretend the multi-runner is installed.",
    "codeagent-wrapper": "This upstream workflow expects the Claude-side wrapper; in Codex, use only the conceptual workflow unless a compatible wrapper is installed.",
    "ccg prompts": "These prompts are part of the ccg-workflow runtime; mention that requirement explicitly.",
    "pm2": "If PM2 is missing, explain the install step and stop at process-plan guidance.",
    "AgentShield": "If AgentShield is missing, explain the install command before offering the security-scan workflow.",
    "npx package": "This flow may rely on an external package; confirm the runtime/tool exists before execution.",
    "Codex CLI": "If Codex CLI orchestration helpers are unavailable, keep the workflow advisory and use the role guidance only.",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    fm = text[4:end]
    data: dict[str, str] = {}
    for line in fm.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def slugify(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return re.sub(r"-{2,}", "-", name)


def condense_agent_instructions(text: str) -> str:
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            body = text[end + 5 :]
    lines = [line.strip() for line in body.splitlines()]
    lines = [line for line in lines if line and not line.startswith("#")]
    sentences: list[str] = []
    for line in lines:
        if line.startswith("- "):
            line = line[2:]
        if line.startswith("1. ") or line.startswith("2. ") or line.startswith("3. "):
            line = line[3:]
        if len(line) < 24:
            continue
        if line not in sentences:
            sentences.append(line.rstrip("."))
        if len(sentences) >= 6:
            break
    return "\n".join(sentences) if sentences else "Follow the upstream ECC agent intent closely and stay within the assigned role."


def extract_command_dependencies(text: str) -> list[str]:
    deps: list[str] = []
    patterns = [
        (r"ccg-workflow", "ccg-workflow"),
        (r"codeagent-wrapper", "codeagent-wrapper"),
        (r"~/.claude/.ccg", "ccg prompts"),
        (r"\bpm2\b", "pm2"),
        (r"playwright", "playwright"),
        (r"AgentShield|agentshield", "AgentShield"),
        (r"context7", "Context7"),
        (r"\bexa\b", "Exa"),
        (r"codex exec", "Codex CLI"),
        (r"npx ", "npx package"),
    ]
    for pattern, label in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            deps.append(label)
    return deps


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def build_agent_roles() -> list[str]:
    roles: list[str] = []
    agent_dir = REPO_ROOT / "agents"
    out_dir = STAGING_ROOT / "codex-home" / "agents"
    manifest = []
    for md in sorted(agent_dir.glob("*.md")):
        text = read_text(md)
        fm = parse_frontmatter(text)
        role_name = slugify(fm.get("name", md.stem))
        roles.append(role_name)
        preferred_model = fm.get("model", "sonnet").lower()
        model, effort = AGENT_MODEL_MAP.get(preferred_model, ("gpt-5.4", "medium"))
        sandbox = AGENT_SANDBOX_MAP.get(role_name, "workspace-write")
        description = fm.get("description", "").strip()
        instructions = condense_agent_instructions(text)
        content = (
            f'model = "{model}"\n'
            f'model_reasoning_effort = "{effort}"\n'
            f'sandbox_mode = "{sandbox}"\n\n'
            'developer_instructions = """\n'
            f'{description}\n\n'
            f'{instructions}\n'
            'Stay within the role scope, cite concrete evidence when making claims, and call out missing integrations explicitly instead of assuming they exist.\n'
            '"""\n'
        )
        write(out_dir / f"{role_name}.toml", content)
        manifest.append({"name": role_name, "source": md.name, "model": model, "effort": effort, "sandbox": sandbox})
    write(STAGING_ROOT / "metadata" / "roles.json", json.dumps(manifest, indent=2))
    return roles


def build_command_skills() -> list[str]:
    commands_dir = REPO_ROOT / "commands"
    out_root = STAGING_ROOT / "codex-home" / "skills"
    command_names: list[str] = []
    manifest = []
    for md in sorted(commands_dir.glob("*.md")):
        text = read_text(md)
        fm = parse_frontmatter(text)
        command_name = md.stem
        command_names.append(command_name)
        skill_name = f"ecc-{command_name}"
        deps = extract_command_dependencies(text)
        backing = COMMAND_BACKING_SKILLS.get(command_name, ["search-first"])
        dep_lines = "\n".join(f"- `{dep}`: {COMMAND_DEP_HINTS.get(dep, 'Check that this dependency is installed before attempting the advanced path.')}" for dep in deps) or "- None for the baseline guidance path."
        backing_lines = "\n".join(f"- `{item}`" for item in backing)
        description = fm.get("description") or f"Codex adaptation of ECC /{command_name}."
        body = f"""---
name: {skill_name}
description: Codex adaptation of ECC `/{command_name}`. {description}
---

# {skill_name}

Use this skill when the user is asking for the ECC `/{command_name}` workflow inside Codex.

## Purpose

This skill adapts the upstream Claude-oriented command into a Codex-usable workflow. It should preserve the intent of `/{command_name}` while staying honest about missing integrations or runtime dependencies.

## Backing Skills

{backing_lines}

## Workflow

1. Restate the user's goal in the language of the `/{command_name}` workflow.
2. Check whether the required local context, tools, and integrations are present before taking the advanced path.
3. If the advanced path is available, execute the workflow using Codex-native tools, generated roles, and the backing skills above.
4. If the advanced path is not available, provide the highest-fidelity guidance path available and state exactly what is missing.
5. Never claim Claude-only slash-command, hooks, or wrapper behavior exists inside Codex when it does not.

## Dependency Gating

{dep_lines}

## Upstream Source

- Command file: `{md.name}`
- Original description: {description}
"""
        write(out_root / skill_name / "SKILL.md", body)
        manifest.append({"skill": skill_name, "command": command_name, "dependencies": deps, "backing_skills": backing})
    write(STAGING_ROOT / "metadata" / "commands.json", json.dumps(manifest, indent=2))
    return command_names


def build_catalog_skills(role_names: list[str], command_names: list[str]) -> None:
    skills_root = STAGING_ROOT / "codex-home" / "skills"
    role_lines = "\n".join(f"- `{name}`" for name in role_names)
    cmd_lines = "\n".join(f"- `ecc-{name}` for `/{name}`" for name in command_names)
    write(
        skills_root / "ecc-role-catalog" / "SKILL.md",
        f"""---
name: ecc-role-catalog
description: Catalog of the adapted ECC Codex role wrappers and when to use them.
---

# ecc-role-catalog

Use this skill when the user wants to know which adapted ECC roles are available in Codex or which role should handle a task.

## Available Roles

{role_lines}

## Selection Rule

Pick the narrowest role that matches the task. If no specialized role fits, fall back to the general Codex workflow and cite the nearest matching ECC role as guidance.
""",
    )
    write(
        skills_root / "ecc-command-catalog" / "SKILL.md",
        f"""---
name: ecc-command-catalog
description: Catalog of Codex-adapted ECC command-equivalent skills and the upstream command each one maps to.
---

# ecc-command-catalog

Use this skill when the user asks what ECC command-equivalent workflows are available in Codex.

## Available Command Adaptations

{cmd_lines}

## Important Constraint

These are Codex skill adaptations of upstream Claude commands. They are not literal slash commands and should never be presented as Claude command UI inside Codex.
""",
    )


def build_integrations_catalog() -> None:
    parts = []
    for name, info in INTEGRATION_INFO.items():
        req = ", ".join(info["required_for"]) if info["required_for"] else "None"
        opt = ", ".join(info["optional_for"]) if info["optional_for"] else "None"
        parts.append(
            f"## {name}\n\n"
            f"- Required for: {req}\n"
            f"- Optional for: {opt}\n"
            f"- Notes: {info['notes']}\n"
        )
    write(
        STAGING_ROOT / "codex-home" / "skills" / "ecc-integrations-catalog" / "SKILL.md",
        f"""---
name: ecc-integrations-catalog
description: Inventory of ECC integrations, MCP servers, external runtimes, and service dependencies for the Codex adaptation layer.
---

# ecc-integrations-catalog

Use this skill when the user asks which integrations are required, optional, or unavailable for the ECC Codex adaptation layer.

{''.join(parts)}
""",
    )


def build_home_agents_md() -> None:
    base = Path("/Users/sanjayb/.codex/AGENTS.md")
    existing = read_text(base) if base.exists() else "# AGENTS.md\n"
    supplement = """

## ECC Codex Adaptation Layer
- Home-local ECC plugin root: `~/plugins/everything-claude-code`
- Marketplace file: `~/.agents/plugins/marketplace.json`
- Adapted Codex roles live in `~/.codex/agents/`
- Adapted command-equivalent skills live in `~/.codex/skills/` as `ecc-*`
- Use the upstream root `skills/` catalog as the canonical ECC skill source.
- Treat Claude-only hooks and rules as guidance material, not executable Codex features.
- If an ECC workflow depends on an integration such as Exa, Context7, Playwright, AgentShield, ccg-workflow, PM2, VideoDB, fal.ai, Nutrient, or X API, check availability first and state the missing dependency explicitly.
""".rstrip()
    if "## ECC Codex Adaptation Layer" not in existing:
        merged = existing.rstrip() + "\n" + supplement + "\n"
    else:
        merged = existing
    write(STAGING_ROOT / "codex-home" / "AGENTS.md", merged)


def build_home_config(role_names: list[str]) -> None:
    existing = read_text(Path("/Users/sanjayb/.codex/config.toml"))
    lines = [existing.rstrip(), "", '# ECC Codex adaptation layer']
    if "approval_policy" not in existing:
        lines.append('approval_policy = "on-request"')
    if "sandbox_mode" not in existing:
        lines.append('sandbox_mode = "workspace-write"')
    if "web_search" not in existing:
        lines.append('web_search = "live"')
    if "[features]" not in existing:
        lines.extend(["", "[features]", "multi_agent = true"])
    elif "multi_agent" not in existing:
        lines.append("multi_agent = true")
    if "[mcp_servers.github]" not in existing:
        lines.extend(["", "[mcp_servers.github]", 'command = "npx"', 'args = ["-y", "@modelcontextprotocol/server-github"]'])
    if "[mcp_servers.context7]" not in existing:
        lines.extend(["", "[mcp_servers.context7]", 'command = "npx"', 'args = ["-y", "@upstash/context7-mcp@latest"]'])
    if "[mcp_servers.exa]" not in existing:
        lines.extend(["", "[mcp_servers.exa]", 'url = "https://mcp.exa.ai/mcp"'])
    if "[mcp_servers.memory]" not in existing:
        lines.extend(["", "[mcp_servers.memory]", 'command = "npx"', 'args = ["-y", "@modelcontextprotocol/server-memory"]'])
    if "[mcp_servers.sequential-thinking]" not in existing:
        lines.extend(["", "[mcp_servers.sequential-thinking]", 'command = "npx"', 'args = ["-y", "@modelcontextprotocol/server-sequential-thinking"]'])
    if "[agents]" not in existing:
        lines.extend(["", "[agents]", "max_threads = 12", "max_depth = 1"])
    role_block = []
    for role in role_names:
        section = f"[agents.{role.replace('-', '_')}]"
        if section in existing:
            continue
        role_block.extend([
            "",
            section,
            f'description = "ECC adapted role: {role}"',
            f'config_file = "agents/{role}.toml"',
        ])
    lines.extend(role_block)
    write(STAGING_ROOT / "codex-home" / "config.toml", "\n".join(lines) + "\n")


def build_marketplace_json() -> None:
    data = {
        "name": "local-codex-marketplace",
        "interface": {"displayName": "Local Codex Marketplace"},
        "plugins": [
            {
                "name": "everything-claude-code",
                "source": {"source": "local", "path": "./plugins/everything-claude-code"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity",
            }
        ],
    }
    write(STAGING_ROOT / "agents-home" / "plugins" / "marketplace.json", json.dumps(data, indent=2))


def main() -> None:
    if STAGING_ROOT.exists():
        shutil.rmtree(STAGING_ROOT)
    role_names = build_agent_roles()
    command_names = build_command_skills()
    build_catalog_skills(role_names, command_names)
    build_integrations_catalog()
    build_home_agents_md()
    build_home_config(role_names)
    build_marketplace_json()


if __name__ == "__main__":
    main()
