---
name: "datadog"
description: "Use when the user needs to query, investigate, or interact with any Datadog product via the pup CLI. Covers APM, traces, logs, metrics, monitors, error tracking, RUM, network, infrastructure, security, incidents, SLOs, synthetics, CI/CD, service catalog, dashboards, cost, cloud integrations, fleet, and 30+ other API domains. Triggers: \"check logs\", \"query metrics\", \"APM traces\", \"error tracking\", \"monitors\", \"Datadog\", \"pup\", \"service health\", \"latency\", \"error rate\", \"RUM sessions\", \"network flows\", \"security signals\", \"incidents\", \"SLOs\", \"synthetics\", \"infrastructure\", \"hosts\", \"Kubernetes\", \"CI/CD pipeline\", \"observability\"."
---

# Datadog Product Query

Announce: "I'm using the /datadog skill to query Datadog via the pup CLI."

## Step 1: Execution Strategy

pup is installed and pre-authenticated. Do not check if it exists or verify auth — use it directly.

All pup output is JSON. Follow these rules for efficient querying:

| Rule | Detail |
|-|-|
| jq filters to file | Write jq to `/tmp/filter.jq`, run `jq -f /tmp/filter.jq`. Avoids shell escaping issues with zsh `!`, backticks, nested quotes. Exception: trivial access like `jq '.data'`. |
| Cache responses | Redirect first query to file (`> /tmp/result.json`). Filter cached file for follow-ups. Never re-query the same API. |
| Parallel queries | Background independent queries: `pup ... > /tmp/a.json & pup ... > /tmp/b.json & wait`. Batch as many initial queries as possible. |
| Trust documented schemas | For commands in [references/query-patterns.md](references/query-patterns.md), trust the response schemas. Do not `\| head` to learn structure. Only `\| head` for unlisted commands. |
| Pre-filter exploration | For undocumented shapes: `jq '.data \| keys'` then `jq '.data[0]'` to see structure before writing complex filters. |
| Budget awareness | Partial answer from available data beats no answer. Prefer one comprehensive jq filter over many single-purpose ones. |
| Switch data sources | If an approach yields no results in 2 attempts, try a different domain or data source. |

For multi-org setups, add `--org <name>` to all commands.
When unsure about a domain's subcommands or flags, run `pup <domain> --help`.

## Step 2: Classify Intent and Execute

Determine which pup domain maps to the user's request.
Many requests span multiple domains — start with the most specific, then chain.

| User Intent | Primary | Chain With |
|-|-|-|
| Service performance, latency, throughput | `apm` | `logs`, `monitors` |
| Application errors, exceptions | `error-tracking` | `logs`, `apm` |
| Log search, patterns, volume | `logs` | `metrics` |
| Custom or system metrics | `metrics` | `dashboards` |
| Alert status, monitor health | `monitors` | `downtime`, `slos` |
| Frontend performance, user sessions | `rum` | `synthetics` |
| Host inventory, containers | `infrastructure` | `fleet`, `tags` |
| Security findings, threat detection | `security` | `audit-logs` |
| Incident management | `incidents` | `cases`, `on-call` |
| SLO status, error budgets | `slos` | `monitors` |
| Synthetic tests, uptime | `synthetics` | `monitors` |
| CI/CD pipelines, flaky tests | `cicd` | `code-coverage` |
| Service ownership, metadata | `service-catalog` | `scorecards` |
| Cost analysis, billing | `cost` | `usage` |

For command patterns, response schemas, and jq filters per domain,
see [references/query-patterns.md](references/query-patterns.md).

### Query Syntax

**Logs**: `status:error service:web-app @attr:val host:i-* "exact phrase"`.
Operators: `AND`, `OR`, `NOT`, `-field:val` (negation), `*` (wildcard).

**Metrics**: `<agg>:<metric>{<filter>} by {<group>}`.
Example: `avg:system.cpu.user{env:prod} by {host}`.

**Traces**: `service:<name> resource_name:<path> @duration:>5s status:error`.

**Monitors**: `--name` for substring, `--tags` for tag filter, `--query` for full-text search.

## Step 3: Investigation Workflows

When diagnosing issues, batch initial queries in parallel, then narrow.

### Service Degradation

```bash
pup monitors list --tags="service:<name>" > /tmp/monitors.json &
pup logs search --query="service:<name> status:error" --from="1h" > /tmp/errors.json &
pup apm dependencies list --env prod --start $(date -v-1H +%s) --end $(date +%s) > /tmp/deps.json &
wait
```

1. Check alerting monitors from `/tmp/monitors.json`
2. Review error logs from `/tmp/errors.json`
3. Check downstream dependencies from `/tmp/deps.json`
4. If needed: `pup apm services stats --start EPOCH --end EPOCH --env prod` for throughput

### Error Spike

```bash
pup logs search --query="service:<name> status:error" --from="4h" > /tmp/logs.json &
pup error-tracking issues search > /tmp/et-issues.json &
pup events search --query="source:deploy" > /tmp/events.json &
wait
```

1. Quantify spike from cached log data (write jq group-by filter to file)
2. Group errors by type from error-tracking
3. Correlate with deploy events
4. If needed: `pup apm services stats` for throughput changes

After each step, summarize findings and identify patterns before querying further.

## Step 4: Domain-Specific Gotchas

| Gotcha | Detail |
|-|-|
| APM requires `--env` | All APM commands need `--env prod` (or target environment). |
| APM flow-map unreliable | Use `pup apm dependencies list` for upstream/downstream mapping. |
| Service catalog: no team filter | Requires per-service lookups. For team queries, use `pup monitors search` (monitors carry team tags). |
| Team names are shorthand | User team names may not match Datadog tags. Use `pup monitors search --query="<name>"` to discover actual tag values first. |
| Epoch math (macOS) | `$(date -v-1H +%s)` for 1 hour ago. Linux: `$(date -d '1 hour ago' +%s)`. |
| Missing `--from` | Most commands default to 1h but some don't. Always specify explicitly. |
| Huge result sets | Start with 10-50, refine query, then increase. |
| Duration units | APM durations are nanoseconds. Prefer shorthand: `@duration:>5s`. |
| Missing aggregation | `pup metrics query` requires prefix: `avg:`, `sum:`, `max:`, `min:`, `count:`. |
| Log counting | Use `pup logs aggregate --compute count`, not fetch-and-count. |
| Wide time ranges | `--from=30d` is slow. Start narrow (1h), widen if needed. |
| Large org listings | Never list all monitors or logs unfiltered. Always add `--tags` or `--query`. |

## Error Handling

| Error | Action |
|-|-|
| `pup` not found | Tell user to install pup (check internal Datadog docs) |
| 401 Unauthorized | `pup auth login` to re-authenticate |
| 403 Forbidden | User lacks API permissions; check role assignments |
| 429 Rate Limited | Narrow query: smaller `--limit`, tighter time range, add filters |
| Empty results | Verify tag values with a broader search before retrying syntax variations |
| Timeout | Narrow `--from` range or add more query filters |
| Unknown domain | Run `pup --help` to list all available domains |
