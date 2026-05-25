# Agent DX Scoring Rubric

Score each axis 0-3. Sum for a total between 0-24.
Aligned with the AXI (Agent eXperience Interface) 10 principles —
see [axi-principles.md](axi-principles.md) for the full mapping.

## 1. Machine-Readable Output

Can an agent parse the CLI's output without heuristics?

| Score | Criteria |
|-------|----------|
| 0 | Human-only output (tables, color codes, prose). No structured format. |
| 1 | `--output json` exists but is incomplete or inconsistent across commands. |
| 2 | Consistent JSON output across all commands. Errors return structured JSON. Exit codes distinguish failure categories (usage, not-found, conflict, transient). |
| 3 | NDJSON streaming for paginated results. Structured output is default in non-TTY contexts. Cancellation produces a structured partial-progress signal (`{"interrupted": true, "completed": N, "total": M}`). |

### What to check

- Run `<cli> <command> --output json` or `-o json`
- Pipe output: `<cli> <command> | cat` — does it detect non-TTY and switch to JSON?
- Trigger an error: does the error come back as structured JSON?
- List a large collection: does it stream (NDJSON) or buffer the entire array?
- Check exit codes: does `<cli> get nonexistent` return a different exit code than `<cli> create duplicate`?
- Trigger a cancellation mid-stream: does the CLI emit a structured partial-progress signal or die silently?

## 2. Raw Payload Input

Can an agent send the full API payload without translation through bespoke flags?

| Score | Criteria |
|-------|----------|
| 0 | Only bespoke flags. No way to pass structured input. |
| 1 | `--json` or stdin JSON for some commands, but most require flags. |
| 2 | All mutating commands accept raw JSON that maps to the underlying API schema. |
| 3 | Raw payload is first-class alongside convenience flags. Agent uses API schema docs directly with zero translation. |

### What to check

- Can you pass `--json '{...}'` to create/update commands?
- Does the JSON structure match the underlying API schema (no translation layer)?
- Can you pipe JSON via stdin: `echo '{}' | <cli> create --json -`?
- Are convenience flags still available for human use cases?

## 3. Schema Introspection

Can an agent discover what the CLI accepts at runtime?

| Score | Criteria |
|-------|----------|
| 0 | Only `--help` text. No machine-readable schema. |
| 1 | `--help --json` or `describe` command for some surfaces. |
| 2 | Full schema introspection for all commands — params, types, required fields — as JSON. |
| 3 | Live runtime-resolved schemas from a discovery document. Includes scopes, enums, nested types. |

### What to check

- Run `<cli> schema <command>` or `<cli> <command> --describe`
- Is the output JSON with parameter names, types, required/optional, and descriptions?
- Does it reflect the current API version (not a stale snapshot)?
- Are nested types and enums fully described?

## 4. Context Window Discipline

Does the CLI help agents control response size?

| Score | Criteria |
|-------|----------|
| 0 | Returns full API responses with no way to limit fields or paginate. |
| 1 | `--fields` or field masks on some commands. Minimal field defaults (3-4 fields per list item, not 10+). |
| 2 | Field masks on all read commands. Pagination with `--page-size` or equivalent. Truncation hints on large fields with `--full` escape hatch. Definitive empty states (explicit "No items found" messages, not ambiguous empty output). |
| 3 | NDJSON streaming pagination. Pre-computed aggregates in responses (`total_count`, CI rollups, summaries) so the agent never needs a follow-up counting query. Guidance in context files on field mask usage. |

### What to check

- Run a list command: how large is the default response?
- Is `--fields "id,name"` or `--select` supported?
- Does pagination work? (`--page-size`, `--limit`, `--cursor`)
- For large responses: does it stream or buffer?
- Does a list response include a `total_count` field, or must the agent paginate to count?
- Are long text fields truncated with a hint and `--full` escape?
- Run a query that returns zero results: is the output an explicit "No items found" message or an ambiguous empty array?

## 5. Input Hardening

Does the CLI defend against agent hallucination patterns?

| Score | Criteria |
|-------|----------|
| 0 | No input validation beyond basic type checks. |
| 1 | Some validation, but misses agent-specific hallucination patterns. |
| 2 | Rejects control chars, path traversals (`../`), percent-encoded segments, embedded query params. Returns all validation errors at once (batch validation), not one at a time. |
| 3 | All of the above plus output path sandboxing, HTTP-layer encoding. Smart normalization of unambiguous inputs (case, whitespace) while rejecting ambiguous ones. Treats agent as untrusted operator. |

### What to check

- Pass `../../etc/passwd` as a resource ID — does it reject?
- Pass `fileId?fields=name` — does it reject the embedded query params?
- Pass `%2e%2e%2f` — does it detect double encoding?
- Pass strings with control characters (null bytes, newlines) — does it reject?
- Check source code for input sanitization functions
- Submit a command with 3 invalid flags at once — does it report all three errors or just the first?
- Pass `Production` where `production` is expected — does it normalize or reject? (Normalize is correct: unambiguous case difference.)

## 6. Safety Rails

Can agents validate before acting?

| Score | Criteria |
|-------|----------|
| 0 | No dry-run. No response sanitization. Interactive prompts block non-TTY callers. |
| 1 | `--dry-run` for some mutating commands. `--yes` flag on some confirmation-gated commands. |
| 2 | `--dry-run` for all mutating commands. Agent can validate without side effects. Non-interactive by default when piped. Headless auth via env vars, stdin, or credential files (no browser redirect). Pagers auto-disabled outside TTY. |
| 3 | Dry-run plus response sanitization against prompt injection in API data. Secret redaction in all output modes (stdout, stderr, `--verbose`, `--dry-run`). Process args avoid secrets (prefer stdin/env). Full request-response loop defended. |

### What to check

- Run `<cli> delete <resource> --dry-run` — does it validate without executing?
- Does dry-run show what would happen (the request that would be sent)?
- Are API responses filtered before display?
- Is there a confirmation prompt for destructive operations?
- Pipe a destructive command: `echo | <cli> delete <resource>` — does it hang waiting for a prompt, proceed with `--yes`, or reject?
- Run `<cli> login` without a TTY — does it offer env-var or stdin auth, or require a browser?
- Run `<cli> --verbose` with credentials configured — are tokens redacted in the output?

## 7. Agent Knowledge Packaging

Does the CLI ship agent-consumable knowledge?

| Score | Criteria |
|-------|----------|
| 0 | Only `--help` and a docs site. No agent-specific context files. |
| 1 | A `CONTEXT.md` or `AGENTS.md` with basic usage guidance. |
| 2 | Structured skill files (YAML frontmatter + Markdown) with per-command workflows. Error output includes next-step hints and recovery paths (concrete corrective commands, valid values). Help text is concise (5-10 lines per command, not 100). Content-first defaults: bare command in a project context shows live status data, not help text. |
| 3 | Comprehensive skill library with agent guardrails, versioned and following a standard. Mutation receipts include undo commands. help[] blocks after output with contextual next-step commands (specific to the result, not generic help). Context files are focused on non-inferable invariants only. |

### What to check

- Look for `CONTEXT.md`, `AGENTS.md`, `.claude/`, `.cursor/rules/` in the repo
- Are there skill files with YAML frontmatter?
- Do the files encode agent-specific invariants ("always use --dry-run", "always add --fields")?
- Are they versioned and maintained alongside the CLI?
- Trigger an error: does the output include a concrete corrective command, or just a message?
- Run a mutation: does the receipt include an undo command?
- Run `<cli>` with no subcommand in a repo context: does it show live data or just help text?
- Run `<cli> <command> --help`: is it concise (5-10 lines) or overwhelming (100+ lines)?
- After any command output: are there help[] blocks with contextual next-step commands?

## 8. Efficiency & Composition

Does the CLI minimize agent token consumption and compose well in shell pipelines?

| Score | Criteria |
|-------|----------|
| 0 | Full verbose JSON by default. No pipe-safe conventions. Commands require multiple round-trips for action+observation. |
| 1 | Minimal default fields on list commands (3-4 fields, not 10+). stdout/stderr separation (data on stdout, diagnostics on stderr). |
| 2 | Token-efficient output option (TOON or equivalent) alongside JSON. Combined action+observation commands (mutations return the affected resource inline, no follow-up GET needed). Shell-pipeable output (one record per line, filterable with grep/jq). |
| 3 | Ambient context via session hooks (state shown before invocation without agent querying). help[] blocks with contextual next-step commands appended after output. Full shell composition: pipes, process substitution, combined operations that eliminate round-trips. |

### What to check

- Run a list command: how many fields in the default output? (Target: 3-4, not 10+)
- Does the CLI offer a TOON or compact output mode alongside JSON? (`--output toon`)
- Run a mutation: does the response include the created/updated resource, or must you query again?
- Can you pipe output to grep, jq, or another CLI? (`<cli> list | jq '.[] | .id'`)
- Does the CLI install session hooks or show ambient state? (`<cli> shell-hook install`)
- After output, are there help[] blocks suggesting next commands?
- Can you chain commands in a pipeline? (`<cli> list --output ndjson | jq 'select(.status == "failed")' | <cli> delete --stdin`)

## Interpreting the Total

| Range | Rating | Description |
|-------|--------|-------------|
| 0-6 | Human-only | Built for humans. Agents struggle with parsing, hallucinate inputs, lack safety rails. |
| 7-12 | Agent-tolerant | Agents can use it but waste tokens, make avoidable errors, need heavy prompt engineering. |
| 13-18 | Agent-ready | Solid agent support. Structured I/O, input validation, some introspection. A few gaps remain. |
| 19-24 | Agent-first | Purpose-built for agents. Full introspection, hardening, safety rails, packaged knowledge, efficient composition. |

## Bonus: Multi-Surface Readiness

Not scored, but note whether the CLI exposes multiple agent surfaces:

- [ ] **MCP (stdio JSON-RPC)** — typed tool invocation, no shell escaping
- [ ] **Extension / plugin install** — agent treats CLI as native capability
- [ ] **Headless auth** — env vars for tokens/credentials, no browser redirect

### Anti-pattern: ToolSearch Overhead

AXI benchmarks show ToolSearch-based tool discovery reduces agent success by ~15 percentage points
compared to explicit tool listings.
Agents guess wrong tool names (e.g., `take_screenshot` vs `take_snapshot`),
causing context overflow and failures.
Prefer shipping a SKILL.md or CONTEXT.md with explicit command names
over relying on agents to discover tools dynamically.
