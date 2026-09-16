# Test boundaries and independent expected-result checks

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

## Select inputs from the contract

Before structuring a test, choose inputs using the contract:

- **Equivalence classes:** partition values expected to behave alike; select
  representatives from valid and invalid classes rather than many duplicates.
- **Boundary values:** for ordered partitions, test each limit and neighboring
  values. For an inclusive integer range 1–100, use 0, 1, 2, 99, 100, 101;
  missing or malformed input is a separate class, not a numeric neighbor.
- **Decision tables:** when conditions interact, enumerate feasible condition
  combinations and expected actions. For permission plus account state, test
  authorized/unauthorized against active/suspended rather than each flag alone.
- **State transitions:** when history matters, specify starting state, event,
  guard, next state, and effects. Exercise meaningful sequences and forbidden
  transitions; covering each state does not cover each transition.
- **Structural coverage:** use uncovered branches to locate missing behavioral
  evidence, not to invent a percentage target. Covered code can assert nothing.

Combine techniques only where they distinguish different defects. Derive
expected outcomes independently of the implementation. These techniques follow
the [ISTQB CTFL 4.0.1 syllabus][techniques], not a mandated test-case count.

Separate verification of specified behavior from validation of intended use.
User acceptance needs representative tasks and agreed stakeholder criteria; unit
or E2E success alone cannot establish that the product meets the need. Record
which claim a test supports and which acceptance remains unobserved.

## Derive expected results independently

Expected values should come from requirements, a normative standard, a reviewed
fixture, or an independent reference implementation. Copying the algorithm into
the expected-value calculation duplicates its mistakes. A round trip can catch
information loss but may miss a serializer and parser that share the same bug;
include independent standard vectors or an independently implemented consumer.

For example, a SemVer validator must reject non-ASCII numeric identifiers and
trailing characters even if its own regex currently accepts them. [SemVer's
grammar][semver] supplies the expected-result rule, not the current regex. Test
through the documented CLI as well as the relevant parsing boundary when exit
status and machine-readable output are part of the contract.

## Independent invoice result

**Deciding condition:** The invoice total is a contractual value that the test
must verify independently from its implementation. The reviewed requirement is
199 cents per item, quantity two, less a 49-cent invoice discount: 349 cents.

### Defect: copy the production calculation

```python
invoice = {"price": 199, "quantity": 2, "discount": 49}
assert total(invoice) == invoice["price"] * invoice["quantity"]
```

An implementation omitting the discount passes; this repeats its mistake.

### Correction: assert the independently reviewed result

```python
invoice = {"price": 199, "quantity": 2, "discount": 49}

assert total(invoice) == 349
```

The discount is observable without reimplementing the algorithm in the
expected-result calculation.

Check: in a disposable fixture, implement `total` with multiplication and then
with repeated addition, both subtracting the discount. corrected example passes
both. Omit the discount: corrected example fails with 398 instead of 349, while
defective example passes.

## Review snapshots semantically

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
[semver]: https://semver.org/
[pact]: https://docs.pact.io/
[packaging]:
https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
[techniques]: https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf
