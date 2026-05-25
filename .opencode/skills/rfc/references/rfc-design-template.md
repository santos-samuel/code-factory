# RFC Design Template

*This template is for the design phase of the RFC process. It describes how the project will be built, operated, and maintained. The design phase should not begin until the problem statement has been reviewed and approved.*

*Design documents can get long. If the document exceeds six pages, move detailed information to appendices while keeping key elements in the first six pages.*

---

| Authors | |
| :---- | :---- |
| **Team** | |
| **Date** | |
| **Shepherd** | |
| **Reviewers** | |
| **Status** | Draft |

# Design

## Architectural Overview

*Brief overview of the system: modules, components, technologies, frameworks, and implementation language(s). Include a high-level system diagram.*

## Interfaces & APIs

*External interfaces (gRPC, REST, etc.) or APIs (for libraries). Cover what callers can achieve, not every call detail (details go in appendices). Include control flow and data flow diagrams where helpful.*

## Data Stores

*Temporary and permanent data stores. List major objects/tables/stores (full schema in appendices). For caches: sync strategy. For durable stores: data size and retention.*

## Deployment

*How the application/service will be deployed. Include node/pod types, counts, spare capacity, and growth projections.*

### Scalability

*How the application/service scales up and down.*

### Reliability

*How the system operates during:*
- *Dependency failures (other services, databases, cloud infrastructure, AZ outages)*
- *Internal failures (module failures, recovery, continued operation)*

## Security

*Security concerns and mitigations: hacking, DDoS, injection attacks, etc. Sensitive/PII data handling.*

## Compliance

*Applicable compliance specifications (PCI, HIPAA, SOX) and how they will be met.*

# Testing

*Testing beyond standard unit/CI/CD testing. Outline approach (individual tests in appendices).*

# Key Milestones

*Delivery phases from the user's perspective. Include functionality per milestone and rollout phases (staging → org2 → limited beta → GA).*

# Operations

## Failure Modes

*Known limitations and system boundaries: max throughput, storage, failure tolerance, scale limits. Design for graceful, gradual degradation.*

## Upgrades

*How the system is upgraded post-deployment. Prefer minimal/no interruption over downtime.*

## Monitoring

*Key metrics, logs, dashboards, and alerts for monitoring the application/service.*

## Operational Impact

*What changes for the oncall team. Include:*
- *New alerts and their thresholds*
- *New dashboards or modifications to existing ones*
- *Runbook steps for common failure scenarios*
- *Changes to oncall rotation or escalation paths*
- *SLO impact: new SLOs or changes to existing ones*

# Cost and Capacity

*Estimated resource requirements with stated assumptions. Include:*
- *Compute: instance types, counts, estimated monthly cost*
- *Storage: size, growth rate, retention*
- *Network: bandwidth, cross-region traffic*
- *State the load assumptions behind each estimate (e.g., "Assumes 50K events/s steady state, 200K peak").*

# Success Metrics

*Measurable metrics with baselines and targets. Include:*
- *Performance: "Reduce P99 from X to Y, measured via Z"*
- *Reliability: "99.95% availability over 30-day window"*
- *Adoption: "N teams onboarded within M weeks"*
- *How we know it worked: acceptance criteria and measurement method for each metric.*

# Sharp Edges

*What an honest author would warn you about. Include:*
- *What will break first under load or edge cases*
- *What is annoying about this design that we accept anyway*
- *What we are explicitly punting to a later phase*
- *The strongest objection a reviewer would raise, and why we proceed despite it*

# Open Questions

*Significant unresolved questions that can impact design or operations. Include:*
- *The question*
- *Why it is unresolved*
- *Who owns answering it*
- *Impact if the answer goes against our assumptions*

*Record answers here as they are resolved rather than removing questions.*

# Appendices

*Low-level details that distract from understanding the system as a whole: full API specs, detailed schemas, individual test plans, etc.*
