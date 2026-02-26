---
name: pr-fix
description: >
  Use when the user wants to address PR review feedback, fix PR comments, resolve review threads,
  or respond to code review suggestions on a pull request.
  Triggers: "fix pr feedback", "address pr comments", "resolve pr reviews", "pr fix",
  "address review feedback", "fix review comments", "handle pr feedback",
  "respond to pr review", "address pr feedback".
argument-hint: "[PR number or URL, optional --reviewer <name>]"
user-invocable: true
allowed-tools: Bash(git:*), Bash(gh:*), Read, Write, Edit, Grep, Glob, AskUserQuestion, Task
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

**For disagreements**, present each one explicitly:

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

**For everything else**, ask:

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

## Step 8: Summary

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

### Next Steps
- {if all resolved}: Ready for re-review
- {if unresolved remain}: {count} threads need follow-up
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
