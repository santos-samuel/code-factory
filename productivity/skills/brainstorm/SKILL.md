---
name: brainstorm
description: >
  Use when the user wants to brainstorm an idea, explore a problem space,
  think through a project proposal, or develop an idea before implementing.
  Triggers: "brainstorm", "I have an idea", "let me think through",
  "explore this idea", "what if we", "is this worth building",
  "new project idea", "problem statement".
argument-hint: "[idea description or path to existing brainstorm]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(date:*), Bash(mkdir:*), Task, AskUserQuestion
---

# Brainstorm

Announce: "I'm using the /brainstorm skill to explore and sharpen this idea."

## Step 1: Initialize

```bash
TODAY=$(date +%Y-%m-%d)
```

```bash
mkdir -p ~/docs/brainstorms
```

## Step 2: Determine Mode

Parse `$ARGUMENTS` to determine new vs resume:

| Signal | Mode |
|--------|------|
| Path to existing `~/docs/brainstorms/*.md` file | **Resume** — load and continue |
| Short name matching an existing brainstorm file | **Resume** — find and continue |
| Idea description (free text) | **New** — create brainstorm file |
| No arguments | **List** — show existing brainstorms and ask what to do |

### List mode

```bash
ls -1t ~/docs/brainstorms/*.md 2>/dev/null
```

For each file, read the frontmatter to extract `status` and the `# Title`.
Present as a table and ask whether to resume one or start a new brainstorm.

## Step 3: Create or Load Brainstorm File

### New brainstorm

Derive a slug from the idea description (kebab-case, max 40 chars).

Create `~/docs/brainstorms/<slug>.md`:

```markdown
---
date_created: <TODAY>
date_modified: <TODAY>
status: draft
tags: []
---

# <Title derived from idea>

## Overview

<Initial idea description — reframed around the problem, not the solution>

## Problem Statement

<To be sharpened through brainstorming>

## Evidence

<Concrete data supporting the problem — to be gathered>

## Stakeholders

<Who is affected — to be identified>

## Parked Solution Ideas

- <Solutions mentioned during brainstorming>

## Challenge Log

### Session: <TODAY>
```

Tell the user the file path.

### Resume

Read the existing brainstorm file.
Pass the full content to the brainstormer agent for continuation.

## Step 4: Dispatch Brainstormer

Dispatch the brainstormer agent to drive the conversation:

```
Task(
  subagent_type = "productivity:brainstormer",
  description = "<new|resume> brainstorm: <slug>",
  prompt = "
<brainstorm_file>
<path>~/docs/brainstorms/<slug>.md</path>
<content>
<full file content>
</content>
</brainstorm_file>

<idea>
<the user's idea description, or 'resume' if continuing>
</idea>

<today><TODAY></today>

<task>
<For new>: Start a new brainstorm. The file has been created with the initial idea.
Analyze whether the idea is problem-shaped or solution-shaped, then begin the diagnostic progression.
Ask one question at a time. Update the brainstorm file after each exchange.
<For resume>: Resume an existing brainstorm. Read the file, summarize where things stand,
and continue from where the last session left off.
</task>
"
)
```

## Step 5: Report

After the brainstormer agent completes, read the brainstorm file and report:

| Field | Value |
|-------|-------|
| **File** | `~/docs/brainstorms/<slug>.md` |
| **Status** | `draft` / `developing` / `sharp` / `parked` |
| **Problem sharp?** | Yes/No (apply the Sharp Problem Test) |
| **Next steps** | Suggested actions based on status |

Suggested next steps by status:

| Status | Suggestion |
|--------|-----------|
| `draft` | "Run `/brainstorm <slug>` to continue sharpening." |
| `developing` | "Run `/brainstorm <slug>` to continue. Focus on: <open question>." |
| `sharp` | "Problem is well-defined. Ready for `/do` or `/rfc`." |
| `parked` | "Brainstorm is parked. Resume anytime with `/brainstorm <slug>`." |

## Error Handling

| Error | Action |
|-------|--------|
| `~/docs/brainstorms/` not writable | Report error and exit |
| No arguments and no existing brainstorms | Ask for an idea description |
| Slug conflicts with existing file | Append a number suffix (e.g., `my-idea-2.md`) |
| Brainstormer agent fails | Save current file state, report error, suggest manual resume |
| User wants to stop mid-conversation | Update file with current state, set status to `developing` or `parked` |
