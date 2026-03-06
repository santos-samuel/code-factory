# Phase Flow — Detailed Descriptions

Reference for detailed phase behaviors. Loaded by the orchestrator when executing phases.

## REFINE Phase
- Spawn `refiner` to analyze, clarify, and explore approaches for the feature
- Output: Refined specification with problem statement, chosen approach, scope, behavior, acceptance criteria
- Well-specified descriptions pass through quickly; vague ones get iterative refinement
- Refiner proposes 2-3 approaches with trade-offs and gets user preference before finalizing
- Refiner asks one question at a time (prefer multiple choice) to reduce cognitive load
- **Interactive**: Asks clarifying questions, proposes approaches, confirms refined spec with user
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

**Two-step review: consistency check → substantive review.**

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
- **Interactive**: Present review findings, ask user for final approval before execution
- **Autonomous**: Auto-approve if no critical issues, loop back for required changes only

## EXECUTE Phase
**Working directory is already set up.** Branch and worktree (if applicable) were created in Step 4 before any phase work began. The orchestrator works from `<workdir_path>` and writes all state to `~/docs/plans/do/<short-name>/`.

**Plan critical review — before implementing anything:**

The orchestrator re-reads the entire plan with fresh eyes, verifies task ordering and dependencies, checks the worktree has what the plan expects. Raises concerns before any code is written.

**Batch execution with two-stage review:**

The orchestrator reads the plan once, extracts all tasks with full text, then executes tasks in **batches of 3** (adjustable). After each batch: report progress, collect feedback (interactive) or log summary (autonomous), then continue.

Per-task sequence within each batch:
1. **Dispatch fresh implementer** with full task text + scene-setting context inlined (milestone position, prior task summary, upcoming tasks, relevant discoveries, architectural context)
2. Implementer asks questions → answers provided → implements → self-reviews → reports (NO commit)
3. **Spec compliance review** — fresh reviewer acknowledges strengths, then verifies implementation matches spec (nothing missing, nothing extra, nothing misunderstood)
4. If issues → implementer fixes → re-review (loop until compliant)
5. **Code quality review** — fresh reviewer receives plan context, reports strengths first, then assesses code quality, architecture, plan alignment, patterns, testing
6. If critical issues → implementer fixes → re-review (loop until approved)
7. If plan deviations found → orchestrator updates PLAN.md if warranted
8. Mark task complete, update state, proceed to next task in batch (do NOT commit yet)

After each batch:
- Report: tasks completed, test status, discoveries
- **Interactive**: Ask to continue, adjust, review code, or stop
- **Autonomous**: Log summary and continue (stop only on blockers)

At milestone boundary (all tasks in milestone complete + tests pass):
- Run `/atcommit` to organize ALL accumulated changes into atomic commits grouped by concept
- `/atcommit` builds dependency graphs and groups files that belong together (e.g., package + tests, wiring + config)
- Typical result: 3-5 commits per feature instead of one per task
- Verify all commits build in isolation before proceeding to next milestone

**Mid-batch stop conditions**: missing dependencies, systemic test failures, unclear instructions, repeated verification failures, or discoveries that invalidate the plan's assumptions.

**Re-plan trigger**: If a discovery during execution reveals the plan needs fundamental changes, stop the batch, log the discovery with evidence, and re-read the plan before proceeding.

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
