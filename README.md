# code-factory

rtfpessoa's personal [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [OpenCode](https://opencode.ai) marketplace. It packages reusable skills and agents for structured feature delivery, docs workflows, and git operations.

## Quick Reference

| Command | Plugin | Purpose |
|---------|--------|---------|
| `/do` | productivity | Orchestrate feature delivery with phase/state tracking |
| `/rfc` | productivity | Write RFCs and design docs with iterative research |
| `/debug` | productivity | Systematic debugging with root-cause-first workflow |
| `/execplan` | productivity | Author/review/execute/resume execution plans |
| `/doc` | productivity | Create/update/improve/audit Markdown docs |
| `/workspace` | productivity | Manage Datadog remote development workspaces |
| `/reflect` | productivity | Capture session learnings into knowledge files |
| `/skill-workbench` | productivity | Create or improve skills and agents |
| `/review` | productivity | Review a pull request with structured findings |
| `/tour` | productivity | Guided code walkthroughs (interactive or written) |
| `/commit` | git | Create structured git commits |
| `/atcommit` | git | Organize and validate atomic commit sets |
| `/fixup` | git | Create fixup commits targeting earlier branch commits |
| `/pr` | git | Create PRs (draft/open) or mark draft as ready |
| `/branch` | git | Create a well-named feature branch |
| `/pr-fix` | git | Address PR review feedback end-to-end |
| `/fix-conflicts` | git | Resolve merge/rebase/cherry-pick/revert conflicts |
| `/worktree` | git | Create an isolated git worktree |

## Plugins

### productivity

**Skills:**

- [`/do`](#do-lifecycle) -- Full lifecycle feature orchestration (see detailed breakdown below).
- `/rfc` -- RFC authoring workflow with refinement, research, exploration, consistency check, and write phases.
- `/debug` -- Root-cause-first debugging protocol (`REPRODUCE -> INVESTIGATE -> FIX -> VERIFY`) with persistent state.
- `/doc` -- Documentation lifecycle management (create, update, improve, maintain, audit, sync, status) with templates.
- `/execplan` -- Manage ExecPlans in four modes: author, review, execute, and resume.
- `/review` -- Structured PR review across correctness, security, design, testing, and style.
- `/tour` -- Codebase tours in interactive or written modes.
- `/workspace` -- Datadog workspace lifecycle management (`create`, `list`, `delete`, `ssh`, `connect`, `validate`).
- `/reflect` -- Session learning extraction with confidence-based auto-apply/queue behavior.
- `/skill-workbench` -- Skill and agent creation/improvement toolkit.

**Agents:**

- `orchestrator` -- State-machine orchestrator for `/do` lifecycle execution.
- `refiner` -- Clarifies vague requests into actionable feature specs.
- `explorer` -- Read-only codebase mapper and extension-point finder.
- `researcher` -- Internal/external research synthesis.
- `planner` -- Plan author that converts research into executable tasks.
- `consistency-checker` -- Iteratively fixes contradictions in planning artifacts.
- `reviewer` -- Plan quality/completeness reviewer.
- `implementer` -- Plan-driven implementation agent.
- `spec-reviewer` -- Verifies implementation matches spec exactly.
- `code-quality-reviewer` -- Evaluates maintainability/testing/convention quality.
- `validator` -- Runs checks and validates acceptance criteria with evidence.
- `execplan` -- Specialized ExecPlan author/reviewer/executor persona.
- `skill-grader` -- Scores evaluation runs with pass/fail evidence.
- `skill-comparator` -- Blind A/B output comparator for skill evaluations.
- `memory-extractor` -- Extracts reusable learnings from session transcripts.

### git

**Skills:**

- `/commit` -- Structured commit flow with staging assistance and fixup detection.
- `/atcommit` -- Atomic commit grouping based on dependency analysis.
- `/fixup` -- Commit matching and autosquash-ready fixup creation.
- `/pr` -- PR creation flow with base detection, commit analysis, and ready-mode support.
- `/branch` -- Branch naming from ticket/description using local conventions.
- `/pr-fix` -- Pull and resolve PR review threads, apply changes, and reply/resolve.
- `/fix-conflicts` -- Conflict-state-aware conflict resolution workflow.
- `/worktree` -- Detached worktree creation from the default branch.

## `/do` Lifecycle

Full lifecycle feature orchestration — from vague idea to merged PR. Supports interactive (approve at each phase) or autonomous (`--auto`) modes. All state persists in `~/docs/plans/do/<name>/` for cross-session resume.

### Phase Diagram

```
REFINE ──→ RESEARCH ──→ PLAN_DRAFT ──→ PLAN_REVIEW ──→ EXECUTE ──→ VALIDATE ──→ DONE
                            ^               |    |           ^          |
                            |               v    v           |          v
                            |          consistency  +--------+-- (fix forward) ──+
                            |            check      |
                            |               |       |
                            |               v       |
                            +──── (changes requested)
```

### Phase Details

| Phase | Agents | What Happens | Output |
|-------|--------|-------------|--------|
| **REFINE** | `refiner` | Clarify vague requests. Propose 2-3 approaches with trade-offs, get user preference. One question at a time (prefer multiple choice). | Refined spec: problem statement, chosen approach, scope, acceptance criteria |
| **RESEARCH** | `explorer` + `researcher` (parallel) | Explorer maps local codebase (modules, patterns, conventions). Researcher searches Confluence + external docs. Both mandatory. | Context, assumptions, constraints, risks, open questions |
| **PLAN_DRAFT** | `planner` | Convert research into milestones and tasks. Plan embeds relevant context inline (not links only). | Milestones, task breakdown (TDD-first), validation strategy, recovery plan |
| **PLAN_REVIEW** | `consistency-checker` → `reviewer` | **Step 1:** Consistency checker fixes contradictions, mismatched IDs, path inconsistencies, terminology drift (edits directly, max 10 iterations, `sonnet` model). **Step 2:** Reviewer critiques coverage, paths, dependencies, safety, executability. May loop back to PLAN_DRAFT. | Review report, required changes |
| **EXECUTE** | `implementer` + `spec-reviewer` + `code-quality-reviewer` | Batched execution with two-stage review (see below). TDD enforced for behavioral tasks. Atomic commits at milestone boundaries via `/atcommit`. | Implemented code, atomic commits |
| **VALIDATE** | `validator` | Run automated checks + quality scorecard (1-5 per dimension). All dimensions must score ≥ 3/5. May loop back to EXECUTE. | Validation report, acceptance evidence, quality scorecard |
| **DONE** | — | Write retrospective, run final test suite. Create PR (interactive: user chooses; autonomous: auto-creates). | PR URL or merge commit |

### EXECUTE Phase — Batch Loop

```
Plan Critical Review → Execute Batch (3 tasks) → Batch Report → Feedback → Next Batch
                             |                                       ^
                             v                                       |
                       Per-task loop:                          (loop batches)
                       Dispatch implementer → Spec review → Code quality review → Next task
                             ^                    |                  |
                             +── Fix gaps ←── ISSUES           Fix issues
                             +── Fix quality ←──────────────── ISSUES

                       At MILESTONE BOUNDARY (all milestone tasks done + tests pass):
                       Run /atcommit → group changes by concept → 3-5 atomic commits
```

**Per-task sequence:**

1. Dispatch fresh `implementer` with full task text + scene-setting context (milestone position, prior task summary, upcoming tasks, discoveries, architecture)
2. Implementer asks questions → answers provided → implements → self-reviews → reports (no commit)
3. `spec-reviewer` verifies implementation matches spec (nothing missing, nothing extra, nothing misunderstood)
4. If issues → implementer fixes → re-review (loop until compliant)
5. `code-quality-reviewer` assesses maintainability, testing, conventions, plan alignment
6. If critical issues → implementer fixes → re-review (loop until approved)
7. Mark task complete, update state, proceed to next task in batch (no commit yet)

**TDD enforcement** (behavioral tasks only):

1. Write failing test (complete, not placeholder)
2. Run test — verify it fails for the expected reason
3. Write minimal implementation to pass the test
4. Run test — verify it passes and no regressions

Code written before its test is deleted and restarted.

**Milestone boundary commits:** `/atcommit` analyzes file dependencies and groups changes by concept (e.g., package + tests, integration layer, config + wiring). Typical result: 3-5 atomic commits per feature.

**Stop conditions:** missing dependencies, systemic test failures, unclear instructions, repeated verification failures, or plan-invalidating discoveries.

### Workspace Modes

| Mode | Description |
|------|-------------|
| Worktree + branch (default) | Isolated git worktree with feature branch — main workspace stays clean |
| Branch only | Feature branch in current directory |
| Current branch | Work on the already checked-out branch |
| Datadog workspace | Remote cloud development environment via `/workspace` |

### State Files

All artifacts live in `~/docs/plans/do/<name>/`:

| File | Written After | Contents |
|------|---------------|----------|
| `FEATURE.md` | Creation | YAML frontmatter, acceptance criteria, progress, decisions, outcomes |
| `RESEARCH.md` | RESEARCH | Codebase map, research brief, findings, open questions |
| `PLAN.md` | PLAN_DRAFT | Milestones, task breakdown, validation strategy, recovery |
| `REVIEW.md` | PLAN_REVIEW | Review feedback, required changes |
| `VALIDATION.md` | VALIDATE | Test results, acceptance evidence, quality scorecard |

### Input Isolation

User descriptions are wrapped in `<feature_request>` tags to prevent prompt injection into subagents.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/rtfpessoa/code-factory.git
   cd code-factory
   ```

2. Run bootstrap:

   ```bash
   ./init.sh
   ```

   `init.sh` performs the full local setup:

   - Installs or updates `rtk` via `cargo install --git https://github.com/rtk-ai/rtk --config net.git-fetch-with-cli=true`.
   - Symlinks root configs:

     | Source | Destination |
     |--------|-------------|
     | `mcp.json` | `~/.mcp.json` |
     | `settings.json` | `~/.claude/settings.json` |
     | `opencode.jsonc` | `~/.config/opencode/opencode.jsonc` |

   - Symlinks files from `hooks/` into `~/.claude/hooks/`.
   - Regenerates `.opencode/` assets by running `./sync-opencode.sh`.
   - Symlinks generated `.opencode/{skills,agents,commands,plugins}` into `~/.config/opencode/`.
   - Symlinks `.githooks/*` into `.git/hooks/` for this local clone.

   If a destination already exists as a regular file, bootstrap records an error and exits non-zero so you can fix the conflict explicitly.

3. Validate the repo state:

   ```bash
   make all
   ```

## Development Notes

- Source of truth is under `productivity/` and `git/`; do not edit generated files under `.opencode/` directly.
- `make all` runs checks (`make check`) and config linting (`make lint`).
- `make check` also verifies OpenCode sync freshness (`./sync-opencode.sh --check`).
- Re-run `./init.sh` after changing local bootstrap-managed files.

## Configuration Files

### `settings.json` (Claude Code)

Claude Code global configuration: environment flags, permission rules, default model (`opus`), MCP server enablement, installed marketplaces/plugins, and hooks (including Stop-hook invocation of `/reflect`).

### `opencode.jsonc` (OpenCode)

OpenCode CLI configuration in JSONC. Includes provider setup (Anthropic, OpenAI, Google, NVIDIA NIM, LM Studio), default model selection (`openai/gpt-5.3-codex`), permission policies, agent presets, and MCP wiring.

### `mcp.json` (MCP servers)

Declares Atlassian, Datadog, and chrome-devtools MCP servers for Claude Code.

### `sync-opencode.sh`

Generates `.opencode/skills`, `.opencode/agents`, and `.opencode/commands` from plugin source definitions, including frontmatter/tool-name transformations and stale-check mode (`--check`).
