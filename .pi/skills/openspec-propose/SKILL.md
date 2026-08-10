---
name: "openspec-propose"
description: "Use when the user wants to create a complete OpenSpec proposal from a feature, fix, or change description. Triggers: \"openspec propose\", \"opsx propose\", \"create OpenSpec change\", \"spec-driven proposal\"."
---

# OpenSpec Propose

Announce: "I'm using the openspec-propose skill to create a complete OpenSpec proposal."

Create a change and every artifact required before implementation.

**Planning boundary**: This workflow creates planning artifacts only. The request that selected or triggered it authorizes planning only, even if it asks to build or fix something. Do not edit project code. After the planning artifacts are complete, stop. Do not start implementation in the same response, even if the initial request asks for it. Wait for a new user request after the artifacts are presented; then start `/openspec-apply-change`.

## Step 1: Resolve the Request and Planning Root

Parse `$ARGUMENTS` for a kebab-case change name, feature description, and optional store.
Retrieve answers available from the repository, existing OpenSpec artifacts, history, or supplied references before asking.
Ask one question at a time in architecture, behavior, then polish order.
For minor details, make a reasonable assumption and record it in the planning artifacts; ask only about ambiguities that would materially affect scope, externally observable behavior, compatibility, or acceptance criteria.

When the user names a store, run:

```bash
openspec store list --json
```

Resolve the store id and treat `--store "<id>"` as sticky for every command below that accepts it (`new change`, `status`, `instructions`, `list`, `show`, `validate`, `archive`, `doctor`, `context`, `view`).
Without a store, commands act on the nearest OpenSpec root.

If the selected root already contains the change, inspect it and ask whether to continue or choose another name.
Do not assume `openspec/changes/<name>` is the planning path.

## Step 2: Determine the Schema and Create the Change

Use the configured default schema unless the user explicitly requests another.
If the user asks to see workflows, resolve the authoritative root first:

```bash
openspec context --json [--store "<id>"]
```

Then run `openspec schemas --json` with its working directory set to the returned `root.path` and let the user choose (`schemas` does not accept `--store`; it follows the working directory, which preserves roots selected by a local `store:` pointer or the global `defaultStore`). If context reports `no_openspec_root`, run `openspec schemas --json` from the current working directory instead.

Create and inspect the change:

```bash
openspec new change "<name>" [--schema "<schema>"] [--store "<id>"]
openspec status --change "<name>" --json [--store "<id>"]
```

Use the JSON fields as the source of truth:

- `schemaName` and `applyRequires`
- artifact `status`, `requires` edges, and the `skipped` flag
- `planningHome`, `changeRoot`, `artifactPaths`, and `actionContext`

Respect `actionContext.allowedEditRoots` and any affected-area requirement before writing.

## Step 3: Generate the Full Required Artifact Set

Track artifact progress with `TodoWrite`.
The required set is `applyRequires` plus every artifact reachable from those by following the `requires` edges in `status --json` — walk them transitively (spec-driven closes over proposal, specs, design, tasks). `status` is file-existence only, so a `done` artifact does not imply its dependencies exist; use `requires` edges, not `status`, to build the set.

Loop until every artifact in the required set is `done` or `skipped`:

1. Select the next `ready` artifact from the live status graph.
2. Run `openspec instructions <artifact-id> --change "<name>" --json [--store "<id>"]`.
3. Re-read every dependency path returned by the instructions from disk, even if it appeared earlier in the conversation.
4. Follow the returned `instruction`, `template`, `context`, and `rules`. If the `instruction` field delegates creation to a specific skill or command, invoke it to produce the artifact instead of writing the file yourself, then verify the file exists at `resolvedOutputPath`.
5. Write to the returned `resolvedOutputPath`; when it is a glob, choose a concrete path using the schema instruction.
6. Verify the file exists, then re-run status before selecting the next artifact.

Treat `context` and `rules` as authoring constraints, never as artifact content.
An artifact reading `status: "skipped"` is satisfied: the change declares `skip_specs` in `.openspec.yaml`, so its files must not exist — never try to create one. Skip a conditional artifact only when its own `instruction` marks it optional (e.g., spec-driven's `design.md`); tell the user and do not reconsider. Dependencies are enablers, not gates: if a required artifact is still `blocked` only because you skipped a conditional dependency, write it anyway.
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
Report the change name, resolved location, schema, artifacts created (plus any conditional artifact skipped and why), validation, and readiness for `/openspec-apply-change`.

## Error Handling

| Failure | Resolution |
|-|-|
| `openspec` is missing | Tell the user to run this repository's `./init.sh` or install `@fission-ai/openspec`. |
| Store id is unknown | Show `openspec store list --json` results and ask for a valid store. |
| Existing change name conflicts | Inspect the existing change and ask whether to continue or rename. |
| Schema is unknown | Resolve the root with `openspec context --json`, then show `openspec schemas --json` and ask for a valid schema. |
| Artifact instructions are blocked | Report missing dependencies and create those first. |
| An artifact is `skipped` | Honor `skip_specs`; never create its files. |
| `instruction` delegates to a skill/command | Invoke it to produce the artifact, then verify the file exists. |
| Output path is a glob | Use the schema instruction to choose a concrete file; never write to the glob string. |
| Action context disallows a write | Stop and report the allowed roots or required area selection. |
| Context remains decision-critical | Ask one focused question before writing the affected artifact. |
| Validation fails | Fix the affected artifact and re-run strict validation. |
