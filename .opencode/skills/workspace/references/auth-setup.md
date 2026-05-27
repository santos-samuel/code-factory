# Workspace Auth Setup

Detailed auth validation and setup procedures for Datadog workspaces.
Referenced from SKILL.md Steps 2b, 2c, 3e, and 6c.

wmux is the authoritative auth evaluator for workspaces.
Its `wmuxd` daemon runs on the workspace and evaluates all configured auth checks in parallel,
returning typed statuses per check and an overall readiness verdict.

## Auth Check Categories

wmux evaluates these categories. Each has config rows in `~/.config/wmux/config.json`:

| Category | Config rows | Examples |
|----------|-------------|---------|
| Environment secrets | `env.openai_api_key`, `env.anthropic_api_key` | Workspace-exported API keys |
| Auth providers | `auth.gh`, `auth.gh_signing`, `auth.gitlab`, `auth.codex`, `auth.claude` | OAuth/device-code login |
| ddtool datacenters | `ddtool.auth.datacenter.*` | `us1.ddbuild.io`, `us1.staging.dog` |
| ddtool tokens | `ddtool.auth.token.*` | `code-gen`, `rapid-data-science-autonomous-agents` |
| dd-auth domains | `dd-auth.domain.*` | Domain-specific auth |
| Kube contexts | `dd.kube_context` | `us1.release.mgmt.dog` |
| MCP servers | `mcp.*`, `claude-mcp.*` | Codex and Claude MCP OAuth |
| Fixed prerequisites | `auth.appgate` | Non-triggerable, report-only |

## Auth Status States

Each check resolves to one of:

| Status | Meaning | Blocking? |
|--------|---------|-----------|
| `ok` | Healthy, authenticated | No |
| `missing` | Requires browser/device flow | Yes (if required) |
| `pending` | Device flow in progress | Yes (action required) |
| `checking` | Evaluation in progress | Transient |
| `failed` | Check implementation failure | Yes |
| `configured` | MCP present but OAuth required | Yes |

Overall workspace status:

| Status | Meaning |
|--------|---------|
| `ready` | All checks ok |
| `auth_required` | Actionable checks exist |
| `blocked` | Terminal failures exist |
| `checking` | Checks in progress |

## Workspace Secrets Validation (Pre-Create)

Before creating a workspace, validate required secrets are registered and exported.
Run locally BEFORE `workspaces create`:

```bash
wmux validate-workspace-config
```

This checks:
- `ANTHROPIC_API_KEY` is present and exported via `workspaces secrets`
- `OPENAI_API_KEY` is present and exported via `workspaces secrets`
- `workspaces` CLI is available

If secrets are missing, guide the user:

```bash
workspaces secrets set ANTHROPIC_API_KEY=<key> --export
workspaces secrets set OPENAI_API_KEY=<key> --export
```

Secrets only propagate to FUTURE workspaces. If a workspace already exists without them, it must be recreated.

After registration, re-run `wmux validate-workspace-config` to confirm.

## Pre-Flight Auth Checks (Local)

Run on the LOCAL machine before creating or entering a workspace.

### SSH Agent Validation

Before any SSH with `-A` (agent forwarding):

```bash
ssh-add -l 2>&1
```

| Result | Action |
|--------|--------|
| Keys listed | Proceed |
| `Could not open...` or empty | Surface fix via AskUserQuestion |

Fix:

```bash
eval $(ssh-agent) && ssh-add
```

After fix, re-check `ssh-add -l` to confirm keys are present.
Block until resolved -- SSH agent forwarding is required for git operations on the workspace.

### Comprehensive Local Auth Check

Use wmux to evaluate all configured local auth checks:

```bash
wmux auth status --pending 2>&1
```

This shows all actionable (non-ok) checks. If any actionable items appear:

1. Surface the list to the user
2. For each actionable check, offer to resolve:

```bash
wmux auth open --check <check-id> --wait 2>&1
```

The `--wait` flag blocks until the check resolves (up to 2 min timeout).
wmux handles: browser opening, device-code clipboard, callback proxy, and completion polling.

If `wmux` is not installed, fall back to manual checks:

1. **GitHub auth:** `ddtool auth github status` (fix: `ddtool auth github login`)
2. **SSH agent:** `ssh-add -l` (fix: `eval $(ssh-agent) && ssh-add`)

## Post-Creation Auth Setup (Remote via SSH)

After workspace creation completes and SSH is available,
evaluate auth on the workspace using wmux:

```bash
wmux auth status --workspace <name> --pending 2>&1
```

This returns all checks that need attention on the workspace.
For each actionable check, resolve it:

```bash
wmux auth open --workspace <name> --check <check-id> --wait 2>&1
```

wmux's auth action runner handles the full phase lifecycle per check:
1. **Validation** -- check workspace/check validity
2. **Trigger** -- call `wmuxd` to initiate auth (get URL, code, attempt ID)
3. **ProxyReuse** -- start/reuse localhost callback listener
4. **CodeCopy** -- copy device code to clipboard
5. **BrowserOpen** -- open browser to auth URL
6. **Wait** -- poll auth status until ok (2 min default timeout)

Run checks sequentially -- each may need user browser interaction.
Warn the user before starting:

```
AskUserQuestion(
  header: "Auth setup",
  question: "About to run auth setup on the workspace. This may prompt for browser-based login. Please be ready. Proceed?",
  options: [
    "Proceed" -- I'm ready for browser auth prompts,
    "Skip auth" -- Continue without auth setup (may cause failures later)
  ]
)
```

### OIDC Device-Code Surfacing Protocol

When wmux or any auth command produces a device-code or browser-auth prompt,
detect and surface it immediately -- codes expire in minutes.

#### Detection Patterns

After running an auth command, scan output for:

| Pattern | Example |
|---------|---------|
| `enter code` or `one-time code` | `When prompted, enter code BXYZ-LMNO` |
| `Open the following link` or `open.*browser` | URL on next/same line |
| `github.com/login/device` | GitHub device flow |
| `google.com/device` | Google device flow |
| Device code format | `XXXX-XXXX`, `XXX-XXX-XXXX` |
| Bare URL near auth keywords | `https://...` near login/authenticate/device/verify |

#### Surfacing

When detected, present immediately:

```
AskUserQuestion(
  header: "Auth required",
  question: "An auth flow needs your browser.\n\nOpen: <URL>\nCode: <DEVICE_CODE>\n\nComplete the login in your browser, then confirm here.",
  options: [
    "Done" -- I completed the authentication,
    "Retry" -- Run the auth command again,
    "Skip" -- Continue without this auth (may cause failures later)
  ]
)
```

#### Post-Confirmation Verification

After "Done", re-check the specific auth status:

```bash
wmux auth status --workspace <name> --pending 2>&1
```

If the check is still failing, offer retry (max 3 attempts before moving on with a warning).

### Fallback: Manual Auth Commands

If wmux is not available on the workspace, fall back to manual commands sequentially:

1. **ddtool staging:** `ssh -A workspace-<name> "ddtool auth login --datacenter us1.staging.dog 2>&1"`
2. **ddtool ddbuild:** `ssh -A workspace-<name> "ddtool auth login --datacenter us1.ddbuild.io 2>&1"`
3. **GitHub on workspace:** `ssh -A workspace-<name> "gh auth status 2>&1"` (login if needed with `gh auth login --hostname github.com --git-protocol https --web`)
4. **SSH forwarding:** `ssh -A workspace-<name> "ssh-add -l 2>&1"`
5. **DD_API_KEY:** `ssh -A workspace-<name> "echo \$DD_API_KEY | head -c4 2>&1"` (informational only)

Monitor output for OIDC patterns per the Detection Patterns above.

## Post-Setup Health Check

After auth setup completes, verify overall readiness:

```bash
wmux auth status --workspace <name> 2>&1
```

| Overall status | Action |
|----------------|--------|
| `ready` | Proceed to tmux/Claude launch |
| `auth_required` | Surface remaining actionable items, offer another round |
| `blocked` | Surface terminal failures, offer recovery options |
| `checking` | Wait briefly (5s), re-check |

## Auth on Entry (Lightweight)

For SSH to an existing workspace (not freshly created), run a lighter check:

1. **Local:** SSH agent validation (same as pre-flight)
2. **Remote (after SSH succeeds):**

```bash
wmux auth status --workspace <name> --pending 2>&1
```

3. If actionable items:

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

If "Yes", resolve each actionable check with `wmux auth open --workspace <name> --check <id> --wait`.

## Auth Diagnostics

When auth issues persist after retries:

```bash
wmux auth doctor --workspace <name> 2>&1
```

This provides detailed diagnostic output per check.

## Recovery Paths

| Failure scenario | Recovery |
|-----------------|----------|
| Secrets missing (can't create) | `workspaces secrets set KEY=VALUE --export`, then retry |
| Auth check stuck in `pending` | `wmux auth open --workspace <name> --check <id> --wait` |
| Auth check `failed` after retries | `wmux auth doctor --workspace <name>`, surface diagnostics |
| Multiple checks blocked | Offer: run full auth setup, delete and recreate workspace, or skip |
| Callback proxy port conflict | wmux auto-retries with backoff (up to 2 retries) |
| Device code expired | Re-trigger with `wmux auth open --check <id>` (generates fresh code) |
| Workspace exists but auth broken | SSH in, run `wmux auth status --pending`, resolve each check |
