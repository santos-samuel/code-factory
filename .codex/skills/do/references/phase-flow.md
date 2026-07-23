# Phase Flow — Detailed Descriptions

Reference for detailed phase behaviors. Loaded by the orchestrator when executing phases.

## Phase Dispatch Protocol

The SKILL.md outer loop first checks whether approved existing evidence satisfies the phase.
Only unsatisfied phases dispatch a fresh orchestrator.
Dispatches receive artifact paths plus the smallest useful capsule,
following [resource-efficiency.md](resource-efficiency.md).

### Context Payloads (what SKILL.md loads per phase)

| Phase | Capsule and artifact paths | Limit |
|-|-|-|
| REFINE | Feature request, brainstorm/hydrated paths, repo root | 1,200 words |
| RESEARCH | Refined-spec path, known evidence, repo root | 1,200 words |
| PLAN_DRAFT | FEATURE, RESEARCH, and CONVENTIONS paths plus settled decisions | 1,200 words |
| PLAN_REVIEW | PLAN, REVIEW, FEATURE, RESEARCH, and CONVENTIONS paths plus risk classification | 1,200 words |
| BUNDLE_GENERATION | PLAN, RESEARCH, FEATURE, and CONVENTIONS paths | 1,000 words |
| EXECUTE | Milestone capsule, task-bundle paths, SNAPSHOT path, five-event tail | 1,000 words |
| VALIDATE | Criteria/strategy paths, base ref, changed-file list, diff stat | 1,200 words |
| DONE | FEATURE, VALIDATION, and events paths plus outcome capsule | 1,000 words |

Agents read only the sections they need from those paths.
Do not inline the same artifact into nested prompts.

### Prepared-Context Phase Satisfaction

Apply Prepared-Context Reuse from
[resource-efficiency.md](resource-efficiency.md)
before REFINE, RESEARCH, and PLAN_DRAFT.
A reused phase writes its normal artifact and FEATURE.md phase-history entry,
then passes the same return-contract checks as a dispatched phase.
It appends `PHASE_END`.

### Return Contract (what SKILL.md reads after each dispatch)

| Phase | SKILL.md Reads | Decision |
|-|-|-|
| REFINE | FEATURE.md phase_status, phase_terminal_reason | approved → advance; blocked → route by terminal reason |
| RESEARCH | FEATURE.md phase_status, phase_terminal_reason, RESEARCH.md exists | approved → advance; blocked → route by terminal reason |
| PLAN_DRAFT | FEATURE.md phase_status, phase_terminal_reason, PLAN.md exists | approved → advance; blocked → route by terminal reason |
| PLAN_REVIEW | FEATURE.md phase_status, phase_terminal_reason | approved → bundle + EXECUTE; blocked → PLAN_DRAFT (or route per terminal reason) |
| BUNDLE_GENERATION | tasks/ directory populated | verified → EXECUTE |
| EXECUTE (milestone) | FEATURE.md progress, task bundle statuses | all complete → next milestone or VALIDATE |
| VALIDATE | FEATURE.md phase_status, phase_terminal_reason | approved → DONE; blocked → EXECUTE (or route per terminal reason) |
| DONE | FEATURE.md (outcomes, PR URL) | report to user |

### Terminal Reason Routing (blocked phases)

When `phase_status: blocked`, SKILL.md reads `phase_terminal_reason` and chooses the recovery path.
See state-file-schema.md "Phase Status and Terminal Reasons" for the enum semantics.

| `phase_terminal_reason` | SKILL.md action |
|-|-|
| `failed` | Re-dispatch the same phase, passing critic/reviewer feedback as `<state_drift>` context |
| `timed_out` | Re-dispatch the same phase with the original context — no feedback to add |
| `stalled` | Re-dispatch the same phase with the original context — no feedback to add |
| `canceled_by_reconciliation` | Surface the reconciliation `check` and `detail` to the user; do NOT re-dispatch until the underlying drift is resolved |
| `user_blocked` | Halt; resume only when the user issues an explicit instruction |
| `succeeded` | Treat as a writer error — the reason is reserved and must not appear with `phase_status: blocked`. Log and surface for review. |

Loop limits in **Phase Loop Conditions** still apply when re-dispatching after `failed` / `timed_out` / `stalled`.

### Phase Dispatch Protocol (orchestrator responsibilities on return)

Every phase orchestrator MUST, before its dispatch returns:

1. Set `phase_status` in FEATURE.md frontmatter to one of `approved`, `in_review`, or `blocked`.
2. If `phase_status: blocked`, also set `phase_terminal_reason` to a non-null value from the enum
   (state-file-schema.md "Phase Status and Terminal Reasons"). Setting `blocked` without a reason
   is a workflow violation — SKILL.md cannot route the recovery without it.
3. If `phase_status` advances away from `blocked`, set `phase_terminal_reason: null` in the same write.
4. Record the phase result in FEATURE.md phase history.
   Append `PHASE_END` with `phase`, `phase_status`,
   `duration_ms`, and `phase_terminal_reason` (when blocked). The event MUST mirror the FEATURE.md write.

The outer loop appends `PHASE_ENTER` before each phase begins and records
`DISPATCH_STARTED` / `DISPATCH_RETURNED` around each orchestrator dispatch.
DONE appends `SESSION_COMPLETE` after its return contract is verified.

### Phase Loop Conditions

| Loop | Trigger | Max Iterations |
|-|-|-|
| PLAN_REVIEW → PLAN_DRAFT | Required changes or critical red-team findings | 3 |
| VALIDATE → EXECUTE | Validation failures or quality gate fails | 2 |
| EXECUTE milestone retry | Review budget exhausted and re-plan required | 1 (then escalate) |

### Resume Snapshot Protocol

The SKILL.md outer loop generates SNAPSHOT.md at every phase transition and milestone completion.
See state-file-schema.md for the full schema.

**When to regenerate:**
1. After each phase completes (before advancing `current_phase`)
2. After each milestone completes during EXECUTE
3. On resume (Step 5a) — verify snapshot matches reality, regenerate if stale

**How to generate:**
1. Read FEATURE.md (progress, decisions, open questions)
2. Read task bundle statuses to find the next pending task
3. Read that task bundle's frontmatter for its path, status, dependencies, files, and risk
4. Extract relevant decisions from FEATURE.md Decisions Made
5. Include only decisions or deviations not already present in the next task bundle
6. Summarize completed tasks (one line each: task ID, milestone, what it produced)
7. Include active deviations and plan amendments
8. **Enumerate pending triage bundles:** list every `tasks/T-DISC-*.md` where `status: discovered`
   (`Grep(pattern="^status: discovered$", path="tasks/")`). Populate the Discovered Tasks table with
   id, discovered_from, discovered_by, risk, and the first-line summary from the bundle body.
   If none, write "(none)".
9. Include budget status if `token_budget_usd` or `token_budget_total` is set
10. Keep the snapshot under 80 lines or 1,500 tokens.
11. Write to `SNAPSHOT.md` in the state directory.

**Why snapshots exist:** A cold milestone orchestrator needs a pointer to the next bundle,
dependency state, and deltas since that bundle was generated.
The snapshot is not a second copy of the task contract or conventions.
The snapshot compresses all accumulated decisions into a task-scoped document.

### Milestone Dispatch Protocol (EXECUTE)

SKILL.md reads PLAN.md to build the milestone dependency graph and reads task bundle statuses.

1. Identify ready milestones: all dependencies complete, has pending tasks
2. Check File Impact Map for file overlap between ready milestones
3. No overlap → one group orchestrator dispatches parallel implementers in one message
4. Shared files → dispatch sequentially
5. After each milestone completes: regenerate SNAPSHOT.md, re-read task bundles, update dependency graph, identify next ready milestones

## EXECUTE Batch Loop

```
Plan reconciliation -> Pre-flight validation gate (build + test + lint + typecheck baseline, hard gate)
  -> Identify ready milestones (dependency graph) -> Execute round -> Batch Report -> Feedback -> Next round

Execute round:
  1. Find READY milestones (all dependencies completed, status = pending or in_progress)
  2. If multiple ready milestones have NO file overlap (per File Impact Map) -> run in PARALLEL
     Otherwise -> run SEQUENTIALLY (current behavior)
  3. For each active milestone, promote next pending task to `ready` (frontmatter status), pick next ready task:
     - Dispatch implementers (parallel across milestones, sequential within)
     - Shift-left (lint/format/typecheck) per task
     - Apply the cumulative Review Budget from resource-efficiency.md
     - Use one task-critic for Medium/High tasks; do not add separate spec and quality reviewers
     - Add a red team only for distinct High-risk trust, concurrency, security, or destructive-data coverage
     - File `discovered_from` bundles for any out-of-scope failures surfaced (Discovery Capture Protocol)
     - Append TASK_COMPLETE event to events.jsonl with tokens/duration/cost
  4. At MILESTONE BOUNDARY: Run /atcommit, append MILESTONE_COMPLETE event to events.jsonl

STOP on: missing deps, test failures, unclear instructions, exhausted review budget with unresolved flaws, plan-invalidating discoveries
DEVIATION_MINOR: propose plan edit, ask user (interactive) or log and adjust (autonomous)
DEVIATION_MAJOR: pause execution, recommend re-planning
```

## DONE Finalization

```
Tests pass -> /atcommit (remaining) -> git push -> /pr (create PR) -> /pr-fix (validate + fix)
                                                                           |
                                                                           v
                                                                  New feedback? --yes--> /pr-fix (max 2 loops)
                                                                           |
                                                                           no
                                                                           |
                                                                           v
                                                                     Report + Archive
```

## REFINE Phase
- Spawn `refiner` to analyze, clarify, and explore approaches for the feature
- Output: Refined specification with problem statement, chosen approach, scope, behavior, acceptance criteria
- Well-specified descriptions pass through quickly; vague ones get iterative refinement
- Refiner proposes 2-3 approaches with trade-offs and gets user preference before finalizing
- Refiner asks one question at a time (prefer multiple choice) to reduce cognitive load
- Before asking, the refiner retrieves answers available from repository code, documentation, history, supplied references, and existing state artifacts
- The refiner asks unresolved questions by blast radius: architecture-changing first, behavior-defining second, polish last; it provides a recommendation for consequential choices and stops when remaining uncertainty is cheaper and safe to resolve during implementation
- **Interactive**: Asks clarifying questions, proposes approaches. After refiner completes, orchestrator presents the refined spec summary and WAITS for explicit user approval before proceeding to RESEARCH. User can approve, adjust, or request further refinement.
- **Autonomous**: Synthesizes from context, selects best approach, logs decisions in Decisions Made

## RESEARCH Phase

First evaluate which evidence is missing:

- Local integration or convention gaps → dispatch `explorer`
- External API, protocol, or product gaps → dispatch `researcher`
- Both independent gaps → dispatch both in parallel
- Neither → satisfy the phase through Prepared-Context Reuse

- `explorer`: **local codebase** mapping (modules, patterns, conventions)
- `researcher`: follows a structured research sequence:
  - **Step 0 — Domain Research Evaluation**: determines if the task relies on knowledge outside the codebase (external APIs, file formats, protocols, specs, third-party services)
  - **Step 1 — External Domain Research** (only if triggered): WebSearch/WebFetch for authoritative sources, edge cases, and non-obvious behaviors BEFORE Confluence
  - **Step 2 — Confluence + General Web Research**: design docs, RFCs, APIs, best practices
- When a reference implementation is supplied, both agents treat it as a semantic specification before planning target code:
  - Summarize behaviors, guarantees, deliberate decisions, and evidence
  - Separate incidental language/framework details from required semantics
  - Map semantics to native target-repository conventions and report translation gaps
  - Confirm the license before reusing implementation text; if unclear, analyze behavior only and copy nothing
  - If the source is unavailable or evidence is insufficient, label what remains unverified and ask for access only when it changes architecture, behavior, or scope
- Output: Context, Assumptions (tagged: [EXTERNAL DOMAIN], [CODEBASE], [TASK DESCRIPTION]), Constraints, Risks, Open Questions
- Search Confluence only when the feature references internal design knowledge
  or repository/external evidence leaves a material internal question.
- Do not repeat authoritative external research already cited in prepared context.
- **Interactive**: Present research summary, ask user to confirm assumptions and scope
- **Autonomous**: Proceed with best interpretation, log assumptions in Decisions Made

### Conventions Extraction (end of RESEARCH phase)

After explorer and researcher return,
the orchestrator extracts project conventions into `CONVENTIONS.md` —
an immutable artifact that all downstream agents inherit.

**Why this exists**: Conventions scattered across RESEARCH.md get re-derived by every agent,
causing drift (one agent uses one pattern, another uses a different one)
and wasting tokens on redundant deliberation.
CONVENTIONS.md front-loads these decisions once.

**Extraction protocol:**
1. Read explorer's Conventions section and pattern catalog
2. Read explorer's Build Environment section for exact commands
3. Read explorer's Key Types/Functions for naming patterns
4. Synthesize into CONVENTIONS.md using the schema from state-file-schema.md
5. Every convention MUST cite a specific `file:line` as evidence
6. Write to `~/docs/plans/do/<short-name>/CONVENTIONS.md`

**Immutability rule**: CONVENTIONS.md is not updated during EXECUTE.
If a convention proves wrong,
the deviation is handled through the Plan Amendment Protocol
(update PLAN.md task contracts and FEATURE.md deviations, not CONVENTIONS.md).

## PLAN_DRAFT Phase
- Spawn `planner` to create a plan using the prepared research and conventions paths
- Output: Milestones, Task Breakdown, Validation Strategy
- Plan must summarize decision-relevant evidence and cite its artifact or source path;
  it must not duplicate full research sections
- **Interactive**: Present a decision-first summary from PLAN.md, then ask user to approve or request changes. Lead with outcome, chosen approach, riskiest assumption, tweakable decisions with one alternative and later-change cost, known unknown defaults with pivot signals, then compressed mechanical work.
- **Autonomous**: Proceed to review, let reviewer catch issues

## PLAN_REVIEW Phase

**Risk-routed review: every review covers a distinct question.**

Consistency checking is now the planner's responsibility (self-consistency pass in planner Step 5).
No separate consistency-checker dispatch is needed.

1. Always dispatch one `reviewer`.
2. Add `red-teamer` only when the plan crosses a trust boundary,
   introduces concurrency or retry semantics,
   changes authentication/authorization,
   handles destructive data,
   or has another explicitly cited High-risk assumption.
3. Add a Codex plan challenge only when the architecture is novel,
   evidence conflicts,
   or reviewer/red-team independence materially improves a named risk.
   Skip otherwise and record `CODEX_SKIPPED` with `reason: plan_review_not_distinct`.
4. When multiple reviews are justified, dispatch them in parallel:
   - `reviewer`: substantive critique (coverage, path verification, research cross-check, dependency analysis, safety, executability)
     - Output: Review report, required changes
   - `red-teamer` in plan mode: adversarial challenge of plan assumptions
     - Attacks assumptions (checks evidence strength in RESEARCH.md)
     - Enumerates failure modes per milestone (external deps, internal assumptions, data edge cases)
     - Identifies security attack vectors and missing recovery paths
     - Assesses blast radius of shared code changes
     - Output: Red Team Plan Review with Critical / High / Medium findings

5. After justified reviews complete, merge findings:
   - Codex plan concerns → append to REVIEW.md under `## Codex Plan Challenge`
   - If reviewer has required changes → loop back to PLAN_DRAFT and preserve all findings as input
   - **Critical red-team findings** → loop back to PLAN_DRAFT (must address before execution)
   - **High findings (interactive)** → present to user, ask whether to address or track as risks
   - **High findings (autonomous)** → log as tracked risks, proceed
   - **Medium findings** → logged as risks to watch during EXECUTE
- **Interactive**: Present review + red-team findings as an update to the decision-first PLAN.md summary. Keep execution dependency order unchanged, but put user-tweakable choices and unresolved pivot signals before task mechanics. Ask for final approval before execution.
- **Autonomous**: Auto-approve if no critical issues, loop back for required changes only

## EXECUTE Phase
**Working directory is already set up.** Branch and worktree (if applicable) were created in Step 4 before any phase work began.
The orchestrator works from `<workdir_path>` and writes all state to `~/docs/plans/do/<short-name>/`.

**Session Activity Log:**

`events.jsonl` was initialized when the feature state was created.
On legacy resume only, initialize it with `SESSION_START` carrying `source: "legacy_resume"`;
do not synthesize events for phases that ran before the log existed.
Append one JSON object per line after every significant action (see state-file-schema.md for event types, schema, and required fields).
Every event MUST include `ts`, `type`, and `actor`.
The log is append-only — never rewrite or truncate.
Tell the user the log path so they can tail it (`tail -f events.jsonl | jq .`) or query it with `jq` to watch progress in real-time.

**Plan reconciliation — before implementing anything:**

Read only PLAN.md task metadata, dependencies, risk levels, and File Impact Map.
Verify that ready-task dependencies and expected paths still match the worktree.
This is a deterministic reconciliation, not another substantive plan review.
Do not dispatch a reviewer or reread narrative research.

**Context Preparation:**

Read PLAN.md headings, task metadata, dependencies, risk levels, and the File Impact Map.
Build the milestone dependency graph.
Store a milestone capsule under 1,000 words.
Pass task-bundle paths and let each worker read only its assigned bundle.

**Milestone-Level Parallelism:**

After context preparation, identify **ready milestones** — milestones whose dependencies are all completed.
When multiple milestones are ready simultaneously, check the File Impact Map for file overlap:

| Condition | Execution Mode |
|-|-|
| Ready milestones have **no file overlap** in File Impact Map | Run in **parallel** — one task per milestone dispatched in a single message |
| Ready milestones **share modified files** | Run **sequentially** — one milestone at a time (current behavior) |

Parallel dispatch: spawn one implementer Task per ready milestone in a single response message.
After all return, run shift-left checks and reviews for each.
Within a single milestone, tasks always run sequentially (they share files by definition).

Log parallel milestones as an event:
`{"ts":"<ISO8601>","type":"MILESTONE_START","actor":"orchestrator","milestone":"M-002","title":"<title>","parallel_with":["M-003"]}`

**Per-task sequence** (same whether running one or multiple milestones):

1. **Dispatch fresh implementer** with the assigned task-bundle path and a compact scene-setting capsule
   (milestone position, dependency state, relevant discoveries, active risk).
   Implementer self-evaluates before reporting — catches obvious issues before external review.
2. Implementer asks questions → answers provided → implements → self-evaluates → reports (NO commit)
3. **Shift-left validation** (deterministic — orchestrator runs directly, no subagent):
   lint + format + type-check. Auto-fix formatting.
   Return to implementer if lint/type errors persist.
   Only proceed to risk-routed review after shift-left passes.
4. **Risk-routed review** — apply the Review Budget in resource-efficiency.md.
   Low-risk tasks stop after self-review and deterministic checks.
   Medium/High tasks get one task-critic pass.
   A rejection gets one focused fixer/recheck, not a restarted escalating review.
5. **Distinct red-team review** — only within the remaining High-risk review budget,
   and only for trust, concurrency, security, retry/idempotency, or destructive-data risk
   not already covered by the critic.
6. **Discovery Capture Protocol** — before marking the task complete,
   file a `discovered_from` bundle for every out-of-scope failure the task surfaced.
   See **Discovery Capture Protocol** section below. This runs even when review ACCEPTs.
7. Mark task complete (only after ACCEPT verdict — safety valve outcomes are blocking),
   update state (set bundle `status: complete`, populate measured token fields and `duration_ms`),
   append a `TASK_COMPLETE` event to events.jsonl with token, duration, review-pass,
   and cost-source metrics

**Risk-Proportional Review Budget:**

| Task risk | Critic | Focused recheck | Distinct red team |
|-|-|-|-|
| Low | No | No | No |
| Medium | One pass | Only after rejection | No |
| High | One pass | Only after rejection | If the second slot remains and a distinct risk exists |

The task-critic evaluates spec compliance and code quality together.
Separate spec-review and code-quality-review agents are forbidden in `/do`.

**Step 4a: Task Contract (Pre-Computed in Bundle)**

The task contract is pre-computed in each TASK-XXX.md bundle during bundle generation.
The orchestrator does not extract it at runtime. The format is:

```markdown
## Task Contract for T-XXX

### Scope
[Task description from PLAN.md]

### Acceptance Criteria (pass/fail)
1. Build passes with zero errors after changes
2. All existing tests pass
3. Lint and type check pass with zero violations
4. [AC-1 from plan — made concrete and testable]
5. [AC-2 from plan — made concrete and testable]

### Mandatory Invariants (always apply, even if not in plan)
1. Error handling: errors at system boundaries are caught, logged, and propagated
2. Compatibility: no breaking changes to public APIs unless task explicitly requires it
3. Observability: existing logging/metrics/tracing preserved or extended
4. Security: no new injection vectors, exposed secrets, auth gaps
5. Codebase conventions: new code follows patterns in comparable files

### Out of Scope
- Changes to files not listed in the task's file impact
- Pre-existing issues in unrelated modules
- Improvements beyond stated requirements
```

Each criterion must be binary pass/fail — not "looks good."
Include project-level criteria (build, lint, tests) from the pre-flight baseline.
The Mandatory Invariants ensure the critic can block on non-functional regressions
even if the plan omitted them.

**Step 4b: Focused Review Loop**

```
if task risk is Low:
  accept implementer self-review + deterministic evidence
else:
  1. Dispatch one task-critic with the complete contract and named risk focus.
  2. If ACCEPT: continue.
  3. If REJECT:
     a. Dispatch the implementer with only proven findings and required evidence.
     b. Re-run focused deterministic validation.
     c. Reuse the same critic for one focused recheck of those findings.
  4. If the focused recheck rejects: STOP and escalate. Do not add another reviewer.
  5. For High risk, dispatch a red team only if the second slot was not used
     and its scope is distinct from the critic.
```

The safety valve is blocking in both modes.
Autonomous mode does not convert unresolved critical flaws into tracked risks.

**Discovery Capture Protocol** (all phases — RESEARCH, PLAN, EXECUTE, VALIDATE):

Every failure, broken test, latent bug, stale doc, or out-of-scope issue surfaced by an agent MUST
be captured as a `discovered_from` bundle in `tasks/`. The protocol is not EXECUTE-only — obstacles
uncovered during research, planning, review, or validation deserve the same structural capture.
Never delete, disable, comment out a failing test, or silently drop a finding to "keep moving" —
filing a discovered bundle is always the right escape hatch.

**When to file a discovered bundle** (any of the following, in any phase):

| Phase | Signal | Example |
|-|-|-|
| EXECUTE | Pre-existing failing test uncovered by the task's work | Unrelated test in same package newly fails after refactor |
| EXECUTE | Latent bug the task's code exposes but does not cause | Null pointer in caller revealed by tightened API contract |
| EXECUTE | Dead code, TODO, or broken invariant spotted while navigating | `// FIXME` comment referencing a real ticket-less defect |
| EXECUTE | Out-of-scope refactor opportunity blocking clean test coverage | Shared helper needs split to unit-test the new path |
| EXECUTE/RESEARCH | Convention or doc mismatch with the code as it actually exists | CONVENTIONS.md says X, code does Y and Y is the true pattern |
| RESEARCH | Stale or incorrect Confluence/README/ADR referenced by the feature | Linked design doc still describes v1 API after v2 migration shipped |
| RESEARCH | Adjacent system defect surfaced during codebase mapping | Explorer finds an unhandled error branch unrelated to the feature |
| PLAN_DRAFT/PLAN_REVIEW | Planner or reviewer spots work outside scope but worth capturing | Review flags a latent migration safety gap while validating task contracts |
| VALIDATE | Validator detects a regression outside the feature's changeset | Baseline comparison surfaces a pre-existing flaky test newly unmasked |

**How to file** (one frontmatter write — seconds of work):

1. Create `tasks/T-DISC-<NNN>.md` with frontmatter:
   ```yaml
   id: T-DISC-<NNN>
   status: discovered
   risk: <low|medium|high>
   milestone: null
   discovered_from: <T-XXX | RESEARCH | PLAN_DRAFT | PLAN_REVIEW | VALIDATE>
   discovered_by: <actor>           # implementer | task-critic | red-teamer | validator | explorer | researcher | planner | reviewer
   summary: <one-line description>
   ```
   For RESEARCH/PLAN/VALIDATE origins where no parent task exists, set `discovered_from` to the
   phase name (e.g., `RESEARCH`) and leave `milestone: null`.
2. Body: 3-5 sentences — what was found, where (file:line or doc URL), why it is out of scope for
   the current feature, what the minimum fix looks like.
3. Append a `DISCOVERED` event to events.jsonl with `from_task` (or phase name), `discovered`
   (bundle id), `summary`, and `risk`.
4. **Never auto-promote** discovered tasks to `ready`. They enter a triage queue the user reviews
   at batch boundaries, milestone report time, or the DONE-phase triage step (see DONE step 1.3).

**Rationalization resistance — STOP and file a bundle if you catch yourself thinking:**

| Rationalization | Reality |
|-|-|
| "This test was already broken — not our problem." | Nothing is pre-existing. If it fails on this branch, YOUR work owns it. File a bundle and document the diagnosis. |
| "The red-team found a latent bug but it's out of scope — ignore it." | Out-of-scope means *file it*, not *forget it*. A discovered bundle takes 30 seconds and preserves the finding. |
| "I'll just `t.Skip()` this test to stay green and come back later." | Later never comes. Skipping a test without a discovered bundle is a workflow violation. |
| "Context is tight — I'll skip filing and remember it." | You will not remember. Context pressure is the exact moment when filing matters most and costs least. |
| "This is a convention drift, not a bug — doesn't need a task." | Convention drift compounds. File it even if priority is low. |

A single `discovered_from` bundle is cheaper than a post-mortem about silently disavowed work.

**Token and Timing Tracking:**

After each subagent Task completes, record every runtime-provided token field,
duration, model, reasoning effort, tool-call count, wait-call count, and spawned-agent count.
Do not replace actual fields with a hand estimate.
Track cumulatively at three levels:

| Level | What's tracked | When reported |
|-|-|-|
| Per-task | Sum of implementer + justified reviews | TASK_COMPLETE event and bundle frontmatter |
| Per-milestone | Sum of all tasks in the milestone | MILESTONE_COMPLETE event |
| Grand total | Sum of all milestones + overhead (research, planning, validation) | SESSION_COMPLETE event |

Include token/duration data in batch reports so the user can see resource consumption.

**Budget Enforcement** (when `token_budget_usd` or `token_budget_total` is set in FEATURE.md):

After each TASK_COMPLETE, update token totals in FEATURE.md.
Record dollars only when the runtime supplies cost or an explicitly configured model rate applies.
Otherwise write `cost_usd: null` and `cost_source: unknown`.
Never price Codex tokens with a Claude model rate or vice versa.

| Threshold | Action |
|-|-|
| 80% of budget | Append `BUDGET_WARNING` event to events.jsonl, include in batch report |
| 100% of budget | **Interactive**: pause, ask user to increase budget or stop gracefully at current milestone |
| 100% of budget | **Autonomous**: complete the current task, then stop. Do not start the next task. Append `BUDGET_EXHAUSTED` event. |

The budget check runs before dispatching each task — not after.
If exact or configured cost is unavailable,
surface that the dollar budget cannot be verified and require a token ceiling before continuing.
Do not invent a dollar estimate from an unidentified model.

**Batch reporting** (after every batch or parallel round):

Every report MUST include the same six fields — discoveries are not optional, they are the
mechanism that makes the work-disavowal resistance visible to the user.

Required fields: **tasks completed**, **test status**, **discovered bundles this batch**,
**token fields**, **cost source**, **duration**, **agent/tool/wait counts**, and
**metric provenance** (`measured`, `derived`, or `lower_bound`).

- **Autonomous — one-line format** (emitted at every `MILESTONE_COMPLETE`):

  ```
  Milestone M-XXX complete (<name>). Tasks: <done>/<total>. Tests: <pass>/<fail>. Discovered: <N>. Tokens: <X>k (<cached> cached). Cost: <value|unknown> (<source>). Agents/tools/waits: <A>/<T>/<W>. Duration: <Z>s. Provenance: tokens=<P>, counts=<P>, duration=<P>. Next: M-YYY.
  ```

  `Discovered: 0` when nothing new was filed this batch — always print the field so its absence
  is informative.

- **Interactive — structured block** (presented between batches):

  ```
  ## Batch Report — M-XXX

  Tasks: T-001, T-002, T-003 (3/3 complete)
  Tests: 158 pass / 0 fail (baseline +16)
  Tokens: 99.7k (80.1k cached)    Cost: unknown    Agents/tools/waits: 3/24/2    Duration: 6m 35s
  Provenance: tokens=derived, counts=measured, duration=derived

  Discovered this batch:
  - T-DISC-001 (from T-002, Medium): <summary>
  - T-DISC-002 (from T-003, Low): <summary>

  Deviations: A1 applied (rate limiter needs Redis — see PLAN.md Amendments)

  Next: M-002 (Protected Routes). Continue?
  ```

  When nothing was discovered this batch, replace the Discovered section with
  `Discovered this batch: none`. Present an `AskUserQuestion` with the usual options:
  continue / adjust / review code / stop.

At milestone boundary (all tasks in milestone complete + tests pass):
- Run `/atcommit` to organize ALL accumulated changes into atomic commits grouped by concept
- `/atcommit` builds dependency graphs and groups files that belong together (e.g., package + tests, wiring + config)
- Typical result: 3-5 commits per feature instead of one per task
- Append `MILESTONE_COMPLETE` event to events.jsonl with milestone totals and commit count
- **Integrated Review:** Run Codex or an independent reviewer when the milestone completes a coherent
  user-visible behavior slice or combines packages/trust boundaries.
  Record `reviewed_head`.
  Defer review for support-only milestones that cannot yet be evaluated as behavior.
  Critical findings → focused implementer fix and focused recheck.

**Mid-batch stop conditions**: missing dependencies, systemic test failures,
unclear instructions, repeated verification failures,
or discoveries that invalidate the plan's assumptions.

**Structured Deviation Handling:**

When an implementer or reviewer reports that something doesn't match the plan's assumptions,
classify the deviation by severity and handle accordingly:

| Severity | Detection | Handling |
|-|-|-|
| **Minor** — wrong assumption, step needs adjusting, small addition | Implementer says "this won't work because..." or "this already exists" or reviewer flags plan misalignment as justified | **Interactive**: propose specific PLAN.md edit, show before/after, ask user approval via `AskUserQuestion` before writing. **Autonomous**: log rationale in Decisions Made, apply edit, continue. |
| **Major** — wrong approach, missing phase, scope change, fundamental rethink | Implementer reports approach is infeasible, or discovery invalidates multiple downstream tasks | **Both modes**: stop the current batch, append a `DEVIATION_MAJOR` event to events.jsonl with evidence, present the issue to the user. Recommend re-planning (return to PLAN_DRAFT). |

**Plan Amendment Protocol** (applies to both severity levels):

Deviations that change assumptions feed back into PLAN.md — not just into events.jsonl.
A resuming agent reads the current plan, not the original plan plus unstructured deviation logs.

1. Append a `DEVIATION_MINOR` or `DEVIATION_MAJOR` event to events.jsonl with trigger, evidence, and affected tasks
2. Update affected task contracts in PLAN.md:
   - Modify preconditions/postconditions of the affected task
   - Re-validate downstream task preconditions — if a downstream task assumed what changed, update its contract too
   - Add an entry to the `## Plan Amendments` section with trigger, changes, and downstream impact
3. Update FEATURE.md: set `last_plan_amendment` to current timestamp, log in Surprises and Discoveries
4. Regenerate SNAPSHOT.md to reflect the amended plan
5. Run focused validation for the amended contract and record the evidence before resuming downstream work

After resolving a deviation, re-read the latest PLAN.md before resuming — it may have changed.
Log all deviations as events in events.jsonl and in the Surprises and Discoveries section of FEATURE.md.

**TDD-first execution for behavior-changing tasks:**
When a task introduces or changes behavior, follow this exact sequence — no exceptions:
1. Write the failing test (complete test code, not a placeholder)
2. Run the test — verify it FAILS for the expected reason (not a syntax error)
3. Write minimal implementation to make the test pass
4. Run the test — verify it PASSES and all other tests still pass
5. Do NOT commit — changes accumulate until the milestone boundary

**Red flags — STOP and restart the task with TDD if you catch yourself:**
- Writing implementation code before the test
- Skipping the "verify failure" step
- Writing a test that passes immediately (you're testing existing behavior, not new behavior)
- Rationalizing "this is too simple to test" or "I'll add the test after"
- Running `git commit` or `/atcommit` after a single task (commits happen at milestone boundaries only)

**When TDD does not apply:** Config-only changes, documentation updates, refactoring that preserves existing behavior (with existing test coverage). Use direct step structure: edit → verify (do NOT commit — wait for milestone boundary).

**Milestone boundary commits:**
When all tasks in a milestone are complete and tests pass, the orchestrator (NOT the implementer) runs `/atcommit` to organize all accumulated changes into atomic commits. `/atcommit` analyzes file dependencies and groups changes by concept (e.g., a complete package with tests, an integration layer, configuration + wiring). This produces 3-5 well-organized commits for a typical feature instead of one commit per task.

**Drift Measurement** (deterministic — at each milestone boundary after committing):

Compare plan vs reality:

| Check | Detection | Threshold | Action |
|-|-|-|-|
| Unplanned files | `git diff --name-only <base_ref>..HEAD` vs File Impact Map | >20% unplanned | Log warning, review with user |
| Test ratio | New test files / New source files | <0.3 | Log warning, may need more tests |
| Scope drift | Count of tasks marked "Extra" in spec reviews | >2 per milestone | Log DEVIATION_MINOR |
| New public APIs | Grep for exported functions not in plan | Any unplanned | Log for review |

Log as event:
`{"ts":"<ISO8601>","type":"DRIFT_CHECK","actor":"orchestrator","milestone":"M-XXX","planned_files":N,"actual_files":N,"unplanned":[...],"test_ratio":N}`

**Never:**
- Dispatch implementers in parallel when their milestones overlap files or dependencies
- Exceed the cumulative review budget in resource-efficiency.md
- Proceed to the next task while a review has unresolved critical flaws
- Let implementer subagents run git commit — only the orchestrator commits at milestone boundaries
- Accept a task-critic verdict that lacks proof for its critical flaws — send it back

## VALIDATE Phase
- Spawn `validator` to run automated checks and criterion verification; it does not repeat
  an integrated code-quality review already accepted for the same scope and HEAD
- Output: Validation report with test results, acceptance evidence, and quality scorecard (1-5 per dimension)
- Quality gate: all dimensions must score >= 3/5 to pass
- Reuse the integrated review when `HEAD == reviewed_head`.
  Populate overlapping quality evidence from the ledger plus deterministic results,
  without dispatching another substantive quality reviewer.
  Run a Codex branch adversarial gate only if code changed after that review
  or the validator surfaced a new material risk.
  Critical findings → loop to EXECUTE and append the result to VALIDATION.md.
- May loop back to EXECUTE for test failures, quality gate failures, or Critical Codex findings
- **Interactive**: Present validation results and quality scorecard, ask user before creating PR
- **Autonomous**: Auto-proceed to DONE if validation and quality gate pass

## DONE Phase

Finalization sequence — each step depends on the previous one succeeding.

### 1. Outcomes & Retrospective
- Write Outcomes & Retrospective to FEATURE.md

### 1.3 Discovered Task Triage

Every `tasks/T-DISC-*.md` bundle that is still `status: discovered` MUST be dispositioned
before the feature closes. Discovery without disposition re-introduces the work-disavowal
failure mode that Milestone 1 was built to prevent.

1. Enumerate pending bundles:
   `Grep(pattern="^status: discovered$", path="tasks/", output_mode="files_with_matches")`
2. For each bundle, read frontmatter + body and present a triage prompt.

**Interactive mode** — one `AskUserQuestion` per bundle:

```
AskUserQuestion(
  header: "Triage T-DISC-<NNN>",
  question: "<one-line summary from bundle> (discovered from <T-XXX>, risk: <level>). Disposition?",
  options: [
    "File as external issue" -- Create GitHub issue via gh, record URL, set status: skipped,
    "Keep as backlog" -- Leave status: discovered for a future /do session to pick up,
    "Discard with rationale" -- Not a real defect; capture why and set status: skipped
  ]
)
```

Bundle updates per choice:

| Choice | Bundle frontmatter update | Body update |
|-|-|-|
| File as external issue | `status: skipped`, `external_issue: <URL>` | Append "Filed as <URL> on <ISO ts>" |
| Keep as backlog | no change (`status: discovered`) | none |
| Discard with rationale | `status: skipped`, `discard_reason: <one-liner>` | Append the full rationale |

For "File as external issue":

```bash
gh issue create --title "<bundle summary>" --body "Discovered during /do <feature-name>. See T-DISC-<NNN> body for diagnosis.

<bundle body contents>

Originating feature: <short-name>
Originating task: <discovered_from>"
```

Record the returned URL in the bundle frontmatter.

**Autonomous mode:** Default all pending bundles to "Keep as backlog" (no destructive action
without user consent). Surface the count in the completion report so the user can triage later.

3. Update FEATURE.md Progress section for every dispositioned bundle (see state-file-schema.md
   Progress conventions for the marker symbols).
4. Append one `TRIAGE_COMPLETE` event to events.jsonl summarizing the dispositions:

```json
{"ts":"<ISO8601>","type":"TRIAGE_COMPLETE","actor":"orchestrator","counts":{"filed":N,"backlog":N,"discarded":N}}
```

**If a bundle's rightful home is the current feature (not a follow-up),** the correct path is
*not* to fold it in during DONE. Answer "Keep as backlog", finish DONE, then start a fresh
`/do` invocation that resumes the bundle — this preserves the one-feature-one-PR boundary.

### 1.5 Documentation Update (Optional)

Check if the feature affects user-facing behavior:
- If API changes: update API docs
- If new CLI flags: update README or help text
- If behavior changes: update CHANGELOG.md entry

If the plan included doc tasks, they were already done in EXECUTE.
This step catches documentation that was missed by the plan.
Skip if the feature is purely internal (no user-facing changes).

### 2. Final Test Suite
- Run the full test suite one final time to confirm everything passes
- If tests fail: loop back to EXECUTE to fix. Do NOT proceed with uncommitted broken code.

### 3. Commit Remaining Changes (`/atcommit`)
- Run `/atcommit` to organize any remaining uncommitted changes into atomic commits
- This catches stragglers missed at milestone boundaries (validation fixes, retrospective updates, etc.)
- If nothing to commit, skip to step 4

### 4. Push to Remote
- Push all commits to the remote branch: `git push`
- If the branch has no upstream: `git push -u origin HEAD`
- If push fails: report the error. Do NOT force-push. Let the user decide.

### 5. Create Pull Request (`/pr`)
- **Interactive**: Present completion options before creating the PR:
  - Create PR as draft (Recommended)
  - Create PR as non-draft (`--open`)
  - Keep branch without PR
  - Discard work
- **Autonomous**: Create PR automatically as draft via `/pr` skill
- Record the PR URL in FEATURE.md frontmatter

### 6. Validate and Fix PR (`/pr-fix`)
- Run `/pr-fix` to check for review feedback from automated reviewers (Greptile, Codex, etc.)
- `/pr-fix` handles: fetching review threads, categorizing feedback, applying fixes, replying to threads, committing, pushing, and monitoring CI
- **Interactive**: `/pr-fix` will ask the user how to handle disagreements and whether to watch CI
- **Autonomous**: `/pr-fix` runs with "Fix all" and "Yes — watch and fix" defaults
- If `/pr-fix` produces additional commits, they are automatically pushed
- Loop `/pr-fix` up to 2 times if new automated review feedback arrives after fixes

### 7. Report and Archive
- Report final outcome to user: PR URL, commit count, CI status, and review thread status
- Read existing canonical state rather than creating a standalone implementation-notes file, and include:
  - Recorded deviation count and the highest-impact plan amendment from events.jsonl, PLAN.md, and FEATURE.md
  - Discovered edge-case count, outstanding-backlog count, and the highest-impact discovery across resolved and outstanding `tasks/T-DISC-*.md` bundles
  - Unresolved review questions from REVIEW.md, VALIDATION.md, and open PR feedback
  - The most consequential learning from Decisions Made, Surprises and Discoveries, or validation evidence
  - Canonical artifact locations for FEATURE.md, PLAN.md, REVIEW.md, VALIDATION.md, and remaining discovery bundles
- Archive run state (mark `current_phase: DONE` in FEATURE.md)

### 7.5. Extract Session Learnings
- Dispatch `memory-extractor` with events.jsonl + Decisions Made + Surprises sections
- Extracts reusable learnings (conventions, corrections, gotchas) into knowledge files
- Runs after archival — cheap post-session knowledge capture
- Dispatch with `run_in_background: true` — this is a non-blocking post-session task that should not delay completion reporting

**Early learning extraction** (in addition to DONE):
- At DEVIATION_MAJOR events — significant discoveries worth capturing immediately
- At session suspension (user says "stop here" during EXECUTE) — partial learnings are better than lost learnings
- At VALIDATE failures that loop back to EXECUTE — captures what went wrong
