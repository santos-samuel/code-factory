# {{TITLE}}

> [!NOTE]
> **Owner:** {{OWNER}}
> **Last Updated:** {{DATE}}
> **Audience:** SRE, On-call Engineers

## Overview

{{Brief description of what this runbook addresses. What problem does it solve? When should someone use this runbook?}}

## Prerequisites

Before starting, ensure you have:

- [ ] Access to {{SYSTEM_OR_SERVICE}}
- [ ] Permissions to {{REQUIRED_PERMISSION}}
- [ ] {{TOOL_OR_CLI}} installed and configured

## Detection

### Symptoms

How do you know this issue is occurring?

- Alert: `{{ALERT_NAME}}` firing in {{MONITORING_SYSTEM}}
- Error message: `{{ERROR_MESSAGE}}`
- User reports: {{DESCRIPTION_OF_USER_IMPACT}}

### Metrics to Check

| Metric | Location | Healthy Range |
|--------|----------|---------------|
| {{METRIC_NAME}} | {{DASHBOARD_LINK}} | {{EXPECTED_VALUES}} |

## Response Steps

### Step 1: Assess Impact

```bash
# Check current state
{{COMMAND_TO_CHECK_STATE}}
```

Expected output: {{DESCRIPTION_OF_EXPECTED_OUTPUT}}

### Step 2: Mitigate

```bash
# Apply mitigation
{{MITIGATION_COMMAND}}
```

> [!WARNING]
> {{IMPORTANT_CONSIDERATION_OR_RISK}}

### Step 3: Fix Root Cause

{{Detailed steps to resolve the underlying issue}}

### Step 4: Verify Resolution

```bash
# Confirm the fix
{{VERIFICATION_COMMAND}}
```

Expected output: {{SUCCESS_INDICATORS}}

## Rollback

If the fix causes additional issues:

```bash
# Rollback procedure
{{ROLLBACK_COMMAND}}
```

> [!CAUTION]
> {{DATA_LOSS_OR_IMPACT_WARNING}}

## Verification

The issue is resolved when:

- [ ] Alert `{{ALERT_NAME}}` has cleared
- [ ] Metric `{{METRIC_NAME}}` is within normal range
- [ ] No new error logs appearing
- [ ] User-reported functionality restored

## Post-Incident

After resolving the issue:

1. Document timeline in incident channel
2. Update this runbook if steps changed
3. Create follow-up ticket for prevention: {{TICKET_TEMPLATE}}

## References

- Related runbook: [{{RELATED_RUNBOOK}}](./{{RELATED_RUNBOOK}}.md)
- Dashboard: {{DASHBOARD_URL}}
- Service docs: {{SERVICE_DOCS_URL}}
- Escalation: {{ESCALATION_CONTACT}}
