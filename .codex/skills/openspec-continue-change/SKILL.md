---
name: "openspec-continue-change"
description: "Use when the user wants an existing OpenSpec change to create exactly one next ready artifact and then stop. Triggers: \"openspec continue\", \"opsx continue\", \"next OpenSpec artifact\", \"one artifact at a time\". Do not use for implementation or generating every remaining artifact."
---

# OpenSpec Continue Change

Announce: "I'm using the openspec-continue-change skill to create the next OpenSpec artifact."

Create exactly one ready artifact from the active schema graph.

## Step 1: Select the Change and Planning Root

Parse the user's invocation prompt for a change and optional store.
When a store is named, resolve it with `openspec store list --json` and carry `--store "<id>"`.

If no change is clear, run `openspec list --json [--store "<id>"]`.
Ask the user to choose from the three or four most recent changes; do not guess.

## Step 2: Inspect the Live Graph

Run:

```bash
openspec status --change "<name>" --json [--store "<id>"]
```

Use `schemaName`, `planningHome`, `changeRoot`, `artifactPaths`, `actionContext`, and artifact states.
If `isComplete` is true, report completion and suggest `/openspec-apply-change`.
Respect allowed edit roots and affected-area constraints.

## Step 3: Create One Ready Artifact

Select the first `ready` artifact in status order and run:

```bash
openspec instructions <artifact-id> --change "<name>" --json [--store "<id>"]
```

Then:

1. Re-read every concrete returned dependency path from disk; resolve relative paths against `changeRoot` and use status `existingOutputPaths` for glob dependencies.
2. Apply `context` and `rules` as constraints, not content.
3. Fill the returned template according to `instruction`.
4. Write to `resolvedOutputPath`; if it is a glob, choose one concrete path using the schema instruction.
5. Verify the file exists.

Stop after this single artifact even if more are now ready.

## Step 4: Report Progress

Run `openspec status --change "<name>" [--store "<id>"]`.
Report the artifact created, schema, progress, newly unlocked artifacts, and the next valid workflow.

## Error Handling

| Failure | Resolution |
|-|-|
| Multiple changes match | Ask the user to select one. |
| Store id is unknown | Show registered stores and ask for a valid id. |
| All artifacts are complete | Make no writes and suggest apply or archive. |
| No artifact is ready | Report blocked artifacts and dependencies. |
| Output path is a glob | Choose one concrete path from schema guidance. |
| Context is decision-critical | Ask one focused question before writing. |
| Write is outside action context | Stop and report the allowed roots. |
