# Acceptance criteria

Observations at the contract boundary that decide whether a requirement is
met. The worked criteria are in
[`export-cancellation-spec.md`](../assets/examples/export-cancellation-spec.md),
each with an executable test in
[`test_export_cancel.py`](../assets/examples/test_export_cancel.py).
`assets/examples/verify.sh` also breaks the implementation on purpose to
show that the tests catch it.

## Contents

- Given/When/Then criterion
- Criterion to test mapping
- Controlled interleavings
- Boundary values
- Observations, not implementation details
- Discrimination check

## Given/When/Then criterion

**Definition.** `AC-<ID> verifies REQ-<ID>[, ...]: Given <preconditions>,
when <one event>, then <observable results>.` It borrows the Gherkin
keywords ([Gherkin reference][gherkin]) but needs no Gherkin runner.

**Use when.** Any requirement; each needs at least one criterion.

**Do not use when.** One criterion would chain several events. Split it so
a failure points at one event.

**Example.**

```text
- AC-EXP-004 verifies REQ-EXP-005: Given export content that fails
  validation, when the job runs, then the job is failed, the error names
  the validation rule, no temporary file remains, and the destination is
  unchanged.
```

**Cost removed.** Requirements nobody knows how to accept.

**Verify.**

1. The checker reports requirements with no criterion, criteria that
   reference unknown requirements, and criteria without Given/When/Then.

## Criterion to test mapping

**Definition.** Each criterion becomes one automated test: its name
contains the criterion ID, its setup is the Given, its action is the When,
and its assertions are the Then.

**Use when.** The requirement is testable in code (almost always).

**Do not use when.** The criterion needs human judgment (visual design).
Name the reviewer and the checklist instead.

**Example.**

```python
def test_ac_exp_004_validation_failure(self) -> None:
    job = ExportJob(self.destination, b"not an export\n")
    job.run()
    self.assertEqual(job.state, "failed")
    self.assertIn("rule V1", job.error or "")
    self.assertFalse(job.temporary.exists())
    self.assertEqual(self.destination.read_bytes(), OLD)
```

**Cost removed.** Criteria that drift from tests.

**Verify.**

1. `rg -n 'def test_ac_' tests/` lists one test per criterion ID.

## Controlled interleavings

**Definition.** Test a race in a criterion by pausing one side at a
barrier (an event the test controls), performing the competing operation,
then releasing the paused side.

**Use when.** A criterion mentions concurrency or ordering.

**Do not use when.** You would use `sleep` to "probably" order events; the
test becomes flaky.

**Example.**

```python
at_barrier, release = threading.Event(), threading.Event()

def hold() -> None:
    at_barrier.set()
    release.wait(5)

job = ExportJob(self.destination, NEW, before_publish=hold)
writer = threading.Thread(target=job.run)
writer.start()
assert at_barrier.wait(5)
assert job.cancel() == "cancelled"
release.set()
writer.join(5)
```

**Cost removed.** Flaky concurrency tests.

**Verify.**

1. Run the test 100 times (`for i in $(seq 100); do python3 test.py ||
   break; done`); it never fails.

## Boundary values

**Definition.** For each range in a requirement, write criteria at the
minimum, the maximum, just inside, and just outside, plus empty input.

**Use when.** A requirement contains limits (sizes, counts, durations).

**Do not use when.** The input has no ordering or limit.

**Example.** For "export names are 1 to 255 bytes": criteria for 0, 1,
255, and 256 bytes, and for a 255-byte name whose last character is
multi-byte.

**Cost removed.** Off-by-one defects.

**Verify.**

1. Each numeric limit in the spec has criteria on both sides of it.

## Observations, not implementation details

**Definition.** Then-clauses assert what a caller or operator can observe
(responses, stored data, files, emitted events), not internal calls or log
lines, unless that interaction is itself the contract.

**Use when.** Writing any Then-clause.

**Do not use when.** No exception. "No errors were logged" or "returns
200" alone never proves the work was done.

**Example.** "The destination holds the previous bytes" instead of
"`os.replace` was not called".

**Cost removed.** Tests that pass while the behavior is wrong.

**Verify.**

1. Each Then-clause names a caller-visible result.

## Discrimination check

**Definition.** Break the implementation so it violates one requirement,
and confirm that the matching acceptance test fails.

**Use when.** The tests for a requirement are written.

**Do not use when.** No exception for a critical requirement.

**Example.** `verify.sh` replaces the cancelled-state check with `if
False:`, so a cancelled job still publishes; `test_ac_exp_001` fails.

**Cost removed.** Tests that cannot fail.

**Verify.**

1. `sh assets/examples/verify.sh` prints `PASS AC-EXP-001 fails when a
   cancelled job still publishes`.

[gherkin]: https://cucumber.io/docs/gherkin/reference/
