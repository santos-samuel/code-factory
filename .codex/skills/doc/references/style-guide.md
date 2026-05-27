# Documentation Style Guide

All documents created or improved by this skill follow these conventions.

## Headings

- Use ATX-style headings (`#`, `##`, etc.)
- One H1 per document (the title)
- No skipped levels (H2 → H4 is invalid, use H2 → H3 → H4)
- Headings should be descriptive, not generic ("Configure Authentication" not "Configuration")

## Links

- Use descriptive link text: `[installation guide](./install.md)` not `[click here](./install.md)`
- Prefer relative links for internal docs: `./setup.md` not absolute URLs
- External links should include context: "See the [official documentation](https://...)"

## Code Blocks

- Always include language identifier: ` ```bash `, ` ```python `, ` ```yaml `
- Use `bash` for shell commands, `shell` for interactive sessions with output
- Use `text` for output-only blocks
- Include comments explaining non-obvious commands

## Admonitions

Use GitHub-style admonitions (compatible with ddoc):

```markdown
> [!NOTE]
> Informational content.

> [!TIP]
> Helpful suggestions.

> [!WARNING]
> Important cautions.

> [!CAUTION]
> Critical warnings about data loss or security.
```

## Frontmatter

For ddoc-enabled documents:

```yaml
---
ddoc:
  confluence_space: "TEAM"
  confluence_parent: "123456"
  title: "Document Title"  # optional, defaults to H1
---
```

## Writing Rules

| Rule | Example |
|------|---------|
| Use active voice | "Run the command" not "The command should be run" |
| Be direct | "Configure X" not "You will need to configure X" |
| Avoid jargon | Define terms on first use or link to glossary |
| Short sentences | Max 25 words per sentence |
| One idea per paragraph | Break complex explanations into steps |
| Present tense | "This command creates..." not "This command will create..." |

## Typographic Rules

| Rule | Detail |
|------|--------|
| No em dashes | Do not use `---` or `—`. Use a period, colon, or split the sentence. |
| No en dashes | Do not use `–` anywhere, including number ranges. Use `to` (e.g., "10 to 20 req/s"). |
| Straight quotes only | Use `"` and `'`. No curly quotes. |
| No mid-sentence styling | No `**bold**` or `*italic*` inside sentences. Use headings, lists, or code formatting. |

## Banned Vocabulary

These words signal AI-generated text in documentation. Replace with the specific command, flag, metric, or behavior.

| Banned | Replace with |
|--------|-------------|
| delve, delve into | "covers", "explains", or start the content |
| crucial, pivotal | State the consequence directly |
| robust | Describe the failure mode handled |
| seamless, seamlessly | Describe the handoff or integration cost |
| leverage, leveraging | "use", "call", "extend" |
| tapestry, multifaceted, nuanced | Delete or name the specific parts |
| comprehensive | List what is and is not covered |
| streamline | "removes N of M manual steps" |
| empower, enable | Describe the concrete capability |
| best-in-class, cutting-edge, world-class | Cite a benchmark or drop it |
| stands as a testament | Delete |
| ensure, guarantee | "reduces the chance of X", "detects X within Y seconds" |
| scalable (without numbers) | "scales to N req/s per pod" |

## Structural Rules

- No rule-of-three padding. Two examples are fine. Four are fine. Do not pad for rhythm.
- No trailing `-ing` clauses ("..., enabling users to..."). End the sentence.
- No motivational transitions ("It is worth noting that...", "Moving forward...").
- No thesis restatements in each section.
- No closing pep talks.

## Smell Tests

Run before publishing any page with narrative prose.

| Test | Question | Action |
|------|----------|--------|
| Landing-page | Could this sentence appear on a vendor marketing page? | Rewrite with specifics. |
| Read-aloud | Read the paragraph out loud. Does it cringe or sound like ad copy? | Rewrite in plainer language. |
| Signature | Would you defend every word to a reader who asks "show me"? | Remove or replace. |

## Density Rule

One AI-slop word in a short doc is fine if backed by specifics. Five AI-slop words in two paragraphs means rewrite the whole passage. The problem is register, not vocabulary.
