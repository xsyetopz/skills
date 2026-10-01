# Regressions, nondeterminism, and retirement

## Contents

- [Regression tests](#regression-tests)
- [Races](#races)
- [Time and waiting](#time-and-waiting)
- [Isolation and flaky tests](#isolation-and-flaky-tests)
- [Retiring tests](#retiring-tests)

## Regression tests

- Keep the smallest complete input that triggered the bug, including the boundary that caused it
  (encoding, transaction, packaging). Reduce secrets and personal data out first (see
  `$debug-software-failures`).
- Show red on the faulty version: check out the faulty commit in a disposable worktree, or revert
  only the fix, and quote the failure line. Check it comes from the assertion, not from setup or an
  import error. Then show green on the fix together with the neighboring cases.
- After a failed operation, assert what it left behind (files, rows, messages, temporary files), not
  only the exception: a fault that truncates the file before validating raises the same `ValueError`
  as the correct code.

```python
def test_invalid_text_leaves_existing_file_unchanged(self):
    path.write_text("port=80\n", encoding="utf-8")
    with self.assertRaises(ValueError):
        write_config(path, "not a config")
    self.assertEqual(path.read_text(encoding="utf-8"), "port=80\n")
```

## Races

Force the bad schedule with a barrier, event, or latch at a hook in the code instead of running it
many times and hoping: both threads read, wait on the barrier, then both write. With no seam for a
hook, use a stress run with a recorded seed and report it as probabilistic, or a race detector
(`go test -race`, ThreadSanitizer).

## Time and waiting

- Code that depends on time takes a clock parameter; the test sets the time. A TTL test then runs in
  microseconds instead of sleeping.
- When a test must wait on an external condition, poll it with a deadline and fail with the last
  observed state. A fixed `sleep` is too short on a loaded machine and wastes time on a fast one.
  Find offenders with `rg -n 'time\.sleep|Thread\.sleep|setTimeout' tests/`.
- A real latency budget is a benchmark, not a unit test.

## Isolation and flaky tests

- Each test builds its own state: fresh objects, per-test directories, ports chosen by the operating
  system (port 0), reset registries. Run suspects alone, in reverse, and randomized
  (`pytest-randomly` [ref][randomly]) to expose order dependence.
- Diagnose a flaky test in order: record the seed, order, worker count, time, and logs of the
  failing run; reproduce; then vary one source of nondeterminism at a time (order, parallelism,
  time, randomness, external service). Do not add retries or lengthen timeouts to get green ([flaky
  tests][pytest-flaky]; for browser waits see [Playwright best practices][playwright]).

## Retiring tests

For a test that breaks during a behavior-preserving change, choose one: retain (it catches a real
defect), rewrite (the requirement matters but the test is coupled), consolidate (it duplicates
another), remove (obsolete requirement, or it only mirrors the code), or unresolved (evidence
missing). A change-detector test repeats the implementation instead of checking correctness
([Change-Detector Tests][detector]). Deleting an unexplained failing test is not retirement:
diagnose first, and name the test that keeps protecting each removed behavior.

[playwright]: https://playwright.dev/docs/best-practices
[randomly]: https://pypi.org/project/pytest-randomly/
[pytest-flaky]: https://docs.pytest.org/en/stable/explanation/flaky.html
[detector]: https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html
