---
name: debug
description: >
  Use when encountering any bug, test failure, unexpected behavior, or production issue
  that requires investigation before fixing.
  Triggers: "debug", "investigate bug", "fix failing test", "why is this broken",
  "root cause", "debug this", "what's causing", "track down", "bisect".
argument-hint: "[bug description, error message, or failing test]"
user-invocable: true
---

# Systematic Debugging

Announce: "I'm using the /debug skill to systematically investigate this issue before proposing fixes."

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.
```

Symptom fixes are failure. Quick patches mask underlying issues. Random changes waste time and create new bugs.

You MUST complete Phase 1 before proposing any fix. Violating the letter of this rule IS violating the spirit.

## When to Apply Full Process

Apply this for: test failures, production bugs, unexpected behavior, performance problems, build failures, integration issues, flaky tests, and data corruption.

Apply **especially** when:
- Time pressure makes "quick fixes" tempting
- The fix seems "obvious"
- Multiple failed attempts have already occurred
- Understanding is incomplete

## Anti-Pattern: "This Is Too Simple To Debug Systematically"

| Rationalization | Reality |
|----------------|---------|
| "Quick fix for now, proper fix later" | "Later" never comes. The quick fix becomes permanent. |
| "I already know what's wrong" | If you knew, you wouldn't have a bug. Verify. |
| "Just try changing X" | Random changes create new bugs and waste time. |
| "Skip testing, I can see the fix" | You can't verify a fix without reproducing the bug first. |
| "This is too simple for process" | Simple bugs with skipped investigation have the highest rework rate. |
| "I'll add tests after the fix" | Tests-after prove "what does this do?" not "what should this do?" |
| "Multiple changes at once will be faster" | Changing multiple variables prevents isolating the cause. |

## Red Flags — STOP Immediately

If you catch yourself thinking any of these, STOP and return to Phase 1:

- "Let me just try..."
- "This should fix it"
- "I don't need to reproduce it"
- "The error message tells me everything"
- "I'll skip the investigation for this one"
- "This is different because..."

## Step 1: Initialize Debug Session

Determine from `$ARGUMENTS` and conversation whether to start a new session or resume:

**If `$ARGUMENTS` references a `.plans/debug/` state file:** Resume mode (Step 1b).
**Otherwise:** New session.

### New Session

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
STATE_ROOT="$REPO_ROOT/.plans/debug"
mkdir -p "$STATE_ROOT"

# Verify .plans/ is in global gitignore (core.excludesFile) — do NOT modify the repo's .gitignore
GLOBAL_IGNORE=$(git config --global core.excludesFile 2>/dev/null)
if [ -z "$GLOBAL_IGNORE" ] || ! grep -q "^\.plans/$" "$GLOBAL_IGNORE" 2>/dev/null; then
  echo "WARNING: .plans/ is not in your global gitignore. Add it to avoid committing state files."
  echo "Run: echo '.plans/' >> $(git config --global core.excludesFile || echo '~/.gitignore') && git config --global core.excludesFile $(git config --global core.excludesFile || echo '~/.gitignore')"
fi
```

Generate a session ID: `<timestamp>-<slug>` (slug from the bug description, kebab-case, max 30 chars).

Format all Markdown written to state files with semantic line breaks: one sentence per line, break after clause-separating punctuation (commas, semicolons, colons). Target 120 characters per line.

Create `$STATE_ROOT/<session-id>/DEBUG.md`:

```markdown
---
session_id: <session-id>
status: investigating
phase: REPRODUCE
created: <ISO timestamp>
last_updated: <ISO timestamp>
---

# Debug Session: <brief description>

## Bug Report
<user's description, error messages, and context>

## Reproduction
- [ ] Reproduced consistently
- Reproduction steps: <pending>
- Environment: <pending>

## Investigation Log
<!-- Append-only log of what you tried and learned -->

## Hypotheses
<!-- Numbered hypotheses with status: UNTESTED, CONFIRMED, REJECTED -->

## Root Cause
<pending — do NOT fill until Phase 2 completes>

## Fix Applied
<pending — do NOT fill until Phase 3 completes>

## Verification
<pending — do NOT fill until Phase 4 completes>
```

### Resume (Step 1b)

Read the state file. Parse `phase` from frontmatter. Route to the appropriate phase. Read the Investigation Log to restore context.

## Step 2: Phase 1 — Reproduce and Investigate

**Goal:** Consistent reproduction and root cause identification. NO fixes allowed in this phase.

### 2a: Read Error Messages Carefully

Read the full error output — stack traces, warnings, and surrounding log lines. Do not skip past warnings.

### 2b: Reproduce Consistently

Before any investigation, reproduce the bug:

1. Run the failing command or test exactly as reported.
2. Capture the full output.
3. If it fails intermittently (flaky), run 3-5 times and note the pattern.

**If you cannot reproduce:** Log this in the Investigation Log and explore recent changes (Step 2c) to understand what changed.

Update the Reproduction section with exact steps and output.

### 2c: Check Recent Changes

```bash
git log --oneline -20
git diff HEAD~5 --stat
```

Look for changes in the area where the bug manifests. This often reveals the introducing commit.

For deeper bisection:

```bash
git bisect start
git bisect bad HEAD
git bisect good <known-good-commit>
# Then run the reproduction command at each bisect step
```

### 2d: Gather Evidence

Dispatch the `explorer` agent to map the relevant code area:

```
Task(
  subagent = "explorer",
  description = "Explore bug area: <brief description>",
  prompt = "
  <bug_context>
  <error message, stack trace, and reproduction steps>
  </bug_context>

  <role>
  You are a read-only codebase exploration agent investigating a bug.
  </role>

  <task>
  Map the code path where this bug occurs. Produce a Codebase Map focused on:
  1. The exact call chain from entry point to error location
  2. Data flow through the failing path — what values are passed at each step
  3. Related test files and their coverage of this path
  4. Recent changes to files in this path (check git log for each file)
  5. Similar working code paths for comparison

  Trace BACKWARD from the error: start at the symptom, find the immediate cause,
  then trace up the call chain until you find the original trigger.
  </task>

  <constraints>
  - Every finding must cite file:line
  - Separate observations (what you saw) from hypotheses (what you infer)
  - Focus only on the bug-relevant code path
  </constraints>"
)
```

If the bug involves external APIs, libraries, or unfamiliar patterns, also dispatch the `researcher`:

```
Task(
  subagent = "researcher",
  description = "Research: <library/API involved>",
  prompt = "
  <bug_context>
  <error message and relevant code snippets>
  </bug_context>

  <role>
  You are a research agent investigating a bug involving external dependencies.
  </role>

  <task>
  Research the specific behavior causing this bug:
  1. Search for known issues, breaking changes, or behavioral quirks
  2. Check library documentation for the specific API/method involved
  3. Search for similar bug reports or Stack Overflow discussions
  4. Identify version-specific behavior differences

  Cite every finding with its source.
  </task>"
)
```

### 2e: Root Cause Tracing

Apply backward tracing through the call chain. For detailed technique, see [references/root-cause-tracing.md](references/root-cause-tracing.md).

The sequence:
1. **Observe the symptom** — Document what manifests.
2. **Find immediate cause** — Which code directly produces the error.
3. **Trace one level up** — What called that code? What values were passed?
4. **Keep tracing** — Continue up the call chain, examining values at each level.
5. **Find original trigger** — Where the invalid state originated.

At each level, verify values by reading the actual code — do not infer.

### 2f: Form and Test Hypotheses

State your theory: "I think X is root cause because Y" (cite evidence).

Add each hypothesis to the Hypotheses section:

```markdown
## Hypotheses
1. [UNTESTED] The empty string passed as `cwd` causes git init in the wrong directory
   - Evidence: `src/manager.ts:42` receives `projectDir` which is `''`
   - Test: Add logging before git init to confirm value
```

Test hypotheses one at a time. Update status to CONFIRMED or REJECTED with evidence.

### 2g: Update State

Update `DEBUG.md`:
- Set `phase: ROOT_CAUSE_FOUND` (or `phase: INVESTIGATING` if not yet found)
- Fill in the Root Cause section with the confirmed hypothesis
- Log all investigation steps in the Investigation Log

**Do NOT proceed to Phase 2 until root cause is confirmed with evidence.**

## Step 3: Phase 2 — Pattern Analysis

**Goal:** Understand the fix context before writing code.

1. **Find similar working code** in the codebase — use Glob and Grep to locate analogous patterns that work correctly.
2. **Compare working vs broken** — Identify all differences between the working and failing code paths.
3. **Check for wider impact** — Does this root cause affect other code paths? Search for the same pattern elsewhere.
4. **Understand dependencies** — What else depends on the code you'll change?

Log findings in the Investigation Log.

## Step 4: Phase 3 — Fix Implementation

**Goal:** Minimal, targeted fix addressing the root cause.

### 4a: Write Failing Test First

Create a test that reproduces the bug:

1. Write a test that triggers the exact bug condition.
2. Run it — verify it FAILS for the expected reason.
3. This test proves the fix works when it passes.

**If a test cannot be written** (environment-specific, race condition): Document why in the Investigation Log and describe the manual verification method.

### 4b: Implement Single Fix

Fix the root cause — not the symptom. Change one thing at a time.

Dispatch a fresh `implementer` if the fix requires significant code changes:

```
Task(
  subagent = "implementer",
  description = "Fix bug: <brief description>",
  prompt = "
  <root_cause>
  <confirmed root cause with evidence>
  </root_cause>

  <fix_approach>
  <specific fix to implement — what to change and why>
  </fix_approach>

  <context>
  <relevant code paths, working analogies, and constraints from investigation>
  </context>

  <role>
  You are an implementation agent fixing a specific, investigated bug.
  </role>

  <task>
  Implement the fix described in <fix_approach>. Follow TDD:
  1. The failing test already exists (or write one first)
  2. Implement the minimal fix to make the test pass
  3. Verify all existing tests still pass
  4. Commit via /atcommit skill
  </task>

  <constraints>
  - Fix ONLY the root cause — no refactoring, no improvements, no cleanup
  - One logical change only
  - Do not change code outside the bug-relevant path
  </constraints>"
)
```

### 4c: Add Defense-in-Depth

After the primary fix, add validation at intermediate layers to prevent regression. See [references/defense-in-depth.md](references/defense-in-depth.md).

The four layers:
1. **Entry point validation** — Reject invalid input at API boundaries
2. **Business logic validation** — Check preconditions in internal functions
3. **Environment guards** — Prevent dangerous operations in specific contexts
4. **Debug instrumentation** — Log forensic context for future investigation

Add only layers that are proportional to the bug's severity. A typo fix does not need four layers of defense.

## Step 5: Phase 4 — Verification

**Goal:** Prove the fix works and nothing else broke.

1. **Run the failing test** — Verify it now PASSES.
2. **Run the full test suite** — Verify no regressions.
3. **Reproduce the original scenario** — Verify the original bug report scenario is resolved.
4. **Check edge cases** — Run related tests or manually verify adjacent scenarios.

Update `DEBUG.md`:
- Set `phase: VERIFIED`
- Fill in the Verification section with commands and output
- Set `status: resolved`

### Failure Protocol

If the fix doesn't work:
- **Attempt < 3:** Return to Phase 1 (Step 2). The root cause analysis was incomplete.
- **Attempt >= 3:** Question the architecture. The bug may be structural — escalate to the user.

Log each attempt in the Investigation Log.

## Step 6: Report

Present a debug summary:

```markdown
## Debug Summary

**Bug:** <one-line description>
**Root Cause:** <one-line explanation>
**Fix:** <one-line description of the change>
**Verification:** <test names and results>
**Defense layers added:** <list or "none — proportional to severity">
**Session file:** <path to DEBUG.md>
```

## Error Handling

| Error | Action |
|-------|--------|
| Cannot reproduce the bug | Log reproduction attempts. Check environment differences. Ask user for more context. |
| Root cause unclear after full investigation | Log all findings. Present hypotheses to user. Ask for domain knowledge. |
| Fix introduces new test failures | Revert the fix. Return to Phase 2 — the pattern analysis missed a dependency. |
| Fix attempt >= 3 fails | Stop. Present all investigation findings. Recommend architectural review. |
| State file not found during resume | List existing debug sessions or start fresh. |
| Flaky test (intermittent failure) | Run 10+ times. Check for shared state, timing dependencies, or resource contention. |
