# code-factory

rtfpessoa's personal marketplace for [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [Codex](https://github.com/openai/codex), and [pi.dev](https://pi.dev). It packages reusable skills and agents for structured feature delivery, docs workflows, and git operations.

## Quick Reference

| Command | Plugin | Purpose |
|-|-|-|
| `/do` | productivity | Orchestrate feature delivery with phase/state tracking |
| `/rfc` | productivity | Write RFCs and design docs with iterative research |
| `/debug` | productivity | Systematic debugging with root-cause-first workflow |
| `/doc` | productivity | Create/update/improve/audit Markdown docs |
| `/workspace` | productivity | Manage Datadog remote development workspaces |
| `/reflect` | productivity | Capture session learnings into knowledge files |
| `/wrap-up` | productivity | End-of-session checklist: ship, reflect, publish |
| `/brag` | productivity | Update brag document with recent accomplishments |
| `/daily` | productivity | Daily work journal and weekly summaries in Obsidian vault |
| `/notes` | productivity | Obsidian notes: 1:1s, meetings, career plans, promotions |
| `/performance-feedback` | productivity | Write evidence-backed performance reviews |
| `/brainstorm` | productivity | Sharpen problems or compare disposable divergent prototypes |
| `/change-quiz` | productivity | Explain a branch or PR, then test maintainer understanding read-only |
| `/datadog` | productivity | Query Datadog products (logs, metrics, APM, monitors) via pup CLI |
| `/code-simplify` | productivity | Simplify and refactor code for clarity without changing behavior |
| `/ai-cli` | productivity | Evaluate and improve CLI design for AI agent usage |
| `/openspec-propose` | productivity | Create OpenSpec changes and generate proposal/design/spec/task artifacts |
| `/openspec-explore` | productivity | Explore OpenSpec ideas and artifacts without implementation |
| `/openspec-new-change` | productivity | Create an OpenSpec change scaffold without writing artifacts |
| `/openspec-continue-change` | productivity | Create the next ready artifact for an OpenSpec change |
| `/openspec-ff-change` | productivity | Generate all artifacts required for OpenSpec implementation |
| `/openspec-update-change` | productivity | Reconcile existing OpenSpec planning artifacts without editing code |
| `/openspec-apply-change` | productivity | Implement pending tasks from an OpenSpec change |
| `/openspec-sync-specs` | productivity | Merge delta specs into main specs without archiving |
| `/openspec-verify-change` | productivity | Verify implementation against OpenSpec artifacts |
| `/openspec-archive-change` | productivity | Archive completed OpenSpec changes |
| `/openspec-bulk-archive-change` | productivity | Preflight and archive a selected batch of OpenSpec changes |
| `/openspec-onboard` | productivity | Learn OpenSpec through a guided real change |
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

- `/review` -- Structured PR review across correctness, security, design, testing, and style.
- `/tour` -- Codebase tours in interactive or written modes.
- `/workspace` -- Datadog workspace lifecycle management (`create`, `list`, `delete`, `ssh`, `connect`, `validate`).
- `/reflect` -- Session learning extraction with confidence-based auto-apply/queue behavior. Includes self-improvement analysis for skill gaps, friction, and automation opportunities.
- `/wrap-up` -- End-of-session checklist: commits via `/atcommit`, deploys if available, cleans up tasks, runs `/reflect` for learnings, and drafts publishable content.
- `/brag` -- Brag document management: auto-collects work from GitHub, Jira, Confluence, git, and daily logs; asks interactive questions for undiscoverable work; maintains monthly docs at `~/log/YYYY-MM/brag.md`.
- `/daily` -- Daily work journal and weekly summaries in Obsidian: captures work activity, meetings, achievements, team pulse, travel, learning, and kudos. Weekly summary mode (`/daily summary`) aggregates daily notes with GitHub PRs, Jira tickets, and Confluence pages into dual-format output (Confluence + Slack). Resolves people names via Obsidian People directory with wikilinks and backlinks. Feeds into `/brag` as a data source.
- `/notes` -- Obsidian notes management: 1:1 records, meeting notes, per-person career plans, promotion proposals, achievements tracking, and general notes. Shares `~/docs/People/` directory with `/daily` for graph integration.
- `/performance-feedback` -- Evidence-backed performance review writer: gathers data from 1:1 notes, achievements, daily logs, brag docs, GitHub PRs, Jira tickets, and Confluence pages for a specific person over a review period, then synthesizes into structured feedback by dimension (impact, technical quality, collaboration, growth, communication).
- `/brainstorm` -- Problem-focused brainstorming by default, with an explicit `--prototype` mode for comparing three to five disposable variants of one decision. Saves brainstorms and learned requirements to `~/docs/brainstorms/`.
- `/change-quiz` -- Read-only branch or PR comprehension check. Reports behavioral intent, interactions, blast radius, deviations, and maintainer mental-model changes, then asks a five-to-eight-question graded quiz one question at a time. Passing requires every critical answer and at least 80 percent overall accuracy; the result is advisory and never merges or updates a PR.
- `/datadog` -- Datadog product query via pup CLI: APM, logs, metrics, monitors, error tracking, RUM, infrastructure, security signals, incidents, SLOs, synthetics, CI/CD, and 30+ other API domains.
- `/code-simplify` -- Code simplification across any scope (file, directory, package, branch diff, staged changes, or entire repo). Preserves behavior while improving clarity and maintainability.
- `/ai-cli` -- CLI design evaluation and improvement for AI agents: scores against 8 Agent DX axes aligned with the AXI (Agent eXperience Interface) framework (machine-readable output, raw payload input, schema introspection, context window discipline, input hardening, safety rails, agent knowledge packaging, efficiency & composition), recommends prioritized improvements, and guides implementation.
- `/openspec-*` -- The complete 12-workflow OpenSpec suite: propose, explore, scaffold, one-artifact continuation, fast-forward, planning reconciliation, implementation, spec sync, verification, single/bulk archive, and guided onboarding. The [MIT-licensed upstream workflows](https://github.com/Fission-AI/OpenSpec/tree/main/skills) are adapted to local conventions with store-aware paths, decision-first reviews, evidence-backed verification, deviation handling, and CLI-driven archiving. The CLI command `openspec update` regenerates assistant instructions; `/openspec-update-change` instead revises one change's existing planning artifacts.
- `/skill-workbench` -- Skill and agent creation/improvement toolkit.

The exploration, planning, brainstorming, implementation, and PR workflows share an unknowns-aware layer:
they retrieve discoverable answers before asking questions, order remaining questions by blast radius,
analyze references for behavior rather than transliterating source, surface consequential blindspots,
keep deviations in canonical artifacts, and package reviewer context proportionally to change complexity.
These behaviors adapt ideas from the MIT-licensed
[finding-unknowns-skills](https://github.com/Neeeophytee/finding-unknowns-skills) project without importing its skills or instruction text wholesale.

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

- `skill-grader` -- Scores evaluation runs with pass/fail evidence.
- `skill-comparator` -- Blind A/B output comparator for skill evaluations.
- `brainstormer` -- Problem-focused thinking partner for brainstorming sessions.
- `red-teamer` -- Adversarial reviewer finding failure modes, flawed assumptions, and edge cases.
- `code-simplifier` -- Single-file code simplification agent for clarity, consistency, and maintainability.
- `memory-extractor` -- Extracts reusable learnings from session transcripts.

### git

**Skills:**

- `/commit` -- Structured commit flow with staging assistance and fixup detection.
- `/atcommit` -- Atomic commit grouping based on dependency analysis.
- `/fixup` -- Commit matching and autosquash-ready fixup creation.
- `/pr` -- PR creation flow with base detection, commit analysis, and ready-mode support. Medium and complex PRs add available demonstrations, the problem and chosen bet, expert-review questions, known deviations, and explicit non-goals; simple PRs stay concise.
- `/branch` -- Branch naming from ticket/description using local conventions.
- `/pr-fix` -- Pull and resolve PR review threads, apply changes, and reply/resolve. Supports `--auto` for bot/CI automation and `--auto-human` for fully autonomous mode.
- `/fix-conflicts` -- Conflict-state-aware conflict resolution workflow.
- `/worktree` -- Detached worktree creation from the default branch.

## `/do` Lifecycle

Full lifecycle feature orchestration — from vague idea to merged PR. Supports interactive (approve at each phase) or autonomous (`--auto`) modes. Phase gates reuse complete, user-approved evidence instead of repeating refinement, research, or planning. Review depth and agent count scale with task risk, and compact task bundles keep nested prompts bounded. All state persists in `~/docs/plans/do/<name>/` for cross-session resume.

### Phase Diagram

```
REFINE ──→ RESEARCH ──→ PLAN_DRAFT ──→ PLAN_REVIEW ──→ EXECUTE ──→ VALIDATE ──→ DONE
                            ^               |                ^          |
                            |               v                |          v
                            +──── (changes requested)        +-- (focused fix)
```

### Phase Details

| Phase | Agents | What Happens | Output |
|-|-|-|-|
| **REFINE** | `refiner` when evidence is incomplete | Validate that the prepared context has a clear problem, scope, behavior, and acceptance criteria; reuse it when complete. | Refined spec or evidence-reuse record |
| **RESEARCH** | `explorer` and/or `researcher` for specific gaps | Fill only missing local, internal, or external evidence. Reference implementations are analyzed as semantic specifications with translation and license gaps. | Context, assumptions, constraints, risks, open questions |
| **PLAN_DRAFT** | `planner` | Convert research into milestones and tasks. The plan summarizes decision-relevant evidence and cites artifact paths without copying full research. | Milestones, task breakdown (TDD-first), validation strategy, recovery plan |
| **PLAN_REVIEW** | `reviewer`; optional risk-specific `red-teamer` | Review correctness once, adding an independent challenge only for a named high-risk assumption. | Review report, required changes |
| **EXECUTE** | `implementer`; `task-critic` for Medium/High risk | Batched execution with deterministic shift-left checks and a cumulative review budget. TDD is enforced for behavioral tasks. Atomic commits happen at milestone boundaries via `/atcommit`. | Implemented code, atomic commits |
| **VALIDATE** | `validator` | Run automated checks and acceptance validation. Reuse an integrated review when `HEAD` has not changed. May loop back to EXECUTE for a focused fix. | Validation report, acceptance evidence, quality scorecard |
| **DONE** | — | Write retrospective, run final tests, summarize deviations, discoveries, unresolved review questions, and the key learning from canonical state, then offer PR creation. | PR URL or merge commit |

### EXECUTE Phase — Batch Loop

```
Pre-flight → Execute ready task → Shift-left checks → Risk-routed review → Milestone report
                     ^                                            |
                     +--------------- focused fix -----------------+
```

**Per-task sequence:**

1. Dispatch a fresh `implementer` with one self-contained task bundle and a compact scene-setting capsule.
2. Implementer asks questions → answers provided → implements → self-reviews → reports (no commit)
3. **Shift-left validation** (deterministic — orchestrator runs directly): lint + format + type-check. Auto-fixes formatting. Returns to implementer if errors persist.
4. Low-risk tasks stop after self-review and checks. Medium/High tasks get one integrated `task-critic` pass.
5. A rejection gets one focused fixer/recheck within the cumulative budget; a second rejection blocks.
6. High-risk tasks may use the second review slot for a distinct trust, security, concurrency, retry, or destructive-data risk.
7. Mark the task complete, record runtime telemetry, and proceed (no commit yet).

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
|-|-|
| Worktree + branch (default) | Isolated git worktree with feature branch — main workspace stays clean |
| Branch only | Feature branch in current directory |
| Current branch | Work on the already checked-out branch |
| Datadog workspace | Remote cloud development environment via `/workspace` |

### State Files

All artifacts live in `~/docs/plans/do/<name>/`:

| File | Written After | Contents |
|-|-|-|
| `FEATURE.md` | Creation | YAML frontmatter, acceptance criteria, progress, decisions, outcomes |
| `RESEARCH.md` | RESEARCH | Codebase map, research brief, findings, open questions |
| `PLAN.md` | PLAN_DRAFT | Milestones, task breakdown, validation strategy, recovery |
| `REVIEW.md` | PLAN_REVIEW | Review feedback, required changes |
| `VALIDATION.md` | VALIDATE | Test results, acceptance evidence, quality scorecard |
| `SNAPSHOT.md` | Each transition | Capped resume context for the next task or phase |
| `events.jsonl` | Creation through DONE | Append-only lifecycle, dispatch, review, token, and duration telemetry |

### Resource Controls and Telemetry

`/do --token-budget <tokens>` enforces an exact token-denominated ceiling. The legacy
`--budget <USD>` form is enforced only when the runtime supplies cost or an explicitly configured
model rate; otherwise cost remains `null` with `cost_source: unknown`, and `/do` requires a token
ceiling instead of inventing a price.

Telemetry preserves runtime token categories and labels metrics as `measured`, `derived`, or
`lower_bound`. Batch reports include tokens, duration, agent/tool/wait activity, discoveries, and
their provenance. Reviews use one ledger keyed by scope and `HEAD`, so unchanged accepted work is
not reviewed again.

Codex generation maps read-heavy and orchestration roles to `gpt-5.6-terra` with Medium effort.
Implementation and named adversarial roles (`implementer`, `task-critic`, and `red-teamer`) use
`gpt-5.6-sol` with High effort. Portable agent instructions keep abstract roles; the
platform-specific mapping and its validation live in `sync-codex.sh`.

### Codex Session Audits

`/reflect` includes a bounded deterministic analyzer for a Codex root session and all unique
descendants:

```bash
python3 productivity/skills/reflect/scripts/analyze-codex-session.py --list-roots --days 7
python3 productivity/skills/reflect/scripts/analyze-codex-session.py --root <root-id> --days 7
```

Add `--json` for machine-readable output. The analyzer uses one final cumulative token record per
thread, sanitizes prompt previews, labels observed activity as a lower bound, skips malformed JSONL
safely, and never estimates dollar cost.

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

   - Symlinks root configs:

     | Source | Destination |
     |-|-|
     | `settings.json` | `~/.claude/settings.json` |
     | `claude/CLAUDE.md` | `~/.claude/CLAUDE.md` |
     | `pi-settings.json` | `~/.pi/agent/settings.json` |

   - Installs MCP servers from `mcp.json` into Claude Code and Codex and generates the Pi MCP adapter config.
   - Installs or updates the OpenSpec CLI with npm (`@fission-ai/openspec@latest` by default).
   - Symlinks files from `hooks/` into `~/.claude/hooks/`.
   - Symlinks generated `.codex/{skills,agents}` and managed `codex/rules/*.rules` into `~/.codex/`.

   If a destination already exists as a regular file, bootstrap records an error and exits non-zero so you can fix the conflict explicitly.

3. Validate the repo state:

   ```bash
   make all
   ```

## Development Notes

- Source of truth is under `productivity/` and `git/`; do not edit generated files under `.codex/` or `.pi/` directly.
- OpenSpec uses a hybrid model: `init.sh` keeps the CLI up to date through npm, while this repo owns adapted copies of the 12 upstream workflow skills so generated global agent assets remain deterministic. Do not run project-level `openspec update` to refresh these copies; edit the canonical OpenSpec skill directories under `productivity/skills/` and run the repository sync targets. Set `OPENSPEC_INSTALL=0` to skip CLI installation, `OPENSPEC_NPM_PACKAGE=@fission-ai/openspec@1.3.1` to pin a package, or `OPENSPEC_NPM_CACHE=<path>` to override the npm cache used by bootstrap.
- `make all` runs checks (`make check`) and config linting (`make lint`).
- `make check` also verifies Codex/Pi sync freshness and managed Codex config/rules.
- Re-run `./init.sh` after changing local bootstrap-managed files.

## Configuration Files

### `settings.json` (Claude Code)

Claude Code global configuration: environment flags, permission rules, default model (`opus`), MCP server enablement, installed marketplaces/plugins, and hooks (including Stop-hook invocation of `/reflect`).

### `mcp.json` (MCP servers)

Declares MCP servers for Claude Code, Codex, and pi.dev.
`init.sh` installs these into Claude Code and Codex, and `sync-pi.sh` generates `.pi/mcp.json` for `pi-mcp-adapter`.

### `sync-codex.sh`

Generates `.codex/skills` (with collapsed single-line frontmatter and per-skill `agents/openai.yaml` metadata) and `.codex/agents/*.toml` for [OpenAI Codex](https://github.com/openai/codex). Stale-check mode (`--check`).

### `codex/config.toml` and `codex/rules/`

Managed Codex defaults. `codex/config.toml` sets `gpt-5.6-sol` with high reasoning effort and uses granular approval policy settings so Codex does not pause for sandbox approval prompts during non-interactive runs.
Filesystem and network access come from the `code-factory` permission profile: Codex can read most files, write only selected development roots (`~/dev`, `~/dd`, `~/go`, `~/docs`, `~/Downloads`, `/tmp`, and `/private/tmp`), write narrow Datadog auth/cache paths, and allow `~/.ssh/known_hosts` write access for git host key updates.
Managed shell environments set `TMPDIR`, `TMP`, and `TEMP` to `/tmp` so command temp files are created under an approved writable root.

`codex/rules/code-factory.rules` prompts for concrete dangerous command prefixes such as system mutation, destructive recursive deletion of high-value roots, history-rewriting git operations, and global package installs. Codex execpolicy rules are prefix-based, not full shell-string scanners, so broad shell commands like `zsh -lc "..."` are not inspected the same way Claude's Bash hook can inspect command text.

### `install-codex-mcp.sh`

Updates `~/.codex/config.toml` from `codex/config.toml` and `mcp.json`, preserving unrelated Codex settings and unrelated MCP servers.
The generated sections are marked in the TOML file so rerunning `./init.sh` refreshes managed settings and servers idempotently.
Managed Codex MCP servers use `default_tools_approval_mode = "auto"` so read-only tools can run normally while Codex prompts for side-effecting MCP operations based on tool metadata.
When an MCP server declares an OAuth `callbackPort`, the script also writes Codex's global MCP OAuth callback port and localhost callback URL as top-level TOML settings so OAuth providers with fixed redirect URIs can complete login.

### `pi-settings.json` (Pi)

Symlinked to `~/.pi/agent/settings.json`. Tracks `defaultProvider`, `defaultModel`, `defaultThinkingLevel`, `theme`, `packages`, and `enabledModels` (Ctrl+P model cycling list). `enabledModels` entries support a `provider/model:thinkingLevel` suffix, so switching models with Ctrl+P also restores that model's remembered effort level (e.g. `datadog-ai-gateway/openai/gpt-5.5:xhigh`). Pi rewrites this file directly when installing/removing packages, so `init.sh` backs up and relinks on drift the same way it does for `~/.claude/settings.json`. Deliberately omits `lastChangelogVersion`, a volatile field Pi bumps on every update.

### `sync-pi.sh` and `pi-extensions/`

Generates `.pi/skills`, `.pi/prompts` (slash-command templates for user-invocable skills), `.pi/agents` (for `pi-subagents`), `.pi/extensions/ask-question`, and `.pi/mcp.json` (for `pi-mcp-adapter`) for [pi.dev](https://pi.dev). `init.sh` symlinks managed assets into `~/.pi/agent/` and installs Pi packages from two sources:

- Community: `pi-subagents@0.31.1`, `pi-mcp-adapter@2.10.0`, `pi-web-search@1.3.0`
- Datadog [`ddoghq-sandbox/datadog-pi-packages`](https://github.com/ddoghq-sandbox/datadog-pi-packages): cloned to `$DD_PI_REPO` (default `~/dd/datadog-pi-packages`), then `pi install` for `refresh-models` and `confluence-adf`

If `ddtool` is authenticated and `models.json` has no AI Gateway provider, `init.sh` seeds `~/.pi/agent/models.json` from `pi.json` (providers and models, with `{{email}}` and `{{team}}` substituted at install time) so sessions route through the Datadog AI Gateway with `ml_app=pi` tagging. Edit `pi.json` to change providers or model lists, then run `make install`. After install, run `/refresh-models` from a Pi session to discover live model IDs (including Ollama) and migrate to the managed `ai-gw-*` provider layout. Opt out of the static seed with `PI_AUTOCONFIG=0`.

`sync-pi.sh` rewrites generated Pi skill and agent references to use package-provided tools: `Task`/`Agent` become `subagent`, `AskUserQuestion` becomes `ask_question`, Claude MCP calls become the `mcp` proxy tool, and `WebSearch`/`WebFetch` become `web_search`. The generated `.pi/mcp.json` is HTTP-only, lazy, proxy-mode MCP configuration derived from root `mcp.json`; OAuth servers use `pi-mcp-adapter`'s OAuth flow instead of wrapper-specific bearer-token environment variables.
