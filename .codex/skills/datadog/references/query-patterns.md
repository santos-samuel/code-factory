# Query Patterns, Response Schemas, and jq Filters

For domains not listed here, run `pup <domain> --help` to discover subcommands and flags.

## Response Schemas

Trust these schemas — do not `| head` to learn structure for documented commands.

### Logs

`pup logs search` returns:

```
.data.data[].attributes.{
  attributes: {caller, level, ...},
  tags: ["service:X", "datadog_index:Y", ...],
  status, timestamp
}
```

For index breakdown, group by `{datadog_index}`.

### APM

`pup apm services list` returns:

```
.data.data.attributes.services[]   // flat string array of service names
```

`pup apm services stats` returns:

```
.data.data.attributes.services_stats[] with {service, operation, spanKind, hits, requestPerSecond, errorsPercentage}
```

`pup apm entities list` returns:

```
.data.data[].attributes.{id_tags: {service: "..."}, stats: {operation, spanKind}}
```

`pup apm dependencies list` returns:

```
.data.{"<service-name>": {"calls": ["downstream-svc-1", ...]}}
```

### Synthetics

`pup synthetics tests list` returns:

```
.data.tests[] with {name, public_id, status, tags, config.request.url}
```

## jq Filter Patterns

Write complex jq filters to `/tmp/filter.jq` and run `jq -f /tmp/filter.jq /tmp/result.json`.

### Pre-filter Exploration

Run these FIRST for undocumented response shapes:

```bash
jq '.data | keys' /tmp/result.json            # top-level structure
jq '.data[0]' /tmp/result.json                # first object shape
jq '.data.data[0]' /tmp/result.json           # nested first object
```

### Common Filters

Filter synthetics by service tag:

```jq
[.data.tests[] | select(any(.tags[]?; . == "service:SVC"))]
```

Filter synthetics by URL:

```jq
[.data.tests[] | select((.config.request.url // "") | test("PATTERN"; "i"))]
```

Filter APM stats by service:

```jq
[.data.data.attributes.services_stats[] | select(.service == "SVC")]
```

Get callers from dependency map:

```jq
to_entries | map(select(.value.calls | index("SVC"))) | map(.key)
```

## Domain Commands

### Logs

```bash
pup logs search --query="service:X status:error" --from="1h"
pup logs query --query="service:X" --from="4h" --to="now"
pup logs aggregate --query="service:X" --compute count --group-by status --from="1h"
```

### APM

All APM commands require `--env prod` (or target environment).
`pup apm flow-map` is unreliable — use `pup apm dependencies list` instead.

```bash
pup apm services list --env prod
pup apm services stats --start EPOCH --end EPOCH --env prod
pup apm entities list --start EPOCH --end EPOCH --env prod
pup apm dependencies list --env prod --start EPOCH --end EPOCH
```

### Monitors

```bash
pup monitors list [--name="pattern"] [--tags="service:X,team:Y"]
pup monitors search --query="tag:service:X"
pup monitors get ID
```

### Service Catalog

Requires per-service lookups. Does not support team filtering.

```bash
pup service-catalog list
pup service-catalog get SERVICE_NAME
```

### On-Call / Teams

Team names in user questions are often shorthand.
Use `pup monitors search --query="<name>"` to discover actual tag values first.

```bash
pup on-call teams list
pup on-call teams memberships list TEAM_ID
```

### Incidents

```bash
pup incidents list
pup incidents get INCIDENT_ID
```

### Synthetics

```bash
pup synthetics tests list
pup synthetics tests get TEST_ID
```

### RUM

```bash
pup rum apps list
pup rum sessions list --from="1h"
```

### Error Tracking

```bash
pup error-tracking issues search
pup error-tracking issues get ISSUE_ID
```

### Cost / Usage

```bash
pup cost projected
pup cost attribution --start-month=YYYY-MM --fields=team
pup usage summary --start="YYYY-MM-DD" --end="YYYY-MM-DD"
```

### Infrastructure

```bash
pup infrastructure hosts list [--filter="env:production"]
```

### Events

```bash
pup events list --from="1h"
pup events search --query="source:deploy"
```

### Dashboards

```bash
pup dashboards list
pup dashboards get DASH_ID
```

### Metrics

```bash
pup metrics search --query="<metric-name>"
pup metrics query --query="avg:<metric>{env:prod} by {host}" --from="1h"
pup metrics list
pup metrics tags --metric <metric-name>
```

### Security

```bash
pup security signals --query="status:critical" --from="1d"
pup security findings --from="1d"
pup audit-logs search --from="1d"
```

### CI/CD

```bash
pup cicd pipelines --from="1d"
pup cicd flaky-tests --from="7d"
```

### Network

```bash
pup network flows --from="1h"
pup network devices
```

### Cloud Integrations

```bash
pup cloud aws
pup cloud gcp
pup cloud azure
pup integrations list
```

### SLOs

```bash
pup slos list
pup slos status --id <slo-id>
```

### Downtime

```bash
pup downtime list
```
