---
name: write-behavior-tests
description: >-
  Writes tests that check observable behavior instead of implementation
  details, with fixtures, fakes, and property tests. Use when adding or
  fixing tests or a regression test.
---

# Write Behavior Tests

A test is useful when it fails on a meaningful fault and passes every
implementation that meets the contract. Write down the contract and its
authority first: a requirement, standard, issue, or the user.

## Rules

- A regression test must be seen failing without the fix. Run it on the
  faulty commit (disposable worktree) or with only the fix reverted, and
  check the failure line comes from the assertion, not from setup or an
  import error. A test never seen red protects nothing.
- Take expected values from the contract, never from running the code under
  test, the same formula, the current output, or a snapshot. A user's
  guessed cause is evidence, not an expected value.
- Do not mock the unit under test. Replace only collaborators that are
  slow, dangerous, unavailable, or nondeterministic; use the real object
  for pure functions and value objects, and the real engine (an isolated
  database or file system) for engine semantics such as constraints.
- No assertion-free tests, and no assertion that only checks "did not
  raise". After a failing operation, assert what it left behind (files,
  rows, messages), because a bug can raise the same exception.
- No snapshot rubber stamps: never regenerate a snapshot or golden file to
  get green. Normalize only what varies, and review every diff.
- No fixed `sleep` as synchronization. Inject a clock, force the thread
  interleaving with a barrier, or poll with a deadline and report the last
  state. Every wait has a deadline.
- Assert outcomes through the public operation, not private helpers,
  storage, call order, or counts, unless the call is the contract. Tests
  that break on refactors that change no behavior are change detectors.
- One behavior per test, with the action visible in the body, so a failure
  names one rule.
- Do not weaken assertions, skip tests, add retries, or lengthen timeouts
  to get a green run. Diagnose, and report unexplained failures.
- In a tests-only task, do not fix production code; report the failing
  behavior.
- Do not touch devices, flash firmware, or call live services without
  explicit approval. Run the narrower layer and label it.
- When the project already has a mutation tool, run it on the changed
  functions (see [generative](references/generative.md)) and classify each
  survivor as a missing test, a weak assertion, or an equivalent mutant.
  Otherwise report it as not run and do not add one without approval.

## Workflow

1. Write the contract; map each claim to the smallest layer that can
   observe it.
1. Choose inputs: classes and boundaries, a decision table, transitions,
   standard vectors, or properties.
1. Write the tests, then run them where the behavior is missing and record
   the red line.
1. Make the change, rerun the test and its neighbors.
1. Report each claim with its layer, the commands run, and what was not
   run.

## References

- Read [test design](references/test-design.md) when choosing expected
  values, boundaries, or a layer, when picking a mock, stub, or fake, when a
  test breaks on every refactor, or for package, host, and hardware claims.
- Read [regressions and flakiness](references/regressions-and-flakiness.md)
  when fixing a bug, for races, timeouts, expiry, tests that pass alone and
  fail in the suite, or before deleting a test.
- Read [generative](references/generative.md) for property tests, fuzzing
  untrusted input, sanitizers, or judging test strength with mutation
  testing.
