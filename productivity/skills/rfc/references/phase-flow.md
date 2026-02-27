# RFC Phase Flow: Detailed Agent Dispatch

Reference for each phase's agent dispatch, prompts, and expected outputs.

## REFINE Phase

**Agent:** `productivity:refiner`

**Dispatch prompt template:**

```
Task(
  subagent_type = "productivity:refiner",
  description = "Refine RFC topic: <short topic>",
  prompt = "
<rfc_topic>
<user's topic>
</rfc_topic>

<context>
RFC type: <problem_statement|design>
</context>

<task>
Refine this RFC topic into a detailed specification. This is for an RFC document, not code.

1. Analyze the topic for ambiguity, missing context, and scope questions.
2. Propose 2-3 approaches to scoping this RFC. For each approach:
   - What would be included and excluded
   - Target audience and stakeholders
   - Estimated complexity and coverage
   Lead with the recommended approach and explain why.
3. After the user selects an approach, produce a refined specification:
   - Problem statement (2-3 sentences)
   - Scope boundaries (in/out)
   - Target audience
   - Key questions that research must answer
   - Success criteria for the RFC document itself
4. Questions to the user should be ONE at a time, preferring multiple choice.
</task>
"
)
```

**Output:** Refined specification written to RFC-STATE.md body section.

**Phase status transitions:** `not_started` → `in_progress` → `completed`

## RESEARCH Phase

**Agent:** `productivity:researcher`

**Dispatch prompt template:**

```
Task(
  subagent_type = "productivity:researcher",
  description = "Research for RFC: <short-name>",
  prompt = "
<rfc_specification>
<refined spec from REFINE phase>
</rfc_specification>

<key_questions>
<questions identified during REFINE>
</key_questions>

<task>
Research the following for an RFC document. Do NOT write the RFC. Only gather and organize findings.

Research sources (search ALL of these):
1. **Web**: Prior art, industry best practices, benchmark data, similar systems at other companies
2. **Confluence**: Internal documentation, existing RFCs, architecture decisions, team wikis
3. **Jira**: Related tickets, epics, past work, ongoing initiatives
4. **GitHub**: Related PRs, issues, existing implementations, code patterns

For each finding:
- Cite the source (URL, page title, ticket ID, file path)
- Extract the relevant data point or insight
- Note how it relates to the RFC topic

Organize findings by:
1. **Domain Context**: What exists today, what has been tried before
2. **Technical Findings**: Relevant technologies, patterns, benchmarks
3. **Organizational Context**: Teams involved, dependencies, constraints
4. **Data Points**: Metrics, benchmarks, cost figures, timelines
5. **Open Questions**: What could not be answered (needs user input or further investigation)

CRITICAL: Every finding must have a source citation. Do not present assumptions as findings.
</task>
"
)
```

**Output:** Write `RESEARCH.md` in the plan directory.

## EXPLORE Phase

**Agent:** `productivity:explorer`

**Skip condition:** The RFC has no source code component (pure process/organizational RFC). Mark as `skipped` in state.

**Dispatch prompt template:**

```
Task(
  subagent_type = "productivity:explorer",
  description = "Explore codebase for RFC: <short-name>",
  prompt = "
<rfc_specification>
<refined spec>
</rfc_specification>

<research_findings>
<summary of RESEARCH.md>
</research_findings>

<task>
Explore the codebase to gather technical context for an RFC document. Do NOT write the RFC.

1. Map the relevant code areas:
   - Key files, modules, and packages
   - Interfaces and APIs
   - Data models and schemas
   - Dependencies (internal and external)

2. Identify existing patterns:
   - How similar problems are currently solved
   - Architectural conventions and constraints
   - Testing patterns in use

3. Assess impact:
   - What code would be affected by the RFC's proposal
   - Which teams own the affected areas
   - What integration points exist

Output a structured exploration report with file paths and code references.
CRITICAL: Cite specific file paths and line numbers for all findings.
</task>
"
)
```

**Output:** Write `EXPLORATION.md` in the plan directory.

## PLAN Phase

**Agent:** `productivity:planner`

**Dispatch prompt template:**

```
Task(
  subagent_type = "productivity:planner",
  description = "Plan RFC writing: <short-name>",
  prompt = "
<rfc_specification>
<refined spec>
</rfc_specification>

<research_findings>
<full RESEARCH.md content>
</research_findings>

<exploration_notes>
<full EXPLORATION.md content, or 'N/A - no code component' if skipped>
</exploration_notes>

<rfc_template>
<the appropriate template content based on rfc_type>
</rfc_template>

<task>
Create a section-by-section writing plan for this RFC. Do NOT write the RFC. Plan how to write it.

For each section in the template:
1. **What to write**: Key points, arguments, data to include
2. **Sources to cite**: Which research findings or code references to use
3. **Quality criteria**: What makes this section complete and convincing
4. **Open questions**: What must be resolved before this section can be written
5. **Estimated depth**: Brief (1-2 paragraphs) or detailed (multiple subsections)

Also include:
- **Section ordering**: Any sections that should be written before others (dependencies)
- **Diagram needs**: Which sections benefit from architecture, flow, or deployment diagrams
- **Data gaps**: Research findings still needed (flag for user)
- **Reviewer guidance**: What reviewers should focus on per section

The plan must be specific enough that a writer can execute it without further research.
</task>
"
)
```

**Output:** Write `PLAN.md` in the plan directory.

## CONSISTENCY_CHECK Phase

**Agent:** `productivity:consistency-checker`

**Dispatch prompt template:**

```
Task(
  subagent_type = "productivity:consistency-checker",
  description = "Check RFC plan consistency: <short-name>",
  prompt = "
<plan>
<full PLAN.md content>
</plan>

<research>
<full RESEARCH.md content>
</research>

<specification>
<refined spec from RFC-STATE.md>
</specification>

<task>
Check this RFC writing plan for internal consistency. Look for:

1. **Contradictions**: Does the plan say different things about the same topic in different sections?
2. **Terminology drift**: Are the same concepts referred to by different names?
3. **Missing references**: Does a section reference findings that don't appear in the research?
4. **Scope mismatch**: Does the plan include sections outside the refined scope, or miss required sections?
5. **Unsupported claims**: Does the plan assume data points not found in research?
6. **Ordering issues**: Are section dependencies satisfied by the proposed writing order?

Fix minor issues directly. Flag blocking issues that require user decision.
</task>
"
)
```

**Output:** Updated PLAN.md (fixes applied), blocking issues noted in RFC-STATE.md.

## REVIEW Phase

**No agent dispatch.** Direct interaction with user.

**Interactive mode:**
1. Present the writing plan section by section
2. Highlight key decisions and trade-offs
3. Show open questions that need resolution
4. Ask for: approval, feedback, or backtrack target

**Autonomous mode:**
1. Log the plan summary
2. Proceed unless blocking open questions exist
3. If blocked: stop and report

**Output:** Write `REVIEW.md` with feedback and decisions.

## WRITE Phase

**Agent:** `general-purpose` (fresh subagent with full context)

**Dispatch prompt template:**

```
Task(
  subagent_type = "general-purpose",
  description = "Write RFC: <short-name>",
  prompt = "
<writing_plan>
<full PLAN.md content>
</writing_plan>

<research_findings>
<full RESEARCH.md content>
</research_findings>

<exploration_notes>
<full EXPLORATION.md content or 'N/A'>
</exploration_notes>

<rfc_template>
<the appropriate template content>
</rfc_template>

<writing_guidelines>
<content from references/writing-guidelines.md>
</writing_guidelines>

<review_decisions>
<full REVIEW.md content>
</review_decisions>

<output_path>
<path to output RFC file>
</output_path>

<task>
Write the RFC document following the plan exactly. Write to the output_path.

Rules:
1. Follow the template structure. Do not add or remove sections unless the plan specifies it.
2. Write each section per the plan's instructions (key points, sources, quality criteria).
3. CITE SOURCES: Every technical claim must reference a research finding, code path, or user decision.
   Use inline citations: (Source: <reference>)
4. Open questions that could not be resolved go in the 'Open Questions' section. Do not guess answers.
5. Use clear, direct prose. Write from a staff software engineer perspective:
   - Data-backed claims with specific numbers
   - Explicit trade-off analysis for every decision
   - Concrete alternatives with clear rejection rationale
   - Measurable success metrics
   - Realistic risk assessment with mitigation strategies
6. Follow these typographic rules strictly:
   - No em dashes (--- or the character). Rewrite the sentence, use a colon, semicolon, or split into two sentences.
   - Straight quotes only: " and '. Never use curly quotes.
   - No bold or italic formatting inside sentences. Use headings, lists, or code formatting instead.
7. After writing all sections, do a self-review pass:
   - Check coherence: do sections reference each other consistently?
   - Check completeness: are all plan items covered?
   - Check citations: does every claim have a source?
   - Check quality: would a staff engineer find this convincing?
   - Check typography: no em dashes, no curly quotes, no mid-sentence bold/italic?
8. Write the final document to the output path.
</task>
"
)
```

**Post-write review (interactive mode):**
1. Read the generated RFC
2. Present a section-by-section summary to the user
3. Ask for feedback on each section
4. Dispatch follow-up edits as needed

**Output:** RFC at `~/docs/rfcs/<short-name>-<date>.md`

## DONE Phase

**No agent dispatch.**

1. Update RFC-STATE.md: `current_phase: DONE`, all phases `completed`
2. Read the final RFC and present summary:
   - Document location and word count
   - Key decisions made
   - Sources referenced (count and types)
   - Open questions remaining
   - Suggested next steps:
     - For problem statements: "Share for review, then proceed to design phase if approved"
     - For design docs: "Share for review, address feedback, then publish"
3. Suggest reviewers based on stakeholders identified during REFINE
