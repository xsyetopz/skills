# Regressions, nondeterminism, and retirement

How to keep a bug from returning, make timing and concurrency tests
deterministic, and decide what to do with a test that keeps breaking.
The examples are in [`test_regressions.py`][regressions], with weak
counterparts in `weak_examples.py`.

## Contents

- Regression reproducer
- Persisted effects after failure
- Deterministic interleaving
- Injected clock and bounded waits
- Test isolation from shared state
- Flaky test diagnosis
- Test retirement decision

## Regression reproducer

**Definition.** The smallest complete input that triggered a reported
bug, kept as a test. It is shown to fail on the faulty version and pass
on the fix, for the intended reason. It keeps the boundary that caused
the bug: encoding, a race, a transaction, packaging.

**Use when.** Every bug fix.

**Do not use when.** The input contains secrets or personal data.
Reduce it or synthesize an equivalent first (for reduction, see
`$debug-software-failures`).

**Example.**

```python
def test_empty_fields_are_kept(self):
    # Reproducer from the incident: 'a::b' lost its middle field.
    cases = {"a::b": ["a", "", "b"], "a:": ["a", ""], ":": ["", ""], "": [""]}
    for line, fields in cases.items():
        with self.subTest(line=line):
            self.assertEqual(impl.split_fields(line), fields)
```

**Cost removed.** Reintroduced bugs. The red run is recorded in
[observed red](test-structure.md#observed-red-then-green). The weak
`WeakSplit` uses input without empty fields and passes the bug.

**Verify.**

1. Run the test on the faulty version, in a disposable worktree or with
   a mutant, and quote the failure line.
1. Run it on the fix, together with the nearby cases.

## Persisted effects after failure

**Definition.** After an operation fails, assert what it left behind:
files, rows, messages. An exception or a nonzero exit alone does not
show that the old state was kept.

**Use when.** The operation writes to storage and can fail partway:
configuration writes, migrations, uploads, multi-step updates.

**Do not use when.** The contract allows partial output, such as a
streamed export. Test that contract instead, for example by checking
the marker for an incomplete file.

**Example.**

```python
def test_invalid_text_leaves_existing_file_unchanged(self):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "app.conf"
        path.write_text("port=80\n", encoding="utf-8")

        with self.assertRaises(ValueError):
            impl.write_config(path, "not a config")

        self.assertEqual(path.read_text(encoding="utf-8"), "port=80\n")
        self.assertEqual(
            sorted(p.name for p in Path(directory).iterdir()), ["app.conf"]
        )
```

**Cost removed.** Data loss on error paths.
`bug_config_truncates` empties the file before validating. It raises
the same `ValueError`, so the weak test that checks only the exception
passes, and this test fails on the file's content.

**Verify.**

1. Each failing-path test asserts the state of every resource the
   operation touches, including leftover temporary files.

## Deterministic interleaving

**Definition.** A test forces the problematic thread schedule with a
synchronization primitive (a barrier, an event, a latch) at a hook in
the code, instead of running the code many times and hoping the
schedule occurs.

**Use when.** A race is suspected or was reported: lost updates, a
check-then-act, double initialization.

**Do not use when.** The code has no seam for a hook, and adding one
is not allowed. Use a stress run with a recorded seed and report it as
probabilistic, or use a race detector (TSan, `go test -race`).

**Example.**

```python
def test_concurrent_deposits_are_not_lost(self):
    account = impl.Account()
    barrier = threading.Barrier(2)

    def both_read_before_either_writes():
        # With the lock held, the second thread cannot arrive: the wait
        # times out and the barrier breaks, which is the expected path.
        with contextlib.suppress(threading.BrokenBarrierError):
            barrier.wait(timeout=0.5)

    account.before_write = both_read_before_either_writes
    threads = [
        threading.Thread(target=account.deposit, args=(10,))
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive(), "deposit thread hung")

    self.assertEqual(account.balance, 20)
```

**Cost removed.** Races that appear once in a thousand runs. With
`bug_account_no_lock`, both threads read 0 before either writes, and
the balance ends at 10 on every run; the sequential weak test passes.
Compare `$debug-software-failures`, where an unforced race failed 0 of
200 runs.

**Verify.**

1. The test fails on the unsynchronized version every time. Run it 20
   times: `for i in $(seq 20); do VARIANT=bug_account_no_lock
   python3 -m unittest test_regressions.AccountRaceTests || true; done`.
1. Every wait in the test has a timeout, so a hang fails the test
   instead of stalling it.

## Injected clock and bounded waits

**Definition.** Code that depends on time takes a clock as a
parameter, so the test can set the time. A test that must wait for an
external condition polls it with a deadline and never sleeps for a
fixed time.

**Use when.**

- Expiry, timeouts, rate limits, and schedules: inject a clock.
- Asynchronous results from a real process or service: use a bounded
  wait.

**Do not use when.** The test's purpose is real timing, such as a
latency budget. That is a benchmark, not a unit test.

**Example.**

```python
class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_session_expires_exactly_at_ttl(self):
    clock = FakeClock()
    session = impl.Session(ttl=30, clock=clock)

    clock.now += 29.999
    self.assertFalse(session.expired)
    clock.now += 0.001
    self.assertTrue(session.expired)
```

A bounded wait for a real condition:

```python
def wait_until(predicate, timeout=5.0, interval=0.01):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval)
    raise AssertionError(f"condition not met within {timeout}s")
```

For browser tests, use the runner's retrying assertions instead
([Playwright][playwright]).

**Cost removed.**

- Slow tests: the TTL test runs in microseconds instead of sleeping for
  30 seconds.
- Flaky tests: a fixed sleep is too short on a loaded machine.

`bug_session_wall_clock` ignores the injected clock, and the test
catches it.

**Verify.**

1. `rg -n 'time\.sleep|Thread\.sleep|setTimeout' tests/` lists no fixed
   sleep used as synchronization.
1. The time-based test runs in under 0.1 s.

## Test isolation from shared state

**Definition.** Each test starts from a known state and does not
depend on which tests ran before it: fresh objects, per-test
directories, ports chosen by the operating system, reset registries.

**Use when.** Tests touch module globals, singletons, environment
variables, the current directory, or shared files and databases.

**Do not use when.** The state is an expensive read-only fixture,
shared on purpose, and no test mutates it.

**Example.** `RegistryTests.setUp` calls `impl.reset_registry()`.
The weak `WeakRegistry` has no reset:

```text
$ python3 -m unittest weak_examples.WeakRegistry
FAIL: test_b_first_registration_again
$ python3 -m unittest weak_examples.WeakRegistry.test_b_first_registration_again
OK
```

**Cost removed.** Failures that depend on test order: they appear when
a runner shuffles or parallelizes, and pass when the test runs alone.
See [pytest's flaky-test guidance][pytest-flaky].

**Verify.**

1. Run the suite in shuffled order and in parallel, and compare with a
   serial run. `go test -shuffle=on` prints the seed.
   [pytest-randomly][randomly] shuffles by default and prints the seed
   for `--randomly-seed`. Rust tests already run on parallel threads,
   and `cargo test -- --test-threads=1` gives the serial run.
1. `run_matrix.py --only Registry` shows the class failing and the
   single test passing.

## Flaky test diagnosis

**Definition.** A flaky test passes and fails on the same code.
Diagnose it in this order:

1. Record the failing run's seed, order, worker count, time, and logs.
1. Reproduce the failure.
1. Vary one source of nondeterminism at a time: order, parallelism,
   time, randomness, or an external service.

**Use when.** A test fails in CI and passes on rerun.

**Do not use when.** The failure reproduces every time. Then it is a
normal bug.

**Example.**

```sh
python3 -m unittest weak_examples.WeakRegistry          # fails
python3 -m unittest weak_examples.WeakRegistry.test_b_first_registration_again
# passes alone -> order dependence -> look for shared state
```

**Cost removed.** Retries that hide real races, and deleted tests that
were catching real bugs. A passing retry shows that the failure is
intermittent, not that it is fixed.

**Verify.**

1. The report names the source of nondeterminism and the experiment
   that isolated it.
1. Quarantine, retries, or a longer timeout need the owner's approval
   and keep the failure evidence. They are never the fix.

## Test retirement decision

**Definition.** For a test that breaks during behavior-preserving
changes, choose one decision:

- **retain:** it catches a real defect;
- **rewrite:** the requirement matters, but the test is coupled;
- **consolidate:** it duplicates another test;
- **remove:** it covers an obsolete requirement or only mirrors the
  code;
- **unresolved:** the evidence is missing.

A *change-detector test* repeats the implementation instead of
checking correctness ([Change-Detector Tests][detector]).

**Use when.** A refactor keeps breaking the same test, or someone asks
for a suite review.

**Do not use when.** The failure is unexplained. Diagnose it first;
deleting a failing test to go green is not retirement.

**Example.** `WeakFeeMirror` asserts `DELIVERY_FEES == [5]` and
`delivery_fee(10) == 5`. `alt_fees_tuple` stores `(5,)` with the same
fee, and the mirror fails. `DeliveryFeeTests` asserts only the fee, so
it passes the tuple and fails `bug_fee_six`.

The mirror, from `assets/examples/behavior/weak_examples.py`:

```python
class WeakFeeMirror(unittest.TestCase):
    """Mirrors private storage: fails alt_fees_tuple although the fee is
    right."""

    def test_fee_storage_and_value(self):
        self.assertEqual(subjects.DELIVERY_FEES, [5])
        self.assertEqual(impl.delivery_fee(10), 5)
```

The retained test, from [`test_regressions.py`][regressions]:

```python
class DeliveryFeeTests(unittest.TestCase):
    def test_flat_fee_for_any_distance(self):
        for distance in (0, 10, 500):
            with self.subTest(distance=distance):
                self.assertEqual(impl.delivery_fee(distance), 5)
```

Run locally from `assets/examples/behavior/`:

```sh
python3 run_matrix.py --only 'alt_fees_tuple :: test_regressions'
# ok   alt_fees_tuple :: test_regressions: passes
python3 run_matrix.py --only 'bug_fee_six'
# ok   bug_fee_six :: test_regressions: fails test_flat_fee_for_any_distance
```

`python3 run_matrix.py --only 'alt_fees_tuple :: weak'` reports that
`WeakFeeMirror` fails `test_fee_storage_and_value` on the tuple.

| Test | Decision | Retained protection |
| --- | --- | --- |
| `WeakFeeMirror` storage assert | remove | `DeliveryFeeTests` checks the fee |
| `WeakBasket._items` | rewrite | `BasketTests` value assertion |
| mocked vs real-store duplicate | retain both | different boundaries |

**Cost removed.** Test edits on every refactor that catch no bug. The
evidence: the mirror failed a correct change, and the retained test
still fails a wrong fee.

**Verify.**

1. For each removed test, name the test that still fails the defect it
   covered, and show that it fails on a mutant.
1. The retained tests pass on the refactored code and fail on a fault.

[regressions]: ../assets/examples/behavior/test_regressions.py
[playwright]: https://playwright.dev/docs/best-practices
[randomly]: https://pypi.org/project/pytest-randomly/
[pytest-flaky]: https://docs.pytest.org/en/stable/explanation/flaky.html
[detector]: https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html
