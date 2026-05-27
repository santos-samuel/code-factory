# Persuasion Principles for Skill Design

Reference for making skills that agents reliably follow, especially discipline-enforcing skills that carry compliance costs.

## Why This Matters

Testing with 28,000 AI conversations showed persuasion techniques doubled compliance rates from 33% to 72% (Meincke et al., 2025). LLMs trained on human text respond to psychological principles similarly to humans encountering such language.

## The Five Useful Principles

### 1. Authority

Imperative framing with non-negotiable requirements.

| Technique | Example |
|-----------|---------|
| Bright-line rules | "NEVER skip validation. No exceptions." |
| Imperative commands | "YOU MUST run tests before committing." |
| Elimination of ambiguity | "Delete means delete. Not 'save for reference.'" |

**Best for:** Discipline-enforcing skills, safety-critical practices, validation gates.

**Why it works:** Eliminates decision fatigue. Agents don't need to evaluate whether to comply — the rule is absolute.

### 2. Commitment

Force explicit choices and track accountability.

| Technique | Example |
|-----------|---------|
| Announce lines | `Announce: "I'm using TDD to implement this feature."` |
| Checklists | `- [ ] Tests written before implementation` |
| Action-forcing choices | "Choose A, B, or C — explain your choice." |

**Best for:** Multi-step processes, workflows where agents might skip steps.

**Why it works:** Public commitment creates consistency pressure. Once announced, agents resist contradicting their stated approach.

### 3. Scarcity

Time-bound requirements and sequential dependencies.

| Technique | Example |
|-----------|---------|
| Temporal urgency | "Immediately after completing Step 2, run validation." |
| Sequential gates | "Do NOT proceed to Step 3 until Step 2 passes." |
| Window language | "Before committing, verify all checks pass." |

**Best for:** Verification tasks, preventing procrastination on critical steps.

**Why it works:** Creates urgency without artificial deadlines. "Immediately after" framing prevents agents from deferring validation.

### 4. Social Proof

Establish behavioral norms through universal language.

| Technique | Example |
|-----------|---------|
| Universal language | "Every skill follows this structure." |
| Failure documentation | "Common mistake: skipping the announce line." |
| Norm establishment | "All descriptions start with 'Use when'." |

**Best for:** Convention enforcement, establishing patterns across a codebase.

**Why it works:** Agents align with perceived norms. Documenting what "everyone does" creates pressure to conform.

### 5. Unity

Collaborative language reflecting shared identity and goals.

| Technique | Example |
|-----------|---------|
| Shared identity | "As agents working in this codebase, we follow..." |
| Common goals | "This ensures consistency for all future sessions." |
| In-group language | "Our convention is kebab-case for all skill names." |

**Best for:** Team standards, non-hierarchical practices, collaborative workflows.

## Principles to Avoid

| Principle | Why to Avoid |
|-----------|-------------|
| **Reciprocity** | Rarely needed in agent context. Can feel manipulative. |
| **Liking** | Conflicts with honest feedback. Creates sycophancy. Never use for compliance. |

## Application by Skill Type

| Skill Type | Primary | Secondary | Avoid |
|------------|---------|-----------|-------|
| Discipline (TDD, verification) | Authority + Commitment | Social Proof | Liking, Reciprocity |
| Workflow (commit, PR) | Commitment + Social Proof | Moderate Authority | Heavy authority |
| Reference (API docs) | Clarity only | — | All persuasion |
| Collaboration (code review) | Unity + Commitment | — | Authority, Liking |

## Bulletproofing Against Rationalization

Agents are intelligent and find loopholes under pressure. Counter this systematically:

### Close Every Loophole Explicitly

```markdown
# WEAK: Leaves room for interpretation
Write code before test? Delete it.

# STRONG: Closes specific workarounds
Write code before test? Delete it. Start over.

**No exceptions:**
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete
```

### Build Rationalization Tables

Capture every excuse agents use during testing and add explicit counters:

```markdown
| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests-after prove "what does this do?" not "what should this do?" |
| "This is different because..." | If the rule has exceptions, the rule doesn't exist. |
```

### Create Red Flag Lists

Self-check triggers that signal rationalization in progress:

```markdown
## Red Flags — STOP and Reconsider
- "This is just a small change"
- "I can skip this step because..."
- "The spirit of the rule is..."
- "This doesn't really apply here"
```

### Address "Spirit vs Letter" Arguments

Add the foundational principle early:

> **Violating the letter of the rules IS violating the spirit of the rules.**

This cuts off an entire class of rationalization.

## Ethical Guardrails

| Legitimate | Illegitimate |
|------------|-------------|
| Ensuring critical practices (testing, validation) | Personal manipulation |
| Creating effective documentation | Artificial urgency for urgency's sake |
| Preventing predictable failures | Guilt-based compliance |

**Test:** Would this technique serve users' genuine interests if fully understood?

## Sources

- Cialdini, R. (2021). *Influence: The Psychology of Persuasion* (revised edition)
- Meincke, L. et al. (2025). AI persuasion study across 28,000 conversations
- [superpowers: persuasion-principles](https://github.com/obra/superpowers/blob/main/skills/writing-skills/persuasion-principles.md)
