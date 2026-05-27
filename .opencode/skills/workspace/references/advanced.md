# Advanced Workspace Configuration

## Instance Types

| Instance | vCPUs | RAM | Storage | Arch | Region |
|----------|-------|-----|---------|------|--------|
| `aws:m5d.4xlarge` | 16 | 64 GB | 600 GB NVMe | x86_64 | All |
| `aws:m6gd.4xlarge` | 16 | 64 GB | 950 GB NVMe | ARM Graviton2 | All |
| `aws:g5.2xlarge` | 8 | 32 GB + GPU | 450 GB NVMe | x86_64 + NVIDIA A10G | us-east-1 only |

## Persistent Configuration

Save defaults in `~/.config/datadog/workspaces/config.yaml`:

```yaml
shell: fish
region: eu-west-3
dotfiles: https://github.com/rtfpessoa/dotfiles
vscode-extensions:
  - "bazelbuild.vscode-bazel"
```

## Required Secrets

These secrets MUST be registered and exported BEFORE workspace creation.
Secrets only propagate to future workspaces -- if forgotten, the workspace must be recreated.

| Secret | Required? | Purpose |
|--------|-----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Claude Code API access on workspace |
| `OPENAI_API_KEY` | Yes | Codex API access on workspace |

### Validation

```bash
wmux validate-workspace-config
```

This checks all required secrets are present and exported. Run before every `workspaces create`.

### Registration

```bash
workspaces secrets set ANTHROPIC_API_KEY=<key> --export
workspaces secrets set OPENAI_API_KEY=<key> --export
```

The `--export` flag makes the secret available as an environment variable on the workspace.
Without `--export`, the secret is stored as a file at `/run/user/$(id -u bits)/secrets/<key>` but not exported to the shell environment.

### Verification

After registration:

```bash
workspaces secrets list    # Confirm secrets are listed
wmux validate-workspace-config    # Confirm validation passes
```

## Secrets Management

```bash
workspaces secrets set KEY=VALUE            # Register secret (future workspaces only)
workspaces secrets set KEY=VALUE --export   # Set as env var (not just file)
workspaces secrets list                     # List registered secrets
workspaces secrets get KEY                  # View metadata (not value)
workspaces secrets remove KEY               # Unregister
```

Secrets land in workspace at: `/run/user/$(id -u bits)/secrets/<key>`.

Secrets only propagate to **future** workspaces, not existing ones. To inject into an existing workspace, recreate it.

Disallowed secret names: `PATH`, `ENV`, `USER`, `SHELL`, `HOME`.

## Claude Code in Workspaces

Claude Code is pre-installed in workspaces. The `ANTHROPIC_API_KEY` workspace secret provides API access automatically.

If the secret was not registered before creation:

1. Delete the workspace: `workspaces delete <name>`
2. Register the secret: `workspaces secrets set ANTHROPIC_API_KEY=<key> --export`
3. Recreate the workspace

## wmux Configuration

wmux stores its configuration at `~/.config/wmux/config.json` (version 2).
This file defines which auth checks wmux evaluates on the workspace.

Default auth checks include:
- GitHub CLI (`auth.gh`, `auth.gh_signing`)
- Codex and Claude base login (`auth.codex`, `auth.claude`)
- ddtool datacenters (`us1.ddbuild.io`, `us1.staging.dog`)
- MCP servers (`mcp.*`, `claude-mcp.*`)
- Environment secrets (`env.openai_api_key`, `env.anthropic_api_key`)

Manage auth from the CLI:

```bash
wmux auth status --workspace <name>              # Full auth report
wmux auth status --workspace <name> --pending    # Only actionable items
wmux auth open --workspace <name> --check <id>   # Resolve a specific check
wmux auth doctor --workspace <name>              # Detailed diagnostics
```

## Workspace Lifecycle

| Event | Timing |
|-------|--------|
| Garbage collection | After 20 days of SSH inactivity |
| Hard TTL | 6 months regardless of activity |
| Notifications | Slack SDM Bot at 14, 7, 1 day(s) before deletion |

SSHing in (directly or via IDE) resets the 20-day inactivity clock.

## Devcontainer

Default: `.devcontainer/datadog/default/devcontainer.json` in the repo.

Override with `--devcontainer-config <path>` flag on create.

Pre-built images available for: `dd-source`, `dd-go`, `logs-backend`, `driveline`.

## Regions

| Region | Location |
|--------|----------|
| `us-east-1` | N. Virginia, USA |
| `eu-west-3` | Paris, France |

Choose the region closest to your physical location.

## Additional Create Flags

| Flag | Purpose |
|------|---------|
| `--open-editor` | Open editor immediately after creation |
| `--editor` | `vscode`, `cursor`, `intellij`, `pycharm`, `goland` |
| `--vscode-extensions` | Comma-delimited extension IDs |
| `--jetbrains-plugins` | Comma-delimited plugin IDs |
| `--vscode-template` | Path to a `.code-workspace` template file |
| `--devcontainer-config` | Path to a `devcontainer.json` |
| `--instance-type` | Override instance type |

## Updating Tools Inside Workspace

```bash
update-tool <name>    # NOT brew — use the workspace tool manager
```

## Workspaces API (gRPC)

For programmatic access:

| Endpoint | URL |
|----------|-----|
| Staging | `workspaces-api.us1.ddbuild.staging.dog:443` |
| Production | `workspaces-api.us1.ddbuild.io:443` |

Auth: `ddtool auth token --datacenter <datacenter> rapid-devex-workspaces`

Key RPCs on `workspaces_api.WorkspacesAPI`: `ListWorkspaces`, `CreateWorkspace`, `DeleteWorkspace`, `GetWorkspace`, `StreamWorkflowStatus`, `AgentRun`.

Proto source: `domains/devex/workspaces/apps/apis/workspaces-api/workspaces-api-pb/workspaces_api.proto` in `dd-source`.

## Support

- Slack: [#workspaces](https://dd.enterprise.slack.com/archives/C02PW2547B9)
- Confluence: "Workspaces (official)" in DEVX space
