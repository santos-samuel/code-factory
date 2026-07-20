---
name: openspec-onboard
description: >
  Use when the user wants a guided first OpenSpec workflow on a real small
  codebase change. Triggers: "openspec onboard", "opsx onboard", "teach me
  OpenSpec", "OpenSpec tutorial".
argument-hint: "[optional task] [--store <id>]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, AskUserQuestion
---

# OpenSpec Onboard

Announce: "I'm using the openspec-onboard skill to guide a complete OpenSpec workflow."

Teach one real, small change through exploration, artifacts, implementation, verification, and archive.

## Step 1: Run Preflight

Run `openspec --version`.
If missing, stop and tell the user to run this repository's `./init.sh` or install `@fission-ai/openspec`.

Resolve an optional named store with `openspec store list --json`.
Carry `--store "<id>"` on supported OpenSpec commands.
Never reuse an unrelated active change for the tutorial.

## Step 2: Load the Tutorial Flow

Read [references/tutorial-flow.md](references/tutorial-flow.md) completely.
Follow its `EXPLAIN → DO → SHOW → PAUSE` checkpoints.
Use a real task selected from the repository or supplied by the user.

## Step 3: Keep the Tutorial Resumable

After creating the change, retain its name, store, schema, and `changeRoot` in every progress summary.
At each pause, state the completed phase and exact next command.
When resuming, run status and re-read artifacts from disk rather than reconstructing prior state from conversation memory.

## Step 4: Use the Local Workflow Contracts

Match the behavior of:

- `/openspec-explore` for read-only discovery.
- `/openspec-new-change` and `/openspec-continue-change` for artifact teaching.
- `/openspec-apply-change` for implementation.
- `/openspec-verify-change` before archive.
- `/openspec-archive-change` for CLI-driven finalization.

Do not use manual spec merges or file moves.

## Step 5: Recap

Summarize the completed cycle, artifact locations, implementation validation, archive result, and commands for future independent use.

## Error Handling

| Failure | Resolution |
|-|-|
| CLI is missing | Stop before repository changes and provide installation guidance. |
| Store id is unknown | Show registered stores and ask for a valid id. |
| Suggested task is too large | Offer a smaller slice while allowing the user to override. |
| User pauses | Report the change, phase, status command, and next workflow. |
| Existing change name conflicts | Choose another tutorial name; do not overwrite. |
| Verification finds critical issues | Return to apply; do not archive. |
| User cancels archive | Leave the completed active change intact. |
