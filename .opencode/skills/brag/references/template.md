# Brag Document Template

Use this template when creating `~/docs/log/doc.md` for the first time.
This is a single persistent document — entries accumulate over time, organized by section.

## Template

```markdown
# Brag Document

## Direct Impact

Projects, features shipped, technical decisions, and measurable outcomes.

## Building / Team Formation

Team creation, hiring processes, onboarding new members, establishing team rituals.

## Mentorship

### Current

### Past

## Interviewing

| Type | Count |
|------|-------|

## Engineering Culture

### Operational Practices

### Docs & Talks

### Book Clubs & Learning Groups

## Guilds & Groups

## Consulting

## Customer Engagement

### Cooperative Work

### Discovery

### Syncs & CABs

## People & Networking

## Learning

## Goals

### Current Objectives

### Progress

## Uncategorized
```

## Section Guidance

| Section | Career Dimension | What Reviewers Look For |
|---------|-----------------|------------------------|
| Direct Impact | Technical execution | Shipped work, sound decisions, measurable outcomes |
| Building / Team Formation | Organizational growth | Hiring, team setup, culture definition |
| Mentorship | People development | Developing others, multiplier effect |
| Interviewing | Company building | Pipeline contribution, interview quality |
| Engineering Culture | Technical leadership | Standards, practices, bar-raising |
| Guilds & Groups | Cultural contribution | Community involvement, inclusion |
| Consulting | Force multiplication | Cross-team impact, expertise sharing |
| Customer Engagement | Product awareness | User empathy, discovery, embedded work |
| People & Networking | Relationship building | 1:1s, offsites, cross-org connections |
| Learning | Growth mindset | Continuous improvement, new skills applied |
| Goals | Strategic alignment | Working toward team/org objectives |

## Entry Format

Every entry follows this structure — date and description are mandatory,
links and quotes are required when available:

```markdown
* (YYYY-MM-DD) Brief description — why it matters or what impact it had
  [Link Label](url) | [Another Link](url)
  [Slack thread](url): "quoted proof from ephemeral source"
```

**Date formats** (most specific wins):
- `(2026-03-15)` — exact date (preferred)
- `(~2026-03-W2)` — approximate week
- `(2026-03)` — approximate month
- `(Q1 2026)` — quarter (last resort)

**Ephemeral source rule**: Slack messages, DMs, and temporary shared docs may become inaccessible.
Always capture a 1-2 sentence quote that proves the accomplishment.

### Example Entries

```markdown
## Direct Impact

* (2026-03-15) Fix flaky test timeout in auth module — reduced CI flakiness by 40% for the auth team
  [PR #1234](https://github.com/DataDog/dd-go/pull/1234) | [LOGS-5678](https://datadoghq.atlassian.net/browse/LOGS-5678)

## Consulting

* (2026-03-10) Helped [[Sarah Chen]] from Platform team debug memory leak in trace-agent — root-caused to unbounded cache
  [Slack thread](https://datadoghq.slack.com/archives/C123/p456): "You were right, the LRU eviction was disabled in prod config"
  [PR #987](https://github.com/DataDog/datadog-agent/pull/987)

## Engineering Culture

* (2026-02-28) Led cross-team design review for new ingestion pipeline — aligned 3 teams on schema format
  [RFC: Ingestion Pipeline v2](https://datadoghq.atlassian.net/wiki/spaces/ENG/pages/123)
  [Slack thread](https://datadoghq.slack.com/archives/C789/p012): "Thanks @rodrigo, this saved us weeks of back-and-forth"
  [GSlides: Pipeline Design Review](https://docs.google.com/presentation/d/abc123)
```

## Writing Tips

- **Date every entry**: No undated entries. Use approximate dates if exact date is unknown.
- **Quantify impact** where possible: "reduced flaky test rate by 40%" beats "fixed flaky tests"
- **Include context**: explain why the work matters, not just what you did
- **Link everything**: PRs, Jira tickets, Confluence pages, Google Docs, Slack threads
- **Quote ephemeral sources**: Slack messages, DMs, and temporary docs — capture proof text
- **Capture fuzzy work**: code review quality, onboarding help, unplanned consulting
- **Don't undersell**: if you drove a decision, say "drove" not "helped with"
- **Wikilink people**: use `[[Full Name]]` for all people mentioned — connects to the Obsidian People graph
