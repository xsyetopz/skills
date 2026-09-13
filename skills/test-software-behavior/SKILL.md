---
name: test-software-behavior
description: >-
  Design or review behavioral tests, TDD examples, test retirement, regression,
  integration, property, and flaky-test evidence. Not for general production
  implementation, routine test execution, or CI configuration.
---

# Test Software Behavior

Identify the intended contract, supported environments, and observable failure.
Read existing tests and test configuration before adding tools. Current output,
visible fixtures, and implementation details are evidence, not automatically the
specification. Resolve material uncertainty instead of blessing it with a test.

Choose the smallest combination of test boundaries that can distinguish a real
incorrect implementation. Do not replace a required integration, host, or
install check with compilation or a mocked unit test. Reuse the project's runner
and fixtures; add a maintained test tool only when it supplies a needed
capability.

## Decide what deserves protection

A behavioral contract specifies required results, errors, transitions, effects,
and forbidden effects at a chosen boundary. Its consumer can be another
component; behavioral testing does not require a UI or an E2E test. Replaceable
helpers, algorithms, collections, and incidental ordering are implementation
details unless an independently established requirement makes them contractual.

For each proposed or affected test:

1. State the behavior, starting conditions, and consumer.
1. Identify the required consequence and its authority independently of code.
1. Name a plausible meaningful defect its assertions detect.
1. Identify the actual target action and observation boundary.
1. Ask whether replacing helpers, types, collections, algorithms, or control
   flow could preserve the contract while breaking the test.
1. Justify every asserted interaction, order, concrete type, or structural rule.
1. Choose **retain**, **rewrite/consolidate**, **remove**, or **unresolved** and
   record the deciding reason. Investigate uncertain contracts before deletion.

Prefer observable outcomes and inexpensive real collaborators. Preserve
contractual interactions and independently established architecture constraints;
neither mocks nor source inspection are inherently wrong. Mock verification
alone does not prove real delivery or persistence.

During an authorized refactoring slice, remove redundant, obsolete, or
negative-value tests rather than mechanically replacing each deletion. Rewrite
when a meaningful requirement would otherwise lose its only useful protection.
This is not permission to suppress an unexplained failure or clean up unrelated
suites.

## Load only the relevant guidance

- Read [test boundaries and oracles](references/boundaries-and-oracles.md) when
  selecting boundaries, inputs, independent oracles, or integration/package
  evidence.
- Read [test design and coupling](references/test-design-and-coupling.md) for
  implementation-sensitive assertions, smell terminology, or structural tests.
- Read [interaction testing](references/interaction-testing.md) when choosing
  collaborators, doubles, state verification, or contractual message checks.
- Read [AAA and behavioral TDD](references/aaa-and-tdd.md) for scenario design,
  test-first work, phase clarity, or genuinely history-dependent tests.
- Read [test retirement](references/test-retirement.md) when deciding whether to
  retain, rewrite, consolidate, or remove existing tests.
- Read
  [regressions and nondeterminism](references/regressions-and-nondeterminism.md)
  for bug reproduction, concurrency, asynchronous behavior, and flaky tests.
- Read
  [property, fuzz, and mutation tests](references/generative-and-mutation.md)
  when example-based coverage cannot adequately explore the input/state space.

Use recognizable Arrange–Act–Assert phases for one logical target behavior,
not a mandated statement count or literal comments. Keep necessary transitions
explicit in history-dependent scenarios; split unrelated behaviors. Select a
contractual example for TDD, demonstrate missing behavior, make the smallest
authorized sufficient change, then refactor production and tests.

Reference **RED — DO NOT / GREEN — DO** pairs contrast test designs, not TDD
states. A RED example may pass today yet reject a harmless refactor or miss a
real defect. Check both properties rather than judging syntax or tool choice.

## Verify and report

For a regression, demonstrate failure on the faulty behavior when available,
then success on the fix. Do this without modifying unrelated user work or
rewriting history. In a tests-only task, report discovered product defects; do
not repair production code unless requested. Do not add production APIs solely
for tests.

Use isolated temporary state and synthetic data. Avoid live external writes,
real credentials, and production infrastructure. Never weaken assertions, update
snapshots blindly, disable checks, or add retries/quarantine to hide a failure.

Report the behaviors covered, actual commands and results, failures found,
environment limitations, and remaining gaps. Test count and coverage percentage
alone do not establish correctness. A proposed test plan is not an executed
test.
