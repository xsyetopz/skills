# Test design

## Contents

- [Expected values](#expected-values)
- [Inputs](#inputs)
- [Layer](#layer)
- [Doubles](#doubles)
- [Coupling](#coupling)
- [Packages, hosts, and hardware](#packages-hosts-and-hardware)

## Expected values

- Take the expected value from the contract: a requirement, standard,
  issue, or spec vector. The code under test, a copy of its formula, and
  an existing snapshot are not sources.
- Encoders, parsers, and serializers: assert published vectors, not a
  round trip, because a round trip passes when encode and decode are wrong
  in matching ways.
- Golden files: normalize only what varies (timestamps, temporary paths,
  ordering) and review each diff by hand. Regenerating a snapshot to get
  green accepts the bug.
- One behavior per test, with the action visible in the test body (not
  hidden in a fixture), so a failure names one rule. For rules about
  sequences (close and reopen, retry, undo), keep the history in the test:
  run the steps and assert the final state.

## Inputs

- Equivalence classes and their boundaries: for a limit `N` test `N - 1`,
  `N`, `N + 1`, plus empty, zero, negative, and maximum values. Off-by-one
  faults live exactly there.
- Several interacting conditions: write a decision table and test each
  row. Workflow or protocol states: cover each transition, including the
  illegal ones.
- Large input spaces and laws (round trip, idempotence, ordering,
  invariants): see [generative](generative.md).

## Layer

Map each claim to the smallest layer that can observe it: unit,
integration, contract, end to end, installed package, host, or hardware.
Do not use an end-to-end test for a claim a unit test can see
([Just Say No to More End-to-End Tests][e2e]).

## Doubles

- Replace only collaborators that are slow, dangerous, unavailable, or
  nondeterministic. Use the real object for a dict, a pure function, or a
  value object, and never mock the unit under test.
- Roles ([Meszaros][meszaros]): dummy fills a parameter, stub returns fixed
  answers, spy records calls, mock checks expectations, fake is a working
  simplification such as an in-memory store. A class named `Mock` does not
  say which role it plays; see [Mocks Aren't Stubs][fowler].
- Engine semantics (SQL constraints, collation, transaction isolation,
  `rename`, TLS) belong to the engine: test them on an isolated real
  instance, not on a hand-written fake. Test pure policy that only calls
  the engine with a stub, and the adapter separately.
- Assert the outcome, not the call sequence, when the collaborator is a
  replaceable detail. Assert the exact call, and its absence where
  forbidden, only when the effect is the contract (a message sent, a write
  made).

## Coupling

- Test through the operation consumers call. Tests tied to private helpers,
  their names, or source text break on refactors that change no behavior
  ([Overspecified Software][overspecified]).
- Assert the value the contract promises, not the storage that produces it.
- Docs, prompts, and READMEs: test what the text makes a program do, or
  the machine-read part (schema, frontmatter key, parsed config). Do not
  assert sentences.
- Structural rules: compute an agreed dependency rule from the code
  ("production code never imports test code", [ArchUnit][archunit] on
  Java), not a frozen list of class names.

## Packages, hosts, and hardware

- Packaged artifacts: build with the packaging command (`python -m build`,
  `npm pack`, `cargo package`), never one that tags or publishes, install
  into a clean environment, and run the tests from outside the checkout, so
  local imports and files cannot hide a missing data file or entry point
  ([src layout][src-layout]).
- Behavior that exists only inside a host (editor extension activation,
  contribution points, permission prompts): run the real host, headless if
  possible. Pure-logic changes need only a unit test.
- Hardware and firmware: label each result with its layer (host unit test,
  simulator, HDL simulation, hardware-in-the-loop, physical measurement). A
  build, a flash, or test discovery is not a behavior check. Do not flash
  devices, change fuses or voltages, or call live services without
  explicit approval; run the narrower layer and say so.

[e2e]: https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html
[meszaros]: https://www.informit.com/content/images/9780131495050/samplechapter/0131495054_CH23.pdf
[fowler]: https://martinfowler.com/articles/mocksArentStubs.html
[overspecified]: https://test-smell-catalog.readthedocs.io/en/latest/Code%20related/In%20association%20with%20production%20code/Overspecified%20Software.html
[archunit]: https://www.archunit.org/userguide/html/000_Index.html
[src-layout]: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
