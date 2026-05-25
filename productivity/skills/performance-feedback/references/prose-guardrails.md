# Prose Guardrails for Performance Feedback

Reference for every paragraph of narrative prose in a performance review.
The signature test matters more here than anywhere else. The reader (the reviewee, calibration committee, HR) should hear the manager's voice, not an AI template.

## Hard Rules

| Rule | Why |
|------|-----|
| Every claim has a date and a link (PR, ticket, doc) or a direct quote from a 1:1 note. | Unsourced prose reads as AI-generated padding. |
| No em dashes (`—` or `---`) or en dashes (`–`). | Use periods, colons, or `to` in ranges. |
| Straight quotes only (`"` and `'`). | Curly quotes signal auto-formatted text. |
| No mid-sentence `**bold**` or `*italic*`. | Use structure, not typography, for emphasis. |

## Banned Vocabulary

Performance feedback is where AI-slop hides best. Replace every instance with a specific behavior, outcome, or metric.

| Banned | Replace with |
|--------|-------------|
| delve, delve into | "digs into X", or state the finding directly |
| crucial, pivotal | Describe the impact directly |
| robust | "handled X failure mode", "recovered in Y seconds" |
| seamless, seamlessly | Name the integration or handoff |
| leverage, leveraging | "used", "extended", "applied" |
| tapestry, intricate tapestry | Delete |
| multifaceted, nuanced | Name the facets or distinctions |
| comprehensive | List what was covered |
| streamline, streamlined | "cut N manual steps", "reduced cycle time from X to Y" |
| empower, enable, enabling | Describe the capability |
| best-in-class, cutting-edge, world-class | Cite the comparison or drop it |
| stands as a testament | Delete |
| strong communicator, excellent collaborator | Give a specific example |
| team player, go-getter, self-starter | Describe the behavior |
| exceeded expectations (without evidence) | Quote the evidence |
| impressive, outstanding, exceptional (as standalone) | Describe what made it so |

## Structural Rules

- No rule-of-three padding. If you have two strong examples, stop at two.
- No trailing `-ing` clauses. Not "shipped the auth refactor, demonstrating leadership." End the sentence, start a new one.
- No motivational transitions ("It is important to note that...", "Moving forward...").
- No thesis restatements in each dimension.
- No closing pep talks ("We are excited to see what X does next...").

## Smell Tests

Run every paragraph through all three before saving.

| Test | Question | Action |
|------|----------|--------|
| Landing-page | Could this paragraph appear on a careers-page testimonial? | Rewrite with specifics, dates, and metrics. |
| Read-aloud | Read the paragraph to yourself out loud. Does it sound like you in a calibration meeting? | If it sounds like an HR template, rewrite. |
| Signature | Would you defend every word if the reviewee asked "what do you mean by this?" | Replace any word you would not. |

## Density Rule

One "robust" in a 2-page review is fine if backed by a specific example.
Five AI-slop words across two paragraphs means rewrite the whole passage, not just the individual words.
The register is wrong, not the vocabulary.

## Situation / Behavior / Impact

For every specific example, use the pattern:

- **Situation**: date, context, stakes. "In Q2, during the DATA-4521 migration, the auth refactor was blocking three teams."
- **Behavior**: what the person did, in active voice. "She proposed splitting the migration into four PRs, owned the rollout, and debugged the staging regression on 2026-03-14."
- **Impact**: measurable outcome. "The rollout completed two weeks ahead of schedule with zero production incidents."

If you cannot fill all three slots with specifics, the example is not ready. Ask the user or drop it.

## Quoting From 1:1 Notes

When quoting directly from a 1:1 log, include the date and use straight double quotes.

> On 2026-02-12, she raised: "I want to lead the next migration end-to-end." By 2026-04-02 she had shipped DATA-4521 as primary driver.

This grounds the narrative in real conversation and resists the AI-template drift.

## Common Failure Modes

| Symptom | Fix |
|---------|-----|
| Every dimension has three bullets of the same length. | Let the evidence determine count. Two is fine. One is fine if that is what you have. |
| "Strong collaborator" with no example. | Name the collaboration: who, when, what they did, what shipped. |
| "Areas for growth" reads like coaching-manual filler. | Tie each growth area to a specific incident or 1:1 theme with a date. |
| The review is all praise. | Re-read Areas for Growth. If it sounds vague or aspirational, rewrite with a specific incident. |
| The tone shifts between sections. | One human voice. Not "she demonstrated X" in one section and "Sarah shipped Y" in the next. Pick one and hold it. |

## Final Check

Before saving, ask yourself: if the reviewee read this over your shoulder and said "show me where that came from", could you point to a PR, ticket, 1:1 note, or meeting note for every claim?
If not, remove the claim.
