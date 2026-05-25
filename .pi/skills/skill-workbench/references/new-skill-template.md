# Creating New Skills and Plugins

Reference for creating new skills or plugins during `/skill-workbench` sessions. For significant new features, suggest running `/do` instead.

## New Skill Checklist

1. Determine which plugin it belongs to (`productivity`, `git`, `code`).
2. Create `{plugin}/skills/{name}/SKILL.md` (folder name in kebab-case).
3. Add YAML frontmatter with all required fields (see template below).
4. Follow the Announce -> Steps -> Error Handling structure.
5. Update the plugin's `.claude-plugin/plugin.json` version (minor bump).
6. Run `make all` to validate.

## New Plugin Checklist

1. Create `{name}/.claude-plugin/plugin.json` with name, version, description, author.
2. Create skill directories under `{name}/skills/`.
3. Add the plugin to `.claude-plugin/marketplace.json`.
4. Confirm with the user before proceeding (per AGENTS.md boundaries).

## YAML Frontmatter Template

```yaml
---
name: {name}
description: >
  Use when {trigger condition}.
  Triggers: "{phrase1}", "{phrase2}", "{phrase3}".
argument-hint: "[{argument description}]"
user-invocable: true
---
```

### Optional Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `allowed-tools` | Restrict tool access | `Bash(git:*), Read, Grep, Glob` |
| `disable-model-invocation` | Prevent auto-invocation | `true` |

## Skill Body Template

```markdown
# {Skill Title}

Announce: "I'm using the {name} skill to {purpose}."

## Step 1: {First Action}

{Specific instructions with commands.}

## Step 2: {Second Action}

{Specific instructions with commands.}

## Error Handling

| Error | Action |
|-------|--------|
| {error condition} | {specific resolution} |
```
