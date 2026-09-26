# Coupling and test doubles

How to keep tests on the contract instead of the current implementation,
and when to replace a collaborator. The examples are in
[`test_doubles.py`][doubles] and [`test_architecture.py`][arch]. The weak
counterparts are in [`weak_examples.py`][weak]. `run_matrix.py` runs
both against conforming alternatives (`alt_*`) and faults (`bug_*`).

## Contents

- Public consequence, not private helper
- Value, not representation
- Architecture rule, not frozen declarations
- Test double roles
- Outcome, not call choreography
- Required and forbidden effects
- Real engine for engine semantics

## Public consequence, not private helper

**Definition.** Test the operation that consumers call, through its
observable result. Helpers, their names, and the source text may
change unless a requirement fixes them; tests tied to them are
*Overspecified Software* ([Test Smell Catalog][overspecified]).

**Use when.** A test imports a private helper (`_trim`), inspects
source text, or asserts that a helper was called.

**Do not use when.** The source is itself the product (a code
generator or formatter), or the team agreed on a structural rule (see
the [architecture card](#architecture-rule-not-frozen-declarations)).

**Example.**

```python
class RenderNameTests(unittest.TestCase):
    def test_surrounding_whitespace_is_removed(self):
        self.assertEqual(impl.render_name("  Ada \n"), "Ada")
```

The weak version checks `"_trim" in getsource(render_name)` and
`_trim(" Ada ") == "Ada"`.

**Cost removed.** The weak test fails in both directions:

- It passes `bug_render_ignores_trim`, which calls `_trim` and then
  returns the untrimmed input.
- It fails `alt_render_inline`, a correct refactor.

The public test does the reverse on both.

**Verify.**

1. `python3 run_matrix.py --only render` shows the public test failing
   only on the bug, and the weak test failing only on the refactor.

## Value, not representation

**Definition.** Assert the value that the contract promises, not the
internal storage that produces it.

**Use when.** A test reads a private attribute (`_items`, `_cache`) or
asserts a container type.

**Do not use when.** The collection itself is what the function
returns, with a promised order or type.

**Example.**

```python
def test_count_reports_each_addition(self):
    basket = impl.Basket()
    basket.add("book")
    basket.add("book")

    self.assertEqual(basket.count("book"), 2)
```

**Cost removed.** False alarms and missed bugs. The weak
`basket._items == ["book", "book"]` errors on `alt_counting_basket`,
which stores a Counter correctly, and passes `bug_basket_counts_once`,
which stores the list but reports 1.

**Verify.**

1. `rg -n '\._[a-z]' tests/` lists no private attribute reads except
   those the report justifies.
1. The matrix shows the value test passing the alternative
   representation.

## Architecture rule, not frozen declarations

**Definition.** A structural test computes an agreed dependency rule
from the code, for example "production code never imports test code".
It does not snapshot class or module names. Java projects can use
[ArchUnit][archunit] for layer and cycle rules.

**Use when.** An agreed architecture rule exists and was violated
before, or reviews enforce it by hand.

**Do not use when.** The "rule" is the current list of classes.
Freezing it rejects allowed refactors and misses forbidden
dependencies.

**Example.**

```python
def violations(path: Path) -> set[str]:
    return {
        name
        for name in imported_modules(path)
        if name in TEST_MODULES or name.startswith(("test_", "weak_"))
    }


class ArchitectureTests(unittest.TestCase):
    def test_production_code_does_not_import_tests(self):
        self.assertEqual(violations(HERE / "subjects.py"), set())
```

`test_rule_detects_a_forbidden_import` writes a probe file that
imports `harness`, and asserts that the rule reports it.

**Cost removed.** Forbidden dependencies that slip past review. The
probe shows that the check detects one.

**Verify.**

1. The rule has a test that proves it can fail, like the probe above.
1. The report names the authority for the rule: an ADR, AGENTS.md, or
   a review decision.

## Test double roles

**Definition.** A test double replaces a collaborator. The roles, from
[Meszaros's catalog][meszaros]:

- **dummy:** fills an unused parameter.
- **stub:** returns fixed answers.
- **spy:** records calls for later assertions.
- **mock:** has expectations and checks them.
- **fake:** a working, simplified implementation, such as an in-memory
  store.

A mocking library's class name, such as `Mock`, does not say which
role an object plays. [Mocks Aren't Stubs][fowler] contrasts state and
behavior verification.

**Use when.** The real collaborator is slow, unavailable, dangerous
(sends email, charges money), or nondeterministic (time, randomness),
or the test needs an error that the real one cannot be made to
raise.

**Do not use when.**

- The collaborator is cheap and deterministic, such as a dict, a pure
  function, or a value object. Use the real one.
- The claim is about the collaborator's own semantics, such as SQL
  constraints or file system errors. Use the
  [real engine](#real-engine-for-engine-semantics).

**Example.** The same suite uses three roles:

- a **spy** (`Mock()` passed as `send`, asserted afterwards) in
  `NotifyTests`;
- a **stub** clock (`FakeClock`, whose `now` the test sets) in
  `SessionTests`;
- a real in-memory SQLite database in `UsersTests`, which is the engine
  itself, not a fake.

The spy, from [`test_doubles.py`][doubles]:

```python
class NotifyTests(unittest.TestCase):
    def test_allowed_address_gets_exactly_one_ready_message(self):
        send = Mock()

        accepted = impl.notify("a@example.invalid", True, send)

        self.assertIs(accepted, True)
        send.assert_called_once_with("a@example.invalid", "ready")
```

The stub clock, from `assets/examples/behavior/test_regressions.py`:

```python
class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class SessionTests(unittest.TestCase):
    def test_session_expires_exactly_at_ttl(self):
        clock = FakeClock()
        session = impl.Session(ttl=30, clock=clock)

        clock.now += 29.999
        self.assertFalse(session.expired)
        clock.now += 0.001
        self.assertTrue(session.expired)
```

**Cost removed.** Slow, dangerous, or flaky collaborators. The session
test needs no `sleep`, and `test_session_expires_exactly_at_ttl` runs
in microseconds.

**Verify.**

1. Each double in the diff has a one-line reason naming the property
   of the real collaborator it avoids.
1. Each double matches the real collaborator for the cases used, and
   the real adapter has its own integration test.

## Outcome, not call choreography

**Definition.** When a collaborator is a replaceable detail, assert the
result, not the exact sequence of calls made to it.

**Use when.** The test asserts `mock_calls`, call order, or call counts
on a collaborator whose call pattern no requirement fixes.

**Do not use when.** The calls are the contract. See
[required effects](#required-and-forbidden-effects).

**Example.**

```python
def test_listed_price_is_returned(self):
    self.assertEqual(impl.price_for("book", {"book": 20}), 20)
```

The weak version passes a `MagicMock` catalog and asserts
`[call.__contains__("book"), call.__getitem__("book")]`.

**Cost removed.** Refactoring breakage and missed bugs. The weak test
fails `alt_price_direct`, which indexes directly and is correct, and
passes `bug_price_zero`, which makes the exact calls and returns 0.
The outcome test does the opposite. [Seemann][seemann] shows the same
refactoring cost.

**Verify.**

1. `rg -n 'mock_calls|assert_has_calls|call_count' tests/` lists each
   interaction assertion with its requirement.

## Required and forbidden effects

**Definition.** When sending a message, writing, or calling a boundary
is the required behavior, assert the effect exactly, and assert its
absence where it is forbidden.

**Use when.** The contract names an outbound effect: a notification, a
payment, an audit record, a publish-after-commit order.

**Do not use when.** The effect is incidental, such as internal
logging or a cache fill.

**Example.**

```python
def test_allowed_address_gets_exactly_one_ready_message(self):
    send = Mock()

    accepted = impl.notify("a@example.invalid", True, send)

    self.assertIs(accepted, True)
    send.assert_called_once_with("a@example.invalid", "ready")


def test_denied_address_gets_no_message(self):
    send = Mock()

    accepted = impl.notify("a@example.invalid", False, send)

    self.assertIs(accepted, False)
    send.assert_not_called()
```

**Cost removed.** Missing or forbidden effects that return values
alone hide. `bug_notify_never` and `bug_notify_when_denied` both return
the right booleans and pass `WeakNotify`; each fails one of these
tests. The spy proves only that the call reached this boundary.
Delivery needs a separate integration check.

**Verify.**

1. For each effect, one test asserts one call with the exact
   arguments, and one asserts no call where the effect is forbidden.
1. When order matters, assert only the required relation, such as
   commit before publish, not the full trace.

## Real engine for engine semantics

**Definition.** Test behavior that belongs to a database, file system,
protocol stack, or host API against that engine: constraints,
collation, isolation, `rename` semantics, TLS. Use an isolated instance
of the engine, not a hand-written fake.

**Use when.** The claim depends on the engine: uniqueness, foreign
keys, case-insensitive collation, transactions, file permissions.

**Do not use when.** The logic under test is pure policy that only
calls the engine. Test the policy with a stub, and the adapter
separately.

**Example.**

```python
class UsersTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)

    def test_email_differing_only_in_case_is_rejected(self):
        users = impl.Users(self.db)
        users.add("Ada@example.invalid")

        with self.assertRaises(sqlite3.IntegrityError):
            users.add("ada@example.invalid")
```

**Cost removed.** Constraint bugs that a dict fake cannot show.
`bug_users_case_sensitive` drops `COLLATE NOCASE`. It passes
`WeakUsers`, which checks only the returned ids, and fails here because
no `IntegrityError` is raised. When production uses another engine,
such as PostgreSQL, run that engine in a container: SQLite collation
does not prove PostgreSQL behavior.

**Verify.**

1. The test uses the same engine and version as production, or the
   report states the difference.
1. Each engine instance is created per test and closed with
   `addCleanup` or a fixture teardown.

[doubles]: ../assets/examples/behavior/test_doubles.py
[arch]: ../assets/examples/behavior/test_architecture.py
[weak]: ../assets/examples/behavior/weak_examples.py
[overspecified]: https://test-smell-catalog.readthedocs.io/en/latest/Code%20related/In%20association%20with%20production%20code/Overspecified%20Software.html
[archunit]: https://www.archunit.org/userguide/html/000_Index.html
[meszaros]: https://www.informit.com/content/images/9780131495050/samplechapter/0131495054_CH23.pdf
[fowler]: https://martinfowler.com/articles/mocksArentStubs.html
[seemann]: https://blog.ploeh.dk/2019/02/18/from-interaction-based-to-state-based-testing/
