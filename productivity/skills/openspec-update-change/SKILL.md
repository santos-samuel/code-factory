---
name: openspec-update-change
description: >
  Use when the user wants to revise, refine, reconcile, or audit the coherence
  of existing OpenSpec planning artifacts or acceptance criteria without
  creating missing artifacts or editing implementation code. Triggers:
  "openspec update change", "opsx update", "revise OpenSpec plan", "audit
  proposal design specs tasks". Do not use to generate all remaining artifacts.
argument-hint: "[change name] [revision] [--store <id>]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(openspec:*), AskUserQuestion
---

# OpenSpec Update Change

Announce: "I'm using the openspec-update-change skill to reconcile existing OpenSpec artifacts."

Revise existing planning artifacts and keep them coherent without creating new artifacts or editing code.

## Step 1: Select the Change and Planning Root

Parse `$ARGUMENTS` for a change, requested revision, and optional store.
Resolve named stores with `openspec store list --json` and carry `--store "<id>"`.

If no change is clear, run `openspec list --json [--store "<id>"]` and ask the user to choose.
Do not confuse this workflow with CLI `openspec update`, which regenerates assistant instruction files.

## Step 2: Inventory Existing Artifacts

Run:

```bash
openspec status --change "<name>" --json [--store "<id>"]
```

Use the schema graph, planning paths, and action context.
The only writable files are concrete paths in `artifactPaths.<id>.existingOutputPaths`.
Never write to a glob `resolvedOutputPath`.
Do not create missing artifacts or new files under a glob artifact.

## Step 3: Build a Coherence Revision

Read every existing artifact from disk.
If the user specified a revision, start there.
Otherwise audit for contradictions, stale decisions, requirement gaps, task drift, and duplication.

Propagate implications in any direction; build order does not prevent an earlier artifact from changing after a later one.
For missing artifacts or files, record the need and defer creation to `/openspec-continue-change`.
If the artifacts are coherent, make no edits.

## Step 4: Confirm and Apply Per Artifact

For each affected artifact:

1. Show the proposed revision and rationale.
2. Obtain confirmation.
3. For a substantial rewrite, run `openspec instructions <artifact-id> --change "<name>" --json [--store "<id>"]`.
4. Re-read the artifact and dependencies from disk.
5. Edit only its concrete existing paths.
6. Re-read the result before proposing the next artifact.

Never edit implementation code.
If the revision changes the change's core intent, recommend a new change instead.

## Step 5: Validate and Report

Run:

```bash
openspec validate "<name>" --strict [--store "<id>"]
openspec status --change "<name>" [--store "<id>"]
```

Report revised and rejected artifacts, deferred missing artifacts, validation, current status, and the recommended next workflow.

## Error Handling

| Failure | Resolution |
|-|-|
| Multiple changes match | Ask the user to select one. |
| Store id is unknown | Show registered stores and ask for a valid id. |
| Requested file does not exist | Defer it to `/openspec-continue-change`; do not create it here. |
| Output path is a glob | Edit only its `existingOutputPaths`. |
| Revision implies code changes | Record planning changes, then suggest `/openspec-apply-change`. |
| Revision changes core intent | Recommend `/openspec-new-change`. |
| Validation fails | Keep artifacts unreported as complete until coherence is restored. |
