# Phase Flow — Detailed Descriptions

Reference for detailed phase behaviors. Loaded by the orchestrator when executing phases.

## EXECUTE Batch Loop

```
Plan Critical Review -> Pre-flight validation gate (build + test + lint + typecheck baseline, hard gate) -> Initialize SESSION.log
  -> Identify ready milestones (dependency graph) -> Execute round -> Batch Report -> Feedback -> Next round

Execute round:
  1. Find READY milestones (all dependencies completed, status = pending or in_progress)
  2. If multiple ready milestones have NO file overlap (per File Impact Map) -> run in PARALLEL
     Otherwise -> run SEQUENTIALLY (current behavior)
  3. For each active milestone, pick next task:
     - Dispatch implementers (parallel across milestones, sequential within)
     - Shift-left (lint/format/typecheck) per task
     - Spec review (max 2 fix cycles) per task
     - Code quality review (max 2 fix cycles) per task
     - Red-team review (HIGH-RISK TASKS ONLY, max 2 fix cycles) per task
     - Append TASK_COMPLETE to SESSION.log with tokens/duration
  4. At MILESTONE BOUNDARY: Run /atcommit, append MILESTONE_COMPLETE to SESSION.log

STOP on: missing deps, test failures, unclear instructions, repeated failures, plan-invalidating discoveries
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
- **Interactive**: Asks clarifying questions, proposes approaches. After refiner completes, orchestrator presents the refined spec summary and WAITS for explicit user approval before proceeding to RESEARCH. User can approve, adjust, or request further refinement.
- **Autonomous**: Synthesizes from context, selects best approach, logs decisions in Decisions Made

## RESEARCH Phase
- Spawn `explorer` and `researcher` **in parallel** (both in a single message) for latency reduction
- `explorer`: **local codebase** mapping (modules, patterns, conventions)
- `researcher`: follows a structured research sequence:
  - **Step 0 — Domain Research Evaluation**: determines if the task relies on knowledge outside the codebase (external APIs, file formats, protocols, specs, third-party services)
  - **Step 1 — External Domain Research** (only if triggered): WebSearch/WebFetch for authoritative sources, edge cases, and non-obvious behaviors BEFORE Confluence
  - **Step 2 — Confluence + General Web Research**: design docs, RFCs, APIs, best practices
- Output: Context, Assumptions (tagged: [EXTERNAL DOMAIN], [CODEBASE], [TASK DESCRIPTION]), Constraints, Risks, Open Questions
- **Both sources are mandatory** - do not skip Confluence search
- **Interactive**: Present research summary, ask user to confirm assumptions and scope
- **Autonomous**: Proceed with best interpretation, log assumptions in Decisions Made

## PLAN_DRAFT Phase
- Spawn `planner` to create plan (references both codebase findings AND Confluence context)
- Output: Milestones, Task Breakdown, Validation Strategy
- Plan must embed relevant context inline (not only links)
- **Interactive**: Present plan, ask user to approve or request changes
- **Autonomous**: Proceed to review, let reviewer catch issues

## PLAN_REVIEW Phase

**Three-step review: consistency check → substantive review → red-team.**

1. Spawn `consistency-checker` to fix internal inconsistencies in PLAN.md before substantive review:
   - Iteratively scans for contradictions, mismatched task IDs, file path inconsistencies, count mismatches, terminology drift, dangling references
   - **Fixes issues directly** (Edit tool) — does not report them for the planner to fix
   - One fix at a time, re-reads from the top after each fix, max 10 iterations
   - Never changes plan substance — only fixes internal contradictions
   - Flags substantive issues in a Consistency Notes section for the reviewer
   - Uses `sonnet` model (mechanical task, not reasoning-heavy)

2. Re-read PLAN.md after consistency checker completes (it may have been edited).

3. Spawn `reviewer` for substantive critique (coverage, path verification, research cross-check, dependency analysis, safety, executability)
- Output: Review report, required changes
- May loop back to PLAN_DRAFT

4. If reviewer approves, spawn `red-teamer` in plan mode — adversarial challenge of plan assumptions:
   - Attacks assumptions (checks evidence strength in RESEARCH.md)
   - Enumerates failure modes per milestone (external deps, internal assumptions, data edge cases)
   - Identifies security attack vectors and missing recovery paths
   - Assesses blast radius of shared code changes
   - Output: Red Team Plan Review with Critical / High / Medium findings
   - **Critical findings** → loop back to PLAN_DRAFT (must address before execution)
   - **High findings (interactive)** → present to user, ask whether to address or track as risks
   - **High findings (autonomous)** → log as tracked risks, proceed
   - **Medium findings** → logged as risks to watch during EXECUTE
- **Interactive**: Present review + red-team findings, ask user for final approval before execution
- **Autonomous**: Auto-approve if no critical issues, loop back for required changes only

## EXECUTE Phase
**Working directory is already set up.** Branch and worktree (if applicable) were created in Step 4 before any phase work began.
The orchestrator works from `<workdir_path>` and writes all state to `~/docs/plans/do/<short-name>/`.

**Session Activity Log:**

Initialize `SESSION.log` in the state directory on EXECUTE entry.
Append timestamped entries after every significant action (see state-file-schema.md for entry types and format).
The log is append-only — never rewrite or truncate.
Tell the user the log path so they can open it in their editor to watch progress in real-time.

**Plan critical review — before implementing anything:**

The orchestrator re-reads the entire plan with fresh eyes,
verifies task ordering and dependencies,
checks the worktree has what the plan expects.
Raises concerns before any code is written.

**Context Preparation:**

Read PLAN.md and extract ALL tasks with their full text,
acceptance criteria, dependencies, risk levels, and the File Impact Map.
Build the milestone dependency graph.
Store this extracted context — you will inline it into each subagent dispatch.
Never make subagents read plan files; provide full context directly in the prompt.

**Milestone-Level Parallelism:**

After context preparation, identify **ready milestones** — milestones whose dependencies are all completed.
When multiple milestones are ready simultaneously, check the File Impact Map for file overlap:

| Condition | Execution Mode |
|-----------|---------------|
| Ready milestones have **no file overlap** in File Impact Map | Run in **parallel** — one task per milestone dispatched in a single message |
| Ready milestones **share modified files** | Run **sequentially** — one milestone at a time (current behavior) |

Parallel dispatch: spawn one implementer Task per ready milestone in a single response message.
After all return, run shift-left checks and reviews for each.
Within a single milestone, tasks always run sequentially (they share files by definition).

Log parallel milestones in SESSION.log: `MILESTONE_START: M-002 (Title) [parallel with M-003]`

**Per-task sequence** (same whether running one or multiple milestones):

1. **Dispatch fresh implementer** with full task text + scene-setting context inlined
   (milestone position, prior task summary, upcoming tasks, relevant discoveries, architectural context)
2. Implementer asks questions → answers provided → implements → self-reviews → reports (NO commit)
3. **Shift-left validation** (deterministic — orchestrator runs directly, no subagent):
   lint + format + type-check. Auto-fix formatting.
   Return to implementer if lint/type errors persist.
   Only proceed to reviews after shift-left passes.
4. **Spec compliance review** — fresh reviewer acknowledges strengths,
   then verifies implementation matches spec (nothing missing, nothing extra, nothing misunderstood)
5. If issues → implementer fixes → re-review (max 2 fix cycles, then escalate)
6. **Code quality review** — fresh reviewer receives plan context,
   reports strengths first, then assesses code quality, architecture, plan alignment, patterns, testing
7. If critical issues → implementer fixes → re-review (max 2 fix cycles, then escalate)
8. If plan deviations found → handle per **Structured Deviation Handling** below
9. **Red-team review (HIGH-RISK TASKS ONLY)** — only for tasks marked `Risk: High` in the plan.
   Adversarially probes for input edge cases, security vulnerabilities, race conditions, failure modes.
   Receives relevant plan-level red-team findings to focus on known risk areas.
   Critical findings → implementer fixes (max 2 cycles). High/Medium → logged as tracked risks.
   Skipped entirely for Low and Medium risk tasks.
10. Mark task complete, update state, append `TASK_COMPLETE` to SESSION.log with token/duration metrics

**Token and Timing Tracking:**

After each subagent Task completes, extract `total_tokens` and `duration_ms` from the Task result.
Track cumulatively at three levels:

| Level | What's tracked | When reported |
|-------|---------------|--------------|
| Per-task | Sum of implementer + spec reviewer + code quality reviewer | TASK_COMPLETE log entry |
| Per-milestone | Sum of all tasks in the milestone | MILESTONE_COMPLETE log entry |
| Grand total | Sum of all milestones + overhead (research, planning, validation) | SESSION_COMPLETE log entry |

Include token/duration data in batch reports so the user can see resource consumption.

**Batch reporting** (after every batch or parallel round):

Report: tasks completed, test status, discoveries, token usage, duration.
- **Interactive**: Ask to continue, adjust, review code, or stop
- **Autonomous**: Output a brief milestone progress line to the user at each MILESTONE_COMPLETE:
  `Milestone M-XXX complete (<name>). Tasks: N/M done. Tokens: Xk. Duration: Xs. Next: M-YYY.`
  Log summary and continue (stop only on blockers)

At milestone boundary (all tasks in milestone complete + tests pass):
- Run `/atcommit` to organize ALL accumulated changes into atomic commits grouped by concept
- `/atcommit` builds dependency graphs and groups files that belong together (e.g., package + tests, wiring + config)
- Typical result: 3-5 commits per feature instead of one per task
- Append `MILESTONE_COMPLETE` to SESSION.log with milestone totals and commit count

**Mid-batch stop conditions**: missing dependencies, systemic test failures,
unclear instructions, repeated verification failures,
or discoveries that invalidate the plan's assumptions.

**Structured Deviation Handling:**

When an implementer or reviewer reports that something doesn't match the plan's assumptions,
classify the deviation by severity and handle accordingly:

| Severity | Detection | Handling |
|----------|-----------|---------|
| **Minor** — wrong assumption, step needs adjusting, small addition | Implementer says "this won't work because..." or "this already exists" or reviewer flags plan misalignment as justified | **Interactive**: propose specific PLAN.md edit, show before/after, ask user approval via `AskUserQuestion` before writing. **Autonomous**: log rationale in Decisions Made, apply edit, continue. |
| **Major** — wrong approach, missing phase, scope change, fundamental rethink | Implementer reports approach is infeasible, or discovery invalidates multiple downstream tasks | **Both modes**: stop the current batch, log with evidence in SESSION.log (`DEVIATION_MAJOR`), present the issue to the user. Recommend re-planning (return to PLAN_DRAFT). |

After resolving a deviation, re-read the latest PLAN.md before resuming — it may have changed.
Log all deviations in SESSION.log and in the Surprises and Discoveries section of FEATURE.md.

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

**Never:**
- Dispatch multiple implementer subagents in parallel (causes conflicts)
- Skip either review stage (spec compliance OR code quality)
- Start code quality review before spec compliance passes
- Proceed to the next task while review issues remain open
- Let implementer subagents run git commit — only the orchestrator commits at milestone boundaries

## VALIDATE Phase
- Spawn `validator` to run automated checks AND quality assessment
- Output: Validation report with test results, acceptance evidence, and quality scorecard (1-5 per dimension)
- Quality gate: all dimensions must score >= 3/5 to pass
- May loop back to EXECUTE for test failures or quality gate failures
- **Interactive**: Present validation results and quality scorecard, ask user before creating PR
- **Autonomous**: Auto-proceed to DONE if validation and quality gate pass

## DONE Phase

Finalization sequence — each step depends on the previous one succeeding.

### 1. Outcomes & Retrospective
- Write Outcomes & Retrospective to FEATURE.md

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
- Report final outcome to user: PR URL, commit count, CI status, review thread status
- Archive run state (mark `current_phase: DONE` in FEATURE.md)

### 7.5. Extract Session Learnings
- Dispatch `memory-extractor` (haiku) with SESSION.log + Decisions Made + Surprises sections
- Extracts reusable learnings (conventions, corrections, gotchas) into knowledge files
- Runs after archival — cheap post-session knowledge capture
- Dispatch with `run_in_background: true` — this is a non-blocking post-session task that should not delay completion reporting
