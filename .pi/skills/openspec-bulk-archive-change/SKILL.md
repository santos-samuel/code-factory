---
name: "openspec-bulk-archive-change"
description: "Use when the user wants to archive several active OpenSpec changes together. Triggers: \"openspec bulk archive\", \"opsx bulk-archive\", \"archive multiple OpenSpec changes\", \"batch archive changes\"."
---

# OpenSpec Bulk Archive Change

Announce: "I'm using the openspec-bulk-archive-change skill to archive multiple OpenSpec changes."

Preflight a selected batch, then archive each change through the CLI with isolated outcomes.

## Step 1: Select Changes and Planning Root

Parse `$ARGUMENTS` for change names, optional store, and explicit flags.
Resolve named stores with `openspec store list --json` and carry `--store "<id>"`.

Run `openspec list --json [--store "<id>"]`.
If names were not supplied, ask the user to select one or more active changes.
Never select all changes implicitly.

## Step 2: Preflight Every Change

For each selected change, run:

```bash
openspec status --change "<name>" --json [--store "<id>"]
openspec instructions apply --change "<name>" --json [--store "<id>"]
openspec validate "<name>" --strict [--store "<id>"]
```

Record schema, planning paths, artifact completion (treat `status: "skipped"` artifacts as satisfied via `skip_specs`), task completion, validation, and delta capabilities.
Use each selected entry's `lastModified` from the Step 1 `openspec list --json` output.
Do not archive any change during preflight.

## Step 3: Detect Ordering and Conflicts

Map each capability to selected changes whose delta specs touch it.
For overlapping capabilities, order those changes by `lastModified` ascending and label that ordering as the available chronology heuristic.
Use the user's listed order for unrelated changes.

Do not guess how to merge conflicting deltas manually.
The CLI remains authoritative and may reject a later archive if the main spec no longer satisfies its delta.

## Step 4: Confirm the Batch

Show one summary with readiness, incomplete work, validation failures, overlapping capabilities, execution order, and explicit flags.
Ask for one confirmation covering the exact batch.
Offer to exclude incomplete or invalid changes.

## Step 5: Archive Independently

After confirmation, run each change in order:

```bash
openspec archive "<name>" --json --yes [--store "<id>"] [--skip-specs]
```

Use `--yes` because the exact batch was confirmed.
Do not pass `--skip-specs` unless the user requested it.
If one change fails, leave it active, record the error, and continue with later changes whose preflight remains valid.
Never use manual file moves.

## Step 6: Report Every Outcome

Report successful archive paths and spec results, skipped changes, failed active changes, overlap ordering, and warnings.

## Error Handling

| Failure | Resolution |
|-|-|
| No active changes exist | Report the no-op. |
| Store id is unknown | Show registered stores and ask for a valid id. |
| Selection is empty | Stop without archiving. |
| Incomplete or invalid changes exist | Exclude them or require explicit confirmation. |
| Overlapping deltas conflict | Let the CLI fail that item; do not invent a merge. |
| One archive fails | Keep it active, record the failure, and continue safely. |
| User cancels | Archive nothing. |
