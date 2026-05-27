# Root Cause Tracing

Backward tracing technique for finding where bugs originate. Load when the Investigation Log shows the symptom but not the source.

## The Five-Step Process

### 1. Observe the Symptom

Document exactly what manifests. Be specific:
- Wrong value, missing file, unexpected exception, incorrect output
- Exact error message and stack trace
- Environmental context (directory, branch, config)

### 2. Find Immediate Cause

Identify which code directly produces the error:

```
Error at line 42: Cannot read property 'name' of undefined
→ Immediate cause: `user.name` where `user` is undefined
→ File: src/handlers/profile.ts:42
```

### 3. Trace One Level Up

What called that code? What values were passed?

```
profile.ts:42  ← called by router.ts:18 with getProfile(userId)
→ userId = "abc-123" (looks valid)
→ user = await db.findUser(userId) → returned undefined
```

### 4. Keep Tracing

Continue up the call chain, examining values at each level:

```
db.findUser("abc-123") → undefined
→ Query: SELECT * FROM users WHERE id = 'abc-123'
→ Result: empty set
→ Why? User was created with id = "ABC-123" (uppercase)
→ Where did lowercase come from?
```

### 5. Find Original Trigger

The source of the bad data:

```
router.ts:15: const userId = req.params.id.toLowerCase()
→ This normalization doesn't match the database storage format
→ ROOT CAUSE: case normalization applied at the wrong layer
```

## Adding Stack Traces for Hard-to-Trace Bugs

When manual tracing is insufficient, instrument with logging:

```typescript
async function suspiciousFunction(param: string) {
  const stack = new Error().stack;
  console.error('DEBUG suspicious_function:', {
    param,
    cwd: process.cwd(),
    stack,
  });
  // ... rest of function
}
```

**Use `console.error()` in tests** — `console.log()` and loggers may be suppressed.

Capture stderr: `npm test 2>&1 | grep 'DEBUG'`

## Finding Test Pollution

When a test passes in isolation but fails in the suite, another test is polluting shared state.

Bisection approach:
1. Run the full suite — note which test fails.
2. Run the first half of tests followed by the failing test.
3. If it fails, the polluter is in the first half. If it passes, the polluter is in the second half.
4. Repeat until isolated.

Look for: global state mutations, unrestored mocks, database records not cleaned up, environment variable changes, file system artifacts.

## Failure Classification

Classify the failure before tracing. Classification determines the fix strategy.

| Category | Symptoms | Fix Strategy |
|----------|----------|--------------|
| **CODE_ERROR** | Logic bug, wrong algorithm, incorrect condition, off-by-one | Trace to root cause, fix at source |
| **CONFIG_ERROR** | Wrong env var, missing flag, invalid config value, wrong connection string | Check config loading path; validate at startup |
| **DEPENDENCY** | Missing package, version mismatch, incompatible interface, import not found | Check dependency versions, lock files, import paths |
| **INFRA** | Intermittent network timeout, OOM, disk full, port conflict | Verify environment; restart services; check resource limits |
| **FLAKY** | Passes in isolation, fails in suite; non-deterministic; time-sensitive | Bisect for test pollution; check shared state, mocks, and timers |
| **DATA** | Unexpected null, corrupted record, schema mismatch, encoding issue | Trace data origin; add validation at input boundaries |

**Triage order:** CODE_ERROR → CONFIG_ERROR → DEPENDENCY → DATA → INFRA → FLAKY

**Re-run before tracing INFRA/FLAKY:** A re-run costs nothing. Confirm the failure is reproducible before investing in root cause analysis.

## Key Principle

**NEVER fix the symptom.** Trace backward to the original trigger, then:
1. Fix at the source
2. Add validation at intermediate layers
3. Make the bug structurally impossible to reintroduce
