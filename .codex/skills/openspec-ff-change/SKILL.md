---
name: "openspec-ff-change"
description: "Use when an OpenSpec request says every/all remaining artifacts, apply-ready/readiness, no one-by-one approval, or proposal/specs/design/tasks in one pass, whether creating or resuming a local or store-scoped change. Always choose this over new, continue, or propose for that all-artifacts intent. Triggers: \"openspec ff\", \"opsx ff\", \"fast-forward OpenSpec\", \"finish all applyRequires\". Do not use for one artifact, implementation, or spec sync."
---

# OpenSpec Fast-Forward Change

Announce: "I'm using the openspec-ff-change skill to fast-forward OpenSpec artifact creation."

Resume or create a change, then generate all artifacts required for implementation. This is a planning workflow: do not implement tasks or edit project code.

## Step 1: Resolve or Create the Change

Parse the user's invocation prompt for a change name or description, optional schema, and optional store.
When a store is named, resolve it with `openspec store list --json` and carry `--store "<id>"` as sticky for every command below that accepts it.

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

Use the live schema, `applyRequires`, artifact states and `requires` edges, the `skipped` flag, planning paths, and action context.
Do not assume proposal/spec/design/task identifiers.

## Step 3: Generate the Full Required Artifact Set

Track progress with `TodoWrite`.
The required set is `applyRequires` plus every artifact reachable from those by following the `requires` edges in `status --json` — walk them transitively (spec-driven closes over proposal, specs, design, tasks). `status` is file-existence only, so a `done` artifact does not imply its dependencies exist; use `requires` edges, not `status`, to build the set.

Until every artifact in the required set is `done` or `skipped`:

1. Select the next `ready` artifact in status order.
2. Run `openspec instructions <artifact-id> --change "<name>" --json [--store "<id>"]`.
3. Re-read all concrete dependency paths from disk; resolve relative paths against `changeRoot` and use status `existingOutputPaths` for glob dependencies.
4. Follow the returned `instruction`, `template`, `context`, and `rules`. If the `instruction` field delegates creation to a specific skill or command, invoke it to produce the artifact instead of writing the file yourself, then verify the file exists at `resolvedOutputPath`.
5. Write to the resolved output; choose concrete paths for glob artifacts using schema guidance.
6. Verify the output exists and re-run status.

An artifact reading `status: "skipped"` is satisfied: the change declares `skip_specs` in `.openspec.yaml`, so its files must not exist — never try to create one. Skip a conditional artifact only when its own `instruction` marks it optional (e.g., spec-driven's `design.md`); tell the user and do not reconsider. Dependencies are enablers, not gates: if a required artifact is still `blocked` only because you skipped a conditional dependency, write it anyway.
Treat `context` and `rules` as authoring constraints, never as artifact content.
Ask one focused question only when missing context would materially change the artifact.

## Step 4: Report Readiness

Run:

```bash
openspec validate "<name>" --strict [--store "<id>"]
openspec status --change "<name>" [--store "<id>"]
```

Fix validation failures before reporting created and pre-existing artifacts (plus any conditional artifact skipped and why), schema, resolved location, and readiness for `/openspec-apply-change`.

## Error Handling

| Failure | Resolution |
|-|-|
| Input is unclear | Ask what change the user wants to create or resume. |
| Store id is unknown | Show registered stores and ask for a valid id. |
| Schema is unknown | Show `openspec schemas --json` and ask for a valid schema. |
| Existing change has incompatible intent | Stop and ask for a different name. |
| Artifact graph is blocked | Report missing dependencies and stop. |
| An artifact is `skipped` | Honor `skip_specs`; never create its files. |
| `instruction` delegates to a skill/command | Invoke it to produce the artifact, then verify the file exists. |
| Output path is a glob | Choose a concrete path from schema guidance. |
| Action context disallows a write | Stop and report the permitted roots. |
| Artifact validation fails | Fix that artifact before continuing. |
