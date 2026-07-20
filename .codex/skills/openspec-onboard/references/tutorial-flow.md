# OpenSpec Onboarding Flow

Use this teaching flow for a real change.
Keep explanations short and pause only at the marked checkpoints.

## Phase 1: Welcome and Task Selection

Explain that the tutorial covers one complete cycle:

1. Explore a small problem.
2. Create a change.
3. Write proposal, specs, design, and tasks.
4. Implement and verify.
5. Archive through the CLI.

Search for small opportunities such as TODOs, missing tests, swallowed errors, debug artifacts, or missing input validation.
Present three grounded suggestions with locations and estimated scope, plus the user's own option.
Prefer work that fits one or two files and a focused test.

If the selected task is large, recommend the smallest useful slice and let the user decide.

## Phase 2: Explore

Read the relevant code and explain the current behavior, constraint, and likely change.
Do not edit files.

PAUSE for acknowledgment before creating a change.

## Phase 3: Create the Change

Derive a kebab-case name and run:

```bash
openspec new change "<name>" [--store "<id>"]
openspec status --change "<name>" --json [--store "<id>"]
```

Explain the returned schema and artifact graph.
Use `changeRoot` and `actionContext`; do not present assumed paths.

## Phase 4: Proposal

Run:

```bash
openspec instructions proposal --change "<name>" --json [--store "<id>"]
```

Draft the proposal from the returned template and explain that it captures why and what.
Show the draft before writing.

PAUSE for approval, then write it to the resolved output path.

## Phase 5: Specs

Re-run status, select the next ready artifact, and fetch its instructions.
Re-read proposal content from disk.
Draft precise requirements and WHEN/THEN scenarios.
For glob output, choose concrete capability paths using the schema instruction.
Explain that scenarios provide testable behavior, then write the approved content.

## Phase 6: Design

Re-run status and instructions.
Re-read dependencies from disk.
Record context, goals, non-goals, decisions, alternatives, and risks proportionate to the task.
Explain that design captures how and why technical choices were made.

## Phase 7: Tasks

Re-run status and instructions.
Re-read proposal, specs, and design from disk.
Create small ordered checkboxes including focused validation.

PAUSE before implementation.

## Phase 8: Apply

Run:

```bash
openspec instructions apply --change "<name>" --json [--store "<id>"]
```

Read every `contextFiles` path.
For each task:

1. Announce it.
2. Implement the smallest scoped change.
3. Run focused validation.
4. Check it off only after validation passes.

Keep narration focused on how artifacts informed the work.

## Phase 9: Verify

Validate artifact structure:

```bash
openspec validate "<name>" --strict [--store "<id>"]
```

Then verify completeness, correctness, and coherence using file/line and test evidence.
If critical issues remain, return to implementation and re-verify.

PAUSE before archive.

## Phase 10: Archive

Run the OpenSpec CLI archive command.
Do not move files manually:

```bash
openspec archive "<name>" --json [--store "<id>"]
```

Show the archive path and spec merge result from CLI output.
If the user cancels, leave the change active.

## Phase 11: Recap

Explain the rhythm:

- `/openspec-explore`: investigate without implementation.
- `/openspec-propose`: create a complete proposal quickly.
- `/openspec-new-change`: create a scaffold.
- `/openspec-continue-change`: create one artifact.
- `/openspec-ff-change`: generate all apply-required artifacts.
- `/openspec-update-change`: reconcile existing artifacts.
- `/openspec-apply-change`: implement tasks.
- `/openspec-sync-specs`: merge deltas without archive.
- `/openspec-verify-change`: check implementation evidence.
- `/openspec-archive-change`: finalize one change.
- `/openspec-bulk-archive-change`: finalize a selected batch.
- `/openspec-onboard`: repeat this guided tutorial.

## Graceful Exit

When the user stops, report:

- Change name, store, schema, and `changeRoot`.
- Completed phase.
- `openspec status --change "<name>" [--store "<id>"]`.
- `/openspec-continue-change <name> [--store <id>]` or `/openspec-apply-change <name> [--store <id>]` as the next action.

Never pressure the user to continue.
