# Skill Quality Checklist

Reference for evaluating and improving skills during `/skill-workbench` sessions.

## Quality Dimensions

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| Conciseness | 20% | One sentence per concept. Tables over paragraphs. No filler words. |
| Scannability | 20% | Clear headings. Bullet points. Working examples. Quick-start workflow early. |
| Completeness | 20% | All edge cases addressed. Error handling section present. Copy-paste ready code blocks. |
| Consistency | 15% | Announce line present. Numbered Steps. Error Handling section. Follows AGENTS.md conventions. |
| Self-containment | 10% | Works without external context. No references to AGENTS.md content. Duplication preferred over external dependencies. |
| Discoverability | 15% | Description starts with "Use when". Trigger phrases included. No workflow summary. Keywords for common search terms. See [claude-search-optimization.md](claude-search-optimization.md). |

## Filler Words to Remove

Remove these words — they add no information:

> simply, just, easily, basically, actually, really, very, obviously, clearly, of course, in order to, it should be noted that, please note that

## Structure Priorities

1. Quick-start or most common workflow early
2. Copy-paste ready code blocks with expected output
3. Tables for reference, not paragraphs
4. Specific commands, not vague instructions ("Run `make all`" not "Validate your changes")
5. Reference files one level deep from SKILL.md (see [progressive-disclosure.md](progressive-disclosure.md))

## Vague Verbs to Replace

| Vague | Specific Alternative |
|-------|---------------------|
| handle | `catch error and log`, `route to handler`, `parse and validate` |
| process | `run script`, `transform JSON`, `filter results` |
| manage | `create/update/delete`, `track in state file`, `version with semver` |
| ensure | `verify with assertion`, `validate output matches`, `run check command` |
| utilize | `use`, `call`, `run` |

## Before/After Example

### Before (vague, wordy)

```markdown
## Step 2: Process Changes

You should basically just look at the changes that were made and think about
whether they are correct. It's important to actually verify that everything
is working properly before proceeding to the next step. Please note that you
should also check for any potential issues.
```

### After (specific, concise)

```markdown
## Step 2: Verify Changes

1. Run `git diff --stat` to list changed files.
2. For each changed file, verify:
   - No unintended modifications outside the target area
   - New code follows existing patterns in the file
   - No debug statements or temporary code remain
3. Run `make all` to confirm all checks pass.
```

## Best Practices Reference

Key criteria from [best-practices.md](best-practices.md):

| Criterion | Check |
|-----------|-------|
| Token cost | Does each paragraph justify its context window cost? Remove content Claude already knows. |
| Degrees of freedom | Low-freedom for fragile ops (exact commands), high-freedom for context-dependent decisions. See [progressive-disclosure.md](progressive-disclosure.md). |
| Progressive disclosure | SKILL.md under 500 lines. Heavy reference in separate files, one level deep. |
| Description quality | Third person. Starts with "Use when". Includes trigger phrases. No workflow summary. See [claude-search-optimization.md](claude-search-optimization.md). |
| Consistent terminology | One term per concept throughout (not "endpoint"/"URL"/"route" interchangeably). |
| Cross-model validity | Validated on Haiku, Sonnet, and Opus if possible. |

## Discipline Skill Criteria

For skills that enforce rules (TDD, verification, etc.), also check:

| Criterion | Check |
|-----------|-------|
| Bright-line rules | Absolute language ("NEVER", "YOU MUST") for critical requirements |
| Rationalization table | Captures known excuses with explicit counters |
| Red flag list | Self-check triggers that signal rationalization in progress |
| Loophole closure | Specific workarounds are explicitly forbidden |
| Tested with pressure | RED-GREEN-REFACTOR cycle completed (see [testing-with-subagents.md](testing-with-subagents.md)) |

See [persuasion-principles.md](persuasion-principles.md) for the full framework.

## Definition of Done

A skill improvement is complete when:

**Behavioral testing (required for all non-formatting changes):**

- [ ] Appropriate test type executed per skill type (see [testing-with-subagents.md](testing-with-subagents.md))
- [ ] For discipline skills: RED-GREEN-REFACTOR cycle completed with pressure scenarios
- [ ] For technique/workflow skills: application scenario verified agent follows changed steps
- [ ] For pattern skills: recognition/application scenario verified
- [ ] For reference skills: retrieval scenario verified agent finds and applies info
- [ ] For edits: test exercises the specific changes made, not just the skill overall
- [ ] Exception: formatting-only changes (filler words, table alignment) skip behavioral testing

**Structural quality:**

- [ ] All frontmatter fields present and valid (`name`, `description`, `argument-hint`, `user-invocable`)
- [ ] Description starts with "Use when", includes triggers, written in third person
- [ ] Description does NOT summarize the skill's workflow (triggering conditions only)
- [ ] Announce line present as first content line after heading
- [ ] Steps are numbered with specific actions (commands, not vague instructions)
- [ ] Error handling covers all identified failure modes
- [ ] No filler words remain in updated content
- [ ] Readable on first pass by someone unfamiliar with the skill
- [ ] Cross-references to other skills validated (`make check-refs`)
- [ ] SKILL.md body under 500 lines; heavy reference in separate files
- [ ] References kept one level deep from SKILL.md
- [ ] Version bump applied to owning plugin's `plugin.json`
- [ ] `make all` passes
