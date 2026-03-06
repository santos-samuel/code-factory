# CI Validation Loop

Reference for the `pr-fix` skill. Implements an automated check-fix-recheck cycle after pushing PR feedback fixes.

## Overview

After pushing fixes, monitor CI status. If checks fail, analyze failures, apply fixes, commit, push, and recheck. Maximum **3 iterations** to prevent infinite loops.

## Phase 1: Wait for CI

After the push from Step 7, wait for CI to start and complete.

```bash
gh pr checks {number} --watch --fail-fast 2>&1
```

**Exit code 0** → all checks passed → skip to Phase 4 (report success).

**Exit code non-zero** → at least one check failed → continue to Phase 2.

**If `--watch` is unavailable or hangs:** fall back to polling:

```bash
# Poll every 30s, max 20 minutes
gh pr checks {number} --json name,state,bucket,link
```

States: `pending` and `queued` mean still running. `pass` means success. `fail` means failure.

**Wait until no checks are `pending` or `queued` before proceeding.**

## Phase 2: Identify Failures

Fetch the full check results:

```bash
gh pr checks {number} --json name,state,bucket,link
```

Parse into a structured list of failed checks. For each failed check, determine the CI system:

| Link pattern | CI system |
|-------------|-----------|
| `gitlab.ddbuild.io/*` or `mosaic.us1.ddbuild.io/*` | DDCI (GitLab) |
| `github.com/*/actions/*` | GitHub Actions |
| Other | Unknown — report link to user |

### DDCI Failures

1. Extract the DDCI `request_id` from the "DDCI Task Sourcing" check's Mosaic URL:

```bash
# The link looks like: https://mosaic.us1.ddbuild.io/change-request/<request_id>
# Extract request_id from the URL path
```

2. List failed jobs:

```bash
get_ddci_logs.sh --list-failed {request_id}
```

Output is tab-separated: `job_id`, `job_name`, `status`, `failure_reason`.

3. For each failed job, fetch the log summary:

```bash
get_ddci_logs.sh {job_id} {request_id} --summary
```

**If `get_ddci_logs.sh` is not available:** fall back to the `/dd:fetch-ci-results` skill if installed, or report the Mosaic URL to the user and ask them to investigate manually.

### GitHub Actions Failures

1. Extract the run ID from the check link.

2. Fetch failed job logs:

```bash
gh run view {run_id} --log-failed 2>&1 | tail -100
```

3. If the output is too large, fetch per-job:

```bash
gh run view {run_id} --json jobs --jq '.jobs[] | select(.conclusion == "failure") | {name, steps: [.steps[] | select(.conclusion == "failure") | .name]}'
```

## Phase 3: Analyze and Fix

Classify each failure by priority:

| Priority | Category | Examples | Auto-fixable? |
|----------|----------|----------|---------------|
| **P0** | Build errors | Compilation failure, missing imports, syntax errors | Yes — read error, fix code |
| **P1** | Test failures | Unit test assertion, integration test timeout | Maybe — read test output, fix if clear root cause |
| **P2** | Lint/format | Style violations, unused imports, formatting | Yes — run formatter/linter with --fix |
| **P3** | Flaky/infra | Network timeout, runner OOM, service unavailable | No — retry, not fix |

### Re-run Flaky Jobs

For failures classified as P3 (flaky/infra), re-run without fixing code:

**GitHub Actions:**

```bash
gh run rerun {run_id} --failed
```

**DDCI:**

```bash
retry_ddci_job.sh {job_id}
```

**If `retry_ddci_job.sh` is not available:** report the failure and Mosaic link. Let the user retry manually.

After re-running, return to Phase 1 to wait for the new run. Count this as an iteration.

### Fix Strategy

For each failure, in priority order:

1. **Read the error output** — identify the file, line, and error message.
2. **Read the affected file** at the reported location.
3. **Determine if auto-fixable:**
   - If the fix is clear (missing import, type error, lint violation) → apply the fix.
   - If the fix requires design decisions → **stop and ask the user**.
   - If the failure is flaky/infra → **do not fix, offer retry**.
4. **Apply the fix** using the Edit tool.

**Rules:**

| Rule | Detail |
|------|--------|
| Fix only what CI reports | Do NOT proactively fix unrelated issues |
| One concern per iteration | Fix all failures from one CI run, then push and recheck |
| Confidence threshold | Only auto-fix if you can identify the exact root cause from the logs |
| Ask on ambiguity | If multiple fixes are possible, present options to the user |
| Never suppress tests | Do not skip, disable, or mark tests as expected-failure to pass CI |

### Commit and Push

After applying fixes:

```bash
git add {changed files}
git commit -m "$(cat <<'EOF'
fix: address CI failures from PR #{number} feedback

- {description of fix 1}
- {description of fix 2}
EOF
)"
git push
```

## Phase 4: Loop Control

After pushing fixes, return to Phase 1 to wait for the new CI run.

**Exit conditions (stop the loop):**

| Condition | Action |
|-----------|--------|
| All checks pass | Report success → exit |
| Iteration count reaches 3 | Report remaining failures → exit |
| No auto-fixable failures remain | Report unfixable failures → exit |
| User declines a fix | Report status and remaining failures → exit |
| Same failure persists after fix attempt | Report as unfixable → exit |

**Iteration tracking:**

Track across iterations:
- `iteration_count` — incremented each time through the loop
- `fixed_failures` — set of failure signatures already attempted (to detect repeats)
- `total_fixes_applied` — running count of fixes made

**If a failure recurs after a fix attempt**, it means the fix was incorrect. Do NOT retry the same fix. Report it as unfixable and let the user investigate.

## Phase 5: CI Loop Report

Return this report to the calling step (Step 9 in SKILL.md):

```
### CI Validation

| Iteration | Failures Found | Fixes Applied | Result |
|-----------|---------------|---------------|--------|
| 1         | {count}       | {count}       | {pass/fail} |
| 2         | {count}       | {count}       | {pass/fail} |
| ...       | ...           | ...           | ...    |

{if all passed}
All CI checks passing after {N} iteration(s).

{if failures remain}
**Remaining failures ({count}):**
- {check name}: {failure description} — {reason not fixable}

**Recommended next steps:**
- {specific action per remaining failure}
```

## Error Handling

| Error | Action |
|-------|--------|
| `gh pr checks` fails | Verify PR number. Check `gh auth status`. Report error. |
| `--watch` hangs beyond 20 min | Kill and fall back to polling. Report timeout. |
| `get_ddci_logs.sh` not found | Skip DDCI log analysis. Report the Mosaic URL for manual investigation. |
| Log output exceeds context | Truncate to last 100 lines. Focus on the first error in the output. |
| Push fails after fix | Report error. Do NOT force-push. Let user decide. |
| Rate limited by GitHub API | Wait 60s and retry once. If still limited, report and exit. |
| VPN/network timeout | Inform user to check AppGate VPN connection. Stop. |
