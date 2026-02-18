# State File Schema

Reference for the /do skill's state file format. Load when creating or parsing state files.

## Directory Structure

```
.plans/do/<run-id>/
  FEATURE.md              # Canonical state and living document
  RESEARCH.md             # Codebase map + research brief (written after RESEARCH)
  PLAN.md                 # Milestones, tasks, validation strategy (written after PLAN_DRAFT)
  REVIEW.md               # Review feedback (written after PLAN_REVIEW)
  VALIDATION.md           # Validation results with evidence (written after VALIDATE)
```

## FEATURE.md (main state file)

```markdown
---
schema_version: 1
run_id: 20250212-user-auth
repo_root: /path/to/repo
worktree_path: /path/to/worktrees/repo-user-auth  # set during EXECUTE setup (null if no worktree)
workdir_mode: worktree  # worktree | branch_only | current_branch
branch: feature/user-auth
base_ref: abc123
current_phase: EXECUTE
phase_status: in_progress
milestone_current: M-002
last_checkpoint: 2025-02-12T10:30:00Z
last_commit: def456
interaction_mode: interactive  # or "autonomous"
---

# <Feature Name>

<Brief description of what this feature does>

## Acceptance Criteria

**Functional Criteria** (binary pass/fail):

| # | Criterion | Verification Method |
|---|-----------|-------------------|
| F1 | <What must be true> | <Command, test, or observation to verify> |

**Edge Case Criteria** (binary pass/fail):

| # | Criterion | Verification Method |
|---|-----------|-------------------|
| E1 | <Edge case handled> | <How to trigger and verify> |

## Progress

- [x] (2025-02-12 09:45Z) REFINE phase complete
- [x] (2025-02-12 10:00Z) RESEARCH phase complete
- [x] (2025-02-12 10:30Z) PLAN_DRAFT phase complete
- [x] (2025-02-12 11:00Z) PLAN_REVIEW phase complete - approved
- [x] (2025-02-12 11:15Z) T-001: Set up project structure (commit abc123)
- [ ] T-002: Implement core logic
- [ ] T-003: Add tests

## Surprises and Discoveries

<Unexpected findings during implementation>

## Decisions Made

<Decision log with rationale>

- Decision: <what was decided>
  Rationale: <why>
  Date: <timestamp>

## Open Questions

<Unresolved questions requiring input>

## Outcomes and Retrospective

<Final summary when complete - what worked, what didn't, lessons learned>
```

## RESEARCH.md

```markdown
# Research: <Feature Name>

## Problem Statement
- (Summarize the problem clearly - show deep understanding)

## Current Behavior
- (What happens today)
- (If a bug: include minimal repro and expected vs actual)

## Desired Behavior
- (What "done" means - verifiable outcomes)

## Codebase Map

### Entry Points
- `path/to/file:function` - Description

### Main Execution Call Path
- `caller` → `callee` → `next` (describe the flow)

### Key Types/Functions
- `path/to/file:Type` - Description
- `path/to/file:function` - Description

### Integration Points
- Where to add new functionality
- Existing patterns to follow

### Conventions
- Naming patterns, file organization, testing patterns

### Risk Areas
- Complex or fragile code requiring careful changes

## Findings (facts only)
- (Bullets; each includes `file:symbol` or `MCP:<tool> → <result>` or `websearch:<url> → <result>`)
- (Facts only - no assumptions here)

## Hypotheses (if needed)
- H1: <hypothesis> - <evidence supporting it>
- H2: <hypothesis> - <evidence supporting it>
- (Clearly marked as hypotheses, not facts)

## Solution Direction

### Approach
- (Strategic direction: what pattern/strategy, which components affected)
- (High-level only - NO pseudo-code or code snippets)
- (YES: module names, API/pattern names, data flow descriptions)

### Why This Approach
- (Brief rationale - what makes this the right choice)

### Alternatives Rejected
- (What other options were considered? Why not chosen?)

### Complexity Assessment
- **Level**: Low / Medium / High
- (1-2 sentences on what drives the complexity)

### Key Risks
- (What could go wrong? Areas needing extra attention)

## Research Brief

### Libraries/APIs
- Library name: key methods, usage patterns, gotchas

### Best Practices
- Pattern to follow with brief explanation

### Common Pitfalls
- What to avoid and why

### Internal References (Confluence)
- [Page](url) - Summary of what it covers

### External References
- [Source](url) - Summary of what it covers

## Open Questions
- (Questions that need answers before or during planning)
- (Mark as BLOCKING if it prevents planning)
```

## PLAN.md

```markdown
# Plan: <Feature Name>

**Goal:** One sentence describing what this builds
**Architecture:** 2-3 sentences about the approach
**Tech Stack:** Key technologies, libraries, and frameworks involved

## Research Reference
- **Source**: path to RESEARCH.md
- **Problem**: 1-2 sentence summary
- **Solution direction**: 1-2 sentence summary from research recommendation

## Scope

### In Scope
- (Bullet list of what this plan covers)

### Out of Scope
- (Bullet list of what is explicitly NOT part of this change)

## File Impact Map

| File | Change Type | Risk | Description |
|------|-------------|------|-------------|
| `path/to/file.ts` | New / Modify / Extend / Delete | Low / Medium / High | Brief description |

Change types:
- **New**: File created from scratch
- **Modify**: Existing file, changing behavior
- **Extend**: Existing file, adding capability without changing existing behavior
- **Delete**: Removing file or significant code block

## Milestones

### M-001: <Milestone Name>
**Scope**: What exists after this milestone
**Verification**: How to prove it works
**Dependencies**: What must be true before starting

### M-002: <Milestone Name>
...

## Task Breakdown

### Milestone M-001

Each task MUST be broken into bite-sized steps (one action per step). Tasks introducing new behavior MUST follow TDD-first structure. NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.

- [ ] T-001 (M-001) Task description
  - Files: `path/to/file.ts` (New/Modify), `tests/path/to/file.test.ts` (New/Modify)
  - Risk: Low | Medium | High
  - Steps (TDD-first — mandatory for behavior changes):
    1. Write failing test (include complete test code — not "add a test for X")
    2. Run test → `<exact command>` → expected: FAIL with `<specific error message>`
    3. Implement minimal code to pass (include complete code or precise file:line edit instructions)
    4. Run test → `<exact command>` → expected: PASS (and all existing tests still pass)
    5. Commit → `<commit message>`
  - Acceptance: What "done" looks like (observable behavior, not internal state)
- [ ] T-002 (M-001) Task description
  - Depends on: T-001
  - Risk: Medium
  - Steps: (TDD-first when behavior changes; direct edit → verify → commit for config/refactor)
  - Acceptance: What "done" looks like

### Milestone M-002
- [ ] T-003 (M-002) ...

## Integration Points
- (List boundaries this change touches: APIs, file formats, inter-component contracts)
- (Flag any breaking changes or version considerations)

## Risk Guidelines

| Risk Level | When to Apply | Execution Approach |
|------------|---------------|-------------------|
| Low | Simple changes, additive, well-understood patterns | Execute normally |
| Medium | Multiple files, API interactions, state changes | Review code paths before committing |
| High | Security, data migrations, core logic changes | Think through ALL edge cases before writing code |

## Validation Strategy

### Existing Test Coverage
- (What existing tests already validate parts of this?)

### New Tests Required

| Test Name | Type | File | Description |
|-----------|------|------|-------------|
| test_name | Unit / Integration / E2E | path or "new file" | What it verifies |

### Test Infrastructure Changes
- [ ] None required
- [ ] Extending existing test framework
- [ ] Adding new test files to existing framework
- [ ] Significant test infrastructure changes (describe)

### Per-Milestone Validation
- M-001: Command to run, expected output
- M-002: Command to run, expected output

### Final Acceptance
- [ ] Criterion 1: How to verify
- [ ] Criterion 2: How to verify

## Assumptions
- (List assumptions made during planning that could be wrong)
- (These become verification points before/during implementation)

## Open Questions
- (Questions that must be answered before implementing specific tasks)
- (Flag which task is blocked by each question)

## Recovery and Idempotency

### Safe to Repeat
- Tasks that can run multiple times

### Requires Care
- Tasks with side effects

### Rollback Plan
- How to revert if needed
```
