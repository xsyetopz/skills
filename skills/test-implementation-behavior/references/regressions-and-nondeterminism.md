# Regressions, asynchronous work, and flaky tests

## Preserve a useful failure

Reduce the bug to the smallest complete reproducer that retains the relevant
boundary. Record input, runtime/toolchain, configuration, expected outcome, and
observed failure. Include malformed input or a failing dependency when it caused
the incident. Do not simplify away the race, packaging, encoding, or transaction
that makes it fail.

Run the new test on the faulty implementation when available. Check that it
fails for the intended reason, not an import error, missing credential, or
broken test setup. Then run against the fix and representative nearby
success/failure cases. Use a disposable copy/worktree for historical versions or
controlled mutations; do not reset the user's working tree. Keep failing input
as a minimal, non-sensitive fixture when it protects a real contract.

Test persisted effects as well as return values. For example, if an operation
must not replace an existing file after validation fails, compare the
destination's contents after the failed operation. A nonzero process exit alone
does not prove the file was preserved. If partial output is intentionally
allowed, test that contract instead; do not invent an all-or-nothing policy.

## Control the source of nondeterminism

Identify shared state, test ordering, time, randomness, parallel execution,
external services, and leaked resources. [pytest's flaky-test guidance][pytest]
explains common state and cleanup failures. Those causes generalize; its
runner-specific APIs must be verified against the project's installed version.

Use per-test directories, ports allocated by the operating system, isolated
databases, explicit cleanup, and joined tasks/processes. Use existing clock or
scheduler controls when the behavior depends on time. Fixed seeds help reproduce
random choices but do not control thread schedules. Avoid global environment
mutations in parallel tests unless the runner isolates them.

For races, coordinate interleavings with barriers/events through existing test
facilities. Example: arrange two attempts to update the same version before
either commits, then assert the actual transactional outcome. A stress run may
discover a failure, but a deterministic interleaving makes its regression easier
to trust. Do not change the production synchronization just to satisfy the test
schedule.

Use bounded condition-based waits, not arbitrary sleeps. Wait for the observable
state that establishes success or failure, and capture diagnostics on timeout.
For browser tests, use user-facing locators and the runner's retrying
assertions; do not poll unrelated DOM details or rely on an incidental CSS
implementation. [Playwright's documented practices][playwright] cover isolation,
locators, and web-first assertions. Adapt to the runner already used by the
project.

## Diagnose rather than suppress

Capture failing input, order, seed, worker count, timestamps, logs, and traces
when relevant. Reproduce the failing mode, then vary one source of
nondeterminism to isolate the cause. Compare serial and parallel runs when a
shared-state hazard is plausible. A passing retry is evidence of intermittence,
not a repair.

Do not remove an assertion to suppress an unexplained failure, increase timeouts
blindly, mark the test skipped, or change CI checks merely to obtain a passing
result. Evidence-based retirement of redundant or obsolete coverage is a
different decision, not a remedy for an unexplained failure. Quarantine/retry
policy changes require explicit approval and an accountable follow-up; preserve
failure evidence even when that policy is approved. Report an unrelated baseline
failure separately rather than silently repairing it as part of a narrow testing
task.

[pytest]: https://docs.pytest.org/en/stable/explanation/flaky.html
[playwright]: https://playwright.dev/docs/best-practices
