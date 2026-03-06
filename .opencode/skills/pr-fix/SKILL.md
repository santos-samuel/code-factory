---
name: pr-fix
description: >
  Use when the user wants to address PR review feedback, fix PR comments, resolve review threads,
  or respond to code review suggestions on a pull request. Supports --auto for fully autonomous mode.
  Triggers: "fix pr feedback", "address pr comments", "resolve pr reviews", "pr fix",
  "address review feedback", "fix review comments", "handle pr feedback",
  "respond to pr review", "address pr feedback", "pr fix --auto".
argument-hint: "[PR number or URL, optional --reviewer <name>, optional --auto]"
user-invocable: true
allowed-tools: Bash(git:*), Bash(gh:*), Bash(get_ddci_logs.sh:*), Read, Write, Edit, Grep, Glob, AskUserQuestion, Task
---

# Fix PR Feedback

Announce: "I'm using the pr-fix skill to address PR review feedback."

## Step 1: Gather Context

Parse `$ARGUMENTS` for:

| Input | Pattern | Example |
|-------|---------|---------|
| PR number | Digits | `42`, `332190` |
| PR URL | `github.com/.*/pull/\d+` | `https://github.com/org/repo/pull/42` |
| Reviewer filter | `--reviewer <name>` | `--reviewer alice` |
| Autonomous mode | `--auto` | `--auto` |

**Autonomous mode (`--auto`):** Runs the full fix-commit-push-CI-review cycle without user prompts. Defaults: fix all threads, explain-and-keep for disagreements, watch-and-fix CI, review-and-fix automated feedback. Use when you want a hands-off run.

Run in parallel:

- `gh auth status 2>&1`
- `gh repo view --json nameWithOwner -q '.nameWithOwner'` (split on `/` to get `{owner}` and `{repo}` for API calls)
- `git branch --show-current`
- `git status --short`

**If `gh` is not authenticated:** inform the user to run `gh auth login`. Stop.

**If no PR number provided:** detect from current branch:

```bash
gh pr view --json number -q '.number' 2>/dev/null
```

**If still no PR:** ask the user for the PR number. Stop.

## Step 2: Fetch Unresolved Review Threads

Fetch all unresolved review threads using the GraphQL API. See [references/graphql-queries.md](references/graphql-queries.md) for the full query.

```bash
gh api graphql -F owner='{owner}' -F repo='{repo}' -F pr={number} -f query='...'
```

Parse the response into a structured list. For each thread, extract:

| Field | Source |
|-------|--------|
| `threadId` | `reviewThreads.nodes[].id` (GraphQL node ID for mutations) |
| `isResolved` | `reviewThreads.nodes[].isResolved` |
| `path` | `reviewThreads.nodes[].path` |
| `line` | `reviewThreads.nodes[].line` |
| `comments` | Array of `{ databaseId, body, author.login, outdated }` |
| `firstComment` | First comment in the thread (the review comment) |

**If `--reviewer` specified:** filter threads to only those where `firstComment.author.login` matches.

**If no unresolved threads:** inform the user all review threads are resolved. Stop.

## Step 3: Categorize and Prioritize

Classify each thread into one of four categories:

| Category | Signals | Action |
|----------|---------|--------|
| **Suggestion** | Body contains `` ```suggestion `` block | Apply the suggested code change |
| **Code change** | Imperative language ("change X", "add Y", "remove Z"), bug report, missing handling | Edit the code as requested |
| **Question** | Ends with `?`, asks "why", requests clarification | Respond with explanation |
| **Disagreement** | Reviewer challenges a design decision, requests a revert or alternative approach | **NEVER auto-resolve.** Present to user for decision. |
| **Outdated** | Thread `isOutdated` is true or all comments are `outdated` | Read current code at `path`. If the concern is already addressed, resolve with a note. If not, reclassify as Code change or Question. |

Assign priority:

| Priority | Criteria |
|----------|----------|
| **P0** | Bugs, security issues, breaking changes, data integrity |
| **P1** | Refactoring with clear benefit, naming/clarity, type safety, missing error handling |
| **P2** | Nits, style preferences, minor optimizations, "for next time" suggestions |

## Step 4: Present Summary and Get Direction

Show the user a concise summary:

```
PR #{number}: {title}
{total} unresolved threads ({reviewer filter if applied})

P0 (Critical):  {count} — {brief descriptions}
P1 (Should fix): {count} — {brief descriptions}
P2 (Nice to have): {count} — {brief descriptions}

Proposed actions:
- Apply suggestions: {count}
- Code changes: {count}
- Respond with explanation: {count}
- Need your decision: {count} (disagreements)
```

**If `--auto` mode:** Skip all prompts. Default to "Fix all" for non-disagreements and "Explain and keep" for disagreements (safest autonomous default — code stays unchanged, reviewer gets a reasoned explanation). Proceed to Step 5.

**For disagreements** (interactive mode only), present each one explicitly:

<interaction>
AskUserQuestion(
  header: "Review disagreement",
  question: "Thread on {path}:{line} — Reviewer says: '{summary}'. How should we handle this?",
  options: [
    "Fix as requested" — Make the change the reviewer wants,
    "Explain and keep" — Respond with explanation, do not change code,
    "Discuss further" — Reply asking for more context, do not resolve
  ]
)
</interaction>

**For everything else** (interactive mode only), ask:

<interaction>
AskUserQuestion(
  header: "Proceed?",
  question: "Ready to address {count} threads ({suggestions} suggestions, {changes} code changes, {questions} explanations)?",
  options: [
    "Fix all" — Address all threads as categorized,
    "Let me choose" — Review each thread individually before proceeding
  ]
)
</interaction>

If "Let me choose": present each thread with its category and proposed action. Let the user override categories or skip specific threads.

## Step 5: Execute Fixes

Process threads grouped by file. Within each file, sort by line number **descending** (bottom-to-top) to prevent line drift.

### Applying Suggestions

For threads with `` ```suggestion `` blocks:

1. Extract the suggested code from between `` ```suggestion `` and `` ``` `` markers. If a comment contains multiple suggestion blocks, apply the first one. If ambiguous, ask the user.
2. Read the file at `path`.
3. Replace the lines at `line` (or `startLine..line` for multi-line) with the suggested code.
4. Use the Edit tool to apply the change.

### Applying Code Changes

For threads requiring code changes:

1. Read the file at `path` to understand context around `line`.
2. Determine the fix based on the reviewer's comment.
3. Apply the change using the Edit tool.
4. If the fix is unclear, ask the user for clarification before proceeding.

### Preparing Explanations

For threads requiring explanations:

1. Read the code context to understand the design decision.
2. Draft a technical explanation (not defensive — focus on reasoning, constraints, trade-offs).
3. Include links to relevant docs or code if applicable.

## Step 6: Reply and Resolve Threads

For each addressed thread, reply directly to the review comment and resolve the thread.

**Reply** using the REST API (replies to the specific thread, not a generic PR comment). Use a HEREDOC for the body to handle special characters:

```bash
gh api repos/{owner}/{repo}/pulls/comments/{databaseId}/replies \
  -X POST -f body="$(cat <<'EOF'
{response text}
EOF
)"
```

Response format by category:

| Category | Format |
|----------|--------|
| Suggestion applied | `Done — applied the suggestion.` |
| Code change | `Fixed — {brief description of what changed}.` |
| Explanation | `{technical explanation with reasoning}` |
| Disagreement (fix) | `Agreed — {brief description of the fix}.` |
| Disagreement (keep) | `{explanation of reasoning}. Let me know if you'd like to discuss further.` |
| Outdated (addressed) | `This has been addressed in a subsequent update.` |

**Bot attribution:** When replying to automated reviewer comments (Greptile, Codex, etc.), prefix every reply with `*Automated response from Claude:*` to distinguish from human responses.

**Resolve** the thread using GraphQL mutation (see [references/graphql-queries.md](references/graphql-queries.md)):

```bash
gh api graphql -f query='mutation { resolveReviewThread(input: { threadId: "{threadId}" }) { thread { isResolved } } }'
```

**Do NOT resolve:**
- Threads where the user chose "Discuss further"
- Threads where the reply is a question back to the reviewer

## Step 7: Commit and Push

Group changes into logical commits. Strategy:

| Scenario | Commits |
|----------|---------|
| All changes in 1-2 files | Single commit |
| Changes span 3+ files, all related | Single commit |
| Changes span multiple unrelated concerns | One commit per concern |
| Mix of suggestions and code changes | Group by concern, not by category |

Commit message format — follow the repo's convention detected from `git log --oneline -5`. If the repo uses conventional commits:

```
fix(scope): address PR #{number} review feedback

- {description of change 1}
- {description of change 2}
```

Push to remote:

```bash
git push
```

**If push fails due to diverged branch:** inform the user. Do NOT force-push. Let the user decide.

## Step 8: CI Validation + Automated Reviews (Parallel)

After pushing, trigger bot reviews immediately and monitor CI in parallel. Bot reviews don't depend on CI — start them early so they complete during CI.

### 8a: Trigger Automated Reviews (if stale)

Check if new commits exist since the last greptile/codex comments:

```bash
# Get the latest bot comment timestamp
gh api repos/{owner}/{repo}/issues/{number}/comments \
  --jq '[.[] | select(.user.login | test("greptile|codex"; "i")) | .created_at] | sort | last'

# Get the latest commit timestamp on the PR branch
gh api repos/{owner}/{repo}/pulls/{number}/commits \
  --jq '[.[].commit.committer.date] | sort | last'
```

Compare timestamps. If the latest commit is **after** the latest bot comment (or no bot comments exist), reviews are stale.

**If reviews are current:** skip to 8b — no re-trigger needed.

**If `--auto` mode:** Trigger immediately (no prompt).

**Interactive mode:**

<interaction>
AskUserQuestion(
  header: "Re-trigger automated reviews?",
  question: "There are new commits since the last Greptile/Codex reviews. Re-trigger them?",
  options: [
    "Yes — review and fix" — Trigger reviewers, fix actionable feedback after CI (max 3 iterations),
    "Just trigger" — Post review comments but do not auto-fix,
    "No" — Skip automated reviews
  ]
)
</interaction>

If triggering: post `@greptileai review` and `@codex` comments now per [references/automated-review-loop.md](references/automated-review-loop.md) Phase 1. **Do NOT wait for responses** — bots review in background while CI runs.

### 8b: CI Validation Loop

**If `--auto` mode:** Proceed with "Yes — watch and fix" (no prompt).

**Interactive mode:**

<interaction>
AskUserQuestion(
  header: "Watch CI?",
  question: "Fixes pushed. Want me to watch CI and auto-fix any failures?",
  options: [
    "Yes — watch and fix" — Monitor CI, analyze failures, apply fixes, and loop until green (max 3 iterations),
    "Just watch" — Monitor CI and report results without auto-fixing,
    "No" — Skip CI monitoring
  ]
)
</interaction>

**If "No":** skip to 8c.

Follow the CI validation loop in [references/ci-validation-loop.md](references/ci-validation-loop.md).

- **"Yes — watch and fix"**: full loop — wait for CI, analyze failures, fix, commit, push, recheck (max 3 iterations).
- **"Just watch"**: wait for CI to complete and report results. No fixes applied.

### 8c: Process Automated Review Feedback

If bot reviews were triggered in 8a, collect their responses now. By this point bots have had the full CI wait time to complete.

Follow [references/automated-review-loop.md](references/automated-review-loop.md) starting from **Phase 2** (Phase 1 trigger already done in 8a).

- **"Yes — review and fix"**: wait for responses, fix actionable feedback, commit, push, re-trigger (max 3 iterations).
- **"Just trigger"**: wait for responses and report. No fixes applied.
- **If reviews were not triggered in 8a:** skip this substep.

Append both the CI loop and review loop reports to the Step 9 summary.

## Step 9: Summary

Present the final report:

```
## PR #{number} Review Feedback Addressed

### Resolved ({count}/{total})
- {path}:{line} — {category}: {brief description}
  Reply: "{response summary}"

### Unresolved ({count})
- {path}:{line} — {reason not resolved}

### Commits
- {hash} — {message}

### Files Modified
- {list}

### CI Validation
{if CI loop ran, include the report from references/ci-validation-loop.md Phase 5}
{if CI loop skipped, omit this section}

### Automated Review
{if review loop ran, include the report from references/automated-review-loop.md Phase 8}
{if review loop skipped, omit this section}

### Next Steps
- {if all resolved and CI green}: Ready for re-review
- {if unresolved remain}: {count} threads need follow-up
- {if CI failures remain}: {count} CI failures need investigation
```

**Offer to request re-review** if all threads are resolved. Determine reviewers from the `--reviewer` argument (if provided) or by deduplicating `firstComment.author.login` from addressed threads:

```bash
gh pr edit {number} --add-reviewer {reviewer1},{reviewer2}
```

## Error Handling

| Error | Action |
|-------|--------|
| `gh` not authenticated | Inform user to run `gh auth login`. Stop. |
| PR not found | Verify the PR number and repo. Report error. Stop. |
| No unresolved threads | Inform user all feedback is addressed. Stop. |
| GraphQL query fails | Fall back to REST: `gh api repos/{owner}/{repo}/pulls/{number}/comments`. Lose thread resolution data but can still categorize and fix. |
| Thread resolution fails | Report the error. The reply was still posted. Continue with remaining threads. |
| Reply fails | Report the error. Log the intended response. Continue with remaining threads. |
| Edit fails (file not found) | The file may have been renamed or deleted. Report to user. Skip thread. |
| Push fails | Report the error. Do NOT force-push. Let user decide. |
| Merge conflict after edits | Report conflicting files. Let user resolve manually. |
| Line numbers outdated | If comment is marked `outdated`, inform user the code has changed since the review. Read the file and attempt to find the relevant code by context. |
| CI check timeout | If `gh pr checks --watch` hangs beyond 20 min, fall back to polling. Report timeout to user. |
| CI fix loop exceeds 3 iterations | Stop. Report remaining failures with log excerpts. Let user investigate. |
| Same CI failure recurs after fix | Mark as unfixable. Do NOT retry the same fix. Report to user. |
| DDCI logs unavailable | Skip log analysis. Report the Mosaic URL for manual investigation. |
| Greptile/Codex not configured | If no review appears after 15-min timeout, skip that reviewer. Continue with others. |
| Automated review loop exceeds 3 iterations | Stop. Report remaining review comments. Let user investigate. |
