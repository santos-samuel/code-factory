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

# Success Metrics

*Measurable metrics: latency, QPS, cost reduction, time savings, adoption rate, etc.*

# Open Questions

*Significant unresolved questions that can impact design or operations. Record answers here as they are resolved rather than removing questions.*

# Appendices

*Low-level details that distract from understanding the system as a whole: full API specs, detailed schemas, individual test plans, etc.*
