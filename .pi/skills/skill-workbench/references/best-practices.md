# Skill Authoring Best Practices

Reference for writing high-quality skills. Synthesized from Anthropic's official guide, the superpowers `writing-skills` skill, and code-factory conventions.

## Core Principles

| Principle | Rule |
|-----------|------|
| Context window is a public good | Every token in SKILL.md has a cost. Remove content Claude already knows. |
| Conciseness over completeness | One sentence per concept. Tables over paragraphs. No filler words. |
| Specificity over abstraction | `Run make all` not "validate your changes". Exact commands, not vague verbs. |
| Self-containment | Skills work without external context. Duplication preferred over fragile dependencies. |
| Progressive disclosure | SKILL.md under 500 lines. Heavy reference in separate files, one level deep. |

## Degrees of Freedom

Match instruction specificity to task complexity:

| Freedom Level | When | Style |
|---------------|------|-------|
| **Low** (exact scripts) | Fragile ops, critical validation, destructive actions | Exact commands with expected output |
| **Medium** (pseudocode) | Multi-step workflows with some variability | Numbered steps with decision points |
| **High** (guidelines) | Context-dependent judgment calls | Principles and criteria, not prescriptive steps |

Think of it like terrain navigation: narrow bridges need guardrails; open fields allow flexibility.

## Structure Checklist

Every skill must have:

1. **YAML frontmatter** with `name` (kebab-case) and `description` (starts with "Use when")
2. **Announce line** as first content after heading
3. **Numbered steps** (`## Step N: Title`) with specific actions
4. **Error handling** section covering failure modes

## Writing Effective Descriptions

The description field determines whether Claude loads the skill. It is the most important part of the frontmatter.

**Rules:**

- Start with "Use when" — focus on triggering conditions
- Include specific trigger phrases users would say
- Mention relevant file types, tools, or domains
- Write in third person
- Under 1024 characters (aim for under 500)
- **NEVER** summarize the workflow — description says WHEN, not HOW

**Why no workflow summary:** Testing showed Claude follows the description as a shortcut instead of reading the full skill body. A description saying "code review between tasks" caused Claude to do ONE review even though the skill defined TWO.

```yaml
# BAD: Summarizes workflow — Claude may skip reading the skill body
description: Reviews code by running linting, then unit tests, then integration tests

# GOOD: Triggering conditions only
description: >
  Use when the user wants to review code quality before merging.
  Triggers: "review code", "check quality", "pre-merge review".
```

## Writing Style by Skill Type

Match writing style to skill type — the wrong style reduces effectiveness:

| Skill Type | Style | Why |
|------------|-------|-----|
| **Discipline-enforcing** | Authority language ("NEVER", "YOU MUST"), rationalization tables, red flags. | Eliminates decision fatigue. Compliance requires bright-line rules. |
| **Technique/workflow** | Explain the **why** behind instructions. If you write ALWAYS/NEVER for a judgment call, reframe with reasoning instead. | LLMs follow instructions better when they understand the purpose. Rigid structure on judgment calls reduces output quality. |
| **Reference/pattern** | Clear, factual prose. No persuasion techniques. | Authority language is noise in reference material. |

**Yellow flag:** If you find yourself writing heavy-handed MUSTs for a non-discipline skill, stop and explain the reasoning instead. "Do X because Y" is more effective than "YOU MUST DO X" for technique and workflow skills.

## Content Guidelines

### Do

- Use tables for reference material, not paragraphs
- Provide copy-paste ready code blocks with expected output
- Put the most common workflow early (quick-start pattern)
- Use consistent terminology — one term per concept throughout
- Include input/output examples demonstrating desired format
- Handle errors explicitly in scripts rather than deferring to Claude

### Avoid

| Anti-Pattern | Why | Fix |
|--------------|-----|-----|
| Filler words (simply, just, basically, actually) | Zero information, wastes tokens | Delete them |
| Vague verbs (handle, process, manage) | Claude doesn't know the specific action | Use exact commands |
| Multi-language examples | Mediocre quality, maintenance burden | One excellent example in the most relevant language |
| Narrative storytelling | Not reusable, too specific | Extract patterns and techniques |
| Deeply nested references | Claude may not find them | Keep references one level deep from SKILL.md |
| Time-sensitive information | Becomes stale | Use "old patterns" sections for deprecated approaches |
| Excessive options without defaults | Decision paralysis | Provide recommended defaults |
| Overfitting to test cases | Skill used across many prompts — fiddly fixes for specific examples break other cases | Generalize from test feedback. Try different metaphors or patterns when a fix resists. |

## Validation Loops

For multi-step workflows, implement a validator-fix-repeat pattern:

```
1. Execute step
2. Validate output (script or checklist)
3. If validation fails → fix → re-validate
4. Max N iterations → report remaining issues
```

This pattern "greatly improves output quality" by catching errors early.

## Token Optimization

| Technique | Example |
|-----------|---------|
| Move details to tool help | "Run `cmd --help` for flags" instead of listing all flags |
| Cross-reference other skills | "See `/commit` for git conventions" instead of repeating content |
| Compress examples | 20 words beats 42 words if they show the same pattern |
| Eliminate redundancy | Don't repeat what's in referenced files |
| Tables over paragraphs | 3 table rows < 3 paragraphs in tokens |
| Codify loops into scripts | `scripts/poll.sh` with `run_in_background: true` instead of inline "poll every 30s" — see [progressive-disclosure.md](progressive-disclosure.md) |

**Targets:**

- Frequently-loaded skills: under 200 words
- Standard skills: under 500 words in SKILL.md body
- Heavy reference: separate files, linked from SKILL.md

## Cross-Model Testing

Skills behave differently across Claude Haiku, Sonnet, and Opus. Validate on all models before deploying, especially for discipline-enforcing skills that resist rationalization.

## Sources

- [Anthropic: The Complete Guide to Building Skills for Claude](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)
- [Anthropic: Skills Best Practices](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/best-practices)
- [superpowers: writing-skills](https://github.com/obra/superpowers/tree/main/skills/writing-skills)
