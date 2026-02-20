---
name: workspace
description: >
  Use when setting up Claude Code configuration on a new machine, bootstrapping
  the code-factory plugin marketplace, or troubleshooting configuration issues.
  Triggers: "setup workspace", "bootstrap claude", "configure claude code",
  "install plugins", "sync configuration", "update code-factory".
argument-hint: "[setup|update|status]"
user-invocable: true
---

# Workspace Setup

Announce: "I'm using the workspace skill to set up Claude Code configuration."

Bootstrap Claude Code with the code-factory plugin marketplace and personal configuration.

## Overview

This skill helps set up and manage a Claude Code development environment with:
- **Plugin marketplace** (productivity, git, code plugins)
- **MCP server configuration** (Atlassian, Datadog, Chrome DevTools)
- **Claude Code settings** (permissions, model preferences, enabled plugins)
- **OpenCode CLI configuration** (alternative CLI support)

## What Gets Configured

| Source File | Destination | Purpose |
|-------------|-------------|---------|
| `mcp.json` | `~/.mcp.json` | MCP server configuration (Atlassian, Datadog, Chrome DevTools) |
| `settings.json` | `~/.claude/settings.json` | Claude Code global settings (permissions, model, plugins) |
| `opencode.jsonc` | `~/.config/opencode/opencode.jsonc` | OpenCode CLI configuration |

## Step 1: Parse Mode

Check `$ARGUMENTS` to determine the operation:
- `setup` or empty: Full setup from scratch
- `update`: Pull latest changes and re-run bootstrap
- `status`: Check current configuration status

## Step 2: Setup Mode

### Prerequisites

Verify Claude Code is installed:

```bash
claude --version
```

If not installed, provide installation instructions:
```
Claude Code is not installed. Install it with:
  npm install -g @anthropic-ai/claude-code
```

### Clone Repository

If code-factory is not cloned:

```bash
# Clone to ~/dev/code-factory (recommended location)
mkdir -p ~/dev
cd ~/dev
git clone https://github.com/rtfpessoa/code-factory.git
cd code-factory
```

### Run Bootstrap Script

```bash
cd ~/dev/code-factory
./init.sh
```

The script will:
1. Create symlinks for configuration files
2. Skip files that already exist as regular files (with warning)
3. Re-create symlinks if they already exist (idempotent)

### Verify Installation

```bash
# Check symlinks
ls -la ~/.mcp.json ~/.claude/settings.json ~/.config/opencode/opencode.jsonc

# Verify Claude Code sees the plugins
claude --help
```

## Step 3: Update Mode

Pull latest changes and re-run bootstrap:

```bash
cd ~/dev/code-factory
git pull origin main
./init.sh
```

Changes are immediately available via symlinks.

## Step 4: Status Mode

Check current configuration status:

```bash
# Check if symlinks exist and point to correct locations
readlink ~/.mcp.json
readlink ~/.claude/settings.json
readlink ~/.config/opencode/opencode.jsonc

# Check code-factory version
cd ~/dev/code-factory && git log -1 --oneline
```

Report:
- Whether each config file is a symlink to code-factory
- Current code-factory commit
- Any files that are regular files instead of symlinks

## Available Plugins

After setup, these plugins are enabled:

| Plugin | Source | Skills |
|--------|--------|--------|
| `productivity@code-factory` | Local | `/do`, `/debug`, `/doc`, `/execplan`, `/reflect`, `/skill-workbench`, `/workspace` |
| `git@code-factory` | Local | `/commit`, `/atcommit`, `/pr`, `/branch`, `/worktree` |
| `code@code-factory` | Local | `/review`, `/tour` |
| `superpowers@claude-plugins-official` | GitHub | TDD, debugging, brainstorming |
| `dd@datadog-claude-plugins` | GitHub | Datadog-specific tools |

## MCP Servers

The configuration includes these MCP servers:

| Server | Status | Purpose |
|--------|--------|---------|
| `atlassian` | Enabled | Jira and Confluence access |
| `datadog` | Disabled | Datadog API access (enable if needed) |
| `chrome-devtools` | Available | Browser debugging |

To enable/disable servers, edit `settings.json`:
```json
{
  "enabledMcpjsonServers": ["atlassian"],
  "disabledMcpjsonServers": ["datadog"]
}
```

## Customization

### Local Settings Override

For machine-specific settings that shouldn't be synced, create:
```bash
# ~/.claude/settings.local.json (not symlinked, not committed)
{
  "model": "sonnet"
}
```

### Adding New Plugins

Edit `settings.json` to enable additional plugins:
```json
{
  "enabledPlugins": {
    "new-plugin@marketplace": true
  }
}
```

### Adding New Marketplaces

Edit `settings.json` to add plugin sources:
```json
{
  "extraKnownMarketplaces": {
    "my-marketplace": {
      "source": {
        "source": "github",
        "repo": "username/repo"
      }
    }
  }
}
```

## Useful Commands

| Command | Description |
|---------|-------------|
| `./init.sh` | Run bootstrap (idempotent) |
| `make all` | Run all checks and lint |
| `git pull && ./init.sh` | Update to latest |

## Error Handling

| Issue | Solution |
|-------|----------|
| Settings not applied | Restart Claude Code after running init.sh |
| File exists error | init.sh skips regular files; back up and remove, then re-run |
| Plugin not loading | Check `enabledPlugins` in settings.json |
| MCP server error | Check `enabledMcpjsonServers` and credentials |
| Permission denied | Ensure init.sh is executable: `chmod +x init.sh` |
| Symlink broken | Re-run `./init.sh` to recreate |

## Directory Structure

```
~/dev/code-factory/
  init.sh                  # Bootstrap script
  settings.json            # Claude Code settings -> ~/.claude/settings.json
  mcp.json                 # MCP config -> ~/.mcp.json
  opencode.jsonc           # OpenCode config -> ~/.config/opencode/opencode.jsonc
  productivity/            # Productivity plugin
    skills/
      debug/               # /debug skill
      do/                  # /do skill
      doc/                 # /doc skill
      execplan/            # /execplan skill
      reflect/             # /reflect skill
      skill-workbench/     # /skill-workbench skill
      workspace/           # /workspace skill (this file)
  git/                     # Git workflow plugin
    skills/
      atcommit/            # /atcommit skill
      branch/              # /branch skill
      commit/              # /commit skill
      pr/                  # /pr skill
      worktree/            # /worktree skill
  code/                    # Code understanding plugin
    skills/
      review/              # /review skill
      tour/                # /tour skill
```
