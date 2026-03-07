---
name: brag
description: >
  Use when the user wants to update their brag document, log accomplishments,
  reflect on recent work, or prepare for performance reviews.
  Triggers: "brag", "update brag doc", "log accomplishments", "what did I do today",
  "update my doc", "brag doc", "end of day", "weekly update".
argument-hint: "[--week | --month | --since YYYY-MM-DD]"
user-invocable: true
---

# Brag Document

Announce: "I'm using the /brag skill to update your brag document with recent accomplishments."

## Step 1: Initialize

### 1a: Date Range

Parse `$ARGUMENTS` to determine the collection window.

```bash
TODAY=$(date +%Y-%m-%d)
MONTH_DIR=$(date +%Y-%m)
```

| Argument | Range |
|----------|-------|
| (none) | Since `last_run` in state file — catches up automatically. Falls back to today if first run. |
| `--today` | Today only |
| `--week` | Last 7 days |
| `--month` | Current calendar month |
| `--since YYYY-MM-DD` | From that date to today |

Store `START_DATE` and `END_DATE` for all queries.

### 1b: State File

Read `~/log/.brag-state.json`.
If missing, run first-time setup (Step 1c).

The state file tracks persistent data across runs:

| Field | Purpose |
|-------|---------|
| `last_run` | ISO date of last run — determines default date range |
| `github_user` | GitHub username for PR queries |
| `repos` | GitHub repos to search (org/name format) |
| `mentees.current` | Active mentees: `{name, since, notes}` |
| `mentees.past` | Past mentees: `{name, period, notes}` |
| `guilds` | Community groups and ERGs |
| `recurring_meetings` | Regular syncs: `{name, cadence, role}` |
| `interview_types` | Interview types conducted |

### 1c: First-Time Setup

If no state file exists:

```bash
mkdir -p ~/log
GH_USER=$(gh api user --jq .login 2>/dev/null || echo "unknown")
```

Create `~/log/.brag-state.json` with defaults:

```json
{
  "last_run": null,
  "github_user": "<detected>",
  "repos": ["DataDog/dd-source", "DataDog/dd-go", "DataDog/logs-backend", "DataDog/dogweb"],
  "mentees": {"current": [], "past": []},
  "guilds": [],
  "recurring_meetings": [],
  "interview_types": ["System Design", "Team Match", "Coding"]
}
```

Present the defaults and ask the user to confirm or customize repos, mentees, guilds, and meetings.
Mentees are especially important — ask for current mentees by name, since when, and any context.

### 1d: Monthly Document

Find or create `~/log/$MONTH_DIR/brag.md`:

```bash
mkdir -p ~/log/$MONTH_DIR
```

If the file doesn't exist, create it from the [template](references/template.md).
If it exists, read it to understand what's already been captured — this enables deduplication in Step 3.

## Step 2: Automated Collection

Gather accomplishments from multiple sources.
Only collect items within `START_DATE` to `END_DATE`.
Run independent queries in parallel where possible.

### 2a: GitHub PRs Authored

For each repo in `state.repos`:

```bash
gh pr list --author @me --repo <repo> --state all \
  --search "created:>=<START_DATE>" \
  --json number,title,url,state,createdAt,mergedAt --limit 100
```

Record: PR number, title, URL, state (merged/open/closed), dates.

### 2b: GitHub PR Reviews Given

```bash
gh api "search/issues?q=reviewed-by:<github_user>+type:pr+created:>=<START_DATE>+org:DataDog&per_page=50" \
  --jq '.items[] | {number: .number, title: .title, url: .html_url, repo: .repository_url}'
```

### 2c: Jira Tickets

Search using the Atlassian MCP tool if available:

```
mcp__atlassian__searchJiraIssuesUsingJql(
  jql = "assignee = currentUser() AND updated >= '<START_DATE>' ORDER BY updated DESC",
  limit = 50
)
```

Record: ticket key, summary, status, type.

### 2d: Confluence Pages

Search for recently created or updated pages:

```
mcp__atlassian__searchConfluenceUsingCql(
  cql = "creator = currentUser() AND created >= '<START_DATE>' ORDER BY created DESC",
  limit = 20
)
```

### 2e: Git Commits

Search for commits in the current repo and any accessible repo directories:

```bash
git log --author="$(git config user.email)" \
  --since="<START_DATE>" --until="<END_DATE>" \
  --oneline --no-merges
```

### 2f: Daily Log Entries

Scan the Obsidian daily journal (written by `/daily`) for entries in the date range.

```bash
# Find daily notes within range
find ~/docs/Daily/ -name "*.md" -newer <temp_start> ! -newer <temp_end> 2>/dev/null
```

For each daily note file in range, Read the file and extract items from these sections:

| Daily Log Section | Brag Section |
|-------------------|-------------|
| **Work** | Direct Impact |
| **Achievements** | Direct Impact |
| **Kudos** (given by others to the user) | Direct Impact or Uncategorized |
| **Kudos** (given by the user to others) | Consulting or skip |
| **Meetings** (with notable decisions) | Consulting or Direct Impact |
| **Learning** | Learning |

Skip Team Pulse, Travel, and Notes sections — they don't map to brag categories.

Only extract items with enough context to be meaningful in a brag doc.
"4x 1:1s" is too generic — skip it.
"Architecture review — decided to go with option B for the caching layer" is worth capturing.

## Step 3: Deduplicate and Update Document

### 3a: Deduplicate

For each collected item, search the existing monthly doc for:
- URL matches (exact)
- PR/ticket number matches
- Title keyword overlap (fuzzy — use judgment)

Skip items already present.

### 3b: Categorize

Assign each new item to a document section:

| Signal | Section |
|--------|---------|
| PR authored or merged | Direct Impact |
| Jira ticket resolved or in progress | Direct Impact |
| PR review given (cross-team) | Consulting |
| PR review given (own team) | Direct Impact |
| Confluence page created | Docs & Talks |
| Significant commit (not part of a PR) | Direct Impact |

Items that don't clearly fit go in `## Uncategorized` for manual sorting.

### 3c: Format Entries

Format each entry as a bullet point with:
- **What**: Brief description with link
- **Context**: Why it matters or what impact it had (infer from PR title, Jira summary, or ask)

Example: `* [Fix flaky test timeout in auth module](https://github.com/DataDog/dd-go/pull/1234) — Reduced CI flakiness for the auth team`

### 3d: Present and Write

Show the proposed additions grouped by section.
Ask the user to confirm before writing to the monthly doc.
Use the Edit tool to append new entries under the correct section headers.

## Step 4: Interactive Questions

Ask about work that can't be discovered automatically.
Load the question bank from [references/questions.md](references/questions.md).

### Question Flow

1. Read the state file for context (mentees, guilds, meetings, interview types).
2. Skip question categories already well-covered by automated collection.
3. Present questions one at a time using `AskUserQuestion`.
4. For each answer with content, append to the appropriate doc section.
5. For "skip"/"none" answers, move to the next question.
6. Update the state file if persistent data changed (new mentee, new guild, etc.).

### Mentee Check

For each current mentee in `state.mentees.current`:

```
AskUserQuestion(
  header: "Mentorship",
  question: "Any updates on your mentoring of <name> (<since>, <notes>)?",
  options: [
    "Yes" -- I have updates to add,
    "No updates" -- Nothing new this period,
    "Ended" -- This mentorship has concluded
  ]
)
```

If "Yes": ask for details and add to Mentorship section.
If "Ended": move to `state.mentees.past` with the current date as end period.

### Recurring Meeting Check

For each meeting in `state.recurring_meetings`:

```
AskUserQuestion(
  header: "Meetings",
  question: "Anything notable from <name> (<cadence>)?",
  options: [
    "Yes" -- Something worth recording,
    "Nothing notable" -- Skip,
    "No longer attending" -- Remove from recurring list
  ]
)
```

## Step 5: Finalize

### 5a: Write Document

Save the updated brag doc to `~/log/$MONTH_DIR/brag.md`.
Use semantic line feeds: one sentence per line, target 120 characters.

### 5b: Update State

Update `~/log/.brag-state.json`:
- Set `last_run` to today's date
- Persist any mentee, guild, meeting, or interview type changes

### 5c: Summary

Present a summary:

```
## Brag Update Summary

| Section | New Items |
|---------|-----------|
| Direct Impact | N |
| Mentorship | N |
| ... | ... |

**Document**: ~/log/YYYY-MM/brag.md
**Period scanned**: START_DATE to END_DATE
**Next run**: Will auto-collect from END_DATE onward
```

## Error Handling

| Error | Action |
|-------|--------|
| `gh` CLI not installed or not authenticated | Skip GitHub collection, warn user, continue with other sources |
| Repo not found or no access | Skip that repo, log warning, continue with remaining repos |
| Jira/Confluence MCP tools not available | Skip those sources, warn user, continue |
| Monthly doc has unexpected format | Append new items at the end rather than inserting into sections |
| State file corrupted | Back up to `~/log/.brag-state.json.bak`, recreate from defaults |
| No new items found anywhere | Report "no new items found" and proceed directly to interactive questions |
| `~/log` directory not writable | Report error and exit |
