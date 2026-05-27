---
name: "workspace"
description: "Use when the user wants to manage Datadog workspaces (remote cloud development environments): create, list, delete, SSH, connect IDE, or validate setup. Also use when the `/do` skill needs a remote workspace instead of a local worktree. Triggers: \"workspace\", \"create workspace\", \"list workspaces\", \"delete workspace\", \"ssh workspace\", \"datadog workspace\", \"remote dev environment\", \"connect workspace\"."
---

# Datadog Workspace Manager

Announce: "I'm using the workspace skill to manage Datadog workspaces."

Manage remote cloud development environments (CDEs) via the `workspaces` CLI and `wmux` auth system.
Workspaces are dev containers running on dedicated EC2 instances with pre-configured tools and repo access.

## Step 1: Parse Mode

Parse `$ARGUMENTS` to determine the operation:

| Argument prefix | Mode |
|----------------|------|
| `create <name>` | Create a new workspace |
| `list` | List existing workspaces |
| `delete <name>` | Delete a workspace |
| `ssh <name>` | SSH into a workspace |
| `connect <name>` | Connect IDE to a workspace |
| `validate` | Validate prerequisites and setup |
| No arguments | Ask user which operation |

If no arguments:

```
AskUserQuestion(
  header: "Workspace operation",
  question: "What would you like to do?",
  options: [
    "Create" -- Create a new Datadog workspace,
    "List" -- List existing workspaces,
    "Delete" -- Delete a workspace,
    "SSH" -- SSH into a workspace,
    "Connect" -- Connect IDE to a workspace,
    "Validate" -- Check prerequisites and setup
  ]
)
```

## Step 2: Validate Prerequisites

Run before `create`, `ssh`, or `validate` modes. Skip for `list`, `delete`, `connect`.

### 2a: CLI and Network

Check in parallel:

```bash
which workspaces && which wmux
workspaces list 2>&1
```

| Check | Pass | Fail action |
|-------|------|-------------|
| `workspaces` CLI | Binary found | `brew update && brew install datadog-workspaces` |
| `wmux` CLI | Binary found | See [wmux install instructions](https://github.com/DataDog/wmux) |
| Appgate VPN | `workspaces list` succeeds | "Connect to Appgate VPN before continuing" |

If `workspaces` CLI not installed, offer to install:

```bash
brew update && brew install datadog-workspaces
```

If `wmux` is not installed, warn but continue -- fall back to manual auth checks in later steps.

### 2b: Pre-Flight Auth Checks

If `wmux` is available, use it for a comprehensive local auth check:

```bash
wmux auth status --pending 2>&1
```

This evaluates all configured auth checks and surfaces actionable items.
For each check with status != ok, resolve:

```bash
wmux auth open --check <check-id> --wait 2>&1
```

wmux handles browser opening, device-code clipboard, callback proxy, and completion polling.
Monitor output for OIDC device-code patterns per [references/auth-setup.md](references/auth-setup.md).
Surface device codes immediately via AskUserQuestion.

If `wmux` is not available, fall back to manual checks per [references/auth-setup.md](references/auth-setup.md):

1. **SSH agent** -- verify `ssh-add -l` shows keys before any `-A` forwarding.
   If no keys, offer fix (`eval $(ssh-agent) && ssh-add`). Block until resolved.
2. **GitHub auth** -- verify `ddtool auth github status`.
   If expired, run `ddtool auth github login` (may trigger OIDC -- surface device codes per auth-setup.md).

Surface failures with AskUserQuestion and offer fixes.
Stop and fix blocking failures before proceeding.

### 2c: Workspace Secrets Validation (Create Mode Only)

For `create` mode, validate required secrets BEFORE workspace creation.
Secrets only propagate to future workspaces -- skipping this means recreating the workspace later.

If `wmux` is available:

```bash
wmux validate-workspace-config 2>&1
```

If `wmux` is not available, check manually:

```bash
workspaces secrets list 2>&1
```

Verify these secrets are registered and exported:

| Secret | Required | Purpose |
|--------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Claude Code API access |
| `OPENAI_API_KEY` | Yes | Codex API access |

If any are missing:

```
AskUserQuestion(
  header: "Missing workspace secrets",
  question: "Required secrets are missing. These must be set BEFORE workspace creation (cannot be added later).\n\nMissing: <list>\n\nSet them now?",
  options: [
    "Yes — set secrets now" -- I'll provide the API keys,
    "Skip" -- Create without secrets (Claude/Codex won't work on workspace)
  ]
)
```

If "Yes", guide through registration:

```bash
workspaces secrets set ANTHROPIC_API_KEY=<key> --export
workspaces secrets set OPENAI_API_KEY=<key> --export
```

Re-validate after registration. Block until resolved or skipped.

For `validate` mode: report all check results (Steps 2a through 2c) and stop.

## Step 3: Create Workspace

### 3a: Gather Parameters

Determine workspace parameters from arguments and current context:

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
REPO_NAME=$(basename "$REPO_ROOT" 2>/dev/null)
CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null)
WS_PREFIX=$(whoami | cut -d. -f1)
```

The workspace name is always prefixed with the user's first name (extracted from the OS username before the first `.`),
followed by `-`. For example, if `whoami` returns `rodrigo.fernandes` and the user provides `my-feature`,
the final name is `rodrigo-my-feature`.

If the user-provided name already starts with the prefix, do not double it.

| Parameter | Source | Default |
|-----------|--------|---------|
| `name` | `$WS_PREFIX-<slug>` where slug is from arguments after "create" | Ask user for slug |
| `--repo` | Current git repo name | Ask user if not in a repo |
| `--branch` | New feature branch via `/branch` | Created and pushed to remote |
| `--region` | User preference | `eu-west-3` |
| `--shell` | Always | `fish` |
| `--instance-type` | Always | `aws:m6gd.4xlarge` (ARM Graviton2) |

If no name provided:

```
AskUserQuestion(
  header: "Workspace name",
  question: "Name for the new workspace? (will be prefixed with '$WS_PREFIX-')",
  options: []
)
```

After deriving the final workspace name, check for conflicts:

```bash
workspaces list 2>/dev/null | grep -q "<final-name>"
```

If a workspace with that name already exists, ask the user:

```
AskUserQuestion(
  header: "Name conflict",
  question: "Workspace '<final-name>' already exists. What would you like to do?",
  options: [
    "Use a different name" -- I'll pick a new name,
    "Delete and recreate" -- Delete the existing workspace first,
    "Connect to existing" -- SSH or connect IDE to the existing workspace
  ]
)
```

### 3b: Optionally Create Feature Branch

Ask whether to create a new branch for this workspace:

```
AskUserQuestion(
  header: "Feature branch?",
  question: "Create a new feature branch for this workspace?",
  options: [
    "Yes — create new branch" -- Create and push a new branch,
    "No — use current branch '<CURRENT_BRANCH>'" -- Work from the current branch
  ]
)
```

If yes, create and push:

```
Skill(skill="branch", args="<name or feature description>")
```

```bash
git push -u origin <branch-name>
```

Verify the push succeeded before proceeding. If push fails, fix and retry (max 2 attempts).

If no: use `$CURRENT_BRANCH` as `<branch-name>` throughout the remaining steps.

### 3c: Create Workspace

Run the create command **in the background** (`run_in_background: true`) -- it takes 10-20 minutes:

```bash
workspaces create <name> \
  --repo <repo> \
  --branch <branch-name> \
  --region eu-west-3 \
  --instance-type aws:m6gd.4xlarge \
  --shell fish
```

Omit `--repo` if not in a git repo and user doesn't specify one.

Dotfiles are auto-applied from `DataDog/workspaces-dotfiles/users/<first>.<last>/`.
Do not pass `--dotfiles` here -- it would override the auto-apply chain.

**Do NOT wait for the command to finish.** Report immediately after launching.
The background task will notify when complete -- do not poll or sleep.

### 3d: Report Creation Status

Report immediately after launching the background create:

```
Workspace "<name>" is being created on branch "<branch-name>" (takes ~10-20 min).
I'll run auth setup and start a tmux session when it's ready.

Status:  workspaces list
```

### 3e: Post-Creation Auth Setup

After workspace creation completes and SSH config is verified,
run auth setup on the workspace.

Warn the user before starting -- device codes expire in minutes:

```
AskUserQuestion(
  header: "Auth setup",
  question: "Workspace is ready. About to run auth setup — this may prompt for browser-based OIDC login. Please be ready. Proceed?",
  options: [
    "Proceed" -- I'm ready for browser auth prompts,
    "Skip auth" -- Continue without auth setup (may cause failures later)
  ]
)
```

If "Proceed", run auth checks on the workspace.

**If `wmux` is available**, use the unified auth evaluator:

```bash
wmux auth status --workspace <name> --pending 2>&1
```

For each actionable check, resolve sequentially (each may need browser interaction):

```bash
wmux auth open --workspace <name> --check <check-id> --wait 2>&1
```

Monitor output for OIDC device-code patterns per the Surfacing Protocol in
[references/auth-setup.md](references/auth-setup.md).
When a device code or browser URL appears, surface it immediately via AskUserQuestion
and wait for user confirmation before proceeding to the next check.

**If `wmux` is not available**, fall back to manual checks per auth-setup.md:

1. **ddtool staging:** `ssh -A workspace-<name> "ddtool auth login --datacenter us1.staging.dog 2>&1"`
2. **ddtool ddbuild:** `ssh -A workspace-<name> "ddtool auth login --datacenter us1.ddbuild.io 2>&1"`
3. **GitHub on workspace:** `ssh -A workspace-<name> "gh auth status 2>&1"` (login if needed)
4. **SSH forwarding:** `ssh -A workspace-<name> "ssh-add -l 2>&1"`

### 3f: Post-Setup Health Check

After auth setup, verify overall workspace readiness:

```bash
wmux auth status --workspace <name> 2>&1
```

| Overall status | Action |
|----------------|--------|
| `ready` | Proceed to 3g |
| `auth_required` | Surface remaining items, offer another round of auth setup |
| `blocked` | Surface terminal failures, offer recovery (see below) |
| `checking` | Wait 5s, re-check (max 3 attempts) |

If `wmux` is not available, verify with manual spot checks:

```bash
ssh -A workspace-<name> "gh auth status 2>&1 && ssh-add -l 2>&1"
```

**Recovery for blocked status:**

```
AskUserQuestion(
  header: "Auth issues",
  question: "Some auth checks are blocked on the workspace. How to proceed?",
  options: [
    "Run auth doctor" -- Get detailed diagnostics with wmux auth doctor,
    "Retry auth setup" -- Re-run the full auth setup,
    "Continue anyway" -- Start tmux despite auth issues,
    "Delete and recreate" -- Delete this workspace and start over
  ]
)
```

If "Run auth doctor": `wmux auth doctor --workspace <name> 2>&1` and surface results.

### 3g: Start Tmux Session with Claude

When auth setup is complete (or skipped),
SSH into the workspace, cd into the repo, and start a detached tmux session running Claude Code:

```bash
ssh -A workspace-<name> "cd /workspaces/<repo> && git checkout <branch-name> && tmux new-session -d -s main -c /workspaces/<repo> claude"
```

The workspace is created with `--branch`, so the checkout is a no-op in the happy path
but ensures correctness if the workspace defaulted to a different branch.

If SSH fails, run `workspaces ssh-config <name>` first and retry.

Verify tmux session started:

```bash
ssh -A workspace-<name> "tmux has-session -t main 2>&1"
```

If tmux session verification fails, retry the tmux command once.
If still failing, report the error and provide manual join instructions.

Then print the join command for the user:

```
Workspace "<name>" is ready on branch "<branch-name>".

Join the session with Claude open:
  ssh -A workspace-<name> -t "tmux new-session -A -s main"

iTerm2 users can add -CC for native window integration:
  ssh -A workspace-<name> -t "tmux -CC new-session -A -s main"

Other commands:
  IDE:     workspaces connect <name> --editor intellij
  Status:  workspaces list
  Delete:  workspaces delete <name>

The workspace will be garbage collected after 20 days of inactivity
and has a hard TTL of 6 months.
```

## Step 4: List Workspaces

```bash
workspaces list
```

Report the list including workspace names, status, and expiration dates.

## Step 5: Delete Workspace

If name not provided, run `workspaces list` first and ask user to pick.

Confirm before deleting:

```
AskUserQuestion(
  header: "Delete workspace",
  question: "Delete workspace '<name>'? This removes everything including the home directory.",
  options: [
    "Yes, delete" -- Permanently delete the workspace,
    "Cancel" -- Keep the workspace
  ]
)
```

If confirmed:

```bash
workspaces delete <name>
```

## Step 6: SSH into Workspace

### 6a: Pre-SSH Auth Check

Run the pre-flight checks from [references/auth-setup.md](references/auth-setup.md):

1. Verify SSH agent has keys (`ssh-add -l`)
2. If no keys, offer fix before proceeding

### 6b: Connect

```bash
ssh -A workspace-<name>
```

The prefix `workspace-` is required. Tab completion works.
Use `-A` for agent forwarding so git operations work on the workspace.

If SSH fails:

```bash
workspaces ssh-config <name>
```

Then retry SSH.

### 6c: Post-Entry Auth Validation

After successful SSH, run a lightweight auth check on the workspace.

If `wmux` is available:

```bash
wmux auth status --workspace <name> --pending 2>&1
```

If `wmux` is not available:

```bash
ssh -A workspace-<name> "gh auth status 2>&1 && ssh-add -l 2>&1"
```

If actionable items found:

```
AskUserQuestion(
  header: "Workspace credentials",
  question: "Some credentials on the workspace need refresh. Run full auth setup?",
  options: [
    "Yes" -- Run auth setup now (may require browser interaction),
    "Skip" -- Continue without refreshing
  ]
)
```

If "Yes", run the full Post-Creation Auth Setup (Step 3e procedures).

## Step 7: Connect IDE

```bash
workspaces connect <name> --editor <editor>
```

Default editor is `intellij` if not specified.

## Error Handling

| Error | Action |
|-------|--------|
| `workspaces` CLI not found | Install: `brew update && brew install datadog-workspaces` |
| `wmux` CLI not found | Warn and fall back to manual auth checks |
| Connection refused / timeout | Check Appgate VPN is connected |
| Auth error | Run `wmux auth open --check <id>` or fall back to `ddtool auth github login` |
| SSH connection refused | Run `workspaces ssh-config <name>` to fix SSH config |
| Workspace not found | Run `workspaces list` to show available workspaces |
| Create fails | Check Appgate VPN, GitHub auth, instance type availability, and workspace secrets |
| SSH agent forwarding fails | Verify ssh-agent is running and keys are added (`ssh-add -l`). Suggest `eval $(ssh-agent) && ssh-add`. |
| Missing `workspace-` prefix in SSH | Use `ssh workspace-<name>`, not `ssh <name>` |
| OIDC device-code prompt | Surface URL and code immediately via AskUserQuestion. See [references/auth-setup.md](references/auth-setup.md). |
| Branch push fails before create | Fix push issue (auth, permissions, protected branch) and retry before workspace creation |
| Workspace secrets missing | Guide through `workspaces secrets set KEY=VALUE --export`. Workspace must be recreated if already created. |
| Auth blocked after retries | Run `wmux auth doctor --workspace <name>` for diagnostics. Offer delete and recreate. |
| Tmux session fails to start | Retry once. If still failing, provide manual SSH and tmux commands. |

## Reference

For auth setup procedures (pre-flight, post-creation, OIDC surfacing, wmux commands), see [references/auth-setup.md](references/auth-setup.md).

For advanced configuration (secrets, instance types, IDE templates, wmux config, Claude Code setup), see [references/advanced.md](references/advanced.md).
