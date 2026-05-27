# ADR-{{NUMBER}}: {{TITLE}}

| Field | Value |
|-------|-------|
| **Status** | {{STATUS}} (Proposed / Accepted / Deprecated / Superseded) |
| **Date** | {{DATE}} |
| **Author(s)** | {{AUTHORS}} |
| **Reviewers** | {{REVIEWERS}} |
| **Supersedes** | {{ADR_NUMBER_OR_NONE}} |
| **Superseded by** | {{ADR_NUMBER_OR_NONE}} |

## Context

{{What is the issue that we're seeing that is motivating this decision or change? What forces are at play? Include technical, business, and organizational factors. Be specific about the current state and why it's problematic.}}

### Current State

{{Describe how things work today.}}

### Problem

{{What specific problem(s) need to be solved?}}

### Constraints

- {{CONSTRAINT_1}}
- {{CONSTRAINT_2}}
- {{CONSTRAINT_3}}

## Decision Drivers

What factors are most important in making this decision?

- **{{DRIVER_1}}** — {{WHY_IT_MATTERS}}
- **{{DRIVER_2}}** — {{WHY_IT_MATTERS}}
- **{{DRIVER_3}}** — {{WHY_IT_MATTERS}}

## Options Considered

### Option 1: {{OPTION_1_NAME}}

{{Description of this approach.}}

**Pros:**

- {{PRO_1}}
- {{PRO_2}}

**Cons:**

- {{CON_1}}
- {{CON_2}}

**Effort:** {{LOW_MEDIUM_HIGH}}

### Option 2: {{OPTION_2_NAME}}

{{Description of this approach.}}

**Pros:**

- {{PRO_1}}
- {{PRO_2}}

**Cons:**

- {{CON_1}}
- {{CON_2}}

**Effort:** {{LOW_MEDIUM_HIGH}}

### Option 3: {{OPTION_3_NAME}}

{{Description of this approach.}}

**Pros:**

- {{PRO_1}}
- {{PRO_2}}

**Cons:**

- {{CON_1}}
- {{CON_2}}

**Effort:** {{LOW_MEDIUM_HIGH}}

## Decision

We will use **Option {{N}}: {{OPTION_NAME}}**.

### Rationale

{{Explain why this option was chosen over the others. Reference the decision drivers and explain how this option best satisfies them.}}

## Consequences

### Positive

- {{POSITIVE_CONSEQUENCE_1}}
- {{POSITIVE_CONSEQUENCE_2}}

### Negative

- {{NEGATIVE_CONSEQUENCE_1}}
- {{NEGATIVE_CONSEQUENCE_2}}

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| {{RISK_1}} | {{LOW_MED_HIGH}} | {{LOW_MED_HIGH}} | {{MITIGATION}} |
| {{RISK_2}} | {{LOW_MED_HIGH}} | {{LOW_MED_HIGH}} | {{MITIGATION}} |

## Implementation

### High-Level Plan

1. {{IMPLEMENTATION_STEP_1}}
2. {{IMPLEMENTATION_STEP_2}}
3. {{IMPLEMENTATION_STEP_3}}

### Migration Path

{{If this changes existing behavior, how will we migrate? What's the rollback plan?}}

### Success Metrics

How will we know this decision was successful?

- {{METRIC_1}}
- {{METRIC_2}}

## References

- Related ADRs: [ADR-{{RELATED_NUMBER}}](./adr-{{RELATED_NUMBER}}.md)
- RFC/Design Doc: {{LINK_IF_EXISTS}}
- Discussion: {{SLACK_OR_ISSUE_LINK}}

## Changelog

| Date | Author | Change |
|------|--------|--------|
| {{DATE}} | {{AUTHOR}} | Initial proposal |
