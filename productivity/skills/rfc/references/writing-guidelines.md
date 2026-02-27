# Staff Engineer RFC Writing Guidelines

Reference for maintaining staff-level quality in RFC documents.

## Core Principles

| Principle | Rule |
|-----------|------|
| Data over opinion | Every claim backed by a metric, benchmark, citation, or explicit assumption |
| Explicit trade-offs | Every decision has at least one alternative with clear rejection rationale |
| Measurable outcomes | Success metrics are specific numbers, not "improved" or "better" |
| Honest uncertainty | Unknown = Open Question. Never fill gaps with plausible guesses. |
| Audience awareness | Write for experienced engineers without specific domain knowledge |

## Quality Standards by Section

### Problem Statement / Overview

| Standard | Example |
|----------|---------|
| Quantify the pain | "P99 latency increased from 200ms to 1.2s over 6 months" not "latency is getting worse" |
| State the cost of inaction | "Without intervention, we project X by date Y based on trend Z" |
| Name the stakeholders | Specific teams and services, not "various teams" |

### Requirements

| Standard | Example |
|----------|---------|
| Testable criteria | "Must handle 10K req/s with P99 < 100ms" not "must be performant" |
| Prioritized (must/should/nice) | Use MoSCoW or equivalent — not everything is "required" |
| Bounded scope | Explicit "Out of Scope" section with rationale for each exclusion |

### Design / Architecture

| Standard | Example |
|----------|---------|
| Diagrams for complex systems | Architecture, data flow, sequence diagrams — Mermaid preferred |
| Interface contracts | API signatures, proto definitions, or schema examples |
| Failure mode analysis | "If component X fails, the system degrades by Y" with recovery path |

### Alternatives Considered

| Standard | Example |
|----------|---------|
| Minimum 2 alternatives | Even for "obvious" choices — forces explicit reasoning |
| Fair comparison | Present each alternative's strengths before its weaknesses |
| Concrete rejection rationale | "Rejected because X metric is 3x worse" not "didn't feel right" |

### Success Metrics

| Standard | Example |
|----------|---------|
| Baseline + target | "Reduce P99 from 1.2s to 200ms" not "improve latency" |
| Measurement method | "Measured via Datadog APM trace duration for endpoint /api/v2/query" |
| Timeline | "Achieve target within 30 days of GA rollout" |

### Risks

| Standard | Example |
|----------|---------|
| Likelihood + impact | "Medium likelihood, high impact" with justification |
| Mitigation strategy | Concrete actions, not "we'll monitor" |
| Acceptance criteria | When is the risk resolved vs. accepted? |

## Writing Style

| Do | Don't |
|----|-------|
| Use active voice | "The service processes events" not "Events are processed by the service" |
| Be specific | "The batch job runs every 5 minutes" not "The batch job runs periodically" |
| Define jargon on first use | "The LSM (Log-Structured Merge) tree..." |
| Keep paragraphs under 5 sentences | Long paragraphs lose readers |
| Use tables for comparisons | Tables scan faster than prose for structured data |
| Lead with the conclusion | "We recommend approach A because X. Here's the analysis..." |

## Document Length Guidelines

| RFC Type | Target Length | Section Detail |
|----------|-------------|----------------|
| Problem Statement | 3-4 pages (~1000-1200 words) | High-level, focused on the problem and justification |
| Design Document | 6-10 pages, with appendices | Detailed architecture, but move implementation details to appendices |

## Citation Format

Use inline citations for traceability:

```markdown
The current system handles approximately 50K events/second (Source: Datadog APM dashboard, prod-events service, 30-day average).

Previous attempts to optimize this path reduced latency by 40% (Source: RFC-2024-event-pipeline, Section 4.2).

The proposed schema follows the established pattern in the user-service (Source: `services/user/models/schema.go:45-80`).
```

## Self-Review Checklist

Before finalizing any RFC section, verify:

- [ ] Every quantitative claim has a source
- [ ] Every decision has documented alternatives
- [ ] Success metrics have baselines and targets
- [ ] Risks have mitigation strategies
- [ ] No section says "TBD" or "TODO" (use Open Questions instead)
- [ ] Diagrams are included where text alone would be unclear
- [ ] A reader unfamiliar with the domain can follow the argument
- [ ] The document stays within length guidelines
