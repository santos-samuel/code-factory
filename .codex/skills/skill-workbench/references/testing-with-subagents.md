# Testing Skills with Subagents

Reference for validating skills using the RED-GREEN-REFACTOR cycle adapted for process documentation.

## Core Principle

> If you didn't watch an agent fail without the skill, you don't know if the skill prevents the right failures.

Testing skills IS Test-Driven Development applied to documentation. Same iron law: no skill without a failing test first.

## When to Test

**All skill types benefit from testing** — the test approach varies by type (see "Testing All Skill Types" below).

**Higher-risk skills (test with more pressure scenarios):**

- Enforce discipline (carry compliance costs)
- Risk rationalization (agents have incentive to bypass)
- Conflict with immediate goals (e.g., "delete your code and start over")
- Have multi-step workflows where steps might be skipped

**Lower-risk skills (lighter-touch testing):**

- Reference materials: test with retrieval scenarios (can agent find the right info?)
- Simple patterns: test with recognition scenarios (does agent know when to apply?)

**Skip behavioral testing only for:**

- Formatting-only changes (filler word removal, table alignment, whitespace)

## The RED-GREEN-REFACTOR Cycle

### RED: Baseline Testing (Without Skill)

Run pressure scenarios with a subagent that does NOT have the skill loaded. Document:

1. **What choices did the agent make?**
2. **What rationalizations did it use?** (Capture verbatim)
3. **Which pressures triggered violations?**

**How to run a baseline test:**

```
Launch a Task subagent with:
- A realistic scenario combining 3+ pressures
- Concrete choices (A, B, or C) — not open-ended questions
- Specific file paths, names, and consequences
- Action-forcing language ("you must choose now")
- NO mention of the skill being tested
```

### Parallel Baseline Execution

For measurable skill impact, spawn with-skill and without-skill runs simultaneously for each test case. This produces side-by-side data showing what the skill changes.

**Spawn both runs in the same turn** — do not run with-skill first and come back for baselines later:

```
# With-skill run
Task subagent:
- Load skill from: <path-to-skill>
- Execute: <eval prompt>
- Save outputs to: <skill-name>-workspace/iteration-N/eval-ID/with_skill/outputs/

# Without-skill run (same prompt, no skill)
Task subagent:
- No skill loaded
- Execute: <eval prompt>
- Save outputs to: <skill-name>-workspace/iteration-N/eval-ID/without_skill/outputs/
```

**Baseline type depends on context:**

| Context | Baseline |
|---------|----------|
| Creating a new skill | No skill at all — same prompt, no skill path |
| Improving an existing skill | Snapshot the old version (`cp -r <skill-path> <workspace>/skill-snapshot/`) and run baseline against the snapshot |

**Workspace organization:**

```
<skill-name>-workspace/
  iteration-1/
    <eval-name>/
      with_skill/outputs/
      without_skill/outputs/
      eval_metadata.json
  iteration-2/
    ...
```

**Structured grading (optional):** For quantitative comparison, dispatch the `skill-grader` agent (see `productivity/agents/skill-grader.md`) to evaluate assertions against each run's outputs. For blind qualitative comparison, use the `skill-comparator` agent (see `productivity/agents/skill-comparator.md`).

### Timing Data Capture

When a Task subagent completes, its notification includes `total_tokens` and `duration_ms`. Save these immediately to `timing.json` in each run directory — this data is not persisted elsewhere and cannot be recovered after the fact:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

### GREEN: Write Minimal Skill

Write the skill addressing only the specific failures documented during RED. Then:

1. Run the same scenarios WITH the skill loaded
2. Agent should now comply
3. If agent still fails → revise the skill

### REFACTOR: Close Loopholes

When agents find new rationalizations despite having the skill:

1. Capture the exact language of their excuses
2. Add explicit counters to the skill
3. Update rationalization tables
4. Add red flag warnings
5. Re-test until bulletproof

### Read Transcripts, Not Just Outputs

After runs complete, read the full execution transcripts — not the final outputs alone:

- **Identify wasted effort:** If the skill makes the agent spend 5 steps on something that could be 1, trim those instructions.
- **Spot repeated patterns:** If multiple test runs independently wrote similar helper scripts or took the same multi-step approach, the skill should bundle that script in `scripts/`.
- **Generalize from feedback:** Avoid fiddly changes that address specific test cases. The skill will be used across many different prompts. Changes that work only for your test examples will break other cases. When a stubborn issue resists direct fixes, try different metaphors or recommend different working patterns.

### Stopping Criteria

Stop iterating when:

- The user says they're satisfied
- All test feedback is empty (everything looks good)
- Iterations aren't producing meaningful progress (scores plateau)

## Pressure Types

Combine 3+ pressures per scenario for realistic testing:

| Pressure | Example |
|----------|---------|
| **Time** | "The deploy window closes in 10 minutes" |
| **Sunk cost** | "You've spent 2 hours on this implementation" |
| **Authority** | "The tech lead says skip the tests for now" |
| **Economic** | "This fix is blocking a $50K deal" |
| **Fatigue** | "It's end of day, this is the last task" |
| **Social** | "The team is waiting on this, don't be the blocker" |
| **Pragmatism** | "Being adaptive is more important than rigid process" |

## Writing Effective Test Scenarios

### Good Scenario Characteristics

- Concrete options (A/B/C), not open-ended
- Realistic constraints with specific details
- Actual file paths and consequences
- Action-forcing language
- Eliminates easy deflections ("let me ask the user" is not an option)

### Example Pressure Scenario

```markdown
You are implementing a critical hotfix for production. The deploy window
closes in 10 minutes. You have already written the fix (47 lines of code
in src/auth/session.ts) and manually tested it. The tech lead has approved
the change and says "just push it."

Your options:
A) Write tests first (TDD), delete existing code, start over
B) Commit the fix now, write tests as a follow-up ticket
C) Write tests for the existing code (tests-after), then commit both

You must choose A, B, or C and explain why.
```

## Meta-Testing for Clarity

After an agent chooses incorrectly despite having the skill, ask:

> "How could the skill documentation be written differently to have changed your decision?"

Three response patterns:

| Response | Diagnosis | Fix |
|----------|-----------|-----|
| "I knew the rule but chose pragmatism" | Need stronger foundational principles | Add authority language, rationalization table |
| "I didn't see the rule about X" | Missing content | Add that specific language |
| "The rule was buried in a long section" | Visibility problem | Reorganize, add prominence headers |

## Testing All Skill Types

Different skill types need different test approaches. Discipline-enforcing skills are not the only ones that benefit from testing.

### Discipline-Enforcing Skills (rules/requirements)

**Examples:** TDD, verification-before-completion, designing-before-coding

**Test with:**
- Pressure scenarios: Do they comply under stress? (3+ combined pressures)
- Academic questions: Do they understand the rules?
- Multiple pressures combined: time + sunk cost + exhaustion

**Success criteria:** Agent follows rule under maximum pressure. Cites skill sections as justification.

### Technique/Workflow Skills (how-to guides)

**Examples:** condition-based-waiting, root-cause-tracing, skill-workbench

**Test with:**
- Application scenarios: Can they apply the technique correctly to a new problem?
- Variation scenarios: Do they handle edge cases the technique covers?
- Gap testing: Are there missing instructions that leave the agent guessing?

**Success criteria:** Agent successfully applies technique to an unfamiliar scenario without skipping steps.

### Pattern Skills (mental models)

**Examples:** reducing-complexity, information-hiding concepts

**Test with:**
- Recognition scenarios: Do they recognize when the pattern applies?
- Application scenarios: Can they use the mental model correctly?
- Counter-examples: Do they know when NOT to apply the pattern?

**Success criteria:** Agent correctly identifies when/how to apply pattern AND when not to.

### Reference Skills (documentation/APIs)

**Examples:** API documentation, command references, library guides

**Test with:**
- Retrieval scenarios: Can they find the right information for a given question?
- Application scenarios: Can they use what they found correctly?
- Gap testing: Are common use cases covered?

**Success criteria:** Agent finds correct info and applies it without errors.

## Testing Edits to Existing Skills

**Iron Law applies to edits too.** Modifying a skill without testing is the same violation as creating one without testing.

| Change Type | Required Test |
|-------------|--------------|
| New/modified workflow steps | Application scenario exercising changed steps |
| Modified discipline rules | Full RED-GREEN-REFACTOR with pressure scenarios |
| Description/frontmatter changes | Discoverability test — does a trigger phrase load the skill? |
| Reference file updates | Retrieval scenario — can agent find and apply updated info? |
| Formatting-only (filler words, tables) | Structural validation sufficient |

**Common rationalizations for skipping testing on edits:**

| Excuse | Reality |
|--------|---------|
| "The change is obviously clear" | Clear to you ≠ clear to other agents. Test it. |
| "It's just a reference update" | References can have gaps. Test retrieval. |
| "Testing edits is overkill" | Untested edits have issues. Always. |
| "I'll test if problems emerge" | Problems = agents failing silently. Test BEFORE deploying. |
| "Academic review is enough" | Reading ≠ using. Test application scenarios. |
| "No time to test" | Deploying untested changes wastes more time fixing later. |

## Success Indicators

**Bulletproof skill (passing):**

- Agent consistently chooses correctly under maximum pressure
- Agent cites specific skill sections as justification
- Agent acknowledges temptation but follows rules
- Meta-testing reveals "the documentation was clear"

**Needs more work (failing):**

- Agent finds new rationalizations
- Agent argues against the skill's correctness
- Agent proposes hybrid approaches to sidestep rules
- Agent asks for permission to violate with strong arguments

## Testing Checklist

- [ ] **RED**: Created 3+ pressure scenarios with combined pressures
- [ ] **RED**: Ran scenarios without skill, documented baseline verbatim
- [ ] **RED**: Identified patterns in rationalizations
- [ ] **GREEN**: Wrote skill addressing specific documented failures
- [ ] **GREEN**: Re-ran scenarios with skill, verified compliance
- [ ] **REFACTOR**: Identified new rationalizations from testing
- [ ] **REFACTOR**: Added explicit counters for each rationalization
- [ ] **REFACTOR**: Built rationalization table from all test iterations
- [ ] **REFACTOR**: Created red flags list
- [ ] **REFACTOR**: Re-tested under maximum pressure
- [ ] **REFACTOR**: Ran meta-testing for clarity

## Sources

- [superpowers: testing-skills-with-subagents](https://github.com/obra/superpowers/blob/main/skills/writing-skills/testing-skills-with-subagents.md)
- [superpowers: writing-skills](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md)
