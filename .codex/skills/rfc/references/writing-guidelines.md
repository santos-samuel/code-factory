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
| Prioritized (must/should/nice) | Use MoSCoW or equivalent; not everything is "required" |
| Bounded scope | Explicit "Out of Scope" section with rationale for each exclusion |

### Design / Architecture

| Standard | Example |
|----------|---------|
| Diagrams for complex systems | Architecture, data flow, sequence diagrams (Mermaid preferred) |
| Interface contracts | API signatures, proto definitions, or schema examples |
| Failure mode analysis | "If component X fails, the system degrades by Y" with recovery path |

### Alternatives Considered

| Standard | Example |
|----------|---------|
| Minimum 2 alternatives | Even for "obvious" choices. Forces explicit reasoning. |
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

### Sharp Edges

Every RFC must include a "Sharp Edges" section or equivalent content distributed across relevant sections. This is what separates human-written RFCs from generated ones.

| Standard | Example |
|----------|---------|
| What breaks first | "The batch job will OOM above 500K records per run" |
| What is annoying | "Requires manual cert rotation every 90 days until we automate" |
| What we are punting | "Multi-region support is deferred to phase 2; single-region only for GA" |
| Strongest objection | "Critics will argue X. We accept this because Y." |

### Operational Impact

Required for design documents. Encouraged for problem statements that describe a system change.

| Standard | Example |
|----------|---------|
| What changes for oncall | "New alert: queue-depth > 10K for 5 minutes. Runbook: drain and restart consumer." |
| Cost and capacity estimates | "Estimated 3 additional c5.2xlarge instances at ~$400/month. Assumptions: 50K events/s steady state." |
| How we know it worked | "Success: P99 latency < 200ms for 7 consecutive days after GA. Measured via Datadog APM." |

## Writing Style

| Do | Don't |
|----|-------|
| Use active voice | "The service processes events" not "Events are processed by the service" |
| Be specific | "The batch job runs every 5 minutes" not "The batch job runs periodically" |
| Define jargon on first use | "The LSM (Log-Structured Merge) tree..." |
| Keep paragraphs under 5 sentences | Long paragraphs lose readers |
| Use tables for comparisons | Tables scan faster than prose for structured data |
| Lead with the conclusion | "We recommend approach A because X. Here's the analysis..." |
| Prefer nouns and verbs over adjectives | "The queue drops messages above 10K/s" not "The highly performant queue gracefully handles load" |
| Use exact numbers and examples | "Adds 12ms per request at P99" not "adds minimal overhead" |
| Use "We propose" sparingly | Only in the proposal section. Everywhere else, state facts and evidence. |
| Maintain a glossary | Define each term once. Use the same term throughout. |

## Banned Language

These words and phrases signal AI-generated text. Replace them with specific, measurable claims.

| Banned | Why | Replace with |
|--------|-----|-------------|
| robust | Means nothing without a metric | "Survives 3 AZ failures with <5s recovery" |
| seamless | Nothing is seamless; name the integration cost | "Requires a 2-line config change per service" |
| leverage / leveraging | Corporate filler | "use", "call", "extend" |
| best-in-class | Unverifiable superlative | Cite the benchmark or drop it |
| comprehensive | Vague scope claim | List what is covered and what is not |
| streamline | Hides complexity | "Removes 2 of 4 manual steps" |
| cutting-edge / state-of-the-art | Marketing language | Name the specific technique and its trade-offs |
| ensure / guarantee | Overpromises; nothing is guaranteed | "Reduces the probability of X by Y" or "Detects X within Y seconds" |
| scalable (without numbers) | Meaningless alone | "Scales to 100K req/s per pod" |
| world-class | Unverifiable | Delete or cite a specific ranking |
| innovative / novel | Self-congratulatory | Describe what it does differently and why that matters |
| optimize (without target) | Vague | "Reduce P99 latency from X to Y" |
| empower / enable | Corporate filler | Describe the concrete capability added |
| delve / delve into | AI tell; scholarly posturing | "covers", "examines", or just start the analysis |
| crucial / pivotal | Unearned emphasis | State the impact directly or drop the adjective |
| multifaceted / nuanced | Hedging dressed as depth | Name the specific facets or nuances |
| tapestry / intricate tapestry | Purple prose | Delete. Describe the parts directly. |
| stands as a testament | Vendor-page filler | State what the thing does and what it proves |

Also avoid:
- Motivational transitions: "This brings us to...", "It is worth noting that...", "Importantly, ..."
- Thesis restatements: Do not repeat the problem statement in every section.
- Hedging stacks: "It might potentially be possible to..." Pick a position.
- Rule-of-three-every-time: Two examples are fine; four are fine. Do not pad lists to three for rhythm.
- Trailing `-ing` clauses: "..., enabling teams to ship faster." End the sentence. Start a new one if needed.
- Closing pep talks: No "In conclusion, this approach will transform..." sections.

## Smell Tests

Run all three on any passage that feels off.

| Test | Question | Action |
|------|----------|--------|
| Landing-page test | Could this sentence appear verbatim on a vendor marketing page? | Rewrite with specifics. |
| Read-aloud test | Read the paragraph out loud. Does it make you cringe, or sound like ad copy? | Rewrite in plainer language. |
| Signature test | Would you defend every word as your own in a code review? | Remove or replace any word you would not. |

## Density Rule

One "crucial" in a 3-page RFC is fine. Five AI-slop words (banned list above) in two paragraphs means rewrite the whole passage, not just the individual words. The problem is the register, not the vocabulary.

## Typographic Rules

| Rule | Detail |
|------|--------|
| No numbered headings | Do not prefix section titles with numbers (`1. Overview`, `2. Design`). Use plain titles. Numbers in headings are only acceptable when the heading describes a sequence where order matters (e.g., `Step 1: Validate`, migration phases). |
| No em dashes | Do not use `---` or `—`. Rewrite the sentence, use a colon, semicolon, or split into two sentences. |
| No en dashes | Do not use `–` anywhere, including number ranges. Use `to` (e.g., "10 to 20 req/s", not "10–20 req/s"). |
| Straight quotes only | Use `"` and `'`. Do not use curly quotes like " " or ' '. |
| No mid-sentence styling | Do not use `**bold**` or `*italic*` inside sentences. Use headings, lists, or code formatting instead. |

## Document Length Guidelines

| RFC Type | Target Length | Section Detail |
|----------|-------------|----------------|
| Problem Statement | 3-4 pages (~1000-1200 words) | High-level, focused on the problem and justification |
| Design Document | 6-10 pages, with appendices | Detailed architecture, but move implementation details to appendices |

## Citation Format

Use inline markdown links for traceability. Keep link text short (2-5 words).

| Source type | Format | Example |
|-------------|--------|---------|
| Confluence page | `[short title](url)` | `[Event Pipeline RFC](https://confluence.example.com/pages/123456)` |
| Jira ticket | `[TICKET-ID](url)` | `[LOGS-4521](https://jira.example.com/browse/LOGS-4521)` |
| GitHub PR/issue | `[repo#number](url)` | `[logs-backend#1234](https://github.com/org/logs-backend/pull/1234)` |
| Web page | `[short title](url)` | `[Kafka partition limits](https://kafka.apache.org/documentation/#limits)` |
| Code path | inline code | `` `services/user/models/schema.go:45-80` `` |
| Dashboard/metric | `[dashboard name](url)` or parenthetical if no URL | `[prod-events APM](https://app.datadoghq.com/apm/...)` |

```markdown
The current system handles approximately 50K events/second ([prod-events APM dashboard](https://app.datadoghq.com/apm/service/prod-events)).

Previous attempts to optimize this path reduced latency by 40% ([Event Pipeline RFC, Section 4.2](https://confluence.example.com/pages/123456)).

The proposed schema follows the established pattern in the user-service (`services/user/models/schema.go:45-80`).
```

**Rule:** If a source has a URL, use a markdown link. Never write verbose parenthetical citations like `(Source: Confluence, "Page Title" page 123456)` when a link is available.

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
- [ ] No numbered headings (use `## Overview`, not `## 1. Overview`) unless heading describes an ordered sequence
- [ ] No em dashes (`---` or `—`) or en dashes (`–`) anywhere in the document
- [ ] Only straight quotes (`"` and `'`), no curly quotes
- [ ] No bold or italic formatting inside sentences
- [ ] No banned words from the Banned Language list
- [ ] No motivational transitions or thesis restatements
- [ ] No rule-of-three padding; no trailing `-ing` clauses; no closing pep talks
- [ ] Passages survive the landing-page, read-aloud, and signature tests
- [ ] Density rule respected: no more than one AI-slop word per two paragraphs
- [ ] Sharp edges are present: what breaks first, what is annoying, what we are punting
- [ ] Terminology is consistent throughout (same concept = same term)
- [ ] Cost and capacity estimates included, with stated assumptions
- [ ] Operational impact described: oncall changes, alerts, runbooks
