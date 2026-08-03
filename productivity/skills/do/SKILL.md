---
name: do
description: >
  Use when the user wants to implement, build, fix, or deliver a code change
  from an approved idea or plan through a pull request. Triggers: "do",
  "implement the plan", "build this", "fix this", "create feature",
  "ship this", "resume feature work", or references to `/do` state files.
argument-hint: "[feature description] [--fast|--deep] [--interactive] [--branch|--workspace] [--token-budget <tokens>]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task, Skill, AskUserQuestion, WebFetch, WebSearch
---

# Adaptive Code Delivery

Announce: "I'm using `/do` to implement and deliver this change with a risk-sized workflow."

## Step 1: Ground the Run

Read the repository instructions and inspect the current git state before changing files.

Parse these flags:

| Flag | Meaning |
|-|-|
| `--fast` | Use one implementation leaf and skip optional research leaves |
| `--deep` | Allow bounded leaf agents for high-risk or independent workstreams |
| `--interactive` | Pause for user decisions and approval at material checkpoints |
| `--auto` | Backward-compatible alias for autonomous execution |
| `--branch` | Create or reuse a local feature branch without a separate worktree |
| `--workspace` | Create a remote workspace and start this `/do` run there |
| `--token-budget <tokens>` | Advisory stop threshold for measured completed-delegate tokens |
| `--budget <USD>` | Legacy budget; enforce only when the runtime supplies an exact cost source |

`--branch` and `--workspace` are mutually exclusive. If both are present, ask the user to
choose one. Otherwise evaluate repository state in this order; the first matching row wins:

| Repository state | Action |
|-|-|
| Unrelated dirty changes | Stop and ask how to isolate the work |
| `--workspace` | Follow the remote handoff below; do not create a local branch, worktree, or state |
| Existing `/do` state explicitly referenced | Resume it after reconciling state with git |
| Resume or status intent without a state path | Discover matching state; never start a new run |
| Dedicated worktree or non-default feature branch | Reuse it |
| `--branch` on a clean default branch | Create a feature branch in the current checkout; do not create a worktree |
| Clean default branch | Create an isolated worktree and feature branch |

For bare resume or status intent, scan `~/docs/plans/do/*/FEATURE.md` and match the recorded
repository, branch, and status against git. Resume the single match. If several match, ask the
user to choose; if none match, report that no resumable run exists. Never interpret a failed
resume lookup as a request to initialize a new run.

For `--workspace`:

1. Preserve the complete feature request and applicable profile, interaction, and advisory-budget flags.
2. Derive a short workspace slug and delegate once to
   `/workspace create <slug> --claude-prompt <opaque-prompt>`.
3. Set the opaque prompt to invoke `/do` with the preserved feature request and `--branch` in
   the remote checkout. Omit `--workspace` so the handoff cannot recurse.
4. Wait for `/workspace` to confirm that the detached remote session started, then report its
   join command and stop the local run. If remote startup is not confirmed, report a blocker;
   never claim that implementation is running.

Never write state into the repository.
State lives under `~/docs/plans/do/<short-name>/`.

## Step 2: Select One Execution Profile

Choose one profile automatically and report it in one line.
Profiles are alternatives, never additive lifecycle layers.

| Profile | Use when | Work leaves |
|-|-|-|
| **Fast** | Goal, acceptance criteria, and approach are settled; one coherent behavior slice; no material unknown | One implementation leaf |
| **Standard** | One or more local evidence or design gaps remain, or the change crosses a moderate subsystem boundary | One research leaf and one implementation leaf |
| **Deep** | Explicit `--deep`; auth/security; concurrency; destructive migration; multi-repository delivery; or at least three independent workstreams | Up to three bounded research or implementation leaves |

The independent final reviewer in Step 6 is required for every profile and is separate from these
optional research or implementation leaves.

`--fast` skips optional research delegation but never skips evidence, tests, implementation delegation, review, or delivery.
If a safety-critical fact is missing, stop for that fact instead of silently escalating or guessing.

All delegated agents are leaves:

- They receive one bounded question or disjoint file ownership.
- They may not spawn agents, manage lifecycle state, commit, push, or poll.
- Their final response stays under 2,000 characters and lists outcomes, not process.
- Maximum delegation depth is one.

The top agent is the sole owner of decisions, state, planning, integration, validation, remediation, and delivery.
Never dispatch an orchestrator, phase controller, milestone controller, bundle generator,
validation controller, delivery controller, or memory extractor.

### Advisory Token Accounting

`--token-budget` is not a whole-session hard ceiling. Runtime interfaces do not expose a
portable exact total for the top agent, tools, active delegates, and future work. Count only exact
cumulative token totals reported by completed delegated agents. Before starting another optional
leaf or separable task, sum those completed-delegate totals; if the measured sum is at or above the
threshold, stop and report the measured scope and excluded unknown usage. Never estimate missing
usage or claim the total run stayed below the threshold. A run with no delegates has a measured
completed-delegate total of zero.

## Step 3: Initialize or Resume State

Read [references/artifacts.md](references/artifacts.md) before creating or updating run artifacts.

Create artifacts as their evidence gate is reached.
Before delivery, ensure the completed run contains:

- `FEATURE.md`
- `RESEARCH.md`
- `CONVENTIONS.md`
- `PLAN.md`
- `REVIEW.md`
- `VALIDATION.md`
- `SNAPSHOT.md`
- `events.jsonl`
- compact `tasks/TASK-*.md` files when the plan has separable tasks

If a gate reused approved context and produced no unique evidence,
create its artifact with the required headings and one line identifying the reused source.

The top agent writes every artifact.
No artifact exists to feed another controller.

Append events only for:

- `SESSION_START`
- `PROFILE_SELECTED`
- `DECISION`
- `IMPLEMENTATION_COMPLETE`
- `REVIEW_COMPLETE`
- `VALIDATION_COMPLETE`
- `DELIVERY_COMPLETE`
- `BLOCKED`

Do not log individual tools, waits, status requests, or commentary updates.
Pass paths and a short risk/task capsule to leaf agents; never inline complete artifacts.

On resume:

1. Read `FEATURE.md` frontmatter and `SNAPSHOT.md`.
2. Compare recorded branch, commits, and task status with git.
3. Correct stale state from repository truth.
4. Continue from the first unmet acceptance criterion.

## Step 4: Satisfy Evidence Gates in the Top Agent

Treat lifecycle phases as checks, not agent dispatches:

1. **Refine:** Verify the goal, audience, scope, constraints, and binary acceptance criteria.
2. **Research:** Inspect only code, documentation, history, or external facts needed by the plan.
3. **Plan:** Record the chosen approach, affected subsystems, task order, risks, and validation commands.

Reuse approved conversation evidence.
Do not re-ask approved decisions or repeat repository research.

In Fast mode, keep the plan short and proceed as soon as the checks above are satisfied.
In Standard mode, use the optional research leaf for one concrete evidence gap only.
In Deep mode, parallelize independent research or implementation only when file ownership is disjoint.

Interactive mode pauses only for a material product or architecture choice.
Autonomous mode resolves ordinary implementation choices from repository evidence.
Both modes stop for missing authority, destructive scope expansion, or an unresolved safety decision.

## Step 5: Implement and Validate

Delegate the initial implementation to the named `implementer` agent in every profile.
Fast and Standard use exactly one implementation leaf. Deep may use multiple implementation
leaves only when their file ownership is disjoint. Tell every implementer that:

- the top agent retains commit ownership;
- other work may be happening and unrelated edits must be preserved;
- it must implement the approved plan, run focused checks, and return outcomes under 2,000 characters.

For behavior changes:

1. Add or update a focused regression test.
2. Run it and confirm the expected failure.
3. Implement the minimum coherent fix.
4. Run the focused test and nearby regression suite.

The required order is RED test → implementation → GREEN test → stabilized full validation
→ final review → commits → push/PR → one status fetch.

For refactors, configuration, generated code, or documentation,
use the repository's most relevant deterministic verification instead of forcing artificial TDD.

Validation is proportional:

- Run focused checks while editing.
- Run repository-mandated validation once after the diff stabilizes.
- Re-run only checks affected by a subsequent fix.
- Do not run a full baseline before every task or milestone.
- Never delete, disable, or skip a failing test to proceed.

Record unrelated findings in the `FEATURE.md` discovered-work section.
Create a separate discovery task only when the finding blocks or materially affects delivery.
Do not expand the current change automatically.

### Waiting Discipline

Work on independent local checks while a leaf agent is active.
Then use the runtime's completion notification or longest permitted completion wait.

After a timeout:

1. Check status once.
2. If progress is visible, issue at most one further completion wait.
3. If completion still cannot be observed, report the worker as a blocker.

Never send status-only follow-ups, repeatedly call agent-listing tools, or spawn a replacement
until the original worker is confirmed stopped.

## Step 6: Run One Final Review

After deterministic checks pass, dispatch exactly one independent whole-diff reviewer using the
named `task-critic` agent.

Give the reviewer:

- acceptance criteria
- base and head refs
- changed-file list or diff
- named high-risk areas
- exact validation evidence

Do not provide implementation reasoning, full research history, or previous reviewer chains.
The reviewer checks specification compliance, correctness, maintainability, tests, and named risks together.

If the reviewer accepts, record the result in `REVIEW.md`.
If it proves actionable findings:

1. The top agent fixes only the proven findings.
2. Re-run affected checks.
3. Ask the same reviewer for one focused recheck.

A second rejection blocks delivery.
Do not spawn a new critic, red team, spec reviewer, code-quality reviewer, or rescue agent.

## Step 7: Deliver the Pull Request

After review and validation pass:

1. Inspect the final diff for unintended files, debug code, secrets, and generated-file drift.
2. Organize the change into the minimum logical commits without dispatching a commit agent.
3. Follow repository instructions for commit signing and the approved push command.
4. Create or update the intended pull request.
5. Fetch CI and review status once.
6. Update `VALIDATION.md`, `FEATURE.md`, `SNAPSHOT.md`, and `events.jsonl`.
7. Report the PR, commits, checks, known pending status, and artifact path.

Do not poll CI, wait for review bots, invoke `/pr-fix`, or apply new review feedback unless the user asks.

## Step 8: Report Status Without Resuming

For a status request, read `FEATURE.md`, `SNAPSHOT.md`, and git directly.
Report current profile, completed work, tests, blocker, next action, and PR state.
Do not spawn an agent or mutate code/state.

## Error Handling

| Error | Action |
|-|-|
| Goal or acceptance criteria remain ambiguous | Ask the smallest material question before editing |
| Referenced state does not match git | Trust git, repair state, and record one `DECISION` event |
| Worker times out while active | Follow Waiting Discipline; do not replace it based on elapsed time |
| Worker stops without a usable result | Continue in the top agent or dispatch one replacement within the same profile budget |
| Focused test fails for an unrelated reason | Diagnose, record it as discovered work, and keep scope explicit |
| Final validation fails | Fix the failure and re-run affected checks before review or delivery |
| Reviewer rejects twice | Mark `BLOCKED` and report the remaining proven findings |
| Commit signing fails | Preserve staging and ask the user to restore signing; never bypass it silently |
| Push or PR operation fails | Preserve local commits and report the exact recovery command |
| Measured completed-delegate tokens reach the advisory threshold | Stop before the next optional leaf/task and report the measured total, excluded usage, completed work, and smallest continuation |
