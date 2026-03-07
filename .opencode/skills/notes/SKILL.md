---
name: notes
description: >
  Use when the user asks to create, look up, or edit a note in Obsidian —
  especially people-related notes like 1:1s, meeting notes, career plans, promotion docs, or per-person achievements.
  Triggers: "note about", "log a meeting", "record a 1:1", "1:1 with Sarah",
  "update career plan for Alex", "promotion doc for Sam", "track a win for Jamie",
  "add to my notes", "write down", "log that", "record that",
  "find my notes about", "look up notes on", "meeting notes for",
  "what did I write about", "search my notes".
  Does NOT handle: daily work journal entries (use `/daily`),
  monthly brag document or automated accomplishment collection (use `/brag`),
  feedback about a person's performance for review cycles.
argument-hint: "[create | lookup | edit] [description]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(date:*), Bash(mkdir:*), Bash(ls:*), AskUserQuestion
---

# Notes

Announce: "I'm using the /notes skill to manage your Obsidian notes."

You manage structured notes in the user's Obsidian vault —
1:1 records, meeting notes, career plans, promotion proposals, per-person achievements, and general notes.
All notes use consistent frontmatter, tags, and People wikilinks for Obsidian graph integration.

## Vault & Folder Structure

**Vault root:** `~/docs/`

```
~/docs/
├── 1-1s/
│   └── <Person Name>/
│       └── YYYY-MM-DD.md              # one file per session
├── People/
│   └── <Person Name>/
│       ├── <Person Name>.md                                  # overview: who they are, key traits
│       ├── <Person Name> - Career Plan.md                    # goals, milestones, active growth plan
│       ├── <Person Name> - Achievements.md                   # cumulative log of achievements
│       └── <Person Name> - Promotion Proposal to <Level>.md  # promotion doc (e.g. "to Senior")
├── Meetings/
│   └── YYYY-MM-DD-<slug>.md           # non-1:1 meeting notes
├── Daily/                              # managed by /daily — do not write here
└── Misc/
    └── <freeform>.md
```

## Frontmatter Convention

All notes include:

```yaml
---
date_created: YYYY-MM-DD
date_modified: YYYY-MM-DD
category: 1-1 | meeting | career-growth | promotion | achievements | overview | misc
tags: []
---
```

Meeting and 1:1 notes also include:

```yaml
attendees: [Name1, Name2]
```

Career-growth notes always include the tag `career`.

### Tag Extraction

When composing any note, extract relevant tags from content (topics, themes, locations, events, skills).

- **Reuse existing tags**: Grep `~/docs/**/*.md` for `^tags:` to find tags already in use.
  Prefer existing spelling to avoid duplicates (e.g., use `ops-review` if it exists, not `opsreview`).
- Use lowercase hyphenated slugs for multi-word tags (e.g., `paris-summit`, `technical-leadership`).
- Aim for 2-5 content tags per note beyond mandatory ones.

## Step 1: Get Today's Date

**Always run `date +%Y-%m-%d` first.** Store the result as `TODAY`. Never hardcode dates.

## Step 2: Classify the Request

Use this decision tree:

| Signal | Category | Target Path |
|--------|----------|-------------|
| Person + "1:1" / "one on one" / "one-on-one" | `1-1` | `1-1s/<Person>/TODAY.md` |
| "meeting" + multiple people or a topic | `meeting` | `Meetings/TODAY-<slug>.md` |
| Career goals / growth plan / development for a person | `career-growth` | `People/<Person>/<Person> - Career Plan.md` |
| "promotion" for a person | `promotion` | `People/<Person>/<Person> - Promotion Proposal to <Level>.md` |
| Achievements logged for a specific person | `achievements` | `People/<Person>/<Person> - Achievements.md` |
| Overview / profile / "who is X" | `overview` | `People/<Person>/<Person>.md` |
| None of the above | `misc` | `Misc/<slug>.md` |
| **Unclear or ambiguous** | — | **Ask using AskUserQuestion before creating anything** |

Slug = lowercase letters and hyphens, max ~5 words derived from the topic.

## Step 3: Resolve Person Name

When the user mentions someone by first name, nickname, or partial name:

1. Run `ls ~/docs/People/` to get the list of known people.
2. **Unique match**: use the full name exactly as it appears (preserving accents/diacritics).
3. **Multiple matches**: use AskUserQuestion to clarify which person.
4. **No match**: bootstrap a new People entry.
   Create `~/docs/People/<Full Name>/<Full Name>.md` with:

```markdown
---
date_created: YYYY-MM-DD
date_modified: YYYY-MM-DD
category: overview
person: Full Name
tags: [overview, fullname-slug, relationship]
---

# Full Name

## Overview
Brief context from the current interaction.
```

For the relationship tag, use your best guess: `report`, `collaborator`, `peer`, `skip-level`, `external`, etc.
If only a first name is given and you can't infer the full name from context, ask using AskUserQuestion.

Use full names wrapped in Obsidian wikilinks (`[[Full Name]]`) in note content for graph integration.

## Step 4: Determine Operation

Parse the request to determine the operation: **CREATE**, **LOOKUP**, or **EDIT**.

If unclear, default to CREATE for new content and LOOKUP for questions about existing notes.

### CREATE

1. Run `mkdir -p` on the parent directory.
2. Check if the target file already exists (use Read):

| Category | If file exists | If file doesn't exist |
|----------|---------------|----------------------|
| `1-1` | Append a new `## Session` heading with content | Create fresh with frontmatter |
| `career-growth` / `achievements` | Append with `- TODAY: <content>` bullets | Create fresh with frontmatter |
| `meeting` | Ask whether to append or create new file | Create fresh with frontmatter |
| `promotion` | Ask whether to update or create new file | Create fresh with frontmatter |
| All others | Ask whether to append or create new | Create fresh with frontmatter |

3. Compose content: frontmatter + bullet-list body.
4. Write or Edit the file.
5. Confirm the absolute path to the user.

### LOOKUP

1. Glob `~/docs/**/*.md` filtered by relevant filename keywords (exclude `Daily/`).
2. If no filename match: Grep vault content for keywords (exclude `Daily/`).
3. Results:
   - **0 matches**: inform user, offer to create a new note.
   - **1 match**: Read and display the file.
   - **Multiple matches**: use AskUserQuestion to let user pick.

### EDIT

1. Run LOOKUP to find the file.
2. Apply the requested changes (preserve all existing content not being changed).
3. Update `date_modified` in frontmatter to TODAY.
4. Confirm the path and changes to the user.

## Step 5: Update People Backlinks

After creating or editing a note that mentions people,
update each mentioned person's People file by appending a backlink under `## Referenced In`:

```
- `<relative-path-from-vault>` - Brief context of the mention
```

If `## Referenced In` doesn't exist, add it.
If there's already a backlink for today's date in the same file, update rather than duplicate.
This creates two-way links: notes mention people, People files link back to notes.

## Formatting Rules

- **Bullet lists over prose** — use `-` bullets for all note content.
- **Concise** — preserve information density, not narrative or filler.
- Keep frontmatter minimal and correct.
- One blank line between sections, no extra blank lines between bullets.

## Error Handling

| Error | Action |
|-------|--------|
| `~/docs/` directory doesn't exist | Create it with `mkdir -p` and proceed |
| `~/docs/People/` directory doesn't exist | Create it with `mkdir -p` when first person is mentioned |
| Person name ambiguous (multiple matches) | Use AskUserQuestion to clarify |
| Request is completely vague (e.g., "create a note") | Use AskUserQuestion to clarify category before doing anything |
| File has unexpected format | Append content at the end rather than inserting into sections |
| Glob/Grep returns too many results | Narrow with additional keywords, then present top 5 matches |
