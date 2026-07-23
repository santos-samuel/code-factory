# Resource Efficiency

Use these rules to keep `/do` proportional to the feature while preserving lifecycle gates.

## Core Principle

A phase is an evidence gate, not necessarily a new agent dispatch.
Reuse trustworthy work already present in the conversation or state artifacts.
Dispatch another agent only when the existing evidence cannot satisfy the phase exit criteria.

## Prepared-Context Reuse

Classify the invocation before dispatching REFINE, RESEARCH, or PLAN_DRAFT.

| Existing evidence | Reuse |
|-|-|
| Explicitly approved goal, scope, behavior, and binary acceptance criteria | Satisfy REFINE from context |
| Repository citations plus relevant authoritative external evidence | Satisfy RESEARCH from context |
| Explicitly approved implementation plan with files, dependencies, and validation | Satisfy PLAN_DRAFT from context |

For each reused phase:

1. Write the normal state artifact in compact form.
2. Verify every normal exit criterion.
3. Record `source: "reused_context"` in FEATURE.md phase history.
   Append the normal `PHASE_END` event.
4. Advance through the phase normally.

When RESEARCH is reused, synthesize the required compact `CONVENTIONS.md`
from cited repository evidence. If that is not possible, dispatch only the missing local-evidence work.
In interactive mode, do not ask the user to approve an artifact they explicitly approved in the prepared context.

Do not reuse claims that are stale, uncited, contradictory, or missing a material decision.
Run targeted verification for questionable claims instead of repeating the whole phase.

## Context Capsules

Pass file paths and a compact capsule instead of copying complete artifacts through multiple prompts.

| Payload | Limit | Contents |
|-|-|-|
| Phase capsule | 1,200 words | Goal, settled decisions, open risks, artifact paths |
| Milestone capsule | 1,000 words | Task IDs, dependencies, changed behavior, active risks |
| Task bundle | 120 lines or 3,000 tokens | Contract, files, commands, task-specific conventions |
| SNAPSHOT.md | 80 lines or 1,500 tokens | Current state and next action only |
| Event tail | 5 events | State changes since the last checkpoint |

Task bundles already include relevant conventions.
Do not also inline full `CONVENTIONS.md`, `PLAN.md`, `RESEARCH.md`, or `FEATURE.md`.
For validation, pass the base ref and changed-file list; the validator reads the diff from the worktree.

## Review Budget

Reviews are cumulative, not additive.
Each new review must cover a distinct risk or replace an earlier layer.

| Task risk | Per-task external review budget | Routing |
|-|-|-|
| Low | 0 | Implementer self-review plus deterministic checks |
| Medium | 2 maximum; pass 2 only after rejection | One task-critic plus its focused recheck |
| High | 2 total | Task-critic, then a distinct red team only for trust, concurrency, security, or destructive-data risk |

If a critic rejects, reuse that critic for a focused recheck of the proven findings.
Do not restart a full escalating review from round one.
When the recheck consumes a high-risk task's second review slot, defer red-team coverage to the integrated review.

Run an integrated Codex or independent review when a coherent user-visible behavior slice is complete.
Record `reviewed_head`.
Do not review every supporting milestone independently.
At VALIDATE, reuse an integrated review when `HEAD == reviewed_head`;
run another branch review only when code changed afterward or validation exposed a new material risk.

Maintain one implementation-review ledger in FEATURE.md with reviewer, scope, `HEAD`, risk covered,
verdict, and pass count. Every task critic, red team, integrated review, validation review,
and PR-fix review consults it first. Do not review the same scope and unchanged `HEAD`
unless a prior finding is being focusedly rechecked.

## Completion-Driven Waiting

Waiting is not a reasoning task.

1. Use the runtime's completion notification or longest permitted blocking wait.
2. After a timeout, check status once.
3. If the agent or command is active, wait again without redispatching or rereading artifacts.
4. Treat elapsed time alone as insufficient evidence of a stall.
5. Declare a stall only after two consecutive status checks show no progress and no active tool or turn.
6. Confirm the original worker stopped before spawning a replacement.

Do not send follow-ups that only ask for status.
Send a follow-up when it contains new evidence, a corrected constraint, or a concrete unblock.

## Telemetry

Record runtime-provided metrics without inventing precision:

- input tokens
- cached input tokens
- output tokens
- reasoning output tokens
- total tokens
- tool calls
- wait calls
- spawned agents
- duration
- model
- reasoning effort
- cost only when the runtime supplies it or an explicitly configured rate identifies its source

Label each metric `measured`, `derived`, or `lower_bound` in `metric_provenance`.
Omit unavailable metrics instead of reporting zero.
Set `cost_usd: null` and `cost_source: "unknown"` when cost cannot be established.
Never convert an undifferentiated token count into dollars with an unrelated model rate.

## Escalation Signals

Pause and reassess resource routing when any signal fires:

| Signal | Action |
|-|-|
| Actual tokens exceed 2× the PLAN_DRAFT estimate | Stop before the next task and revise the execution/review budget |
| More than two review passes for one task | Escalate the unresolved finding; do not add another reviewer |
| More than two replacement dispatches in one phase | Mark the phase blocked and report the harness failure |
| Wait calls exceed productive tool calls in a phase | Switch to completion-driven waiting before continuing |
| The same full artifact appears in two nested prompts | Replace the copy with a path and capsule |
