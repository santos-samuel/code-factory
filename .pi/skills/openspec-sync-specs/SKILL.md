---
name: "openspec-sync-specs"
description: "Use whenever the user wants to merge or apply an OpenSpec change's delta specs, capability deltas, or ADDED/MODIFIED/REMOVED/RENAMED requirements into canonical/main specs while leaving the change active or skipping archive. Choose this over apply, update-change, or ff for spec-content merges. Triggers: \"openspec sync\", \"opsx sync\", \"apply delta requirements\", \"update main specs\". Never use for CLI `openspec update` or generated assistant files."
---

# OpenSpec Sync Specs

Announce: "I'm using the openspec-sync-specs skill to merge delta specs into main specs."

Apply delta intent to main specs while leaving the change active.

## Step 1: Select the Change and Planning Root

Parse `$ARGUMENTS` for a change and optional store.
Resolve named stores with `openspec store list --json` and carry `--store "<id>"`.

If no change is clear, run `openspec list --json [--store "<id>"]`.
Ask the user to select a change that has delta specs.

## Step 2: Resolve Delta and Main Spec Paths

Run:

```bash
openspec status --change "<name>" --json [--store "<id>"]
```

Use `artifactPaths.specs.existingOutputPaths` as the delta file list.
Use `<planningHome.root>/openspec/specs/<capability>/spec.md` for each main spec.
Derive the capability from the delta's path below the change's `specs/` directory.
Do not assume the current repository owns either path.

If no delta specs exist, report that nothing can be synced and stop.

## Step 3: Preview the Merge

Read every delta and corresponding main spec from disk.
Build a preview grouped by capability:

- ADDED requirements or scenarios.
- MODIFIED requirements or scenarios.
- REMOVED requirements.
- RENAMED requirements.

Preserve main-spec content not addressed by the delta.
Treat an already-applied ADDED requirement as an update, so a second run produces no duplicate.
If a delta is ambiguous or conflicts with current main-spec intent, ask before editing that capability.

## Step 4: Apply Delta Intent

For each capability:

1. Apply renames before other operations.
2. Remove explicitly removed requirements.
3. Merge modifications at requirement and scenario level.
4. Add missing requirements and scenarios.
5. Create a missing main spec only when the delta adds that capability.
6. Re-read the result and confirm the intended requirements appear once.

Do not archive or modify change artifacts.

## Step 5: Validate and Report

Run:

```bash
openspec validate "<name>" --strict [--store "<id>"]
openspec validate --specs --strict [--store "<id>"]
```

Report capabilities changed, requirement operations, validation results, and that the change remains active.
If the preview was already fully applied, report a no-op.

## Error Handling

| Failure | Resolution |
|-|-|
| Multiple changes match | Ask the user to select one. |
| Store id is unknown | Show registered stores and ask for a valid id. |
| No delta specs exist | Make no edits and report the no-op. |
| Main spec path cannot be derived | Stop rather than writing to a guessed path. |
| Delta conflicts with main intent | Ask for a capability-specific decision. |
| Validation fails | Restore coherence before reporting success. |
