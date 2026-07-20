---
name: openspec-propose
description: >
  Use when the user wants to create a complete OpenSpec proposal from a feature,
  fix, or change description. Triggers: "openspec propose", "opsx propose",
  "create OpenSpec change", "spec-driven proposal".
argument-hint: "[change name or feature description] [--store <id>]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(openspec:*), Bash(git log:*), Bash(git show:*), Bash(git blame:*), TodoWrite, AskUserQuestion
---

# OpenSpec Propose

Announce: "I'm using the openspec-propose skill to create a complete OpenSpec proposal."

Create a change and every artifact required before implementation.

## Step 1: Resolve the Request and Planning Root

Parse `$ARGUMENTS` for a kebab-case change name, feature description, and optional store.
Retrieve answers available from the repository, existing OpenSpec artifacts, history, or supplied references before asking.
Ask one question at a time in architecture, behavior, then polish order.

When the user names a store, run:

```bash
openspec store list --json
```

Resolve the store id and add `--store "<id>"` to `new change`, `status`, `instructions`, `list`, and later validation commands.
Without a store, use the nearest OpenSpec root.

If the selected root already contains the change, inspect it and ask whether to continue or choose another name.
Do not assume `openspec/changes/<name>` is the planning path.

## Step 2: Create and Inspect the Change

Run:

```bash
openspec new change "<name>" [--store "<id>"]
openspec status --change "<name>" --json [--store "<id>"]
```

Use the JSON fields as the source of truth:

- `schemaName` and `applyRequires`
- artifact status and dependencies
- `planningHome`, `changeRoot`, `artifactPaths`, and `actionContext`

Respect `actionContext.allowedEditRoots` and any affected-area requirement before writing.

## Step 3: Generate Apply-Required Artifacts

Track artifact progress with `TodoWrite`.
Loop until every artifact in `applyRequires` is `done`:

1. Select the next `ready` artifact from the live status graph.
2. Run `openspec instructions <artifact-id> --change "<name>" --json [--store "<id>"]`.
3. Re-read every dependency path returned by the instructions from disk, even if it appeared earlier in the conversation.
4. Follow the returned `instruction`, `template`, `context`, and `rules`.
5. Write to the returned `resolvedOutputPath`; when it is a glob, choose a concrete path using the schema instruction.
6. Verify the file exists, then re-run status before selecting the next artifact.

Treat `context` and `rules` as authoring constraints, never as artifact content.
If required product or technical context cannot be inferred, ask one focused question and then resume.

## Step 4: Present a Decision-First Review

Re-read the completed artifacts and present:

1. Outcome and chosen approach.
2. Riskiest assumption.
3. Expensive-to-change interfaces, data models, types, and user-visible behavior.
4. One considered alternative for each tweakable decision.
5. Known unknowns with a safe default and pivot signal.
6. A compressed artifact and task summary.

If review feedback changes an artifact, update it and regenerate or reconcile affected downstream artifacts from fresh disk content before declaring readiness.

## Step 5: Verify Readiness

Run:

```bash
openspec validate "<name>" --strict [--store "<id>"]
openspec status --change "<name>" [--store "<id>"]
```

Fix artifact validation failures before reporting readiness.
Report the change name, resolved location, schema, artifacts created, validation, and readiness for `/openspec-apply-change`.

## Error Handling

| Failure | Resolution |
|-|-|
| `openspec` is missing | Tell the user to run this repository's `./init.sh` or install `@fission-ai/openspec`. |
| Store id is unknown | Show `openspec store list --json` results and ask for a valid store. |
| Existing change name conflicts | Inspect the existing change and ask whether to continue or rename. |
| Artifact instructions are blocked | Report missing dependencies and create those first. |
| Output path is a glob | Use the schema instruction to choose a concrete file; never write to the glob string. |
| Action context disallows a write | Stop and report the allowed roots or required area selection. |
| Context remains decision-critical | Ask one focused question before writing the affected artifact. |
| Validation fails | Fix the affected artifact and re-run strict validation. |
