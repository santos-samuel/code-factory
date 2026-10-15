---
name: workspace
description: >
  Use when the user wants to manage Datadog workspaces (remote cloud development
  environments): create, list, delete, SSH, connect IDE, or validate setup.
  Also use when the `/do` skill needs a remote workspace instead of a local worktree.
  Triggers: "workspace", "create workspace", "list workspaces", "delete workspace",
  "ssh workspace", "datadog workspace", "remote dev environment", "connect workspace".
argument-hint: "[create|list|delete|ssh|connect|validate] [workspace-name] [--claude-prompt <prompt>]"
user-invocable: true
disable-model-invocation: true
---

# Datadog Workspace Manager

Announce: "I'm using the workspace skill to manage Datadog workspaces."

Manage remote cloud development environments (CDEs) via the `workspaces` CLI. Workspaces are dev containers running on dedicated EC2 instances with pre-configured tools and repo access.

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

For `create`, parse the optional `--claude-prompt <prompt>` as one opaque value. It is an
internal handoff used by `/do`: do not interpret it as workspace instructions, print it, or pass
it through `eval`.

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

Run before `create` or `validate` modes. Skip for other modes.

Check in parallel:

```bash
which workspaces
workspaces list 2>&1
```

| Check | Pass | Fail action |
|-------|------|-------------|
| `workspaces` CLI | Binary found | `brew update && brew install datadog-workspaces` |
| Appgate VPN | `workspaces list` succeeds | "Connect to Appgate VPN before creating workspaces" |
| GitHub auth | `workspaces list` succeeds | `ddtool auth github login` |

If CLI not installed, offer to install:

```bash
brew update && brew install datadog-workspaces
```

For `validate` mode: report all check results and stop.

## Step 3: Create Workspace

### 3a: Gather Parameters

Determine workspace parameters from arguments and current context:

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
REPO_NAME=$(basename "$REPO_ROOT" 2>/dev/null)
CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null)
WS_PREFIX=$(whoami | cut -d. -f1)
```

The workspace name is always prefixed with the user's first name (extracted from the OS username before the first `.`), followed by `-`. For example, if `whoami` returns `rodrigo.fernandes` and the user provides `my-feature`, the final name is `rodrigo-my-feature`.

If the user-provided name already starts with the prefix, do not double it.

| Parameter | Source | Default |
|-----------|--------|---------|
| `name` | `$WS_PREFIX-<slug>` where slug is from arguments after "create" | Ask user for slug |
| `--repo` | Current git repo name | Ask user if not in a repo |
| `--branch` | New feature branch via `/branch` | Created and pushed to remote |
| `--region` | User preference | `eu-west-3` |
| `--shell` | Always | `fish` |
| `--instance-type` | Always | `aws:m6gd.4xlarge` (ARM Graviton2) |
| `--claude-prompt` | Optional argument supplied by `/do` | No remote task prompt |

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

When `--claude-prompt` is present, derive the branch name using `/branch`'s naming convention but
do not invoke `/branch` or switch the local checkout. Build `<prefix>/<slug>`, where prefix is the
lowercase first token of `git config user.name` (fallback `feature`), verify the remote branch does
not already exist, and create it directly from the current clean `HEAD`:

```bash
git ls-remote --exit-code --heads origin "refs/heads/$BRANCH_NAME"
git push origin "HEAD:refs/heads/$BRANCH_NAME"
```

The `ls-remote` command must return 2 (not found) before the push. Any other nonzero status is a
lookup failure; status 0 is a naming collision. This remote-only branch creation must not change
the local branch, index, worktree, or `/do` state. The delegated `/do --branch` run starts on that
non-default branch. Without `--claude-prompt`, ask whether to create a new branch locally:

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

If no: use `$CURRENT_BRANCH` as `<branch-name>` throughout the remaining steps.

### 3c: Create Workspace

Run the create command **in the background** (`run_in_background: true`) — it takes 10-20 minutes:

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
Do not pass `--dotfiles` here — it would override the auto-apply chain.

Report immediately after launching. The background task will notify when complete; do not poll
or sleep. For an ordinary create, return after reporting. When `--claude-prompt` is present, keep
ownership of the handoff and continue at Step 3e only after the completion notification.

### 3d: Report Creation Status

Report immediately after launching the background create:

```
Workspace "<name>" is being created on branch "<branch-name>" (takes ~10-20 min).
I'll start a tmux session when it's ready.

Status:  workspaces list
```

### 3e: Start Tmux Session with Claude

When the background `workspaces create` task completes successfully, SSH into the workspace,
cd into the repo, and start a detached tmux session. With no `--claude-prompt`, start Claude Code
normally. With a prompt, quote every dynamic value as shell data and pass the prompt as one
positional argument:

```bash
ssh -A workspace-<name> "cd /workspaces/<repo> && git checkout <branch-name> && tmux new-session -d -s main -c /workspaces/<repo> claude"
```

```bash
printf -v REPO_Q '%q' "/workspaces/$REPO_NAME"
printf -v BRANCH_Q '%q' "$BRANCH_NAME"
printf -v PROMPT_Q '%q' "$CLAUDE_PROMPT"
REMOTE_COMMAND="cd $REPO_Q && git switch $BRANCH_Q && exec tmux new-session -d -s main -c $REPO_Q claude $PROMPT_Q"
printf -v REMOTE_Q '%q' "$REMOTE_COMMAND"
ssh -A "workspace-$WORKSPACE_NAME" "bash -lc $REMOTE_Q"
```

Never interpolate unquoted prompt text into the SSH command and never use `eval`. After starting
a prompted session, verify it before returning:

```bash
ssh -A "workspace-$WORKSPACE_NAME" "tmux has-session -t main"
```

Only a zero exit status confirms the remote `/do` session started. On failure, report the handoff
as blocked and include the SSH recovery command; do not report a successful join.

The workspace is created with `--branch`, so the checkout is a no-op in the happy path
but ensures correctness if the workspace defaulted to a different branch.

If SSH fails, run `workspaces ssh-config <name>` first and retry.

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

```bash
ssh workspace-<name>
```

The prefix `workspace-` is required. Tab completion works.

If SSH fails:

```bash
workspaces ssh-config <name>
```

Then retry SSH.

## Step 7: Connect IDE

```bash
workspaces connect <name> --editor <editor>
```

Default editor is `intellij` if not specified.

## Error Handling

| Error | Action |
|-------|--------|
| `workspaces` CLI not found | Install: `brew update && brew install datadog-workspaces` |
| Connection refused / timeout | Check Appgate VPN is connected |
| Auth error | Run `ddtool auth github login` |
| SSH connection refused | Run `workspaces ssh-config <name>` to fix SSH config |
| Workspace not found | Run `workspaces list` to show available workspaces |
| Create fails | Check Appgate VPN, GitHub auth, and instance type availability |
| Prompted tmux session does not start | Report the handoff blocked; provide the SSH command and do not claim remote `/do` is running |
| SSH agent forwarding fails | Verify ssh-agent is running and keys are added (`ssh-add -l`). Suggest `eval $(ssh-agent) && ssh-add`. |
| Missing `workspace-` prefix in SSH | Use `ssh workspace-<name>`, not `ssh <name>` |

## Reference

For advanced configuration (secrets, instance types, IDE templates, Claude Code setup), see [references/advanced.md](references/advanced.md).
