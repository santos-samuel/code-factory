# `/do` Behavioral Evaluations

These scenarios test workflow application, not the presence of documentation phrases.

## RED Evidence

`baseline-report.json` records the audited pathological Codex session that motivated the rewrite.
It is retained as real-world RED evidence and is not re-run.

## GREEN Procedure

1. For each scenario, have the parent process read `evals.json` and generate the exact
   answer-hidden prompt with `check-evals.py --print-prompt <scenario-id>`.
2. Pipe that prompt into its own persisted read-only `codex exec` session. The agent receives the scenario,
   observed field names, skill/scenario digest evidence, but never assertion operations/values or
   evaluation file paths. It reads only the listed skill sources and may not delegate.
3. Capture the sessions into `behavioral-report.json` by passing one mapping per scenario to
   `collect-report.py --session <scenario-id>=<session-id>`. The collector derives execution mode,
   runtime totals, durations, hashes, outputs, and spawn counts from the raw rollouts.
4. Bundle the exact raw rollouts:

   ```bash
   python3 productivity/skills/do/evals/export-transcripts.py
   ```

5. Run:

   ```bash
   make check-do-evals
   ```

The checker recomputes every scenario verdict from observed fields, requires one unique session
and bundled rollout per scenario. A skill-source digest binds every prompt to `/do`, `/workspace`,
and the artifact contract; a definitions digest binds the report to the full scenario set; and a
per-scenario digest lets an unchanged scenario retain valid evidence when another scenario changes.
It verifies transcript hashes, the exact submitted answer-hidden prompt, digest evidence copied into
each structured final output, direct execution mode, duration, runtime token total, required
skill-read tool calls, output and observations, and absence of nested agents or reads of
answer-bearing evaluation artifacts. Validation never falls back to an editable report when local
Codex session files are unavailable.
It never trusts a stored `status: pass` field.

Use the skill grader or comparator to challenge ambiguous observations before recording them.
