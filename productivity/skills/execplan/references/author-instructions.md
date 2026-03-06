# ExecPlan Author Instructions

Include this content in the `<instructions>` block when dispatching the author agent.

## Standard Instructions Block

```
<instructions>
- Before writing the plan, follow this research sequence:

  STEP 0 — DOMAIN RESEARCH EVALUATION (always do this first):
  Ask yourself: does this task rely on knowledge that lives outside this codebase? Triggers include:
    - External data sources, public APIs, or third-party services whose behavior is defined externally
    - File formats, protocols, or specs where the semantics are not obvious from reading our code alone
    - Any domain where your knowledge might be outdated, incomplete, or where well-known edge cases exist
    - Anything where "correct behavior" is determined by an external authority, not by this repo
  If the user's task description contains words like "investigate", "research", or "explore" → domain research is mandatory regardless.
  If ANY of the above apply → proceed to STEP 1 before touching the codebase.
  If NONE apply → skip to STEP 2.

  STEP 1 — EXTERNAL DOMAIN RESEARCH (only if triggered by STEP 0):
  Use WebSearch and WebFetch to research the relevant external domain. Focus on:
    - How the format or ecosystem actually works (not how you assume it works)
    - Known edge cases, pitfalls, and non-obvious behaviors
    - Official documentation or authoritative sources
  Document your findings in the plan's Assumptions section (see mandatory sections below).
  Flag any finding that contradicts what the task description or existing code implies.

  STEP 2 — LOCAL CODEBASE RESEARCH (always do this):
  Use Glob, Grep, and Read to explore relevant files, modules, patterns, and conventions in the repo. Understand the existing architecture, types, and interfaces that the plan will interact with.

  STEP 3 — CONFLUENCE RESEARCH (always do this):
  Use the Atlassian MCP tools (searchConfluenceUsingCql, getConfluencePage) to search for related design docs, RFCs, ADRs, runbooks, and team knowledge. Search using key terms from the task description. Incorporate relevant findings into the plan's Context and Orientation section.

- Embed all research findings directly into the plan — do not reference external links without summarizing the relevant content inline.
- Create the .plans/ directory if it does not exist
- Write the ExecPlan to the output path above
- Follow the ExecPlan format from your agent instructions to the letter
- The plan must be fully self-contained, written for a complete novice
- Honor the chosen approach from <chosen_approach> — do not revisit rejected alternatives or introduce a new strategy without flagging the deviation in the Decision Log
- YAGNI: only plan what was requested — do not add features, abstractions, or capabilities beyond the task description

TASK GRANULARITY AND TDD-FIRST STRUCTURE:
- Break work into bite-sized steps — each step is one action (write test, run test, implement, run test, commit)
- For tasks introducing new behavior, TDD-first structure is MANDATORY: write failing test → verify failure → implement minimal code → verify passing → commit
- NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST — this is non-negotiable for behavior-changing tasks
- Include complete test code in the plan (not "add a test for X")
- Include exact commands with expected output AND expected failure messages (not "run the tests")
- Include complete code for new function signatures and interface definitions
- Include a rationalization table for TDD exemptions: config-only, docs, and behavior-preserving refactors are exempt; everything else must follow TDD

- Include all mandatory sections: Purpose/Big Picture, Assumptions, Progress, Surprises & Discoveries,
  Decision Log, Outcomes & Retrospective, Context and Orientation, Plan of Work,
  Concrete Steps, Validation and Acceptance, Idempotence and Recovery, Artifacts and Notes,
  Interfaces and Dependencies
- The Assumptions section must appear near the top, right after Purpose/Big Picture. For each assumption:
    - Tag it as [EXTERNAL DOMAIN] if it comes from outside this codebase (external specs, public APIs, third-party data sources, etc.)
    - Tag it as [CODEBASE] if inferred from reading the repo
    - Tag it as [TASK DESCRIPTION] if taken at face value from what the user said
  If domain research was done (STEP 1), list key findings here, including any that surprised you or contradicted initial expectations.
  If domain research was skipped, state why: "Domain research not required: task is confined to internal codebase refactoring / config change / etc."
- Do NOT commit the plan file — ExecPlan files are working documents that live in the repo but are never committed
</instructions>
```
