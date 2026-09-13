# Interaction testing and doubles

Load this reference when selecting collaborators or deciding whether a message,
call count, or ordering assertion is contractual.

## Separate the dimensions

In [Fowler's terminology][mocks], **state verification** observes results or
resulting state; **behavior verification** observes interactions. This skill's
phrase *behavioral contract* includes either when required by a consumer.
Neither verification style inherently focuses on contracts: state assertions
can freeze private storage, and interaction assertions can enforce real rules.

Black-box reasoning concerns the authority for cases and expectations.
Sociable/solitary testing concerns real versus replaced collaborators within the
chosen unit; [Fowler's Unit Test discussion][unit] treats both as unit testing.
Classicist/mockist TDD concerns design and collaboration style: classicists
generally favor real collaborators when practical, while mockists more readily
specify collaborations through doubles. These dimensions overlap but are not
interchangeable labels for good and bad tests.

Prefer inexpensive real collaborators and observable outcomes for replaceable
internal collaboration. [Seemann][seemann] shows why indiscriminate interaction
verification can make refactoring brittle. Do not mechanically eliminate all
interactions or redesign production solely to satisfy this preference.

## Choose a double for a named need

[Meszaros's accessible publisher chapter][meszaros] distinguishes test-double
roles: a stub supplies controlled responses, a spy records interactions, a mock
verifies expectations, and a fake supplies a working simplified implementation.
A dummy merely fills an unused parameter. Framework names do not reliably tell
you which role an object plays in a particular test.

Use doubles to control errors, unavailable services, time, or dangerous effects.
Keep their behavior consistent with the real boundary. A fake database does not
prove SQL constraints, transactions, or migrations. Verify adapters with the
real dependency in isolated integration checks when those semantics matter.

## Incidental call sequence versus outcome

**Deciding condition:** `price_for("book", catalog)` returns 20. Lookup count
and access order are not contractual; `catalog` is an inexpensive mapping.

### RED — DO NOT: require the current lookup choreography

```python
from unittest.mock import MagicMock, call

catalog = MagicMock()
catalog.__contains__.return_value = True
catalog.__getitem__.return_value = 20
price_for("book", catalog)
assert catalog.mock_calls == [
    call.__contains__("book"), call.__getitem__("book")
]
```

The test rejects direct indexing and misses a wrong return after those calls.

### GREEN — DO: observe the returned price

```python
catalog = {"book": 20}

price = price_for("book", catalog)

assert price == 20
```

This leaves lookup mechanics replaceable without losing the required value.

Check: GREEN passes membership-then-index and direct-index implementations.
Return zero after performing RED's exact calls: RED passes, GREEN fails.
Direct indexing preserves the stated case but breaks RED's call sequence.

## Required messages and forbidden effects

**Deciding condition:** `notify(address, allowed, send)` returns whether sending
was accepted. For allowed recipients it must invoke the outbound boundary once
with `(address, "ready")`; otherwise it must not invoke it at all. The test uses
synthetic addresses and a spy, never a live sender.

### RED — DO NOT: check acceptance alone

```python
from unittest.mock import Mock

for allowed in (True, False):
    send = Mock()
    assert notify("a@example.invalid", allowed, send) is allowed
```

A missing notification or a forbidden send can leave both return values right.

### GREEN — DO: verify the contractual boundary effects

```python
from unittest.mock import Mock

for allowed in (True, False):
    send = Mock()

    accepted = notify("a@example.invalid", allowed, send)

    assert accepted is allowed
    if allowed:
        send.assert_called_once_with("a@example.invalid", "ready")
    else:
        send.assert_not_called()
```

In a real suite, these two cases may use the existing runner's parameterization.
The branch reflects different required effects, not production logic copied
into the oracle; the exact message is independently specified above.

Check: correct guard-clause and conditional implementations pass GREEN. Missing
send, duplicate send, wrong message, and send-when-denied variants fail the
respective interaction assertions but pass RED when their returns remain right.

Keep ordering assertions when order itself is required, such as authorization
before a write or commit before publication. Assert only the necessary relation,
not the entire internal trace. Mock verification establishes a call at this
boundary; it cannot establish actual message delivery or persistence.
Use real-adapter evidence for those separate claims.

[mocks]: https://martinfowler.com/articles/mocksArentStubs.html
[unit]: https://martinfowler.com/bliki/UnitTest.html
[seemann]:
  https://blog.ploeh.dk/2019/02/18/from-interaction-based-to-state-based-testing/
[meszaros]: https://www.informit.com/content/images/9780131495050/samplechapter/0131495054_CH23.pdf
