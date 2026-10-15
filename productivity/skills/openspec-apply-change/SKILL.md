---
name: openspec-apply-change
description: >
  Use when the user wants to implement or continue implementation of an
  OpenSpec change. Triggers: "openspec apply", "opsx apply", "implement
  OpenSpec change", "continue OpenSpec tasks".
argument-hint: "[change name] [--store <id>]"
user-invocable: true
allowed-tools: Read, Write, Edit, MultiEdit, Glob, Grep, Bash, TodoWrite, AskUserQuestion, Task
---

# OpenSpec Apply Change

Announce: "I'm using the openspec-apply-change skill to implement an OpenSpec change."

Implement pending tasks while keeping canonical artifacts and task state accurate.

## Step 1: Select the Change and Planning Root

Parse `$ARGUMENTS` for a change and optional store.
When a store is named, run `openspec store list --json`, resolve the id, and carry `--store "<id>"` on OpenSpec commands.

If no change is provided, infer it only from clear conversation context.
Otherwise run `openspec list --json [--store "<id>"]`.
Auto-select only when exactly one active change exists; ask when several remain.
Announce `Using change: <name>` before reading artifacts.

## Step 2: Load Live OpenSpec Context

Run:

```bash
openspec status --change "<name>" --json [--store "<id>"]
openspec instructions apply --change "<name>" --json [--store "<id>"]
```

Use status for `schemaName`, `planningHome`, `changeRoot`, `artifactPaths`, and `actionContext`.
Use apply instructions for `contextFiles`, progress, task state, and dynamic instructions.
Respect allowed edit roots and affected-area constraints.

If apply state is `blocked`, report missing artifacts and suggest `/openspec-continue-change`.
If state is `all_done`, report completion and suggest `/openspec-verify-change`.

## Step 3: Read Required Files

Read every concrete path in `contextFiles` from disk.
Create a checklist from the pending tasks while preserving their wording.
Re-read affected context files after user edits, artifact changes, or any deviation before continuing.

## Step 4: Implement Pending Tasks

Work through tasks in dependency order:

1. State the task.
2. Make the smallest scoped implementation change.
3. Run focused validation for that task.
4. Mark its checkbox complete only after validation passes.
5. Continue until complete or blocked.

When evidence contradicts an artifact, classify the deviation:

- **Reversible and behavior-preserving:** update every affected canonical artifact with evidence and rationale, record the focused validation command and result in the affected task or design artifact, re-read changed artifacts, then continue.
- **Behavior-changing, irreversible, or scope-expanding:** stop safely and request user direction without changing disputed artifacts or completion markers.

Do not create a separate implementation-notes file.

## Step 5: Validate and Report

Run the focused project checks required by completed tasks.
Run `openspec validate "<name>" --strict [--store "<id>"]` when artifact content changed.

Report:

- Change and schema.
- Tasks completed this session and overall progress.
- Validation commands and results.
- Canonical deviations recorded.
- Remaining blocker, if any.

When all tasks are complete, recommend `/openspec-verify-change`.

## Error Handling

| Failure | Resolution |
|-|-|
| No change can be selected | List active changes and ask the user to choose. |
| Store id is unknown | Show registered stores and ask for a valid id. |
| Apply instructions are blocked | Report missing artifacts and stop before implementation. |
| Action context disallows an edit | Stop and report the permitted roots or required selection. |
| Reversible deviation appears | Update canonical artifacts, validate, re-read, and continue. |
| Behavior or scope would change | Stop at a safe checkpoint and request direction. |
| Validation fails | Fix the failure before checking off the task. |
| User interrupts | Leave task checkboxes accurate and report current progress. |
