---
name: test-software-behavior
description: >-
  Design, add, or review behavioral and regression tests, diagnose flaky
  tests, and verify package or integration behavior. Use when test design,
  coverage, an oracle, nondeterminism, fuzzing, or a tests-only change is
  the requested outcome; not for routine test execution, CI configuration,
  or performance optimization.
---

# Test Software Behavior

Select this workflow automatically when the task matches its description.
Selection supplies guidance only; it does not authorize operations beyond the
user's request.

Identify the intended contract, supported environments, and observable failure.
Read existing tests and test configuration before adding tools. Current output,
visible fixtures, and implementation details are evidence, not automatically the
specification. Resolve material uncertainty instead of blessing it with a test.

Choose the smallest combination of test boundaries that can distinguish a real
incorrect implementation. Do not replace a required integration, host, or
install check with compilation or a mocked unit test. Reuse the project's runner
and fixtures; add a maintained test tool only when it supplies a needed
capability.

**MUST structure each functional test as `Arrange`, `Act`, `Assert`.** `Arrange`
all inputs and preconditions first, perform one focused invocation or user
operation as `Act`, then `Assert` its observable outcomes. DO NOT alternate
`Act` and `Assert` in one test; split distinct behaviors into separate tests.
Existing framework setup and teardown hooks may surround these phases. Comments
naming the phases are optional when the boundaries are already clear.

- Read [test boundaries and oracles](references/boundaries-and-oracles.md) when
  selecting coverage, assertions, test doubles, contracts, or package checks.
- Read
  [regressions and nondeterminism](references/regressions-and-nondeterminism.md)
  for bug reproduction, concurrency, asynchronous behavior, and flaky tests.
- Read
  [property, fuzz, and mutation tests](references/generative-and-mutation.md)
  when example-based coverage cannot adequately explore the input/state space.

For a regression, demonstrate failure on the faulty behavior when available,
then success on the fix. Do this without modifying unrelated user work or
rewriting history. In a tests-only task, report discovered product defects; do
not repair production code unless requested. Do not add production APIs solely
for tests.

Use isolated temporary state and synthetic data. Avoid live external writes,
real credentials, and production infrastructure. Never weaken assertions, update
snapshots blindly, disable checks, or add retries/quarantine to hide a failure.

Report the behaviors covered, actual commands and results, failures found,
environment limitations, and remaining gaps. Test count and coverage percentage
alone do not establish correctness. A proposed test plan is not an executed
test.
