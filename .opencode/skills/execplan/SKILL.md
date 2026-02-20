---
name: execplan
description: >
  Use when the user wants to create, execute, review, or resume an ExecPlan.
  Triggers: "create a plan", "run this plan", "resume the plan",
  "review the plan", "write a plan for X", or references to .plan.md files.
argument-hint: "[task description or path to existing plan]"
user-invocable: true
---

# ExecPlan

Announce: "I'm using the execplan skill to manage execution plans."

## Step 1: Discover Existing Plans

Ensure `.plans/` is gitignored:

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
if ! grep -q "^\.plans/$" "$REPO_ROOT/.gitignore" 2>/dev/null; then
  echo ".plans/" >> "$REPO_ROOT/.gitignore"
fi
```

Search the project for existing ExecPlan files:

- Glob for `.plans/*.plan.md`
- Glob for `**/*.plan.md` (max depth 3, excluding `.plans/`)
- Check for `EXECPLAN.md` or `PLAN.md` in project root

For each discovered plan, read its Progress section and classify:

| Pattern | Status |
|---------|--------|
| No Progress section or no checked items | `not-started` |
| Has both `- [x]` and `- [ ]` items | `in-progress` |
| All items are `- [x]` | `completed` |

Store the list of discovered plans with their paths and statuses.

## Step 2: Mode Selection

Determine mode from `$ARGUMENTS` and discovered plans.

**IMPORTANT: Never skip Author Mode.** When the arguments are a task description, you MUST dispatch the Author Mode subagent to write a plan. Do not implement the task directly, regardless of how simple it appears. The entire point of `/execplan` is to produce a plan first.

**Anti-Pattern: "This Is Too Simple To Need A Plan"**

Every task goes through the authoring process. A config change, a single-function utility, a "quick fix" — all of them. "Simple" tasks are where unexamined assumptions cause the most wasted work. The plan can be short for truly simple tasks, but you MUST NOT skip it.

| Rationalization | Reality |
|----------------|---------|
| "This is just a one-line change" | One-line changes have the highest ratio of unexamined assumptions to effort. |
| "I already know how to build this" | Knowledge of HOW doesn't replace a documented approach for reproducibility. |
| "The user said 'just do it'" | That's about speed, not about skipping design. Author a concise plan quickly. |
| "This will be faster without the plan" | Skipping plans causes rework. A brief plan for simple tasks costs little. |

**Classification rules — apply in this order:**

1. **Review request** — `$ARGUMENTS` contains the word "review":
   - If a plan path is also provided, use **review** mode for that plan.
   - If no plan path is provided but `not-started` plans exist, ask which plan to review.
   - If no plans exist, inform the user they need to author a plan first.

2. **File path** — `$ARGUMENTS` is a local file path (contains `/` or ends in `.md`) AND does NOT start with `http://` or `https://`:
   - Verify the file exists. If not, report error and list any discovered plans.
   - Classify the plan:
     - `not-started` -> ask user whether to **review** or **execute**
     - `in-progress` -> **resume** mode
     - `completed` -> inform user; offer to author a new plan

3. **Task description** — anything else (including arguments containing URLs):
   - Use **author** mode with the provided description.

**If no arguments and existing plans were found:**

```
AskUserQuestion(
  header: "ExecPlan",
  question: "I found existing execution plans. What would you like to do?",
  options: [
    "Author new plan" -- Create a new ExecPlan from scratch,
    "<plan-name> (status)" -- one option per discovered plan
  ]
)
```

If the user selects a `not-started` plan:

```
AskUserQuestion(
  header: "ExecPlan",
  question: "What would you like to do with this plan?",
  options: [
    "Review" -- Walk through the plan, ask clarifying questions, and refine it before executing,
    "Execute" -- Execute the plan as-is
  ]
)
```

**If no arguments and no plans found:**

```
AskUserQuestion(
  header: "ExecPlan",
  question: "No existing plans found. What would you like to create an execution plan for?",
  options: [] // free-text response expected
)
```

Use their response as the task description for author mode.

## Step 3: Dispatch

### Author Mode

If the task description is fewer than 10 words, ask for more detail before dispatching.

**Approach Exploration (before planning):**

Before dispatching the plan author, explore approaches with the user:

1. Scan the codebase briefly (Glob, Grep, Read) to understand the relevant area.
2. Propose 2-3 approaches with trade-offs. For each: name, trade-off, relative complexity.
3. Lead with your recommended approach and explain why.
4. Present to the user:

```
AskUserQuestion(
  header: "Approach",
  question: "I see <N> ways to approach this. I recommend <approach A> because <reason>. Which approach do you prefer?",
  options: [
    "<Approach A> (Recommended)" -- <one-line trade-off summary>,
    "<Approach B>" -- <one-line trade-off summary>,
    "<Approach C>" -- <one-line trade-off summary>
  ]
)
```

**Skip approach exploration when:** The task is so well-specified that only one viable approach exists, or the user explicitly chose an approach in their description.

**YAGNI check:** Before presenting approaches, remove any that add unnecessary complexity or features not requested.

Include the chosen approach in the dispatch to the plan author.

Generate a slug from the task description: lowercase, hyphens, max 50 chars.

Read [references/author-instructions.md](references/author-instructions.md) and use the `<instructions>` block from it.

Dispatch:

```
Task(
  subagent = "execplan",
  description = "Author ExecPlan: <short description>",
  prompt = "
Author a new ExecPlan for the following task.

<task>
<the user's task description>
</task>

<chosen_approach>
<the approach the user selected, with rationale and rejected alternatives>
</chosen_approach>

<output_path>
.plans/<slug>.plan.md
</output_path>

<instructions from references/author-instructions.md>
"
)
```

After the agent returns, report:
```
ExecPlan authored: .plans/<slug>.plan.md

To review: /execplan review .plans/<slug>.plan.md
To execute: /execplan .plans/<slug>.plan.md
```

### Review Mode

Interactive walkthrough in the main conversation (not a subagent). Read the plan file content:

```
PLAN_CONTENT = Read("<plan_path>")
```

Walk through the plan one section at a time, in order. For each section:

1. **Summarize** the section in 2-3 plain-language sentences, highlighting the key decisions and assumptions the plan makes.
2. **Flag** anything that looks ambiguous, risky, or worth confirming — e.g., technology choices, file paths that might not exist, assumptions about the codebase, missing edge cases, or steps that seem underspecified.
3. **Ask** the user a clarification question using `AskUserQuestion` if there is anything flagged. If the section looks solid and unambiguous, say so and move on without asking.

The sections to walk through, in order:

1. **Purpose / Big Picture** — Does the stated goal match what the user wants? Is the scope right?
2. **Context and Orientation** — Are the referenced files, modules, and terms accurate? Anything missing?
3. **Plan of Work** — Is the sequence of changes logical? Are there missing steps or unnecessary ones?
4. **Concrete Steps** — Are the commands and paths correct? Do they match the project's actual toolchain?
5. **Milestones** (if present) — Is the breakdown reasonable? Are milestones independently verifiable as claimed?
6. **Validation and Acceptance** — Are the acceptance criteria specific enough? Would you know success from failure?
7. **Idempotence and Recovery** — Are there risky steps that need better rollback paths?
8. **Interfaces and Dependencies** — Are the specified types, libraries, and APIs correct?

Skip empty sections (Progress, Decision Log, etc. are filled during execution).

After walking through all sections, present a summary:

```
AskUserQuestion(
  header: "Review complete",
  question: "I've reviewed the plan. Here's a summary of what we discussed:\n\n<bullet list of changes agreed upon, if any>\n\nHow would you like to proceed?",
  options: [
    "Update and execute" -- Apply the agreed changes to the plan, then execute it,
    "Update only" -- Apply the agreed changes but don't execute yet,
    "Execute as-is" -- Execute the plan without changes,
    "Cancel" -- Do nothing for now
  ]
)
```

**If the user chose "Update and execute" or "Update only":**

Dispatch a subagent to apply the revisions:

```
Task(
  subagent = "execplan",
  description = "Revise ExecPlan: <plan filename>",
  prompt = "
Revise the following ExecPlan based on review feedback from the user.

<plan_path>
<the plan file path>
</plan_path>

<plan>
<the full plan content>
</plan>

<revisions>
<numbered list of specific changes to make, gathered from the review conversation>
</revisions>

<instructions>
- Read the current plan from <plan_path>
- Apply each revision precisely
- Maintain all mandatory ExecPlan sections
- Keep the plan self-contained — do not introduce references to this review conversation
- Record each revision in the Decision Log with rationale: 'Review feedback from user'
- Add a note at the bottom of the plan describing the revision pass
- Write the updated plan back to <plan_path>
- Do NOT commit the plan file
</instructions>
"
)
```

After the revise agent returns:
- If the user chose "Update and execute", proceed to **Execute Mode** with the updated plan.
- If the user chose "Update only", report:
  ```
  ExecPlan updated: <plan_path>

  To execute: /execplan <plan_path>
  ```

**If the user chose "Execute as-is":**

Proceed directly to **Execute Mode**.

**If the user chose "Cancel":**

Report that no changes were made and the plan is available at `<plan_path>`.

**If the user provided custom feedback (selected "Other" or gave a free-text response instead of one of the four options above):**

The user has additional feedback that was not covered during the section-by-section walkthrough. Handle it as follows:

1. Collect the user's feedback as additional revision items.
2. Dispatch the revision subagent (same as the "Update and execute" flow above) to apply the changes to the plan.
3. After the revision agent returns, **re-present the "Review complete" summary** with the same four options. Include the user's latest feedback in the bullet list of changes.

This creates a loop: the user can keep giving feedback until they select one of the four predefined options. Do NOT proceed to execution on custom feedback — always re-ask.

### Execute Mode

#### Step 1: Set Up Workspace

Ask the user how they want to work:

```
AskUserQuestion(
  header: "Workspace",
  question: "Where should this plan be executed?",
  options: [
    "Worktree + new branch (Recommended)" -- Create an isolated git worktree and feature branch so main workspace stays clean,
    "New branch in current directory" -- Create a feature branch here without a worktree,
    "Current branch" -- Work on the already checked-out branch with no worktree or branch creation
  ]
)
```

**If the user chose "Worktree + new branch":**

1. Invoke the `/worktree` skill to create an isolated workspace:

```
Skill(skill="worktree", args="<short description from plan>")
```

The skill will report the worktree path. Store it as `WORKTREE_PATH`.

2. Change into the worktree directory:

```
cd <WORKTREE_PATH>
```

3. Invoke the `/branch` skill to create a feature branch:

```
Skill(skill="branch", args="<short description from plan>")
```

4. Copy the plan file into the worktree so the execution agent can update it:

```
cp <original plan_path> <WORKTREE_PATH>/<plan_path>
```

**If the user chose "New branch in current directory":**

1. Store the current working directory as `WORKTREE_PATH`.

2. Invoke the `/branch` skill to create a feature branch:

```
Skill(skill="branch", args="<short description from plan>")
```

No plan file copy is needed — the plan is already accessible.

**If the user chose "Current branch":**

1. Store the current working directory as `WORKTREE_PATH`.

No branch creation or plan file copy needed — work proceeds on the current branch.

#### Step 2: Dispatch Execution Agent

Read the plan file content (it must be inlined — `@` references don't work across Task boundaries).

```
PLAN_CONTENT = Read("<plan_path>")
```

Dispatch:

Read [references/dispatch-instructions.md](references/dispatch-instructions.md) and use the `<instructions>` block from it.

```
Task(
  subagent = "execplan",
  description = "Execute ExecPlan: <plan filename>",
  prompt = "
Execute the following ExecPlan. Follow each milestone in order. Do not prompt the user
for next steps; proceed autonomously. Keep all living document sections up to date.
Commit frequently. Resolve ambiguities autonomously and document decisions in the Decision Log.

<plan_path>
<the plan file path>
</plan_path>

<worktree_path>
<the worktree directory path>
</worktree_path>

<plan>
<the full plan content>
</plan>

<instructions from references/dispatch-instructions.md>
"
)
```

#### Step 3: Complete Development

After the agent returns, read the updated plan and report:
- Progress items completed vs remaining
- Any surprises or decisions logged
- Whether the plan is now complete
- The workspace path and branch name

If the plan is complete (all Progress items are checked), run the full test suite one final time, then present completion options:

```
AskUserQuestion(
  header: "Plan Complete",
  question: "All tasks complete and tests passing. How would you like to finish?",
  options: [
    "Create PR (Recommended)" -- Push branch and open a pull request for review,
    "Merge to base branch" -- Merge directly into the base branch locally,
    "Keep branch" -- Leave the branch as-is for later handling,
    "Discard work" -- Delete the branch and worktree (requires typed confirmation)
  ]
)
```

| Choice | Action |
|--------|--------|
| **Create PR** | `Skill(skill="pr", args="<concise PR title>")`. Report PR URL. |
| **Merge to base** | `git checkout <base>`, `git merge <branch>`, clean up worktree. |
| **Keep branch** | Report branch name and worktree path. No cleanup. |
| **Discard** | Require typed confirmation "discard". Then remove worktree and branch. |

If the plan is NOT complete, report what remains and offer to resume later.

### Resume Mode

#### Step 1: Locate the Workspace

Determine where the plan was executed:

1. Run `git worktree list` to find existing worktrees.
2. Match the worktree by looking for one whose directory name corresponds to the plan slug.
3. If found, store the path as `WORKTREE_PATH` and `cd` into it.
4. If not found, check for the plan's feature branch locally (run `git branch --list` and match by plan slug). If the branch exists, check it out and store the current directory as `WORKTREE_PATH`.
5. If no matching worktree or branch is found, the plan may have been executed on the current branch. Check whether the current branch has commits related to the plan (e.g., `git log --oneline -10` and match against the plan's task description). If so, store the current directory as `WORKTREE_PATH` and continue on the current branch.
6. If none of the above match, ask the user how to proceed using the same workspace question as Execute Mode Step 1. If the branch already exists on the remote, check it out instead of creating a new one.

#### Step 2: Dispatch Resume Agent

Read the plan file content and extract progress context.

```
PLAN_CONTENT = Read("<plan_path>")
```

Parse the Progress section to identify:
- Last completed step (most recent `- [x]`)
- Next incomplete step (first `- [ ]`)

Dispatch:

Read [references/dispatch-instructions.md](references/dispatch-instructions.md) and use the `<instructions>` block from it, adding resume-specific context.

```
Task(
  subagent = "execplan",
  description = "Resume ExecPlan: <plan filename>",
  prompt = "
Resume execution of an in-progress ExecPlan. The plan has been partially completed.
Review the Progress section to understand what has been done and what remains.
Continue from the first incomplete step.

<plan_path>
<the plan file path>
</plan_path>

<worktree_path>
<the worktree directory path>
</worktree_path>

<plan>
<the full plan content>
</plan>

<resume_context>
Last completed: <last completed step text>
Next to do: <next incomplete step text>
</resume_context>

<instructions from references/dispatch-instructions.md>
Additional resume-specific rules:
- Read the full plan including Surprises & Discoveries and Decision Log for prior context
- Continue from the first incomplete Progress item
- Do not re-execute completed steps
- During PLAN CRITICAL REVIEW: consider what was already built and verify remaining tasks still make sense
</instructions>
"
)
```

#### Step 3: Complete Development

After the agent returns, report status as in Execute Mode. If the plan is now complete, run the full test suite and present completion options (same as Execute Mode Step 3). If not complete, report what remains and offer to continue.

## Error Handling

- **Plan file not found**: List discovered plans and ask user to select or provide a valid path
- **Agent failure**: Report what happened, suggest checking the plan's Progress section for partial work, and offer to resume
- **No task description**: Prompt for one before dispatching
