---
name: "openspec-archive-change"
description: "Use when the user wants to finalize and archive one OpenSpec change. Triggers: \"openspec archive\", \"opsx archive\", \"archive OpenSpec change\", \"finalize OpenSpec change\"."
---

# OpenSpec Archive Change

Announce: "I'm using the openspec-archive-change skill to archive an OpenSpec change."

Archive through the OpenSpec CLI so validation, spec merging, and paths remain authoritative.

## Step 1: Select the Change and Planning Root

Parse `$ARGUMENTS` for a change, store, and explicit archive flags.
When a store is named, run `openspec store list --json`, resolve the id, and carry `--store "<id>"`.

If no change is provided, run:

```bash
openspec list --json [--store "<id>"]
```

Ask the user to choose from active changes.
Do not guess when multiple changes exist.

## Step 2: Check Readiness

Run:

```bash
openspec status --change "<name>" --json [--store "<id>"]
openspec instructions apply --change "<name>" --json [--store "<id>"]
```

Use `planningHome`, `changeRoot`, `artifactPaths`, and `actionContext` for reporting.
List artifacts that are neither `done` nor `skipped` (a `skipped` artifact is satisfied — the change declares `skip_specs` in `.openspec.yaml`) and any incomplete tasks.
If work is incomplete, ask for confirmation before proceeding.

Unless the user explicitly passed `--no-validate`, run:

```bash
openspec validate "<name>" --strict [--store "<id>"]
```

Stop on validation failure.

## Step 3: Archive with the CLI

Run:

```bash
openspec archive "<name>" --json [--store "<id>"] [--yes] [--skip-specs] [--no-validate]
```

Pass only flags the user supplied.
Use `--yes` only after explicit non-interactive authorization.
The CLI owns spec merging and the archive move; do not reproduce either with manual file edits or `mv`.

## Step 4: Report the Outcome

Report the schema, archive path, spec merge or skip result, validation state, and warnings returned by the CLI.
If archiving fails, confirm the active change remains at `changeRoot`.

## Error Handling

| Failure | Resolution |
|-|-|
| Multiple changes exist | Ask the user to choose before archiving. |
| Store id is unknown | Show registered stores and ask for a valid id. |
| Incomplete work remains | Warn and require confirmation. |
| An artifact is `skipped` | Treat it as satisfied (`skip_specs`); do not flag it as incomplete. |
| Validation fails | Stop unless the user explicitly requests `--no-validate`. |
| CLI prompts unexpectedly | Pause instead of assuming confirmation. |
| Archive target or spec merge conflicts | Report the CLI error and leave the active change untouched. |
