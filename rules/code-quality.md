# Code Quality

## Style
- Functions under 50 lines. Files under 800 lines. Nesting under 4 levels.
- No magic numbers or hardcoded values; use named constants.
- Organize code by feature/domain, not by type (models/, utils/).
- Prefer immutable data structures. Create new objects; never mutate existing ones.

## Error Handling
- Catch, log, and propagate errors at every layer. Never silently swallow exceptions or ignore return codes.
- Error messages must not leak sensitive data (stack traces, internal paths, secrets).
- Surface user-friendly messages in customer-facing interfaces; detailed context in server logs.

## Design
- No speculative features. Implement only what is requested.
- No premature abstraction. Three similar lines beat a premature helper.
- Replace, don't deprecate. Delete dead code completely.
- Search for battle-tested libraries before implementing new functionality.
