# Claude Search Optimization (CSO)

Reference for making skills discoverable by Claude's skill selection mechanism.

## How Skill Discovery Works

1. Claude encounters a task
2. Claude reads all skill **descriptions** (YAML frontmatter — always loaded)
3. Claude decides which skills to load based on description match
4. Selected skill's SKILL.md body is loaded
5. Claude follows the instructions

**The description field is the only thing Claude sees before deciding to load a skill.** Everything else depends on the description being right.

## Writing Descriptions

### The Golden Rule

**Description = WHEN to use the skill. Never HOW the skill works.**

Testing revealed that when a description summarizes the skill's workflow, Claude follows the description as a shortcut instead of reading the full skill content.

### Format

```yaml
description: >
  Use when {triggering conditions}.
  Triggers: "{phrase1}", "{phrase2}", "{phrase3}".
```

### Rules

| Rule | Rationale |
|------|-----------|
| Start with "Use when" | Focuses on triggering conditions |
| Include 3+ trigger phrases | Covers how users actually phrase requests |
| Write in third person | Injected into system prompt context |
| Under 1024 characters (aim for 500) | Frontmatter size limit |
| No workflow summary | Prevents Claude from shortcutting the skill body |
| Mention file types if relevant | "Use when working with .csv files" |
| Include negative triggers if needed | "Do NOT use for simple data exploration" |

### Examples

```yaml
# BAD: Too vague
description: Helps with projects.

# BAD: Summarizes workflow (Claude may follow this instead of reading skill)
description: >
  Reviews code by running linting, then unit tests, then integration tests,
  and produces a summary report.

# BAD: Missing triggers
description: Creates sophisticated multi-page documentation systems.

# GOOD: Triggering conditions with trigger phrases
description: >
  Use when the user wants to create a structured git commit with conventional
  formatting. Triggers: "commit", "commit changes", "create a commit".

# GOOD: Specific domain with negative trigger
description: >
  Use when processing PDF legal documents for contract review.
  Do NOT use for general document formatting.
  Triggers: "review contract", "analyze PDF", "legal document review".
```

## Keyword Coverage

Include words Claude would search for when matching tasks to skills:

| Category | Examples |
|----------|---------|
| **Error messages** | "Hook timed out", "ENOTEMPTY", "merge conflict" |
| **Symptoms** | "flaky", "hanging", "slow", "broken", "failing" |
| **Synonyms** | "timeout/hang/freeze", "cleanup/teardown/reset" |
| **Tools** | Actual command names, library names, file types |
| **Actions** | Verbs users say: "create", "fix", "review", "deploy" |

## Naming Conventions

Skill names affect discoverability:

| Pattern | Example | Why |
|---------|---------|-----|
| Verb-first, active voice | `creating-skills` not `skill-creation` | Describes the action |
| Gerunds for processes | `debugging-with-logs` | Active, clear purpose |
| Descriptive over abstract | `condition-based-waiting` not `async-helpers` | Communicates the technique |
| Kebab-case | `skill-workbench` not `SkillWorkbench` | Required by spec |

## Countering Under-Triggering

Claude tends to under-trigger — it often doesn't use a skill even when it would be helpful. To counter this, make descriptions slightly "pushy": include contexts where the skill should be used even if the user doesn't name it explicitly.

```yaml
# Weak — only triggers on exact matches
description: >
  Use when the user asks to create a dashboard.

# Stronger — covers adjacent intents that should also trigger
description: >
  Use when the user wants to create a dashboard, visualize data,
  display metrics, or build any kind of data display — even if they
  don't explicitly ask for a "dashboard."
```

## Testing Discoverability

### Trigger Testing

Run 10-20 test queries that should trigger the skill. Track:

- How many times it loads automatically vs requires explicit invocation
- Target: 90%+ automatic triggering on relevant queries

### Over-Triggering Testing

Run 5-10 unrelated queries. Verify the skill does NOT load. If it does:

1. Add negative triggers to description
2. Be more specific about the domain
3. Clarify scope boundaries

### Debug Technique

Ask Claude directly:

> "When would you use the [skill-name] skill?"

Claude will quote the description back. Adjust based on what's missing or misleading.

## Discovery Flow Optimization

Future Claude instances find skills through this flow:

```
1. Encounters problem → 2. Scans descriptions → 3. Loads matching skill
→ 4. Reads overview → 5. Scans quick reference → 6. Loads examples if implementing
```

**Optimize for this flow:** Put searchable terms in the description, core patterns early in the skill body, and detailed examples later or in reference files.

## Sources

- [superpowers: writing-skills — CSO section](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md)
- [Anthropic: The Complete Guide to Building Skills for Claude](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)
