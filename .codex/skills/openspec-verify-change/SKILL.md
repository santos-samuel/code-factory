---
name: "openspec-verify-change"
description: "Use whenever the user wants a read-only evidence audit that checked OpenSpec tasks, implementation code, and tests match proposal/spec/design artifacts before archive, even if they say \"audit evidence\" instead of \"verify\". Choose this over explore for implementation-to-artifact checks. Triggers: \"openspec verify\", \"opsx verify\", \"check implementation against spec\". Never use for artifact syntax/structure validation alone or for fixing findings."
---

# OpenSpec Verify Change

Announce: "I'm using the openspec-verify-change skill to verify implementation against OpenSpec artifacts."

Verify with repository evidence without changing code, artifacts, tasks, specs, or archive state.

## Step 1: Select the Change and Planning Root

Parse the user's invocation prompt for a change and optional store.
Resolve named stores with `openspec store list --json` and carry `--store "<id>"`.

If no change is clear, run `openspec list --json [--store "<id>"]`.
Ask the user to choose a change that has implementation tasks.

## Step 2: Load and Validate Artifacts

Run:

```bash
openspec status --change "<name>" --json [--store "<id>"]
openspec instructions apply --change "<name>" --json [--store "<id>"]
openspec validate "<name>" --strict [--store "<id>"]
```

Read every concrete path in `contextFiles`.
Use planning paths and action context to identify the implementation root.
Do not treat structural validation as implementation verification.

## Step 3: Verify Completeness

Check:

- Every task checkbox and claimed completion.
- Every delta requirement has implementation evidence.
- Expected implementation, tests, documentation, and migrations exist.

An unchecked task is CRITICAL.
A checked task without evidence is CRITICAL and must cite the task plus inspected paths.

## Step 4: Verify Correctness

For every requirement and scenario:

1. Map it to implementation files and line references.
2. Map it to focused tests or executable validation.
3. Run relevant non-mutating checks when feasible.
4. Compare observed behavior with the requirement's intent.

Missing implementation is CRITICAL.
Behavioral divergence or uncovered scenarios are WARNING unless evidence proves the requirement is absent.
Do not infer correctness from keyword matches alone.

## Step 5: Verify Coherence

Compare implementation with recorded design decisions and established repository patterns.
Flag design contradictions as WARNING with file/line evidence.
Flag optional pattern improvements as SUGGESTION.
When design or specs are absent, record which checks were skipped instead of inventing expectations.

## Step 6: Report the Assessment

Report three dimensions:

- Completeness: tasks and requirement coverage.
- Correctness: implementation and scenario evidence.
- Coherence: design and repository-pattern alignment.

Group findings as CRITICAL, WARNING, and SUGGESTION.
Every finding needs an actionable recommendation and evidence.
If any CRITICAL issue exists, state that the change is not ready to archive.
Make no fixes from this skill.

## Error Handling

| Failure | Resolution |
|-|-|
| Multiple changes match | Ask the user to select one. |
| Store id is unknown | Show registered stores and ask for a valid id. |
| Structural validation fails | Report it as CRITICAL and continue only with checks still grounded in valid files. |
| Only tasks exist | Verify task evidence and report skipped spec/design checks. |
| Tests cannot run | Report the command failure and lower confidence; do not claim success. |
| Evidence is ambiguous | Downgrade severity and state the uncertainty. |
| A fix is requested | Route implementation to `/openspec-apply-change`. |
