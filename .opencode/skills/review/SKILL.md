---
name: review
description: >
  Use when user says "review pr", "review pull request", "pr review", "review #123",
  or provides a PR number, URL, or branch name to review.
argument-hint: "[PR number, URL, or branch name]"
user-invocable: true
allowed-tools: Bash(git:*), Bash(gh:*), Read, Grep, Glob
---

# Review PR

Announce: "I'm using the review skill to review a GitHub pull request."

## Context

- Current branch: !`git branch --show-current`
- Repository: !`basename $(git rev-parse --show-toplevel)`
- Remote URL: !`git remote get-url origin 2>/dev/null || echo "no remote"`

## Step 1: Verify Prerequisites

Run in parallel:
- `gh auth status 2>&1`
- `git rev-parse --show-toplevel 2>&1`

**If `gh` is not installed or not authenticated:** inform the user that the `gh` CLI is required (`gh auth login`). Stop.

**If not a git repository:** inform the user and stop.

## Step 2: Identify the PR

Determine the PR from `$ARGUMENTS`:

| Input | Action |
|-------|--------|
| Number (e.g., `123`) | Use directly |
| URL (e.g., `github.com/.../pull/123`) | Extract the number |
| Branch name | `gh pr list --head <branch> --json number --jq '.[0].number'` |
| Empty | `gh pr view --json number --jq '.number' 2>/dev/null` |

**If no PR found:** use AskUserQuestion to request a PR number, URL, or branch name. List recent PRs with `gh pr list --limit 5` as suggestions.

## Step 3: Fetch PR Details

Run in parallel:
- `gh pr view <number> --json title,body,baseRefName,headRefName,author,additions,deletions,changedFiles,url,labels`
- `gh pr diff <number>`

## Step 4: Build Review

Analyze the diff and construct the review using the format below. Each section must be included.

---

### Output Format

<output-format>

## PR Review: <title>

**PR:** <url>
**Author:** <author>
**Base:** <baseRefName> ← <headRefName>
**Changes:** +<additions> -<deletions> across <changedFiles> files

---

### Goal

<1-3 sentences explaining what this PR accomplishes and why. Focus on intent, not implementation details. If the PR body contains useful context, incorporate it here.>

---

### Interface Changes

| Change | Type | Compatibility | Location |
|--------|------|---------------|----------|
| <what changed> | <API/struct/interface/param> | Additive or Breaking | `file:line` |

**Include:** Public API changes, exported types, HTTP endpoints, CLI flags, config schema changes.
**Exclude:** Internal structs, private functions, implementation details.

If none, write "None."

---

### Database / Schema Changes

| Change | Location | Migration Required |
|--------|----------|-------------------|
| <table/column/index change> | `file` | Yes/No |

If none, write "None."

---

### Findings

#### Critical

Issues that must be fixed before merge.

| Category | Location | Issue | Suggestion |
|----------|----------|-------|------------|
| <Correctness/Security/etc> | `file:line` | <description> | <fix> |

#### Suggestions

Improvements that would strengthen the PR.

| Category | Location | Issue | Suggestion |
|----------|----------|-------|------------|
| <Design/Testing/etc> | `file:line` | <description> | <fix> |

#### Nits

Minor style or consistency points.

| Location | Note |
|----------|------|
| `file:line` | <description> |

Omit any severity section with no entries.

---

### Test Coverage

| New/Changed Behavior | Test Coverage |
|---------------------|---------------|
| <feature or code path> | Covered / Missing / Partial |

---

### Impact Assessment

**Customer-facing:** <Changes visible to end users, API consumers, or external behavior. "None" if purely internal.>

**Internal:** <Refactors, tooling, developer experience, or internal APIs.>

---

### Verdict

**<Approve / Request Changes / Comment>**

<1-2 sentence rationale>

</output-format>

---

## Analysis Categories

When reviewing, evaluate against:

<analysis-categories>

| Category | Look For |
|----------|----------|
| **Correctness** | Logic errors, nil/null risks, off-by-one, missing error handling, race conditions |
| **Security** | Hardcoded secrets, injection vectors (SQL/XSS), insecure deserialization, overly permissive access |
| **Design** | Over-engineering, missing abstractions, pattern inconsistency, poor separation of concerns |
| **Testing** | Missing coverage, untested edge cases, weak assertions, brittle tests |
| **Style** | Unclear naming, dead code, misleading comments, formatting inconsistency |

</analysis-categories>

## Rules

- Reference exact file paths and line numbers from the diff.
- Be constructive: suggest fixes, not only problems.
- Do NOT post the review as a GitHub comment automatically. Present it to the user.
- If no findings exist, state that and recommend approval.

## Error Handling

| Error | Action |
|-------|--------|
| `gh` not installed/authenticated | Inform user to run `gh auth login`. Stop. |
| PR not found | Report error. List recent PRs with `gh pr list --limit 5`. |
| Network/API failure | Report the `gh` error message. Let user retry. |
