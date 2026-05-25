# Testing

## Workflow
- TDD when behavior changes: write test (RED) -> verify failure -> implement (GREEN) -> refactor.
- When tests fail, fix the implementation -- not the tests (unless tests have errors).
- Run single tests during development, not the whole suite.

## Coverage
- Both positive and negative test cases for every feature.
- Mock external dependencies; never call real APIs in tests.
- Test names: "should [action] when [condition]".

## Verification
- Every code change must be verifiable. Write a test, run the linter, or check the build output.
- After implementing, run the relevant test command before considering work done.
- If no test framework exists, verify with a build command or a manual smoke test script.
