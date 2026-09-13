# Test boundaries and independent oracles

## Select evidence for the claim

Start with a compact mapping from each changed behavior or risk to an observable
outcome and the test boundary that can observe it. Reuse existing coverage when
it already distinguishes the defect; do not multiply tests because a file
changed.

- Unit/component: decision rules and transformations with controlled inputs. Use
  real collaborators within the component when they are cheap and relevant.
- Integration: interactions whose semantics belong to the actual database,
  filesystem, network stack, protocol implementation, or host API.
- Contract/compatibility: a supported producer and consumer agree on fields,
  errors, optionality, encodings, and behavior across supported versions.
- Functional/E2E: representative user operations through the deployed or
  packaged entrypoint, including the critical wiring lower-level tests cannot
  observe.
- Install/package: the distributed artifact contains its resources and can be
  consumed outside the source checkout on a supported target.

Balance confidence, runtime, isolation, and diagnosis cost. [Google's testing
feedback-loop discussion][feedback] motivates smaller focused tests plus
selected integration and E2E coverage. Its illustrative ratios are not universal
quotas. Do not make every test E2E or assert a fixed pyramid for every
repository.

## Prefer `Arrange`, `Act`, `Assert` for one operation

For a functional test with one operation, use `Arrange`, `Act`, `Assert` in that
order:

1. **`Arrange`:** inputs, dependencies, state, and the target.
1. **`Act`:** once on the behavior under test.
1. **`Assert`:** the resulting values, effects, errors, and forbidden effects.

`Given`, `When`, `Then` is an equivalent form. State-machine, workflow, and
interaction scenarios can require multiple named transitions; keep each
transition and expected state explicit instead of pretending the scenario has
one action.

### Alternating actions and assertions

**Deciding condition:** The test is intended to verify one cart behavior.

```python
def test_cart_lifecycle():
    cart = Cart()
    cart.add("book")
    assert cart.total == 20
    cart.remove("book")
    assert cart.total == 0
```

Why it fails:

- the test contains two target actions and two behaviors;
- a failure does not identify whether adding or removing violated its contract;
- the second assertion depends on the first operation's incidental state.

### Keep one focused Act

```python
def test_adding_a_book_updates_the_total():
    # Arrange
    cart = Cart()

    # Act
    cart.add("book")

    # Assert
    assert cart.total == 20
```

Why it works:

- setup, target behavior, and verification are distinct;
- the test fails specifically when adding does not update the total;
- removal belongs in its own Arrange, Act, Assert test.

Check:

- read the test top to bottom and identify exactly one transition from `Arrange`
  to `Act` and one transition from `Act` to `Assert`.

This enforced structure follows [Automation Panda's description of
`Arrange-Act-Assert`][aaa].

## Make the oracle independent

Expected values should come from requirements, a normative standard, a reviewed
fixture, or an independent reference implementation. Copying the algorithm into
the expected-value calculation duplicates its mistakes. A round trip can catch
information loss but may miss a serializer and parser that share the same bug;
include independent standard vectors or an independently implemented consumer.

For example, a SemVer validator must reject non-ASCII numeric identifiers and
trailing characters even if its own regex currently accepts them. [SemVer's
grammar][semver] supplies the oracle, not the current regex. Test through the
documented CLI as well as the relevant parsing boundary when exit status and
machine-readable output are part of the contract.

Assertions should observe values, persisted effects, visible behavior, errors,
and absence of forbidden effects. “The mock was called” is sufficient only when
that interaction is itself the external contract. Do not assert private helper
names, incidental ordering, line counts, or types already guaranteed by the
compiler. Do not expose private production APIs just to reach them from tests.

### Expected value copied from production logic

**Deciding condition:** The invoice total is a contractual value that the test
must verify independently from its implementation.

```ts
expect(total(invoice)).toBe(
  invoice.lines.reduce((sum, line) => sum + line.price * line.quantity, 0),
);
```

Why it fails:

- the assertion duplicates the same calculation as `total`;
- the same omitted discount or rounding rule can make both sides wrong;
- refactoring production and test code together can preserve the defect.

### Assert a reviewed contractual result

```ts
const invoice = {
  lines: [{ price: 199, quantity: 2 }],
  discount: 49,
};

expect(total(invoice)).toBe(349);
```

Why it works:

- the expected value is explicit and independent of the implementation;
- the fixture makes the discount rule observable;
- changing `total` to ignore `discount` makes this test fail.

Check:

- apply that controlled faulty change in an isolated copy and confirm this test
  fails for the expected-value assertion.

Snapshots are useful for intentionally stable structured or rendered output.
Review semantic differences before updating a golden file. Normalize only fields
that are genuinely irrelevant; normalizing away identifiers, order, or errors
can conceal the failure. Prefer targeted assertions when a full snapshot would
mostly capture incidental formatting or platform noise.

## Keep external semantics real

Mock the remote boundary when testing deterministic policy; exercise its real
adapter separately. An in-memory database substitute may not reproduce
production SQL dialects, constraints, isolation, or migrations. Use the actual
engine for those claims with isolated databases and bounded lifecycle
management.

[Pact][pact] supports consumer/provider contract verification. It can help at
independently deployed boundaries; a provider still needs to verify the
contract, and a passing schema check is not evidence of business effects or
authorization. Use an existing OpenAPI/Protobuf contract and compatible
validators/generators when the project already has them, not a second invented
contract format.

For packages, build with the established release process, install into a fresh
consumer environment, and exercise public entrypoints and required resources.
Run outside the checkout so local imports or assets cannot mask missing package
contents. [Python packaging's layout discussion][packaging] illustrates this
distinction; use the corresponding native workflow for the target ecosystem.

For editor plug-ins or platform APIs, a pure-core test does not verify host
activation, resource packaging, permissions, unload behavior, or UI interaction.
Keep a small actual-host check when those are the changed requirements. Report
an unavailable host as unverified rather than replacing it with a syntax check.

[feedback]:
  https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html
[aaa]:
  https://automationpanda.com/2020/07/07/arrange-act-assert-a-pattern-for-writing-good-tests/
[semver]: https://semver.org/
[pact]: https://docs.pact.io/
[packaging]:
  https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
