---
name: "openspec-ff-change"
description: "Use when an OpenSpec request says every/all remaining artifacts, apply-ready/readiness, no one-by-one approval, or proposal/specs/design/tasks in one pass, whether creating or resuming a local or store-scoped change. Always choose this over new, continue, or propose for that all-artifacts intent. Triggers: \"openspec ff\", \"opsx ff\", \"fast-forward OpenSpec\", \"finish all applyRequires\". Do not use for one artifact, implementation, or spec sync."
---

# OpenSpec Fast-Forward Change

Announce: "I'm using the openspec-ff-change skill to fast-forward OpenSpec artifact creation."

Resume or create a change, then generate all artifacts required for implementation.

## Step 1: Resolve or Create the Change

Parse `$ARGUMENTS` for a change name or description, optional schema, and optional store.
When a store is named, resolve it with `openspec store list --json` and carry `--store "<id>"`.

Run `openspec list --json [--store "<id>"]`.
If the exact change exists, resume it without overwriting completed artifacts.
If it does not exist, derive a kebab-case name and run:

```bash
openspec new change "<name>" [--schema "<schema>"] [--store "<id>"]
```

## Step 2: Load the Artifact Graph

Run:

```bash
openspec status --change "<name>" --json [--store "<id>"]
```

Use the live schema, `applyRequires`, artifact states, planning paths, and action context.
Do not assume proposal/spec/design/task identifiers.

## Step 3: Generate All Apply-Required Artifacts

Track progress with `TodoWrite`.
Until every `applyRequires` artifact is `done`:

1. Select the next `ready` artifact in status order.
2. Run `openspec instructions <artifact-id> --change "<name>" --json [--store "<id>"]`.
3. Re-read all concrete dependency paths from disk; resolve relative paths against `changeRoot` and use status `existingOutputPaths` for glob dependencies.
4. Follow the returned instruction and template.
5. Write to the resolved output; choose concrete paths for glob artifacts using schema guidance.
6. Verify the output exists and re-run status.

Ask one focused question only when missing context would materially change the artifact.
Do not implement tasks.

## Step 4: Report Readiness

Run:

```bash
openspec validate "<name>" --strict [--store "<id>"]
openspec status --change "<name>" [--store "<id>"]
```

Fix validation failures before reporting created and pre-existing artifacts, schema, resolved location, and readiness for `/openspec-apply-change`.

## Error Handling

| Failure | Resolution |
|-|-|
| Input is unclear | Ask what change the user wants to create or resume. |
| Store id is unknown | Show registered stores and ask for a valid id. |
| Schema is unknown | Show `openspec schemas --json` and ask for a valid schema. |
| Existing change has incompatible intent | Stop and ask for a different name. |
| Artifact graph is blocked | Report missing dependencies and stop. |
| Output path is a glob | Choose a concrete path from schema guidance. |
| Action context disallows a write | Stop and report the permitted roots. |
| Artifact validation fails | Fix that artifact before continuing. |
