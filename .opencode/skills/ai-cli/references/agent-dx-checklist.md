# Agent DX Checklist

Quick pass/fail assessment for CLI agent-friendliness.
Based on AXI benchmark findings (985 runs, two domains) and production validation.

## Start Here: Top 5 (highest ROI)

1. JSON by default when output is piped or captured
2. No prompts in non-interactive mode (+ `--yes` flag)
3. Structured errors with recovery suggestions
4. Ship a focused `SKILL.md` with non-inferable invariants only
5. `--dry-run` on all mutating commands

## Full Checklist

### Output

- [ ] `--json` on every command
- [ ] stdout = data, stderr = everything else
- [ ] Minimal default responses (3-4 fields per list item), `--fields` for more
- [ ] Output schemas versioned and validated in CI
- [ ] NDJSON for streaming or large results

### Errors & Control Flow

- [ ] Semantic exit codes (not just 0/1) — distinguish usage, not-found, conflict, transient
- [ ] Structured error JSON with error code + `retryable` flag
- [ ] Recovery suggestions in every error (concrete commands, valid values — not "check your input")
- [ ] Return all validation errors at once (batch validation)
- [ ] Dedicated cancellation signal with partial-progress output

### Interaction

- [ ] Non-interactive by default when piped or captured
- [ ] `--yes` / `--force` / `--no-interactive` flags
- [ ] `--dry-run` with structured diff output
- [ ] Auth via stdin, env vars, or credential files (no browser redirect)
- [ ] No secrets in stdout, stderr, debug output, or process args

### Guidance & Context

- [ ] help[] blocks in output: copy-pasteable next-step commands specific to result context
- [ ] `undo_command` in mutation receipts
- [ ] Pre-computed fields (`total_count`, summaries, CI rollups)
- [ ] Truncation hints with `--full` escape hatch
- [ ] Content-first no-arg defaults where context is clear
- [ ] Definitive empty states (explicit "No items found", not ambiguous empty output)

### Input Handling

- [ ] Reject ambiguous, dangerous, or structurally invalid input
- [ ] Normalize only trivial, unambiguous input (case, whitespace)
- [ ] Never silently "fix" input when the correction could change intent
- [ ] Prefer idempotent operations where possible (`apply`/`sync`/`ensure` over `create`/`delete`)
- [ ] Accept raw JSON payloads matching the API schema for mutations
- [ ] Combined operations where natural (e.g., deploy returns status, create returns resource)

### Design

- [ ] Noun-verb command hierarchy
- [ ] Concise `--help` per command (5-10 lines with examples, not 100+)
- [ ] Focused `SKILL.md` or `CONTEXT.md` with non-inferable invariants only
- [ ] MCP surface (JSON-RPC over stdio) for direct agent integration

### Efficiency & Composition

- [ ] Minimal default fields on list commands (3-4 fields, `--fields` or `--full` for more)
- [ ] Token-efficient output option (TOON format or compact mode) alongside JSON
- [ ] Combined action+observation: mutations return the affected resource inline
- [ ] Shell-pipeable output: one record per line, stdout = data, stderr = diagnostics
- [ ] Ambient context: session hooks or state display before command execution
- [ ] help[] blocks: contextual next-step commands appended after output
- [ ] No ToolSearch dependency: ship explicit SKILL.md with command names

## The One Question Test

For any command, run it, look at the response, and ask:
**"What is the human caller implicitly expected to figure out here?"**

| If the answer is... | The fix is... |
|----------------------|---------------|
| "what format is this?" | Structured output default when piped |
| "how many total?" | `total_count` field |
| "what do I do next?" | Next-step hints |
| "which flag did I get wrong?" | Batch validation — all errors at once |
| "can I undo this?" | `undo_command` in mutation receipt |
| "should I retry?" | `retryable` flag on errors |
| "is it safe to proceed?" | `--yes` flag + non-interactive mode |
| "what state is the system in?" | Ambient context (session hooks showing state) |
| "can I pipe this?" | Shell-composable stdout (data only, one record per line) |

If the answer is "nothing — the tool already made that clear,"
the CLI is agent-friendly for that command.
