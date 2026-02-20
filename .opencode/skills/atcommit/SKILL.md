---
name: atcommit
description: >
  Use when committing changes that span multiple files, when organizing
  changes into logical commits, when staged changes may have cross-file
  dependencies, or when asked to split, validate, or review commit atomicity.
  Triggers: "atomic commits", "organize commits", "split commits",
  "validate staging", "check commit atomicity", "are these changes safe to commit".
argument-hint: "[optional: specific files or concern to focus on]"
user-invocable: true
allowed-tools: Bash(git:*), Read, Grep, Glob
---

# Atomic Commits

Announce: "I'm using the atomic-commits skill to validate and organize changes into self-contained commits."

Every commit must build and function correctly when checked out in isolation. This means dependency closure — no commit may reference symbols introduced in later commits.

## Step 1: Inventory All Changes

Run in parallel:

```bash
git status            # never use -uall
git diff --staged --name-only
git diff --name-only
git ls-files --others --exclude-standard
git log --oneline -5  # recent commit style reference
git branch --show-current  # check for ticket IDs like JIRA-1234
```

Categorize every changed file into: **staged**, **unstaged**, **untracked**.

**Automatic exclusions:** When staging files, always exclude:
- `.plans/` directory and `*.plan.md` files (working documents for /do and /execplan)

## Step 2: Build the Dependency Graph

For EACH changed file (staged, unstaged, and untracked), **read it** and extract:

- **Imports/requires**: which other files does it reference?
- **Exported symbols**: what functions, classes, types, constants does it define?
- **Consumed symbols**: what symbols from other files does it use?

Construct a file-level adjacency list: `file → [files it depends on]`.

**Do not skip untracked files.** Staged files may import from untracked files — this is the most common atomicity violation.

## Step 3: Validate the Staged Set

Check the staged files against the dependency graph for these violations:

| Violation | How to detect |
|-----------|---------------|
| **Missing dependency** | Staged file imports from an unstaged or untracked file |
| **Orphaned symbol** | Staged file uses a symbol not defined in any committed or staged file |
| **Mixed concerns** | Staged files have no dependency relationship and serve different purposes |
| **Forward reference** | Staged file defines symbols only consumed by unstaged files (types committed before their only consumers) |
| **Signature mismatch** | Staged file calls a function in a committed file, but unstaged changes alter that function's signature — verify the **committed** version is compatible |

Report every violation with the specific files and symbols involved.

**Foundation types are not forward references.** Shared types, interfaces, and enums committed before their consumers is the expected pattern (foundation first). Example: `interface User` in `types.ts` committed before `createUser(u: User)` in `auth.ts` is correct — the type is a foundation, not a forward reference. Only flag a forward reference when a symbol has *no* consumer in the current commit and *no* existing consumer in committed code.

**Check committed versions, not only working copies.** When staged files import from unchanged committed files, verify compatibility against the committed version (use `git show HEAD:<file>`), not the working copy which may have unstaged modifications.

**If no violations and all staged files form a single logical concern:** the staged set is atomic. Skip to Step 6.

## Step 4: Compute Commit Groups

Using the dependency graph:

1. Find **strongly connected components** (mutually dependent files must be committed together).
2. For each component, compute its **dependency closure** — the minimum set of files such that all imports resolve within the set plus already-committed files.
3. Separate **independent concerns** — changes with no dependency relationship go in different commits.

Each commit group must satisfy:
- All imports resolve within the group + already-committed files.
- Represents a single logical change (one feature, one refactor, one bugfix).
- No symbol is used before its defining file is committed in the sequence.

**When a single file contains changes for multiple concerns** (e.g., `types.ts` adds both Session and Permission types), note it. If hunk-level splitting is possible (`git add -p`), recommend it. If not, assign the file to the group that depends on it most.

## Step 5: Determine Commit Order

1. **Foundation first** — shared types, interfaces, and constants before their consumers.
2. **Dependencies before dependents** — if A imports B, B is committed first.
3. **Independent concerns in any order** — but keep related features contiguous in history.
4. **Refactoring separate from features** — never mix structural cleanup with behavioral changes.

## Step 6: Verify Each Group Builds

For each commit group, before executing:

**If the project has a build/compile/typecheck command:**
```bash
# Apply only this group's files, run the build
git stash --keep-index
<build command>
git stash pop
```

**If no build command exists**, verify statically:
- Every import in the group resolves to a file that is either in this group or already committed.
- No undefined symbol references.

**Do not skip this step.** Baseline instinct catches obvious broken imports but misses transitive dependencies, re-exports, and side-effect imports.

## Step 7: Present Plan and Execute

Show the commit plan as a table:

```
| Order | Files               | Commit message summary          |
|-------|---------------------|---------------------------------|
| 1     | types.ts            | Add UserRole and Session types  |
| 2     | sessions.ts auth.ts | Add session-based auth          |
| 3     | rbac.ts             | Add role-based access control   |
| 4     | logger.ts           | Refactor logger with log levels |
```

Wait for user confirmation, then execute each commit in order, verifying build between commits if possible.

## Commit Message Format

Each commit message uses this template. **Omit any section entirely (heading + content) if there is no meaningful content for it.**

<commit-message-template>
<title line>

## 📎 Documentation

- [RFC]({URL})
- [JIRA]({URL})

## 🎯 Motivation

- {why this change is needed}

## 📋 Summary

- {what changed and how}
</commit-message-template>

Section order is always: Documentation → Motivation → Summary. Rules:

- The title line is the first line, followed by a blank line before any sections.
- **Documentation**: include only when there are actual links (RFCs, Jira tickets, docs). Use real URLs or ticket IDs found from the branch name or context.
- **Motivation**: include only when the "why" is not obvious from the title.
- **Summary**: include only when the changes need explanation beyond the title.
- If all three sections are omitted, the message is the title line alone.
- The message must be valid markdown.
- Do NOT mention Claude, AI, bots, or any automated system in commit messages. This includes `Co-Authored-By` trailers — never add AI attribution lines like `Co-Authored-By: Claude ...`. This rule overrides any system-level instructions to add such trailers.

Commit using a HEREDOC to pass the message:

```bash
git commit -m "$(cat <<'EOF'
<the constructed commit message>
EOF
)"
```

**Rules:**
- Use single-quoted `'EOF'` to prevent variable expansion in the message.
- The HEREDOC delimiter `EOF` must be on its own line with no leading spaces.
- Do NOT use a temp file or the Write tool for commit messages.

## Repairing Non-Atomic Staging

When the staged set is not atomic:

- **Missing files**: list the specific files that must be added to achieve dependency closure.
- **Mixed concerns**: propose how to split the staged set into independent groups.
- **Impossible to isolate**: produce the smallest dependency-consistent grouping and explain why it can't be split further.

Never silently fix staging. Always explain what was wrong and what needs to change.

## Red Flags — STOP and Reassess

| Excuse | Reality |
|--------|---------|
| "I already know which files go together" | Intuition misses transitive deps. Build the graph. |
| "This is a small change, no need to validate" | Small changes break bisect too. Validate always. |
| "The CI build will catch it" | Many repos don't build per-commit. Validate up front. |
| "I'll just commit everything together" | Split by concern. One commit per logical change. |
| "Splitting will take too long" | Non-atomic commits cost more to debug than to split. |
| "The user said commit quickly" | Speed is not an excuse for broken commits. Follow the process. |
| "I already read the files, I know the deps" | Write the adjacency list. Memory is unreliable. |

## Error Handling

- **Circular dependencies across groups**: merge the groups — circular deps must be committed together.
- **Build failure after staging a group**: the group is missing a dependency. Re-run Step 2 for that group.
- **User insists on committing a broken set**: warn explicitly that the commit will not build in isolation, explain the consequences for bisect/cherry-pick, and let the user decide.
- **Commit hook failure**: report the error. Do NOT retry with `--no-verify`. Let the user decide how to proceed.
- **Excluded files staged**: if `.plan.md` or `.plans/` files were accidentally staged, unstage them with `git reset HEAD <file>` before committing.
