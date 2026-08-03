# `/do` Artifact Contract

Use these schemas to keep runs resumable without turning state into a second implementation.
The top agent owns every file.

## Size Limits

| Artifact | Limit | Purpose |
|-|-|-|
| `FEATURE.md` | 150 lines | Canonical goal, criteria, decisions, progress, outcomes |
| `RESEARCH.md` | 150 lines | Unique repository and external evidence |
| `CONVENTIONS.md` | 150 lines | Only conventions that constrain this change |
| `PLAN.md` | 150 lines | Approach, task order, risks, validation |
| `REVIEW.md` | 100 lines | Final reviewer findings and dispositions |
| `VALIDATION.md` | 100 lines | Commands, results, acceptance evidence |
| `SNAPSHOT.md` | 60 lines | Resume-only current state and next action |
| `tasks/TASK-*.md` | 80 lines each | One separable implementation contract |

Trim superseded narrative before adding more content.
Do not duplicate the same evidence across artifacts.
Every completed run has every non-task artifact listed above.
Task bundles are conditional and exist only when the plan contains a separable task.
When a gate is fully reused, record its source and `No unique evidence added` under the required headings.

## `FEATURE.md`

```yaml
---
name: <human-readable name>
short_name: <kebab-case, max 40 chars>
profile: fast | standard | deep
status: active | blocked | delivered
repo_root: <absolute path>
branch: <branch>
base_ref: <ref>
pr_url: <url or null>
last_checkpoint: <ISO8601>
token_budget_total: <integer or null>
token_budget_scope: completed_delegates | null
---
```

Required body headings:

1. `## Goal`
2. `## Acceptance Criteria`
3. `## Decisions`
4. `## Progress`
5. `## Discovered Work`
6. `## Outcome`

Keep criteria binary.
Keep decisions as one-line choice plus rationale.
Keep discovered work in one list unless an item blocks delivery.

## `RESEARCH.md`

Record only evidence that changed or justified the plan:

- repository path and relevant symbol
- authoritative external source when required
- observed convention
- unresolved gap and its effect

Do not narrate search history.

## `CONVENTIONS.md`

Record exact commands, patterns, and constraints the implementation must follow.
Do not restate repository instructions or general programming knowledge.

## `PLAN.md`

Required headings:

1. `## Summary`
2. `## Tasks`
3. `## Risks`
4. `## Validation`
5. `## Delivery`

Fast mode may have one task.
Standard and Deep modes use dependencies only when they affect execution order.
Do not manufacture milestones around file groups.

## Task Bundles

Create a task bundle only for a separable task.

```yaml
---
id: TASK-001
status: pending | in_progress | complete | blocked
owner: top-agent | <leaf task name>
depends_on: []
files: []
---
```

Required body:

- outcome
- binary acceptance criteria
- owned files
- focused validation
- relevant convention or risk

Do not copy the full plan, research, or repository instructions.

## `REVIEW.md`

Record:

- reviewed base/head
- reviewer identity
- acceptance-criterion verdict
- proven findings with file/line evidence
- fix disposition
- focused-recheck verdict when used

One reviewer session owns the entire review record.

## `VALIDATION.md`

For every command record:

- command
- scope
- exit status
- concise result
- whether it ran before or after the final review fix

Map final evidence to every acceptance criterion.
Do not paste full build logs.

## `SNAPSHOT.md`

Include only:

- profile and status
- branch and current HEAD
- completed task IDs
- next task or blocker
- last green checks
- final-review state
- PR URL/status when delivered

Regenerate after implementation, review, validation, blocking, and delivery.

## `events.jsonl`

Each line is one JSON object:

```json
{"ts":"<ISO8601>","type":"<EVENT>","actor":"top-agent","summary":"<one line>"}
```

Permitted events:

- `SESSION_START`
- `PROFILE_SELECTED`
- `DECISION`
- `IMPLEMENTATION_COMPLETE`
- `REVIEW_COMPLETE`
- `VALIDATION_COMPLETE`
- `DELIVERY_COMPLETE`
- `BLOCKED`

Optional fields may include task ID, commit SHA, PR URL, measured tokens, or duration.
Never log prompts, secrets, complete tool output, individual waits, or status polls.

## Resume Reconciliation

Git is authoritative.
On resume:

1. Verify repo, branch, and HEAD.
2. Compare completed task SHAs with `git log`.
3. Compare dirty files with active task ownership.
4. Update stale progress and snapshot entries.
5. Resume from the first unmet acceptance criterion.

Record one `DECISION` event when reconciliation changes state.
