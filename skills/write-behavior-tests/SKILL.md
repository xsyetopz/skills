---
name: write-behavior-tests
description: >-
  Writes, reviews, and retires behavior tests: independent expected values,
  boundaries, test doubles versus real dependencies, regressions seen failing
  first, deterministic time and races, property and mutation testing. Use when
  adding or judging tests.
---

# Write Behavior Tests

A test is useful when it fails on a meaningful fault and passes every
implementation that meets the contract. Every card is backed by
`assets/examples/`, where one suite runs against the reference code,
conforming alternatives (`alt_*`), and deliberate faults (`bug_*`).
`run_matrix.py` checks that exactly the named tests fail, and weak
versions of each test show which fault they miss.

## Workflow

1. Write down the contract for the change: inputs, outputs, errors,
   state transitions, effects that must happen, and effects that must
   not. Name its authority: a requirement, a standard, the issue, or
   the user. A user's guessed cause, the current output, and an
   existing snapshot are evidence, not expected values.
1. Map each claim to the smallest layer that can observe it: unit,
   integration, contract, end to end, package, host, or hardware
   ([boundary selection][layers]).
1. Choose inputs by technique: classes and boundaries, a decision
   table, transitions, standard vectors, or properties.
1. Write each test. One behavior, a visible action, and an expected
   value from an independent source.
1. Run it where the behavior is missing: the faulty commit, a mutant,
   or before the change. Record the failure line and check that it
   comes from the assertion, not from setup
   ([observed red][red]).
1. Make the change or fix, then rerun: the test, its neighbors, and a
   conforming alternative when one exists.
1. For changed functions, run `scripts/mutate.py`. Classify each
   survivor as a missing test, a weak assertion, or an equivalent
   mutant.
1. Report each claim with its layer, the commands, their results, and
   what was not run.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| One test checks several rules | [One behavior per test][one] |
| Action hidden in a fixture | [Arrange, Act, Assert][aaa] |
| Bug only after close/reopen, retry, undo | [Kept history][history] |
| Test-first, or proving a regression test | [Observed red][red] |
| Expected value computed like the code | [Independent expected result][oracle] |
| Ranges, sizes, off-by-one | [Classes and boundaries][bounds] |
| Several interacting conditions | [Decision table][table] |
| Workflow or protocol states | [Transitions][transitions] |
| Encoder, parser, serializer | [Standard vectors][vectors] |
| Snapshot or golden files | [Golden output][golden] |
| Test reads private helpers or fields | [Public consequence][public], [value][value] |
| Structural or layering rule | [Architecture rule][arch] |
| Choosing a mock, stub, spy, or fake | [Double roles][roles] |
| Test asserts call order or counts | [Outcome][outcome], [required effects][effects] |
| SQL constraints, file system, host APIs | [Real engine][engine] |
| Laws over large input spaces | [Property][property], [stateful model][stateful] |
| Parsers of untrusted input | [Fuzzing and corpus][fuzz], [sanitizers][sanitizer] |
| "Are these tests good enough?" | [Mutation testing][mutation] |
| Bug fix | [Regression reproducer][repro], [persisted effects][persisted] |
| Race or lost update | [Deterministic interleaving][race] |
| Timeouts, expiry, sleeps | [Injected clock and bounded waits][clock] |
| Passes alone, fails in suite | [Isolation][isolation], [flaky diagnosis][flaky] |
| Test breaks on every refactor | [Retirement decision][retire] |
| Data file or entry point in the artifact | [Installed package][package] |
| Editor or IDE plugin behavior | [Host-dependent][host] |
| RTL, firmware, device claims | [HDL testbench][hdl], [evidence layers][layers-hw] |

## Rules

- An expected value never comes from running the code under test, or
  from the same formula as the code.
- A test is not reported as protecting a behavior until it has been
  seen failing on a fault that breaks that behavior.
- Do not weaken assertions, skip tests, add retries, lengthen timeouts,
  or regenerate snapshots to get a green run. Diagnose instead, and
  report unexplained failures.
- Doubles only replace collaborators that are slow, dangerous,
  unavailable, or nondeterministic. Engine semantics are tested on the
  engine.
- Every wait has a deadline. Fixed sleeps are not synchronization.
- In a tests-only task, do not fix production code. Report the failing
  behavior.
- Do not touch devices, flash firmware, or call live services without
  explicit approval. Run the narrower layer and label it.

## Bundled tools

- `scripts/mutate.py TARGET --test CMD [--function NAME] [--json]` is a
  stdlib mutation runner for Python files. It exits 0 when no mutant
  survives, 1 when some survive, and 2 when the baseline fails.
  `scripts/test_mutate.py` holds its tests, including an equivalent
  mutant.
- `assets/examples/behavior/` has `subjects.py`, `variants.py`,
  `harness.py` (selects `VARIANT`), the `test_*.py` suites,
  `weak_examples.py`, `props_examples.py` (Hypothesis), `run_matrix.py`,
  and `expectations.json`.
- `assets/examples/go/escape/` is a fuzz target with a committed corpus.
  `c/overflow.c` is for ASan. `package/` is a wheel with a missing data
  file. `hdl-counter/` holds SystemVerilog designs and a testbench.
- `sh assets/examples/verify.sh [verify|network|fuzz]`. `verify` runs
  offline, `network` adds Hypothesis and the wheel install, and `fuzz`
  adds 10 s of Go fuzzing.

## References

- [Test structure](references/test-structure.md)
- [Inputs and oracles](references/inputs-and-oracles.md)
- [Coupling and doubles](references/coupling-and-doubles.md)
- [Generative, mutation, and instrumented][gen-ref]
- [Regressions, nondeterminism, and retirement][reg-ref]
- [Packages, hosts, and hardware](references/boundaries-and-hardware.md)

## Completion evidence

- A claim-to-layer table, with the command run for each claim.
- The red run, with its failure line, and the green run, for each new
  regression or test-first case.
- Mutation results for changed functions, with each survivor
  classified.
- For suite maintenance: the decision on each test, and the test that
  keeps protecting each removed test's behavior.
- Claims not established, each with its reason: not runnable here, no
  device, needs approval.

## Stop and ask

- The contract or its authority is unclear, and the choice changes
  what the tests assert.
- The only way to green is changing the contract or weakening a test.
- A device, credential, or live service is needed and not approved.

[gen-ref]: references/generative-and-mutation.md
[reg-ref]: references/regressions-and-flakiness.md
[layers]: references/inputs-and-oracles.md#test-boundary-selection
[red]: references/test-structure.md#observed-red-then-green
[one]: references/test-structure.md#one-behavior-per-test
[aaa]: references/test-structure.md#visible-action-arrange-act-assert
[history]: references/test-structure.md#kept-history-for-sequence-rules
[oracle]: references/inputs-and-oracles.md#independent-expected-result
[bounds]: references/inputs-and-oracles.md#equivalence-classes-and-boundary-values
[table]: references/inputs-and-oracles.md#decision-table
[transitions]: references/inputs-and-oracles.md#state-transition-coverage
[vectors]: references/inputs-and-oracles.md#standard-vectors-not-round-trips
[golden]: references/inputs-and-oracles.md#golden-output-with-narrow-normalization
[public]: references/coupling-and-doubles.md#public-consequence-not-private-helper
[value]: references/coupling-and-doubles.md#value-not-representation
[arch]: references/coupling-and-doubles.md#architecture-rule-not-frozen-declarations
[roles]: references/coupling-and-doubles.md#test-double-roles
[outcome]: references/coupling-and-doubles.md#outcome-not-call-choreography
[effects]: references/coupling-and-doubles.md#required-and-forbidden-effects
[engine]: references/coupling-and-doubles.md#real-engine-for-engine-semantics
[property]: references/generative-and-mutation.md#property-based-test
[stateful]: references/generative-and-mutation.md#stateful-model-test
[fuzz]: references/generative-and-mutation.md#coverage-guided-fuzzing-and-corpus-regression
[sanitizer]: references/generative-and-mutation.md#sanitizer-run
[mutation]: references/generative-and-mutation.md#mutation-testing
[repro]: references/regressions-and-flakiness.md#regression-reproducer
[persisted]: references/regressions-and-flakiness.md#persisted-effects-after-failure
[race]: references/regressions-and-flakiness.md#deterministic-interleaving
[clock]: references/regressions-and-flakiness.md#injected-clock-and-bounded-waits
[isolation]: references/regressions-and-flakiness.md#test-isolation-from-shared-state
[flaky]: references/regressions-and-flakiness.md#flaky-test-diagnosis
[retire]: references/regressions-and-flakiness.md#test-retirement-decision
[package]: references/boundaries-and-hardware.md#installed-package-test
[host]: references/boundaries-and-hardware.md#host-dependent-behavior
[hdl]: references/boundaries-and-hardware.md#hdl-testbench-with-a-faulty-alternative
[layers-hw]: references/boundaries-and-hardware.md#evidence-layers-for-firmware-and-devices
