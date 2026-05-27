# /doc Examples

## Create a runbook

```
/doc create --format runbook --title "Kafka Consumer Lag" --path docs/runbooks/kafka-consumer-lag.md
```

Creates a new runbook with sections: Overview, Prerequisites, Detection, Response Steps, Verification, Rollback, and Post-Incident.

## Improve documentation clarity

```
/doc improve --path docs/guides/oncall.md --tone concise
```

Rewrites the oncall guide to be more concise: shortens sentences, removes redundancy, and converts passive to active voice.

## Audit a documentation directory

```
/doc audit --path docs/
```

Generates a full audit report for all Markdown files in `docs/`, including scores, broken links, missing sections, and prioritized recommendations.

## Fix broken links

```
/doc maintain --path docs/api/
```

Scans the API docs for broken links and structural issues, offers to auto-fix where possible.

## Sync to Confluence

```
/doc sync --path docs/ --force
```

Syncs all ddoc-annotated documents in `docs/` to Confluence without prompting.

## Create with Confluence target

```
/doc create --format guide --title "Getting Started" --path docs/getting-started.md \
  --confluence-space "TEAM" --confluence-parent "123456"
```

Creates a guide with ddoc frontmatter pre-configured for Confluence sync.
