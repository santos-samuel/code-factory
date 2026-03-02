# RFC State File Schema

Reference for creating and parsing RFC state files.

## Directory Structure

```
~/docs/plans/<short-name>/
  RFC-STATE.md          # Canonical state
  RESEARCH.md           # Research findings
  EXPLORATION.md        # Source code analysis (optional)
  PLAN.md               # Writing plan
  REVIEW.md             # Review feedback
```

Output: `~/docs/rfcs/<short-name>-<date>.md`

## RFC-STATE.md

### Frontmatter

```yaml
---
schema_version: 1
short_name: <kebab-case, max 40 chars>
rfc_type: <problem_statement|design>
topic: <original user topic>
current_phase: <REFINE|RESEARCH|EXPLORE|PLAN|CONSISTENCY_CHECK|REVIEW|WRITE|DONE>
phase_status: <not_started|in_progress|completed|blocked>
interaction_mode: <interactive|autonomous>
created: <ISO 8601 timestamp>
last_checkpoint: <ISO 8601 timestamp>
output_path: ~/docs/rfcs/<short-name>-<date>.md
# Iteration fields (optional, present when improving an existing RFC)
iterates_on: <path to the existing RFC being improved, omit for new RFCs>
iteration_context: <summary of improvement request and feedback, omit for new RFCs>
phases:
  REFINE: <not_started|in_progress|completed|needs_rerun|skipped>
  RESEARCH: <not_started|in_progress|completed|needs_rerun|skipped>
  EXPLORE: <not_started|in_progress|completed|needs_rerun|skipped>
  PLAN: <not_started|in_progress|completed|needs_rerun|skipped>
  CONSISTENCY_CHECK: <not_started|in_progress|completed|needs_rerun|skipped>
  REVIEW: <not_started|in_progress|completed|needs_rerun|skipped>
  WRITE: <not_started|in_progress|completed|needs_rerun|skipped>
  DONE: <not_started|completed>
---
```

### Body Sections

```markdown
## Refined Specification

<!-- Written during REFINE phase -->

### Problem Statement
<2-3 sentence summary>

### Scope
**In scope:** ...
**Out of scope:** ...

### Target Audience
...

### Key Questions
1. ...
2. ...

### Success Criteria
- ...

## Progress Log

<!-- Append-only log of phase transitions -->

| Timestamp | Phase | Action | Notes |
|-----------|-------|--------|-------|
| ... | REFINE | started | ... |
| ... | REFINE | completed | Refined with approach A |
| ... | RESEARCH | started | ... |

## Decisions Made

<!-- Record key decisions during the process -->

| Decision | Rationale | Phase |
|----------|-----------|-------|
| ... | ... | REFINE |

## Open Questions

<!-- Questions that need resolution -->

| Question | Status | Resolution |
|----------|--------|------------|
| ... | open | |
| ... | resolved | ... |
```

## RESEARCH.md

```markdown
# Research Findings: <short-name>

## Domain Context
<!-- What exists today, what has been tried before -->

### Finding 1: <title>
**Source:** <URL, page title, ticket ID>
**Relevance:** <how it relates to the RFC>
**Key insight:** <the data point or conclusion>

## Technical Findings
<!-- Technologies, patterns, benchmarks -->

## Organizational Context
<!-- Teams, dependencies, constraints -->

## Data Points
<!-- Metrics, benchmarks, costs, timelines -->

| Metric | Value | Source |
|--------|-------|--------|
| ... | ... | ... |

## Open Questions
<!-- What could not be answered -->

| Question | Why unresolved | Suggested next step |
|----------|---------------|-------------------|
| ... | ... | ... |
```

## EXPLORATION.md

```markdown
# Source Code Exploration: <short-name>

## Relevant Code Areas

### Area 1: <name>
**Path:** <file/directory path>
**Purpose:** <what this code does>
**Key files:**
- `path/to/file.go:42`: <description>

## Existing Patterns
<!-- How similar problems are currently solved -->

## Impact Assessment
<!-- What code would be affected -->

| Area | Owner | Impact | Risk |
|------|-------|--------|------|
| ... | ... | ... | ... |

## Integration Points
<!-- External interfaces and dependencies -->
```

## PLAN.md

```markdown
# Writing Plan: <short-name>

## Section Plan

### Section: <template section name>
**Depth:** <brief|detailed>
**Key points:**
1. ...

**Sources to cite:**
- <research finding or code reference>

**Quality criteria:**
- ...

**Open questions:**
- ...

**Depends on:** <other sections, if any>

## Diagram Needs
| Section | Diagram Type | Description |
|---------|-------------|-------------|
| ... | architecture / flow / sequence / deployment | ... |

## Data Gaps
<!-- Research still needed -->

## Writing Order
1. <section>: <reason for ordering>
```

## REVIEW.md

```markdown
# Plan Review: <short-name>

## Review Date
<ISO timestamp>

## Feedback

### Section: <name>
**Status:** approved | needs-changes | blocked
**Feedback:** ...
**Action:** ...

## Decisions
| Decision | Rationale |
|----------|-----------|
| ... | ... |

## Backtrack Requests
<!-- If user requested going back to a previous phase -->
| Target Phase | Reason |
|-------------|--------|
| ... | ... |
```
