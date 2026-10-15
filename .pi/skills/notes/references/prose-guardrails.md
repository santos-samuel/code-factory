# Prose Guardrails for Notes

Reference for any Obsidian note that contains narrative prose rather than bullet logs.
Applies to: overview files, career plans, promotion proposals, misc notes, and the "Overview" / "Key Traits" sections of People files.

The goal is honest, specific prose that a skeptical senior engineer would recognize as human-written.

## Banned Vocabulary

These words signal AI-generated text or vendor-page fluff. Replace with the specific metric, tool, or behavior.

| Banned | Replace with |
|--------|-------------|
| delve, delve into | "covers", "examines", or start the analysis |
| crucial, pivotal | State the impact directly |
| robust | "survives X failure in Y seconds" |
| seamless, seamlessly | Name the integration cost |
| leverage, leveraging | "use", "call", "extend" |
| tapestry, intricate tapestry | Delete. Describe the parts. |
| multifaceted, nuanced | Name the specific facets |
| comprehensive | List what is in scope and what is not |
| streamline | "removes N of M manual steps" |
| empower, enable | Describe the concrete capability |
| best-in-class, cutting-edge, world-class | Cite a benchmark or drop it |
| stands as a testament | Delete the phrase. State what it proves. |

## Typographic Rules

| Rule | Detail |
|------|--------|
| No em dashes | Do not use `---` or `—`. Use a period, colon, or split the sentence. |
| No en dashes | Do not use `–` anywhere, including number ranges. Use `to` (e.g., "10 to 20"). |
| Straight quotes only | Use `"` and `'`. No curly quotes. |
| No mid-sentence styling | No `**bold**` or `*italic*` inside sentences. Use headings or lists. |

## Structural Rules

- No rule-of-three padding. Two examples are fine; four are fine.
- No trailing `-ing` clauses ("..., enabling teams to ship faster"). End the sentence.
- No motivational transitions ("It is important to note that...", "This brings us to...").
- No thesis restatements or closing pep talks.

## Smell Tests

Run all three on any prose paragraph before saving.

| Test | Question | Action |
|------|----------|--------|
| Landing-page | Could this sentence appear on a vendor marketing page? | Rewrite with specifics. |
| Read-aloud | Read it out loud. Does it make you cringe, or sound like ad copy? | Rewrite in plainer language. |
| Signature | Would you defend every word in a 1:1 with this person? | Replace any word you would not. |

## Density Rule

One AI-slop word in a 1-paragraph career-plan entry is fine.
Five AI-slop words across two paragraphs means rewrite the whole passage, not just the individual words.
The problem is register, not vocabulary.

## When This Applies

| Section | Apply guardrails? |
|---------|-------------------|
| Bullet logs in 1:1s, achievements, daily entries | Optional — bullets are short by nature. |
| Career Plan narrative (goals, milestones, rationale) | Yes. |
| Promotion Proposal narrative (impact stories, justification) | Yes. Signature test matters most here. |
| People file Overview and Key Traits prose | Yes. |
| Meeting-note summaries longer than a single bullet | Yes. |
| Misc notes with paragraph-length content | Yes. |
