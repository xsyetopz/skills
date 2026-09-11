# Property, fuzz, mutation, and instrumented tests

Use these techniques for a concrete gap; do not add a framework or a CI matrix
just because a technique exists. Verify the chosen tool's maintained package,
target-version support, and official invocation before installation.

## Property-based testing

Identify a law that comes from the contract: conservation, monotonicity,
idempotence, agreement with an independent oracle, or valid state transitions.
Generate structured inputs that exercise the meaningful space and retain
explicit examples for important boundaries. A property such as “never throws” is
wrong when invalid inputs should fail.

Use a maintained generator/shrinker such as [Hypothesis][hypothesis] where it
fits the ecosystem rather than writing random-input infrastructure. Keep
generation constraints explicit; excessive filtering can discard precisely the
interesting cases. Record the minimized failing case and replay information.
Shrinking makes a failure easier to understand; it does not establish that the
property is correct.

For stateful systems, generate operations against a small independent model with
explicit preconditions and check effects after each step. Do not reuse
production transition helpers in the model. For protocols, include invalid as
well as valid messages; valid-object generation alone does not exercise decoder
failure paths.

## Fuzzing and native instrumentation

Target an input-processing boundary with a complete harness. Use a maintained
fuzzer compatible with the project, seed it with representative inputs, bound
time/memory/output, and retain minimized failures. Avoid live external services,
real secrets, and unbounded filesystem writes. Reset persistent harness state
between inputs when required for reproducibility.

[LLVM libFuzzer][fuzzer] documents coverage-guided in-process fuzzing and its
input-function contract. Its original authors stopped active work, but it
remains supported. Inspect current ecosystem alternatives rather than making it
an automatic new default. Reproduce a crash outside the fuzz loop before
diagnosing it. Fuzz coverage and elapsed runtime do not prove absence of
defects.

For native code, use the target compiler's supported sanitizer configuration.
[AddressSanitizer][asan] detects memory-error classes on executed paths;
[ThreadSanitizer][tsan] detects data races. Verify target support, runtime
linkage, and instrumentation of relevant libraries. Do not assume every
sanitizer can be combined or that instrumented timing represents release
performance. Static analysis complements execution but does not replace a
relevant reproducer.

## Mutation testing

Use mutation testing to ask whether assertions notice plausible wrong behavior,
not to manufacture a coverage target. Target the changed contract with the
existing runner or a supported tool such as [Stryker][stryker]. Inspect
surviving mutations: they can indicate missing coverage, weak assertions,
unreachable code, or an equivalent transformation. Do not change correct
production behavior merely to kill an equivalent mutant.

A failed build or incompatible mutation is not the same as a test detecting a
behavioral defect. Classify tool results using its documented categories. For a
small change, a controlled faulty implementation in an isolated copy can provide
the needed evidence without installing a full mutation framework. Verify that
the original still passes and the mutation fails for the intended assertion.

## Example selection

For a retryable write with a documented idempotency contract, examples should
cover success, repeat of the same logical request, conflicting reuse, and a
transport failure with unknown commit status. A generated operation sequence can
check that accepted effects occur once under that contract. A real-store
integration test must still establish atomicity; a pure in-memory model cannot
prove it.

For a new serializer, first check whether the format and implementation should
already exist. If the requested work really is a serializer, test normative
vectors and independent consumers as well as round trips. Generating more inputs
does not compensate for a shared wrong oracle.

[hypothesis]: https://hypothesis.readthedocs.io/en/latest/
[fuzzer]: https://llvm.org/docs/LibFuzzer.html
[asan]: https://clang.llvm.org/docs/AddressSanitizer.html
[tsan]: https://clang.llvm.org/docs/ThreadSanitizer.html
[stryker]:
  https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/
