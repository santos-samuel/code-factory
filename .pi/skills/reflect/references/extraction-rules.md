# Extraction Rules

Shared rules for extracting learnings from sessions.
Used by both the `/reflect` skill (live sessions) and the `memory-extractor` agent (structured input from `/do`).

## Learning Signals

Scan for these signal types.
Each type has a keyword list and a default confidence range.

### Correction Signals (confidence ≥ 0.85)

User explicitly corrects agent behavior or output.

**Keywords**: "no", "wrong", "instead use", "actually", "don't do that", "should be"

**Examples**:
- User says "No, always use `make all` not `make check`"
- User corrects agent behavior 2+ times on the same point
- User repeats an instruction the agent missed

### Convention Signals (confidence ≥ 0.8)

User states an explicit rule or recurring expectation.

**Keywords**: "always", "never", "make sure to", "remember to"

**Examples**:
- "Always run tests before committing"
- Workflow requirements discovered during work
- Naming conventions or structural patterns stated

### Pattern Signals (confidence 0.6–0.8)

Same approach used consistently, implying a preference.

**Indicators**:
- Same approach used 3+ times in a session
- User consistently prefers one approach over another
- Recurring code patterns or tool usage

### Gotcha Signals (confidence 0.5–0.7)

Unexpected behavior discovered and resolved.

**Keywords**: "found that", "turns out", "the trick is"

**Examples**:
- Unexpected errors and their solutions
- Non-obvious requirements discovered during work
- Tool quirks or workarounds found

### Discovery Signals (confidence 0.5–0.7)

New knowledge about tools, commands, or the codebase.

**Indicators**:
- New tool usage or flag discovery
- Performance insights
- API behaviors that differed from expectations

## Confidence Thresholds

| Level | Score | Action |
|-------|-------|--------|
| **High** | ≥ 0.8 | Auto-apply to target knowledge file |
| **Medium** | 0.5–0.79 | Queue for human review (pending-learnings) |
| **Low** | < 0.5 | Discard — ambiguous or one-off context |

**Scoring principles**:
- Direct user corrections score highest (0.85–1.0)
- Explicit instructions ("always do X") score high (0.8–0.9)
- Implicit preferences (single occurrence) score medium (0.5–0.7)
- When in doubt, score lower. False positives erode trust.

## Target File Selection

| Target | When to use |
|-|-|
| `AGENTS.md` | Repo-wide conventions, workflow rules, structural patterns that all agents should follow |
| `MEMORY.md` | Personal learnings, debugging insights, tool tips, project-specific knowledge |
| `CLAUDE.md` | Project instructions that affect all agents but are project-specific (rare — only for new boundary rules) |
| `.claude/rules/<topic>.md` | Topic-specific instructions scoped to certain file types or areas — use `paths:` frontmatter to scope (e.g., testing rules scoped to `tests/**`) |
| `CLAUDE.local.md` | Personal WIP context, local URLs, sandbox credentials, current focus areas that shouldn't be committed |

**Decision framework:**

| Question | Target |
|-|-|
| Is it a permanent project convention? | `CLAUDE.md` or `AGENTS.md` |
| Is it scoped to specific file types? | `.claude/rules/` with `paths:` frontmatter |
| Is it a pattern or insight the agent discovered? | `MEMORY.md` |
| Is it personal or ephemeral context? | `CLAUDE.local.md` |
| Is it duplicating content from another file? | Use `@import` reference instead |

**Default to MEMORY.md** when uncertain.
AGENTS.md changes affect all contributors and should be high-confidence only.

## Deduplication

Before applying any learning:

1. Search the target knowledge file using Grep for the learning text or its semantic equivalent
2. If the learning already exists → skip
3. If it refines an existing entry → update (not add)
4. If it's genuinely new → proceed with apply/queue per confidence threshold

## Self-Improvement Signals

In addition to knowledge extraction, scan the session for meta-level improvement signals.
These identify how the agent can improve its own behavior, not just what it learned about the codebase.

### Skill Gap Signals (confidence ≥ 0.8)

Things the agent struggled with, got wrong, or needed multiple attempts.

**Indicators**:
- User corrected agent approach 2+ times on the same task
- Agent tried multiple approaches before finding the right one
- Output quality was lower than expected

### Friction Signals (confidence ≥ 0.7)

Repeated manual steps or things the user had to ask for explicitly.

**Indicators**:
- User repeatedly asked for something that should have been automatic
- Same manual step performed 3+ times in a session
- User said "you should always do X" or "why didn't you do Y"

### Automation Signals (confidence 0.5–0.7)

Repetitive patterns that could become skills, hooks, or scripts.

**Indicators**:
- Same multi-step workflow executed 2+ times
- User described a process that could be codified
- Manual orchestration of multiple tools that should be a single skill

## What to Ignore

- One-off task context (specific variable names, temporary file paths)
- Information already in the knowledge files (caught by deduplication)
- Standard practices well-documented in official docs
- Speculative or uncertain observations
- Session-specific debugging steps that won't recur

## Writing Rules

- Each learning is a single imperative bullet point (10–20 words)
- Be specific: include concrete commands, file paths, or patterns — not vague advice
- Format with semantic line breaks: one sentence per line, target 120 characters
- Only append new bullets to existing sections — never reorganize files
- Only add knowledge — never remove existing content
