# Implementation Patterns

Concrete patterns for each Agent DX improvement area.
Language-agnostic principles with examples in Go (cobra) and Python (click).

## 1. Machine-Readable Output

### Dual-format output

Add a global `--output` flag. In non-TTY contexts (piped), default to JSON.

```go
// Go + cobra
var outputFormat string

func init() {
    rootCmd.PersistentFlags().StringVarP(&outputFormat, "output", "o", "", "Output format: json, table (default: auto)")
}

func printOutput(data any) {
    format := outputFormat
    if format == "" {
        if isatty.IsTerminal(os.Stdout.Fd()) {
            format = "table"
        } else {
            format = "json"
        }
    }
    switch format {
    case "json":
        enc := json.NewEncoder(os.Stdout)
        enc.SetIndent("", "  ")
        enc.Encode(data)
    default:
        printTable(data)
    }
}
```

```python
# Python + click
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default=None)
def cli(output):
    if output is None:
        output = 'json' if not sys.stdout.isatty() else 'table'
```

### Structured errors

Return errors as JSON with a consistent schema. Never exit 0 on error.

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource 'abc123' not found",
    "details": {"resource_type": "file", "resource_id": "abc123"}
  }
}
```

Exit codes: 0 = success, 1 = usage error, 2 = runtime error.

## 2. Input Validation and Hardening

### Input sanitizer middleware

Validate all string inputs before they reach business logic.

```go
func validateResourceID(id string) error {
    if strings.Contains(id, "..") {
        return fmt.Errorf("path traversal detected in resource ID: %q", id)
    }
    if strings.ContainsAny(id, "?#") {
        return fmt.Errorf("embedded query params in resource ID: %q", id)
    }
    if strings.Contains(id, "%") {
        return fmt.Errorf("percent-encoded value in resource ID: %q — pass decoded values", id)
    }
    for _, r := range id {
        if r < 0x20 {
            return fmt.Errorf("control character in resource ID: %q", id)
        }
    }
    return nil
}
```

### Hallucination patterns to catch

| Pattern | Detection | Example |
|---------|-----------|---------|
| Path traversal | `..` in resource IDs or paths | `../../.ssh/id_rsa` |
| Embedded query params | `?` or `#` in resource IDs | `fileId?fields=name` |
| Double encoding | `%` in decoded inputs | `%2e%2e` for `..` |
| Control characters | ASCII < 0x20 | Null bytes, newlines in IDs |
| Overly long inputs | Length exceeds reasonable max | 10KB resource ID |

## 3. Schema Introspection

### `schema` subcommand

Add a `schema <method>` command returning the full method signature as JSON.

```json
{
  "method": "files.create",
  "http_method": "POST",
  "path": "/v1/files",
  "parameters": {
    "parent_id": {"type": "string", "required": true, "description": "Parent folder ID"},
    "name": {"type": "string", "required": true, "description": "File name"}
  },
  "request_body": {
    "type": "object",
    "properties": {
      "content": {"type": "string"},
      "mime_type": {"type": "string", "default": "text/plain"}
    }
  },
  "response": {
    "type": "object",
    "properties": {
      "id": {"type": "string"},
      "name": {"type": "string"},
      "created_at": {"type": "string", "format": "date-time"}
    }
  },
  "scopes": ["files:write"]
}
```

### Generate from source of truth

Generate schema from an OpenAPI spec, protobuf definition, or API discovery document.
Avoids schema drift — the CLI always reflects the current API.

## 4. Field Masks and Pagination

### `--fields` flag

Accept a comma-separated list of fields to include in the response.

```go
var fields string
cmd.Flags().StringVar(&fields, "fields", "", "Comma-separated fields to include (e.g., id,name,status)")

// Filter response before output
if fields != "" {
    data = filterFields(data, strings.Split(fields, ","))
}
```

### NDJSON streaming pagination

Stream results as newline-delimited JSON instead of buffering entire arrays.

```go
func streamResults(w io.Writer, paginator Paginator) error {
    enc := json.NewEncoder(w)
    for paginator.HasNext() {
        page, err := paginator.Next()
        if err != nil {
            return err
        }
        for _, item := range page.Items {
            if err := enc.Encode(item); err != nil {
                return err
            }
        }
    }
    return nil
}
```

## 5. Dry-Run Mode

### `--dry-run` flag on all mutations

Show what would happen without executing. Output: HTTP method, URL, headers, body, validation results.

```go
var dryRun bool
cmd.Flags().BoolVar(&dryRun, "dry-run", false, "Validate and show what would happen without executing")

func executeOrDryRun(req *http.Request, dryRun bool) error {
    if dryRun {
        out := map[string]any{
            "method":  req.Method,
            "url":     req.URL.String(),
            "headers": req.Header,
        }
        if req.Body != nil {
            body, _ := io.ReadAll(req.Body)
            out["body"] = json.RawMessage(body)
        }
        return json.NewEncoder(os.Stdout).Encode(out)
    }
    return execute(req)
}
```

## 6. Agent Context Files

### `CONTEXT.md` at repo root

```markdown
# <CLI Name> Agent Context

## Quick Start

<one command to get started>

## Invariants

- Always use `--output json` when parsing output programmatically
- Always add `--fields` to list commands to limit response size
- Always use `--dry-run` before mutating commands
- Never pass user-generated content as resource IDs without validation

## Common Workflows

### Create a resource
<cli> create --json '{"name": "example"}' --dry-run
<cli> create --json '{"name": "example"}'

### List with pagination
<cli> list --fields id,name,status --page-size 50 --output json
```

### Structured skill files

Ship YAML-frontmatter Markdown files for agent-specific workflows:

```yaml
---
name: <cli>-create-resource
version: 1.0.0
---

# Create Resource

1. Validate input: `<cli> schema resources.create`
2. Dry-run: `<cli> resources create --json '{...}' --dry-run`
3. Execute: `<cli> resources create --json '{...}'`
4. Verify: `<cli> resources get <id> --fields id,status`
```

## 7. MCP Surface

### JSON-RPC over stdio

Expose the CLI as an MCP server for direct agent integration.

```json
{
  "mcpServers": {
    "<cli-name>": {
      "command": "<cli>",
      "args": ["mcp", "serve"],
      "env": {"API_KEY": "..."}
    }
  }
}
```

Each CLI command becomes an MCP tool with typed parameters derived from the schema.
Eliminates shell escaping, argument parsing ambiguity, and output parsing.

### Implementation approach

1. Define tools from the same source of truth as CLI commands (OpenAPI, protobuf, discovery doc)
2. Map each command to a tool with typed input/output schemas
3. Handle auth via environment variables (headless — no browser redirect)
4. Return structured JSON responses, not formatted text

## 8. Exit Code Design

### Semantic exit codes

Use distinct exit codes so agents can branch without parsing stderr.
The exact numbering matters less than consistency and documentation.

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Usage / invalid arguments |
| 10 | Resource not found |
| 11 | Conflict with existing state |
| 12 | Permission denied |
| 20 | Transient failure (retryable) |
| 130 | Interrupted (SIGINT) |

### Enhanced structured errors

Return errors as JSON on stderr with `retryable` flag and `suggestions` array.

```json
{
  "error": "invalid_value",
  "field": "--env",
  "message": "Unknown environment 'prod'",
  "retryable": false,
  "suggestions": [
    "Valid values: dev, staging, production",
    "Run `myctl env list` to see all environments"
  ]
}
```

### Cancellation signal

When a streamed operation is interrupted, emit a partial-progress signal:

```json
{"interrupted": true, "completed": 47, "total": 150}
```

This tells the caller what state the system is in without requiring a follow-up query.

## 9. Non-Interactive Mode

### `--yes` and TTY detection

Add a `--yes` flag. In non-TTY contexts, skip prompts automatically.

```go
var yesFlag bool
cmd.Flags().BoolVar(&yesFlag, "yes", false, "Skip confirmation prompts")

// In non-TTY: auto-skip. In TTY without --yes: prompt on stderr.
if yesFlag || !isatty.IsTerminal(os.Stdin.Fd()) { proceed() }
```

### Headless auth

Auth priority: env var > stdin > credential file > browser (last resort).
Browser redirect only in interactive TTY. Support `echo $TOKEN | myctl login --stdin`.

### Secret redaction

Redact `Authorization`, `X-Api-Key`, `Cookie` headers in `--verbose` and `--dry-run` output.
Prefer stdin or env vars over process arguments — process args appear in `ps` and shell history.

### Declarative commands

Where possible, use idempotent verbs: `apply`, `sync`, `ensure` instead of `create`, `delete`.
Agents can safely re-run declarative commands without checking current state first.

## 10. Follow-up Reduction

Patterns that answer the agent's next question before it asks.

### Pre-computed totals

Include `total_count` in list responses.
AXI benchmarks found this was the difference between 5/5 and 0/5 on a `list_labels` task —
without it, agents reported the page size as the total.

```json
{
  "items": [{"id": "abc", "name": "web-1"}],
  "total_count": 47,
  "page": 1,
  "page_size": 25
}
```

### help[] blocks (next-step commands)

Append copy-pasteable commands specific to what just happened.
AXI calls these "help[] blocks" — the primary mechanism for contextual disclosure.
Previously called "hints" in some implementations; AXI standardizes on `help`.

```json
{
  "id": "deploy-123",
  "status": "in_progress",
  "help": [
    "Run `myctl deploy status deploy-123` to check progress",
    "Run `myctl deploy rollback deploy-123` to cancel"
  ]
}
```

### Recovery paths in errors

Include valid values and concrete corrective commands — not vague advice.
See Section 8 (Enhanced structured errors) for the JSON schema with `suggestions` array.

### Truncation hints

When truncating a large field, indicate that more data exists:

```
"body": "First 500 chars of the issue body… [truncated, 2847 chars total; use --full to see complete body]"
```

### Undo commands in mutation receipts

Include the rollback command in mutation responses:

```json
{
  "action": "deploy",
  "resource": "web-api",
  "version": "v2.1",
  "undo_command": "myctl rollback web-api --to v2.0"
}
```

### Content-first defaults

When context is clear (e.g., current repo), a bare command should show live data:

```
$ myctl          # in a repo with a myctl project
{"project": "web-api", "status": "deployed", "version": "v2.1", ...}
```

This collapses a two-step interaction (`myctl --help` then `myctl status`) into one.

### Definitive empty states

Return explicit zero-result messages, not ambiguous empty output:

```json
{"items": [], "total_count": 0, "message": "No deployments found matching filter 'failed'"}
```

Without this, agents may assume the command failed or that results were truncated.

## 11. Batch Validation

### Return all errors at once

Collect all validation errors before returning, instead of failing on the first.

```go
// Accumulate all errors before returning — never fail-fast on the first.
var errs []ValidationError
if !isValidEnv(cmd.Env)   { errs = append(errs, ValidationError{Field: "--env", ...}) }
if cmd.Image == ""         { errs = append(errs, ValidationError{Field: "--image", ...}) }
if !isDuration(cmd.Timeout){ errs = append(errs, ValidationError{Field: "--timeout", ...}) }
return errs // caller formats as JSON with all errors
```

Without batch validation: 3 invalid flags = 3 separate retries.
With batch validation: 1 command, 1 diagnosis, 1 correction pass.

## 12. Reject vs. Normalize

### Decision framework

| Condition | Action | Rationale |
|-----------|--------|-----------|
| Correction could change caller's intent | **Reject** with error | Silent "fix" may do the wrong thing |
| Correction is cosmetic with no ambiguity | **Normalize** silently | Reduces friction without risk |

### Reject these (ambiguous or dangerous)

| Input | Why reject |
|-------|-----------|
| `../../.ssh/config` | Path traversal — dangerous |
| `fileId?fields=name` | Embedded query params — structural error |
| `hello\x00world` | Control characters — injection risk |
| `300` (for a duration) | Ambiguous — could mean 300s, 300ms, or 300m |

### Normalize these (unambiguous cosmetic)

| Input | Normalized | Why safe |
|-------|-----------|----------|
| `Production` | `production` | Case difference, one canonical form |
| `my-resource ` | `my-resource` | Trailing whitespace |
| `us-east-1/` | `us-east-1` | Trailing slash on an ID |

```go
// Reject first (dangerous/ambiguous), then normalize (cosmetic).
// Reject: ".." (traversal), "?#" (embedded params), control chars, ambiguous values.
// Normalize: TrimSpace, TrimRight("/"), ToLower.
```

## 13. Token-Efficient Output (TOON)

TOON (Token-Oriented Object Notation) uses indentation instead of braces and minimal quoting.
~40% token savings over JSON with 74% parsing accuracy vs JSON's 70% across 4 LLM models.
Lossless, deterministic round-trips with JSON. Spec: toonformat.dev

### When to use

Offer as `--output toon` alongside `json` and `table`.
TOON is an option for token-conscious callers, not a replacement for JSON.

### Format comparison

JSON (39 tokens):
```json
[{"id": "web-1", "status": "running", "replicas": 3}, {"id": "web-2", "status": "stopped", "replicas": 0}]
```

TOON (~23 tokens):
```
{fields}
id      status   replicas
web-1   running  3
web-2   stopped  0
```

Uniform object arrays compress into tables: declare fields once, stream row values.

### Go example

```go
func printTOON(w io.Writer, items []map[string]any, fields []string) {
    fmt.Fprintf(w, "{fields}\n")
    fmt.Fprintf(w, "%s\n", strings.Join(fields, "\t"))
    for _, item := range items {
        vals := make([]string, len(fields))
        for i, f := range fields {
            vals[i] = fmt.Sprintf("%v", item[f])
        }
        fmt.Fprintf(w, "%s\n", strings.Join(vals, "\t"))
    }
}
```

### Python example

```python
def print_toon(items: list[dict], fields: list[str], out=sys.stdout):
    out.write("{fields}\n")
    out.write("\t".join(fields) + "\n")
    for item in items:
        out.write("\t".join(str(item.get(f, "")) for f in fields) + "\n")
```

### Integration with `--output` flag

Add `toon` to the output format choices alongside `json` and `table`:

```go
case "toon":
    printTOON(os.Stdout, data, defaultFields)
```

## 14. Combined Operations

Combine action + observation in a single CLI call.
Eliminates follow-up reads after mutations — the primary source of unnecessary agent turns.
AXI benchmarks show combined operations are the key differentiator for browser automation tasks.

### Pattern 1: Mutation returns full resource

Instead of returning only an ID and forcing a follow-up GET:

```go
// Bad: returns only ID — agent must call Get() next
func createHandler(cmd *cobra.Command, args []string) error {
    id, err := client.Create(payload)
    printOutput(map[string]string{"id": id})
    return err
}

// Good: returns the full resource inline
func createHandler(cmd *cobra.Command, args []string) error {
    id, err := client.Create(payload)
    if err != nil { return err }
    resource, err := client.Get(id)
    if err != nil { return err }
    resource["help"] = []string{
        fmt.Sprintf("Run `myctl get %s` to refresh", id),
        fmt.Sprintf("Run `myctl delete %s` to remove", id),
    }
    return printOutput(resource)
}
```

```python
# Good: create returns the full resource
@cli.command()
def create(payload: str):
    resource_id = client.create(json.loads(payload))
    resource = client.get(resource_id)
    resource["help"] = [
        f"Run `myctl get {resource_id}` to refresh",
        f"Run `myctl delete {resource_id}` to remove",
    ]
    print_output(resource)
```

### Pattern 2: Navigate + snapshot (UI CLIs)

For browser or UI automation CLIs, one command opens a URL and returns state:

```bash
# One command does both navigation and snapshot:
myctl open https://example.com --snapshot
# Returns: page title, URL, DOM summary, visible elements
```

### When NOT to combine

Do not combine when the observation is expensive (>5s) or when the caller
may not need it. Offer `--no-fetch` to skip the follow-up read.

## 15. Shell Composition

CLIs that compose via shell pipes achieve multi-step workflows in a single pipeline,
reducing agent turns significantly.
AXI benchmarks: shell composition enabled patterns impossible in MCP.

### Core rules

1. **stdout = data, stderr = diagnostics.** Progress bars, warnings, and debug info go to stderr.
   Data goes to stdout. This lets pipes work correctly.
2. **One record per line for lists.** NDJSON (one JSON object per line) is filterable with grep and jq.
3. **Exit codes must be correct.** Pipe chains short-circuit on non-zero exit —
   incorrect exit codes break composition.
4. **Accept stdin.** Commands that operate on resources should accept IDs via stdin
   for piping from other commands.

### Pipeline pattern

Without composition (3 agent turns):
```
Turn 1: myctl list --status failed --output json > /tmp/failed.json
Turn 2: # Agent parses JSON, extracts IDs
Turn 3: myctl delete id1 id2 id3
```

With composition (1 pipeline):
```bash
myctl list --status failed --output ndjson | jq -r '.id' | xargs myctl delete
```

### Go example: stdin acceptance

```go
func deleteHandler(cmd *cobra.Command, args []string) error {
    ids := args
    if len(ids) == 0 && !isatty.IsTerminal(os.Stdin.Fd()) {
        scanner := bufio.NewScanner(os.Stdin)
        for scanner.Scan() {
            if id := strings.TrimSpace(scanner.Text()); id != "" {
                ids = append(ids, id)
            }
        }
    }
    if len(ids) == 0 {
        return fmt.Errorf("no resource IDs provided (pass as args or via stdin)")
    }
    return client.DeleteBatch(ids)
}
```

### Python example: stdin acceptance

```python
@cli.command()
@click.argument("ids", nargs=-1)
def delete(ids: tuple[str, ...]):
    if not ids and not sys.stdin.isatty():
        ids = tuple(line.strip() for line in sys.stdin if line.strip())
    if not ids:
        raise click.UsageError("No resource IDs provided (pass as args or via stdin)")
    client.delete_batch(ids)
```

## 16. Ambient Context

Self-installing session hooks that display CLI state before each agent invocation.
The agent never needs to spend a turn querying "what is the current state?"

### Shell hook pattern

Provide a `shell-hook` subcommand that detects the shell and emits hook code:

```go
func shellHookCmd() *cobra.Command {
    return &cobra.Command{
        Use:   "shell-hook install",
        Short: "Install a shell hook that shows CLI context before each command",
        RunE: func(cmd *cobra.Command, args []string) error {
            shell := detectShell() // fish, bash, zsh
            switch shell {
            case "fish":
                fmt.Println(`function __myctl_hook --on-event fish_preexec; myctl context --compact 2>/dev/null; end`)
            case "bash":
                fmt.Println(`__myctl_hook() { myctl context --compact 2>/dev/null; }; PROMPT_COMMAND="__myctl_hook;$PROMPT_COMMAND"`)
            case "zsh":
                fmt.Println(`__myctl_hook() { myctl context --compact 2>/dev/null; }; precmd_functions+=(__myctl_hook)`)
            }
            return nil
        },
    }
}
```

### Context subcommand

A `context` command emits a compact one-line state summary:

```bash
$ myctl context --compact
project=web-api env=staging version=v2.1 status=deployed last-deploy=2h-ago
```

This is what the session hook displays before each command.
The agent sees the state in its context window without querying.

### Relationship to help[] blocks

- **Ambient context** shows state BEFORE the command (what is the world right now?)
- **help[] blocks** show next steps AFTER the command (what should I do next?)

Together they frame each CLI invocation,
eliminating both pre-command state queries and post-command "what now?" questions.

## 17. help[] Blocks (Detailed)

After every command output, append a `help` array with contextual next-step commands.
These are not generic help — they are specific to the result.
AXI calls this "contextual disclosure" (Principle 9).

### Format

Include `help` as a top-level field in JSON responses:

```json
{
  "id": "deploy-456",
  "status": "failed",
  "error": "health check timeout",
  "help": [
    "Run `myctl deploy logs deploy-456` to see failure details",
    "Run `myctl deploy retry deploy-456` to retry",
    "Run `myctl deploy rollback deploy-456 --to v2.0` to roll back"
  ]
}
```

Commands should vary help[] content based on the result:

| Result | help[] content |
|--------|---------------|
| Success | Status check, logs, related resources |
| Failure | Logs, retry, rollback, diagnostic commands |
| Partial | Resume, status, cancel commands |
| List | Filter, export, act-on-item commands |

### Go wrapper

```go
func withHelp(data map[string]any, commands ...string) map[string]any {
    data["help"] = commands
    return data
}

// Usage:
result := withHelp(resource,
    fmt.Sprintf("Run `myctl get %s` to refresh", id),
    fmt.Sprintf("Run `myctl logs %s` to view logs", id),
)
```

### Python wrapper

```python
def with_help(data: dict, *commands: str) -> dict:
    data["help"] = list(commands)
    return data

# Usage:
result = with_help(resource,
    f"Run `myctl get {resource_id}` to refresh",
    f"Run `myctl logs {resource_id}` to view logs",
)
```

### In TOON format

For TOON output, help[] blocks appear as an indented list after the main data:

```
id        deploy-456
status    failed
error     health check timeout
help
  Run `myctl deploy logs deploy-456` to see failure details
  Run `myctl deploy retry deploy-456` to retry
  Run `myctl deploy rollback deploy-456 --to v2.0` to roll back
```
