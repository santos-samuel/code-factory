# code-factory

rtfpessoa's personal [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [OpenCode](https://opencode.ai) marketplace -- a collection of plugins, skills, and agent definitions that extend AI coding assistants with structured workflows for productivity, execution planning, and git operations.

## Quick Reference

| Command | Plugin | Purpose |
|---------|--------|---------|
| `/do` | productivity | Orchestrate feature development with lifecycle tracking |
| `/debug` | productivity | Systematic debugging with root cause investigation |
| `/execplan` | productivity | Create, review, execute, or resume execution plans |
| `/doc` | productivity | Create, update, improve, or audit Markdown docs |
| `/workspace` | productivity | Set up Claude Code configuration and plugins |
| `/reflect` | productivity | Capture session learnings and update knowledge files |
| `/skill-workbench` | productivity | Create and improve skills in this marketplace |
| `/review` | productivity | Review a pull request with structured feedback |
| `/tour` | productivity | Guided code walkthrough (interactive or written) |
| `/commit` | git | Create a structured git commit |
| `/atcommit` | git | Validate and organize atomic commits |
| `/fixup` | git | Create a fixup commit targeting an earlier branch commit |
| `/pr` | git | Create a GitHub pull request |
| `/branch` | git | Create a well-named feature branch |
| `/pr-fix` | git | Address PR review feedback: fetch, fix, reply, resolve |
| `/fix-conflicts` | git | Resolve merge, rebase, cherry-pick, and revert conflicts |
| `/worktree` | git | Create an isolated git worktree |
## Plugins

### productivity

Productivity skills -- feature development lifecycle, systematic debugging, documentation management, execution planning, PR review, guided code tours, workspace setup, and skill workbench.

**Skills:**

- `/do` -- Orchestrate feature development with full lifecycle management. Multi-phase workflow (RESEARCH -> PLAN -> EXECUTE -> VALIDATE -> DONE) with resumable state, specialized subagents, and atomic commits. Supports interactive and autonomous modes.
- `/debug` -- Systematic debugging with enforced root cause investigation. Four-phase workflow (REPRODUCE -> INVESTIGATE -> FIX -> VERIFY) with persistent state, hypothesis tracking, and defense-in-depth validation. Leverages explorer and researcher agents for evidence gathering.
- `/doc` -- Manage Markdown documentation lifecycle: create, update, improve, maintain, and audit. Supports Confluence sync via ddoc. Includes templates for runbooks, guides, references, tutorials, and ADRs.
- `/execplan` -- Create, execute, review, or resume an ExecPlan. Supports four modes: author (write a new plan), review (interactive walkthrough with feedback), execute (run a plan from the start), and resume (continue an in-progress plan).
- `/review` -- Review a pull request with structured feedback across five categories (Correctness, Security, Design, Testing, Style) with severity levels (critical, suggestion, nit). Presents findings to the user without posting automatically.
- `/tour` -- Guided code walkthroughs to explain architecture, flows, or structure. Supports three modes: interactive (step-by-step with pauses), written (complete markdown document), and PR comment (collapsible sections posted to a GitHub PR).
- `/workspace` -- Set up and manage Claude Code configuration. Bootstraps the code-factory plugin marketplace, symlinks configuration files, and manages MCP server settings.
- `/reflect` -- Capture session learnings and update knowledge files. Extracts conventions, corrections, patterns, and gotchas from the current session. Uses confidence-based routing: high-confidence learnings are auto-applied, medium-confidence ones are queued for human review.
- `/skill-workbench` -- Create new skills or improve existing ones in this plugin marketplace. Supports two modes: CREATE (scaffold a new skill with frontmatter, structure, and OpenCode command) and IMPROVE (audit skills for clarity, conciseness, and completeness; apply improvements directly).

**Agents:**

- `execplan` -- A specialized agent persona for authoring and executing ExecPlans. Resolves ambiguities autonomously, commits frequently, and breaks work into independently verifiable milestones.
- `orchestrator` -- Orchestrates multi-phase workflows through a state machine. Single writer of FEATURE.md state files.
- `explorer` -- Read-only codebase exploration. Maps architecture, conventions, and integration points.
- `researcher` -- Domain research agent. Searches Confluence, documentation, and web resources.
- `planner` -- Plan authoring. Converts research into actionable execution plans with milestones and tasks.
- `reviewer` -- Plan review. Critically analyzes plans for completeness, safety, and executability.
- `spec-reviewer` -- Spec compliance review. Verifies implementation matches task specification — nothing missing, nothing extra.
- `code-quality-reviewer` -- Code quality review. Assesses code quality, patterns, testing, and maintainability.
- `implementer` -- Implementation. Executes code changes according to plan tasks with atomic commits.
- `validator` -- Validation. Runs automated checks and verifies acceptance criteria with evidence.

### git

Git workflow skills -- structured commits, fixup commits, PR creation, PR review feedback resolution, branch management, and merge conflict resolution.

**Skills:**

- `/commit` -- Create a well-structured git commit with optional Documentation, Motivation, and Summary sections. Analyzes staged changes, detects Jira ticket IDs from branch names, and builds a formatted commit message.
- `/pr` -- Create a GitHub pull request from the current branch. Collects commits since divergence from the base branch, detects ticket IDs and URLs from commit messages, and builds a structured PR description.
- `/branch` -- Create a well-named feature branch from a ticket ID or description. Generates branches with the naming convention `<user>/<slug>-<TICKET-ID>` from the default branch (prefix derived from `git config user.name`).
- `/worktree` -- Create an isolated git worktree for feature development. Sets up a detached worktree from the default branch in a sibling directory, ready for `/branch` to create a feature branch.
- `/atcommit` -- Validate and organize changes into self-contained atomic commits. Builds a dependency graph across changed files, detects violations (missing deps, mixed concerns, forward references), and proposes commit groups in the correct order.
- `/fixup` -- Match current changes to an existing branch commit and create a fixup commit. Scores commits by file overlap and directory proximity, handles ambiguous matches interactively, and reminds the user to autosquash.
- `/pr-fix` -- Address PR review feedback systematically. Fetches unresolved review threads via GraphQL, categorizes comments (suggestion, code change, question, disagreement), applies fixes with bottom-to-top editing, replies to threads via REST API, resolves addressed threads, and commits changes with conventional messages.
- `/fix-conflicts` -- Resolve merge, rebase, cherry-pick, and revert conflicts systematically. Detects conflict state with helper scripts, analyzes both sides using commit history, resolves by conflict type (UU, UD, DU, AU, UA, AA), handles lock files and generated files specially, and verifies no conflict markers remain.

## Installation

1. Clone the repository:

       git clone https://github.com/rtfpessoa/code-factory.git
       cd code-factory

2. Run the init script to symlink configuration files:

       ./init.sh

   This creates the following symlinks:

   | Source | Destination |
   |--------|-------------|
   | `mcp.json` | `~/.mcp.json` |
   | `settings.json` | `~/.claude/settings.json` |
   | `opencode.jsonc` | `~/.config/opencode/opencode.jsonc` |

   If a destination already exists as a regular file (not a symlink), the script warns and skips it. If it exists as a symlink, it is replaced.

3. The marketplace is registered in `settings.json` under `extraKnownMarketplaces` as `code-factory` pointing to `rtfpessoa/code-factory` on GitHub. The plugins `productivity@code-factory` and `git@code-factory` are enabled by default.

## Configuration Files

### settings.json (Claude Code)

Global settings for Claude Code. Defines tool permissions (which bash commands and tools are auto-allowed), the default model (`opus` -- a Claude Code shorthand for the current Opus model), enabled MCP servers, marketplace references, and enabled plugins.

### opencode.jsonc (OpenCode)

Configuration for the OpenCode CLI. Defines model providers (Anthropic, OpenAI, Google), agent profiles for A/B testing different models, MCP server connections, and a granular permission system. Uses JSONC (JSON with comments).

### mcp.json (MCP Servers)

Declares three MCP (Model Context Protocol) servers:

- **atlassian** -- Connects to Atlassian's hosted MCP service for Jira and Confluence integration.
- **datadog** -- Connects to Datadog's MCP service for observability tooling (disabled by default in local settings).
- **chrome-devtools** -- Launches a local Chrome DevTools MCP server via npx for browser debugging.
