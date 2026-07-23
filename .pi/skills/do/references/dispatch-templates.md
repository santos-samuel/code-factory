# Dispatch Templates

Task dispatch prompt templates for the `/do` outer loop.
All dispatches use `agent = "orchestrator"`.

## Dispatch Rules

- Pass artifact paths plus a compact capsule; do not inline complete state artifacts.
- Keep phase capsules under 1,200 words and milestone capsules under 1,000 words.
- Keep event tails to five events.
- Task bundles already contain task-specific conventions;
  do not also pass full `CONVENTIONS.md`.
- Append `DISPATCH_STARTED` immediately before every Task call and `DISPATCH_RETURNED`
  immediately after it returns, including nested implementer and reviewer dispatches.
- Ask every subagent for a final response under 2,000 characters:
  outcomes, evidence, blockers, and changed artifact paths only.

## Phase Orchestrator (non-EXECUTE)

Used for REFINE, RESEARCH, PLAN_DRAFT, PLAN_REVIEW, VALIDATE, DONE.

```
subagent(
  agent = "orchestrator",
  description = "<phase>: <short-name>",
  task = "
<current_phase><PHASE_NAME></current_phase>
<state_path>~/docs/plans/do/<short-name>/FEATURE.md</state_path>
<repo_root><REPO_ROOT></repo_root>
<workdir_path><WORKDIR_PATH></workdir_path>
<interaction_mode><interactive|autonomous></interaction_mode>

<feature_request>
<the user's feature description — REFINE only; omitted for later phases>
</feature_request>

<phase_capsule>
<At most 1,200 words: goal, settled decisions, unresolved risks, and exact artifact paths.
Do not copy complete artifacts here.>
</phase_capsule>

<artifacts>
feature: ~/docs/plans/do/<short-name>/FEATURE.md
research: ~/docs/plans/do/<short-name>/RESEARCH.md
conventions: ~/docs/plans/do/<short-name>/CONVENTIONS.md
plan: ~/docs/plans/do/<short-name>/PLAN.md
review: ~/docs/plans/do/<short-name>/REVIEW.md
validation: ~/docs/plans/do/<short-name>/VALIDATION.md
events: ~/docs/plans/do/<short-name>/events.jsonl
</artifacts>

<change_scope>
<VALIDATE only: base ref plus changed-file names and diff stat.
The validator reads the diff from the worktree.>
</change_scope>

<state_drift>
<discrepancies from state-reality verification — resume mode only>
</state_drift>

<task>
Execute the <PHASE_NAME> phase. Work from <WORKDIR_PATH>.
State files are in ~/docs/plans/do/<short-name>/.
Write phase outputs to the appropriate state file.
Update FEATURE.md phase_status when complete (approved, blocked, or in_review).
Do NOT advance current_phase — the outer loop handles phase transitions.
Read only the artifact sections needed for this phase.
Return under 2,000 characters with outcomes, evidence, blockers, and written artifact paths.
</task>

<workflow_rules_path><path to references/workflow-rules.md></workflow_rules_path>
<resource_efficiency_path><path to references/resource-efficiency.md></resource_efficiency_path>
"
)
```

## Milestone Orchestrator (EXECUTE)

Dispatched once per ready milestone group.
One group may contain multiple milestones only when they have no file or dependency overlap.

```
subagent(
  agent = "orchestrator",
  description = "Execute ready milestone group: <milestone-ids>",
  task = "
<current_phase>EXECUTE</current_phase>
<milestone_group>M-XXX[, M-YYY]</milestone_group>
<state_path>~/docs/plans/do/<short-name>/FEATURE.md</state_path>
<workdir_path><WORKDIR_PATH></workdir_path>
<interaction_mode><interactive|autonomous></interaction_mode>

<milestone_capsule>
<At most 1,000 words: task IDs, dependency state, changed behavior, active risks,
reviewed_head, and exact bundle/snapshot paths.>
</milestone_capsule>

<session_tail>
<Last 5 state-changing events from events.jsonl, or empty if first milestone>
</session_tail>

<task_bundle_paths>
~/docs/plans/do/<short-name>/tasks/TASK-XXX.md
</task_bundle_paths>

<resume_snapshot_path>~/docs/plans/do/<short-name>/SNAPSHOT.md</resume_snapshot_path>

<task>
Execute the milestone group.
Within each milestone, process tasks sequentially and read one task bundle at a time.
When the group contains multiple milestones, dispatch one implementer per milestone in a single message;
their files and dependencies have already been verified as non-overlapping.
Do not reread completed bundles or inline full state artifacts into child prompts.
For each task:
1. Verify preconditions from the task bundle before starting — if any fail, mark task as blocked
2. Dispatch implementer → shift-left → risk-routed review → update task bundle
3. Verify postconditions after completion
4. Update measured token fields and cost provenance in FEATURE.md (check budget if set)
At each milestone boundary: run /atcommit for atomic commits.
If deviations occur: follow the Plan Amendment Protocol (update PLAN.md task contracts, not just events.jsonl).
If the implementer or a reviewer surfaces an issue outside the task contract, file a `discovered_from` bundle
(Discovery Capture Protocol in phase-flow.md).
Append TASK_COMPLETE and MILESTONE_COMPLETE events to events.jsonl (each with `actor: orchestrator`).
Update task bundle frontmatter (status, verdict, review_passes, commit_sha).
Update FEATURE.md Progress section with completed tasks and commit SHAs.
Do NOT advance current_phase — the outer loop handles transitions.
Return under 2,000 characters with outcomes, evidence, blockers, metrics, and changed artifact paths.
</task>

<workflow_rules_path><path to references/workflow-rules.md></workflow_rules_path>
<resource_efficiency_path><path to references/resource-efficiency.md></resource_efficiency_path>
"
)
```

After all implementers in the group return, reconcile their state once and proceed to the next group.

## Bundle Generation (BUNDLE_GENERATION)

Dispatched once between PLAN_REVIEW approval and EXECUTE entry.
Skip if `tasks/` already exists (resume scenario).

```
subagent(
  agent = "orchestrator",
  description = "Generate task bundles: <short-name>",
  task = "
<current_phase>BUNDLE_GENERATION</current_phase>
<state_path>~/docs/plans/do/<short-name>/FEATURE.md</state_path>
<workdir_path><WORKDIR_PATH></workdir_path>

<artifact_paths>
plan: ~/docs/plans/do/<short-name>/PLAN.md
research: ~/docs/plans/do/<short-name>/RESEARCH.md
feature: ~/docs/plans/do/<short-name>/FEATURE.md
conventions: ~/docs/plans/do/<short-name>/CONVENTIONS.md
</artifact_paths>

<task>
Generate individual task execution bundles in ~/docs/plans/do/<short-name>/tasks/.
For each task in PLAN.md, create TASK-XXX.md using the bundle schema from state-file-schema.md:
1. Extract full task description, steps, and acceptance criteria from PLAN.md
2. Extract preconditions/postconditions — convert to verifiable checks with commands
3. Pre-compute the task contract (concrete pass/fail criteria including mandatory invariants)
4. Read relevant codebase files from <workdir_path> and extract architectural context
5. Find pattern references with file:line citations; include at most 10 lines of code only when the pattern is non-obvious
6. Set review_budget based on maximum external passes (Low=0, Medium=2, High=2)
7. Include verification commands with expected output
8. Summarize prior task outputs for tasks with dependencies

Each bundle must be self-contained — an implementer reading only that file
should have everything needed to execute the task without reading PLAN.md or RESEARCH.md.
Include only task-specific conventions not obvious from cited files.
Keep each bundle under 120 lines or 3,000 tokens.
Do not copy full research sections, full convention catalogs, or repeated acceptance criteria.
Once relevant conventions are embedded, the implementer receives the bundle without full CONVENTIONS.md.
Return under 2,000 characters with the bundle paths and validation result.
</task>
"
)
```

After generation, verify the task file count matches the task count in PLAN.md.

## Brainstormer (Pre-REFINE, Optional)

Dispatched from Step 4e of SKILL.md when the user chooses "Brainstorm first".

```
subagent(
  agent = "brainstormer",
  description = "Brainstorm before /do: <slug>",
  task = "
<brainstorm_file><path>~/docs/brainstorms/<slug>.md</path><content><full file content></content></brainstorm_file>
<idea><user's feature description></idea>
<today><TODAY></today>
<task>
Start a new brainstorm. The file has been created with the initial idea.
Analyze whether the idea is problem-shaped or solution-shaped, then begin the diagnostic progression.
Ask one question at a time. Update the brainstorm file after each exchange.
This brainstorm feeds into a /do workflow — the sharpened problem will inform the REFINE phase.
</task>
"
)
```

After completion, read `~/docs/brainstorms/<slug>.md` and pass the content as
`<brainstorm_context>` in the subsequent REFINE dispatch.

## Status Mode (Read-only)

If the user asks for status without resuming, dispatch with a read-only instruction:

```
<task>
Report status without making changes. Read FEATURE.md and report
current phase, progress percentage, last checkpoint, and blockers.
Do not modify state or code.
</task>
```
