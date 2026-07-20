---
name: "openspec-new-change"
description: "Use when the user wants to start only an empty OpenSpec change scaffold and stop before creating any planning artifacts. Triggers: \"openspec new\", \"opsx new\", \"start OpenSpec change\", \"create change scaffold\". Do not use when they want proposal/spec/design/task artifacts or implementation readiness."
---

# OpenSpec New Change

Announce: "I'm using the openspec-new-change skill to start an OpenSpec change scaffold."

Create the change container, show the first artifact instructions, and stop before writing artifacts.

## Step 1: Resolve Input and Planning Root

Parse the user's invocation prompt for a kebab-case name or description, optional schema, and optional store.
Ask what the user wants to build only when the request cannot be inferred.

When a store is named, run `openspec store list --json`, resolve its id, and add `--store "<id>"` to supported commands.
Use the default schema unless the user names another schema.
If the user asks to see workflows, run `openspec schemas --json`.

## Step 2: Check for a Conflict

Run `openspec list --json [--store "<id>"]`.
If the name already exists, suggest `/openspec-continue-change` instead of overwriting it.

## Step 3: Create the Scaffold

Run:

```bash
openspec new change "<name>" [--schema "<schema>"] [--store "<id>"]
openspec status --change "<name>" --json [--store "<id>"]
```

Use the returned `planningHome`, `changeRoot`, `artifactPaths`, `actionContext`, schema, and artifact graph.

## Step 4: Show the First Ready Artifact

Select the first artifact whose status is `ready` and run:

```bash
openspec instructions <artifact-id> --change "<name>" [--store "<id>"]
```

Show its template and current status.
Do not create the artifact.

## Step 5: Stop and Report

Report the change name, resolved location, schema, artifact sequence, progress, and first ready artifact.
Suggest `/openspec-continue-change` for one artifact or `/openspec-ff-change` for all apply-required artifacts.

## Error Handling

| Failure | Resolution |
|-|-|
| Input is unclear | Ask what the user wants to build before creating anything. |
| Name is not kebab-case | Derive a valid name and confirm when the mapping is ambiguous. |
| Store id is unknown | Show registered stores and ask for a valid id. |
| Schema is unknown | Show `openspec schemas --json` and ask for a valid schema. |
| Change already exists | Leave it unchanged and suggest `/openspec-continue-change`. |
| No artifact is ready | Report the status graph and its blockers. |
