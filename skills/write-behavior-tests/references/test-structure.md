# Test structure

How to shape one test so that its failure names one broken behavior,
its action is visible, and it keeps the history it depends on. Every example
is in [`assets/examples/behavior/`][behavior]. `run_matrix.py` runs it
against the reference implementation, conforming alternatives, and
deliberate faults (`VARIANT=...`), and checks which tests fail.
Everything was executed with Python 3.14.7 on macOS arm64.

## Contents

- One behavior per test
- Visible action: Arrange, Act, Assert
- Kept history for sequence rules
- Observed red, then green

## One behavior per test

**Definition.** Each test checks one rule of the contract, and its name
states the condition and the outcome. Parameterize cases that share a
rule and differ only in data (`subTest`, `pytest.mark.parametrize`,
`t.Run`), so a failure in one case does not hide the others
([Test Behaviors, Not Methods][behaviors]).

**Use when.** A test calls one function several times to check
different rules, such as a free tier and a paid tier, or valid input and
rejected input.

**Do not use when.** The asserts together establish one outcome, such
as the returned value plus the forbidden side effect of the same call.
Splitting them hides that both must hold together.

**Example.** From [`test_structure.py`][structure]:

```python
class ShippingTests(unittest.TestCase):
    def test_zero_weight_has_no_shipping_charge(self):
        self.assertEqual(impl.shipping(0), 0)

    def test_positive_weight_has_flat_charge(self):
        self.assertEqual(impl.shipping(2.5), 5)

    def test_negative_weight_is_rejected(self):
        with self.assertRaises(ValueError):
            impl.shipping(-1)
```

For the parameterized form (one rule, several inputs), see
`PercentageTests.test_boundaries_and_neighbors` in `test_oracles.py`,
where `subTest` reports each failing value separately.

**Cost removed.** Diagnosis time. With `VARIANT=bug_shipping_zero`,
only `test_zero_weight_has_no_shipping_charge` fails, and its name
says which rule broke. A bundled
`assert shipping(0) == 0; assert shipping(2) == 5` stops at the first
assert and leaves the later rules unchecked in that run.

**Verify.**

1. For each mutant, the runner reports exactly the tests named in
   `expectations.json`:
   `python3 run_matrix.py --only bug_shipping_zero`.
1. Each test name reads as a sentence about behavior, not a method name
   (`test_shipping`).

## Visible action: Arrange, Act, Assert

**Definition.** A test has three phases: Arrange (the inputs and the
starting state), Act (the one call under test), and Assert (the
consequences). The Act stays in the test body, not inside a fixture
([Arrange-Act-Assert][aaa]; Given-When-Then is the same shape in
scenario language, see [GivenWhenThen][gwt]).

**Use when.** Always; it is the default layout. It matters most when
setup calls the same API as the action, such as adding items before
testing removal.

**Do not use when.** Treating AAA as a syntax rule, for example by
requiring comments or one statement per phase. Several asserts in the
Assert phase are fine when they check one outcome.

**Example.**

```python
def test_removing_a_book_clears_total(self):
    cart = impl.Cart()
    cart.add("book")

    cart.remove("book")

    self.assertEqual(cart.total, 0)
```

`cart.add` is setup and `cart.remove` is the action. If a fixture
called `add` and the test asserted after both calls, the reader would
have to open the fixture to learn what ran.

**Cost removed.** Failures point at the action under test:
`bug_cart_remove_noop` fails only
`test_removing_a_book_clears_total`. Reviews are shorter, because a
reader can name the action without opening another function.

**Verify.**

1. For each test, a reviewer can name the Act line without opening
   another function.
1. A mutant of the action fails the test, and a mutant of setup-only
   code fails the setup's own test instead.

## Kept history for sequence rules

**Definition.** When a rule depends on an earlier sequence, the test
performs that sequence and asserts the intermediate states that prove
it happened, for example that a closed connection can reopen.

**Use when.** The contract names a history: reopen after close, retry
after failure, a second save after edit, undo after two edits.

**Do not use when.** Each step is an independent rule. Split those
tests, as in [one behavior per test](#one-behavior-per-test).

**Example.**

```python
def test_closed_connection_can_reopen(self):
    connection = impl.Connection()
    connection.open()
    connection.close()
    self.assertFalse(connection.is_open)

    connection.open()

    self.assertTrue(connection.is_open)
```

**Cost removed.** Bugs that appear only after a sequence.
`bug_connection_no_reopen` refuses only the second `open()`. It passes
the split tests `WeakConnection.test_open` and `test_close` in
`weak_examples.py` and fails this one.

**Verify.**

1. `python3 run_matrix.py --only no_reopen` shows the history test
   failing and `weak_examples.WeakConnection` passing.
1. The intermediate assertion (`assertFalse(connection.is_open)`)
   proves that the close happened before the reopen.

## Observed red, then green

**Definition.** Test-first work ([Canon TDD][tdd]) runs a new test
against code that lacks the behavior and records the failure. The
failure must come from the behavior (an assertion or the expected
exception), not from an import error or broken setup. Then make the
change and run the same test to green. Red and green name observed
runs, not intentions.

**Use when.**

- Adding behavior test-first.
- Writing a regression test for a reported bug: run it on the faulty
  version first.

**Do not use when.** The faulty version cannot run, for example
because it needs production-only data. Say so, and show the failure
another way: a mutant, or a historical commit in a disposable
worktree.

**Example.** Executed by `verify.sh`:

```text
$ VARIANT=bug_split_drops_empty python3 -m unittest \
    test_regressions.SplitRegressionTests
AssertionError: Lists differ: ['a', 'b'] != ['a', '', 'b']
FAILED (failures=1)
$ python3 -m unittest test_regressions.SplitRegressionTests
OK
```

`verify.sh` also rejects the red run if the log contains
`ImportError`, `ModuleNotFoundError`, or `NameError`.

**Cost removed.** Tests that never failed and so never showed they
detect anything. The red log is the evidence.

**Verify.**

1. The report quotes the red failure line (the assertion message) and
   the green result, for the same test id.
1. The red failure mentions the behavior, not setup.

[behavior]: ../assets/examples/behavior/
[structure]: ../assets/examples/behavior/test_structure.py
[behaviors]: https://testing.googleblog.com/2014/04/testing-on-toilet-test-behaviors-not.html
[aaa]: https://automationpanda.com/2020/07/07/arrange-act-assert-a-pattern-for-writing-good-tests/
[gwt]: https://martinfowler.com/bliki/GivenWhenThen.html
[tdd]: https://newsletter.kentbeck.com/p/canon-tdd
