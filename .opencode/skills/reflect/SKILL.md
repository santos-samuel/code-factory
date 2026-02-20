---
name: reflect
description: >
  Use when the user wants to capture session learnings and update knowledge files,
  review pending learnings from previous sessions, or manually trigger a session reflection.
  Triggers: "reflect", "capture learnings", "update agents.md", "review pending learnings",
  "what did we learn", or at session end via Stop hook.
argument-hint: "[--review to process pending learnings]"
user-invocable: true
---

# Session Reflection

Announce: "I'm using the /reflect skill to capture session learnings and update knowledge files."

## Overview

Extracts actionable knowledge from the current session — conventions, corrections, patterns, and gotchas — and updates the repo's knowledge files. Uses confidence-based routing: high-confidence learnings are auto-applied, medium-confidence ones are queued for human review.

### Knowledge File Targets

| File | Scope | What belongs |
|------|-------|-------------|
| `AGENTS.md` | Repo-wide, all agents | Conventions, workflow rules, structural patterns |
| `MEMORY.md` | Personal, per-project | Debugging insights, tool tips, personal preferences |
| `CLAUDE.md` | Project-wide, all agents | Boundary rules, project-specific instructions (rare) |

### Confidence Thresholds

| Level | Score | Criteria | Action |
|-------|-------|----------|--------|
| High | ≥ 0.8 | User corrections, explicit conventions, repeated patterns | Auto-apply |
| Medium | 0.5–0.79 | Implicit preferences, single-occurrence patterns | Queue for review |
| Low | < 0.5 | One-off context, ambiguous signals | Discard |

## Step 1: Determine Mode

Parse `$ARGUMENTS` to select mode:

| Arguments | Mode |
|-----------|------|
| `--review` | **Review mode** — process pending learnings queue |
| Anything else or empty | **Extract mode** — analyze current session |

## Step 2A: Extract Mode (default)

### 2A.1: Locate Knowledge Files

```
REPO_ROOT = git rev-parse --show-toplevel
AGENTS_MD = $REPO_ROOT/AGENTS.md
CLAUDE_MD = $REPO_ROOT/CLAUDE.md
MEMORY_MD = ~/.claude/projects/<project>/memory/MEMORY.md
PENDING_FILE = ~/.claude/projects/<project>/pending-learnings.md
```

Read all three knowledge files to understand current content.

### 2A.2: Analyze Session

Review the conversation history for learning signals. Look for:

**Correction signals** (confidence ≥ 0.85):
- User says "no", "wrong", "instead use", "actually", "don't do that"
- User corrects agent behavior or output
- User repeats an instruction the agent missed

**Convention signals** (confidence ≥ 0.8):
- User says "always", "never", "make sure to", "remember to"
- Explicit rules stated during the session
- Workflow requirements discovered

**Pattern signals** (confidence 0.6–0.8):
- Same approach used 3+ times
- User consistently prefers one approach over another
- Recurring code patterns or tool usage

**Gotcha signals** (confidence 0.5–0.7):
- Unexpected errors and their solutions
- Non-obvious requirements discovered during work
- Tool quirks or workarounds found

**Discovery signals** (confidence 0.5–0.7):
- "Found that...", "turns out...", "the trick is..."
- New tool usage or flag discovery
- Performance insights

### 2A.3: Deduplicate

For each extracted learning, search the knowledge files using Grep:
- If the learning (or its semantic equivalent) already exists → skip
- If it refines an existing entry → note for update (not addition)

### 2A.4: Route by Confidence

**High confidence (≥ 0.8):**

Apply directly to the target knowledge file:
1. Identify the correct section in the target file (or create a new section if needed)
2. Append the learning as a concise imperative bullet point
3. Use the Edit tool — never restructure or reorganize the file
4. Report: "Auto-applied: [learning] → [file]:[section]"

**Medium confidence (0.5–0.79):**

Queue for human review:
1. Append to `$PENDING_FILE` in this format:

```markdown
## Pending Learning — [date]

- **Learning**: [concise imperative bullet]
- **Confidence**: [score]
- **Target**: [AGENTS.md|MEMORY.md|CLAUDE.md]
- **Section**: [target section name]
- **Evidence**: [brief quote or reference from session]
- **Category**: [correction|convention|pattern|gotcha|discovery]

---
```

2. Report: "Queued for review: [learning] (confidence: [score])"

**Low confidence (< 0.5):**

Discard silently. Do not report discarded learnings unless the user explicitly asks.

### 2A.5: Summary

Present a summary table:

```markdown
## Session Reflection Summary

### Auto-Applied
| Learning | Target | Section |
|----------|--------|---------|
| ... | ... | ... |

### Queued for Review
| Learning | Confidence | Target |
|----------|-----------|--------|
| ... | ... | ... |

### Stats
- Signals analyzed: N
- Auto-applied: N
- Queued: N
- Duplicates skipped: N
- Discarded (low confidence): N
```

## Step 2B: Review Mode (`--review`)

### 2B.1: Load Pending Learnings

Read `$PENDING_FILE`. If it doesn't exist or is empty:
- Report: "No pending learnings to review."
- Exit.

### 2B.2: Present for Review

For each pending learning, present it to the user with `AskUserQuestion`:

```
AskUserQuestion(
  header: "Learning",
  question: "[learning text]\nConfidence: [score] | Target: [file] | Evidence: [evidence]",
  options: [
    "Apply" — Add this learning to the target file,
    "Edit" — Modify before applying,
    "Skip" — Keep in queue for later,
    "Reject" — Remove from queue permanently
  ]
)
```

### 2B.3: Process Decisions

| Decision | Action |
|----------|--------|
| Apply | Edit the target file to append the learning, then remove from queue |
| Edit | Ask user for revised text, then apply the revision and remove from queue |
| Skip | Leave in queue, move to next |
| Reject | Remove from queue, move to next |

### 2B.4: Cleanup

After processing all items:
- Rewrite `$PENDING_FILE` with only skipped items
- If no items remain, delete the file
- Report summary: N applied, N skipped, N rejected

## Error Handling

| Error | Action |
|-------|--------|
| Knowledge file not found | Create it with a header section, then proceed |
| Pending file not found (review mode) | Report "No pending learnings" and exit |
| Edit conflict (content changed since read) | Re-read the file and retry the edit once |
| No learnings extracted | Report "No actionable learnings found in this session" |
| Permission denied on file write | Report the error and queue the learning to pending instead |
