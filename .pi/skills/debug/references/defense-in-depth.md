# Defense-in-Depth Validation

Multi-layer validation technique applied after a bug fix. Load when writing defensive layers in Phase 3 (Step 4c).

## Core Principle

Validate at every layer data passes through. Make the bug structurally impossible to reintroduce.

No single validation point prevents all bugs — refactored code paths bypass entry checks, mocks circumvent business logic, and platform edge cases need environment guards.

## The Four-Layer Framework

### Layer 1: Entry Point Validation

Reject invalid input at API/function boundaries:

```typescript
function createProject(workingDir: string) {
  if (!workingDir) throw new Error('workingDir is required');
  if (!fs.existsSync(workingDir)) throw new Error(`Directory not found: ${workingDir}`);
  // proceed...
}
```

**Check:** Required fields not empty, resources exist, correct types, valid formats.

### Layer 2: Business Logic Validation

Context-aware checks within business functions:

```typescript
async function initializeWorkspace(projectDir: string) {
  assert(projectDir !== '', 'projectDir must not be empty — indicates premature access');
  // proceed...
}
```

**Check:** Preconditions hold, state is consistent, business rules satisfied.

### Layer 3: Environment Guards

Prevent dangerous operations in specific contexts:

```typescript
function gitInit(directory: string) {
  if (process.env.NODE_ENV === 'test' && !directory.startsWith(os.tmpdir())) {
    throw new Error(`Refusing git init outside tmpdir in test environment: ${directory}`);
  }
  // proceed...
}
```

**Check:** Test environment restrictions, platform-specific limits, destructive operations guarded.

### Layer 4: Debug Instrumentation

Capture forensic context for future investigation:

```typescript
function gitInit(directory: string) {
  console.error('DEBUG gitInit:', {
    directory,
    cwd: process.cwd(),
    stack: new Error().stack,
  });
  // proceed...
}
```

**Check:** Current working directory, call stack, relevant parameters.

## When to Add Layers

Not every bug needs all four layers. Match defense depth to severity:

| Severity | Layers |
|----------|--------|
| Data loss / security | All four layers |
| Incorrect behavior with user impact | Layers 1-2 |
| Internal logic error | Layer 2 |
| Cosmetic / low impact | Primary fix only |

## Implementation Checklist

After fixing the root cause:

1. Map the data flow from entry to error location.
2. Identify all intermediate checkpoints.
3. Add validation at each layer proportional to severity.
4. Write a test for each layer's validation independently.
5. Verify bypassing one layer doesn't let invalid data through.
