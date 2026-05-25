# AXI Principles Mapping

Maps AXI's 10 principles to the AI-CLI skill's 8 scoring axes.
Reference: AXI (Agent eXperience Interface) framework.

## Principle → Axis Mapping

### Efficiency (Principles 1-3)

| # | AXI Principle | Skill Axis | Notes |
|---|---------------|------------|-------|
| 1 | Token-efficient output (TOON format) | 8. Efficiency & Composition | ~40% token savings over JSON |
| 2 | Minimal default schemas | 4. Context Window Discipline + 8. Efficiency & Composition | 3-4 fields per list item, `--full` escape hatch |
| 3 | Content truncation | 4. Context Window Discipline | Truncation hints with size + `--full` |

### Robustness (Principles 4-6)

| # | AXI Principle | Skill Axis | Notes |
|---|---------------|------------|-------|
| 4 | Pre-computed aggregates | 4. Context Window Discipline | `total_count`, rollups, summaries |
| 5 | Definitive empty states | 4. Context Window Discipline | Explicit "0 results", not ambiguous empty output |
| 6 | Structured errors & exit codes | 1. Machine-Readable Output + 5. Input Hardening | Idempotent mutations, no interactive prompts |

### Discoverability (Principles 7-9)

| # | AXI Principle | Skill Axis | Notes |
|---|---------------|------------|-------|
| 7 | Ambient context | 8. Efficiency & Composition | Session hooks showing state before invocation |
| 8 | Content first | 7. Agent Knowledge Packaging | Bare command shows live data, not help text |
| 9 | Contextual disclosure (help[] blocks) | 7. Agent Knowledge Packaging + 8. Efficiency & Composition | Next-step commands appended after output |

### Help Access (Principle 10)

| # | AXI Principle | Skill Axis | Notes |
|---|---------------|------------|-------|
| 10 | Consistent help access | 7. Agent Knowledge Packaging | Concise per-subcommand `--help` (5-10 lines, not 100+) |

## Reference Implementations

### gh-axi (GitHub CLI wrapper)

- **Domain:** GitHub issue, PR, and repo management
- **Benchmarks:** 425 runs, 100% task success, $0.050/task, 3 turns average
- **Key patterns:**
  - Pre-computed totals on all list commands (`total_count` field)
  - Minimal default fields (id, title, state, url) with `--full` escape hatch
  - help[] blocks after every command with contextual next steps
  - TOON output support via `--output toon`
  - Combined operations: `gh-axi pr create` returns the full PR object
  - Idempotent mutations: `gh-axi label ensure` creates-or-updates

### chrome-devtools-axi (Browser automation wrapper)

- **Domain:** Browser page navigation, interaction, inspection
- **Benchmarks:** 560 runs, 100% task success, $0.133/task, 4.6 turns average
- **Key patterns:**
  - Combined navigate+snapshot in single command (eliminates follow-up read)
  - Ambient context via session hooks showing current page state
  - Shell pipe composition: `open <url> | grep "selector"` for navigate+extract
  - Structured errors with retry hints for transient failures
  - Content truncation: DOM snapshots truncated with element counts and `--full` escape

## Benchmark Comparison

| Surface | Runs | Success | Cost/Task | Turns | Key Insight |
|---------|------|---------|-----------|-------|-------------|
| AXI wrapper (browser) | 560 | 100% | $0.133 | 4.6 | Combined ops eliminate observation round-trips |
| AXI wrapper (GitHub) | 425 | 100% | $0.050 | 3.0 | Pre-computed totals prevent miscounting |
| Vanilla CLI (no AXI) | — | 86% | — | ~7 | 36% more turns, 39% more tokens |
| MCP (compressed) | — | 100% | $0.150 | 5.9 | Higher cost than CLI even with compression |
| MCP (ToolSearch) | — | ~85% | $0.167 | 7.1 | ~15 point success drop from tool name guessing |

Combined total: 985 runs across two domains.
AXI wrappers lead on every metric: reliability, cost, speed, and turn count.

## Anti-pattern: ToolSearch Overhead

AXI benchmarks show agents using ToolSearch to discover available tools
suffer a ~15 percentage point drop in task success rate compared to agents
with explicit tool listings.
The overhead comes from tool-name guessing (e.g., `take_screenshot` vs `take_snapshot`)
and multiple round-trips to discover capabilities.

**Mitigation:** Ship a SKILL.md or CONTEXT.md that explicitly lists all commands
and their invocations. The agent loads it once and has full knowledge.
Prefer pre-documented subcommand lists over schema-based dynamic discovery.

## TOON Format

TOON (Token-Oriented Object Notation) is a JSON-compatible format optimized for LLM consumption:

- Uses indentation instead of braces, minimal quoting
- Table format for uniform object arrays (declare fields once, stream row values)
- ~40% token savings over JSON with 74% parsing accuracy vs JSON's 70% across 4 LLM models
- Lossless, deterministic round-trips with JSON

See implementation patterns (Section 13) for code examples and format details.
Specification: toonformat.dev
