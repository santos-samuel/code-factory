# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project Overview

Claude Code and OpenCode plugin marketplace. Two plugins — **productivity** and **git** — each containing skills and optionally agents. Tech stack: Markdown skill definitions, JSON configs, Makefile, shell scripts.

## Repository Structure

```
.claude-plugin/marketplace.json   # Marketplace manifest (version, plugin list)
{plugin}/                         # One directory per plugin
  .claude-plugin/plugin.json      #   Plugin manifest
  agents/                         #   Agent definitions (optional)
    {name}.md
  skills/                         #   Skill definitions
    {name}/SKILL.md
Makefile                          # all, check, lint, and install targets
init.sh                           # Bootstrap script
sync-opencode.sh                  # Regenerates .opencode/ from plugin sources
hooks/                            # Claude Code hook scripts linked by init.sh
.githooks/                        # Git hooks linked into .git/hooks by init.sh
.opencode/                        # Generated OpenCode assets (do not edit directly)
settings.json                     # Claude Code global settings
mcp.json                          # MCP server configuration
opencode.jsonc                    # OpenCode CLI configuration
```

Discover available skills and agents by browsing the plugin directories. Each `SKILL.md` and agent `.md` file is self-describing — read it for purpose, usage, and behavior.

## Conventions

### Skill Frontmatter

Required fields for every `SKILL.md`:

| Field | Format | Example |
|-------|--------|---------|
| `name` | kebab-case | `commit`, `skill-workbench` |
| `description` | Starts with "Use when" | `Use when the user wants to...` |
| `argument-hint` | Bracketed placeholder | `[optional PR title]` |
| `user-invocable` | `true` or `false` | `true` |

Optional fields:

| Field | Purpose | Example |
|-------|---------|---------|
| `allowed-tools` | Restrict tool access (kebab-case) | `Bash(git:*), Read, Grep, Glob` |
| `disable-model-invocation` | Prevent auto-invocation by model (skill only runs when user explicitly invokes it) | `true` |

### Skill Structure

Every skill follows this structure:

1. **Announce line**: First line after the heading — a quoted string the agent says when starting.
2. **Numbered Steps**: `## Step N: Title` sections with clear actions.
3. **Error Handling**: Final section covering failure modes as a table or bullet list.

### Agent Frontmatter

Required fields for agent definitions in `agents/*.md`:

| Field | Format |
|-------|--------|
| `name` | kebab-case |
| `description` | Free text |

Optional: `model`, `allowed_tools` (note: **snake_case** in agents, **kebab-case** in skills).

### Cross-References

Skills reference each other with backtick-quoted slash patterns: `` `/commit` ``, `` `/branch` ``. The `make check-refs` target validates these resolve to real skill directories.

## Workflow

Every change must follow these four steps in order.

### 1. Plan

Plan before implementing. Describe:

- The approach and rationale.
- Which files will be created, modified, or deleted.
- Acceptance criteria for the change.

Do not write code until the plan is complete.

### 2. Implement

- Execute the plan step-by-step.
- Keep changes minimal and aligned with existing conventions.
- One logical change per commit.

### 3. Validate

Run after every implementation:

```bash
make all
```

- `make check` verifies skill frontmatter, agent frontmatter, skill cross-references, agent skill references, description conventions, skill structure, plugin manifest references, and OpenCode sync freshness.
- `make lint` validates all JSON and JSONC files.

All checks must pass before proceeding.

### 4. Update Documentation and Metadata

If changes affect functionality, configuration, or behavior:

- Update relevant Markdown docs (`README.md`, skill `SKILL.md` files).
- Update metadata files:
  - `plugin.json` in the affected plugin's `.claude-plugin/` directory.
  - `.claude-plugin/marketplace.json` if plugins are added or removed.
- Bump version numbers following [semantic versioning](https://semver.org/):
  - **patch** — bug fixes, typo corrections.
  - **minor** — new skills, new features, backward-compatible changes.
  - **major** — breaking changes to skill interfaces or plugin structure.

## Boundaries

**Always do:**

- Run `make all` before considering work complete.
- Plan before implementing.
- Follow existing file and directory naming patterns.
- Keep skill definitions self-contained in their `SKILL.md` files.

**Ask first:**

- Adding new plugins to the marketplace.
- Changing `settings.json`, `mcp.json`, or `opencode.jsonc`.
- Modifying agent definitions in `agents/`.

**Never do:**

- Commit secrets, tokens, or credentials.
- Force-push to `main`.
- Delete existing skills or plugins without explicit approval.
- Skip validation (`make all`).
- Modify files in `~/.claude/plugins/cache/`. This directory is a read-only deployment artifact managed by Claude Code's plugin system. Always make changes in the source repo — they propagate to the cache on the next plugin update.
- Edit files in `.opencode/` directly. This directory is generated by `sync-opencode.sh` (run via `make all`). Always edit the source files in `{plugin}/skills/` and `{plugin}/agents/` — changes propagate to `.opencode/` automatically.
