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
