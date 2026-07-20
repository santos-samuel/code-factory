---
name: "openspec-explore"
description: "Use when the user wants to investigate an idea, problem, or existing OpenSpec change without implementing. Triggers: \"openspec explore\", \"opsx explore\", \"think through OpenSpec\", \"inspect OpenSpec change\"."
---

# OpenSpec Explore

Announce: "I'm using the openspec-explore skill to explore OpenSpec context without implementing."

Explore ideas and artifacts without changing code or files.

## Step 1: Resolve Context

Run `openspec list --json` in the nearest root.
When the user names a store, run `openspec store list --json`, resolve the id, and repeat list/status/show commands with `--store "<id>"`.

If a change is relevant, run:

```bash
openspec status --change "<name>" --json [--store "<id>"]
```

Use `changeRoot`, `artifactPaths.<id>.existingOutputPaths`, and `actionContext` rather than hardcoded repository paths.
Re-read relevant existing artifacts from their reported concrete paths.

## Step 2: Explore Without Implementing

Search the repository, inspect history, compare artifacts, and ask questions that materially change the direction.
Do not edit code or artifacts, mark tasks complete, sync specs, or archive changes.
When the user requests implementation, route to `/openspec-apply-change`.
When the user requests a new complete proposal, route to `/openspec-propose`.
When the user requests artifact reconciliation, route to `/openspec-update-change`.

Run a blindspot pass when missing context could change scope, architecture, behavior, or review strategy.
Report only consequential findings:

1. Landmines with evidence.
2. Hidden constraints already encoded in the repository or artifacts.
3. Quality examples that calibrate the target.
4. High-impact questions, with provisional answers when evidence supports them.
5. A revised request or decision summary.

If no consequential blindspots exist, state `No significant blindspots found`.

## Step 3: Analyze References by Semantics

For supplied code, documentation, or another implementation, report:

- Behaviors and guarantees.
- Deliberate decisions and supporting evidence.
- Incidental framework or repository details.
- Native equivalents under this repository's conventions.
- Translation gaps.
- Reference license and whether text may be reused.

Use behavioral semantics rather than transliterating source.
If the license is unclear, do not copy implementation text.

## Step 4: Offer the Correct Capture Path

Exploration is read-only.
When a decision should be recorded, identify the affected existing artifact and suggest `/openspec-update-change`.
When an artifact does not exist, suggest `/openspec-continue-change`.
Do not write it from this skill.

## Step 5: Summarize

Summarize the current OpenSpec state, relevant artifacts, options and trade-offs, unresolved questions, and recommended next skill.

## Error Handling

| Failure | Resolution |
|-|-|
| `openspec` is missing | Continue with repository inspection and tell the user to run `./init.sh`. |
| Store id is unknown | Show registered stores and ask for a valid id. |
| No OpenSpec root exists | Explore normally and suggest `/openspec-propose` when ready. |
| Multiple changes match | Ask which change to inspect. |
| Reference is unavailable | Separate verified facts from assumptions and request it only when decision-critical. |
| Reference license is unclear | Limit the result to behavioral analysis and do not copy text. |
| Evidence is insufficient | Label the point as an open question or omit it. |
