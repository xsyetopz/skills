# Behavioral scenarios, AAA, and TDD

Load this reference for scenario organization, phase clarity, test-first work,
or tests whose behavior genuinely depends on a sequence of transitions.

## Structure reasoning, not syntax

- **Arrange:** establish necessary inputs, dependencies, and starting state.
- **Act:** exercise one logical target behavior, not necessarily one statement.
- **Assert:** verify its consequences with independent expectations. Several
  assertions may be necessary to establish one outcome and forbidden effects.

[Arrange–Act–Assert][aaa] provides a useful default. Prefer recognizable layout
and names; literal AAA comments are optional. Never test labels, formatting,
statement counts, or a mandatory naming grammar. Public operations may establish
setup, but do not bury the target action inside a fixture.

[Given–When–Then][gwt] describes preconditions, the behavior, and expected
consequences in scenario language. Four-Phase Test adds teardown to setup,
exercise, and verification; [Fowler's example][mocks] explains these phases.
Use context managers or the runner's cleanup hooks so resources are released
even after assertion failure. Teardown must not silently swallow failures.

Await asynchronous completion before asserting; use bounded waits for external
observable conditions rather than arbitrary sleeps. Exception assertions wrap
the target action; inspect required error details and preserved state afterward.
Parameterize cases sharing a rule, but keep their inputs and expected outcomes
independently understandable. Multi-transition handling below is this skill's
adaptation of stricter AAA advice, not a claim that the source prescribes it.

## Conditions and outcomes instead of method bundles

**Deciding condition:** `shipping(weight)` returns 0 for zero weight and 5 for
positive weight. The cases must remain independently diagnosable.

### RED — DO NOT: bundle every case because it uses one method

```python
def test_shipping():
    assert shipping(0) == 0
    assert shipping(2) == 5
```

The first failure prevents observing the second case in the same run.

### GREEN — DO: make the behaviors independently runnable

```python
def test_zero_weight_has_no_shipping_charge():
    assert shipping(0) == 0


def test_positive_weight_has_flat_shipping_charge():
    assert shipping(2) == 5
```

Check: make both outcomes wrong and run each test independently through the
runner. GREEN reports both failures; RED reaches only the zero-weight failure.
An existing parameterized-test facility is equally suitable. Names communicate
conditions, not mandatory syntax. This follows
[Test Behaviors, Not Methods][cases].

## Visible action and focused phases

**Deciding condition:** adding a book raises the cart total by 20; removing that
book returns it to zero. These are independently useful behaviors, not a
history-sensitive requirement.

### RED — DO NOT: hide the action and mix unrelated verification

```python
def prepared_cart():
    cart = Cart()
    cart.add("book")
    return cart


def test_cart():
    cart = prepared_cart()
    assert cart.total == 20
    cart.remove("book")
    assert cart.total == 0
```

Adding is hidden in a generic fixture; its failure prevents removal evidence.

### GREEN — DO: make each target action visible without AAA comments

```python
def test_adding_a_book_updates_total():
    cart = Cart()

    cart.add("book")

    assert cart.total == 20


def test_removing_a_book_clears_total():
    cart = Cart()
    cart.add("book")

    cart.remove("book")

    assert cart.total == 0
```

Public `add` is legitimate setup in the removal case. If setup itself is faulty,
diagnose that dependency rather than treating every failure as a removal defect.

Check: a removal-no-op mutant fails the removal assertion; an add-no-op mutant
fails the adding assertion. Both GREEN cases pass a list-to-counter refactor.
Manually identify each target action without opening a fixture; RED requires
opening `prepared_cart` to discover that it already exercised adding.

## Preserve necessary history

**Deciding condition:** after a connection succeeds once, closing and reopening
that same connection must succeed. Fresh connections do not reproduce this rule.

### RED — DO NOT: split away the history to enforce one call per test

```python
def test_open():
    connection = Connection()
    connection.open()
    assert connection.is_open


def test_close():
    connection = Connection()
    connection.open()
    connection.close()
    assert not connection.is_open
```

Both tests pass when reopening a previously closed connection is broken.

### GREEN — DO: keep the necessary transitions explicit

```python
def test_closed_connection_can_reopen():
    connection = Connection()
    connection.open()
    assert connection.is_open
    connection.close()
    assert not connection.is_open

    connection.open()

    assert connection.is_open
```

Check: a variant that refuses only the second open passes RED and fails GREEN's
last assertion. Boolean-backed and explicit-state implementations pass GREEN.
The earlier assertions establish that the required history actually occurred.

## Behavioral TDD, not a ritual

[TDD][tdd] selects a next example, makes it pass, and refactors. Start with a
small list of contractual scenarios, choose a discriminating case, and write
the test from the consumer's perspective. Demonstrate that the current code
lacks the required behavior. A missing API may initially cause a build failure;
make the test runnable and distinguish that from a demonstrated wrong result.
Import errors, broken setup, or unavailable credentials are not behavioral RED.

Implement the smallest sufficient change only within the authorized task. Verify
the example and nearby relevant cases; then refactor both production and tests
without freezing helpers, class layout, or the first algorithm. Add the next
example when it distinguishes another requirement, not merely another method.
In tests-only work, report missing behavior rather than silently fixing code.

Instructional RED/GREEN pairs in this package compare test designs, not these
TDD states. Their RED tests can pass while providing poor evidence. Neither a
passing GREEN example nor the practice of TDD proves complete coverage.

[aaa]:
  https://automationpanda.com/2020/07/07/arrange-act-assert-a-pattern-for-writing-good-tests/
[gwt]: https://martinfowler.com/bliki/GivenWhenThen.html
[mocks]: https://martinfowler.com/articles/mocksArentStubs.html
[cases]:
  https://testing.googleblog.com/2014/04/testing-on-toilet-test-behaviors-not.html
[tdd]: https://martinfowler.com/bliki/TestDrivenDevelopment.html
