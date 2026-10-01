# Property, fuzz, and mutation testing

## Contents

- [Property tests](#property-tests)
- [Fuzzing](#fuzzing)
- [Sanitizers](#sanitizers)
- [Mutation testing](#mutation-testing)

## Property tests

Use a property test for a law over a large input space: round trip,
idempotence, ordering, conservation, or agreement with a simple model.
Write the property from the contract, not from the implementation's
branches, and keep it narrow enough that its failure names one law.
[Hypothesis][hypothesis] (Python) shrinks a failing case and replays saved
failures; keep each shrunken counterexample as an ordinary example test so
the regression does not depend on the generator. For stateful code, generate
operation sequences and compare against a simple model (an in-memory
dict). A property that restates the implementation, or whose generator
never reaches the boundaries, passes every fault.

## Fuzzing

For parsers of untrusted input, use coverage-guided fuzzing: Go's native
`go test -fuzz=FuzzName -fuzztime=10s` ([Go fuzzing][gofuzz]) or
[libFuzzer][libfuzzer] for C and C++. Go writes each failing input to
`testdata/fuzz/FuzzName/`, and plain `go test` replays that corpus, so
commit it as the regression test. State the invariant the fuzz target
checks (no panic, round trip, agreement with a reference), because a target
that only checks "no crash" misses wrong output.

## Sanitizers

Run memory and race checks on the same tests: `-fsanitize=address` for
C and C++ ([AddressSanitizer][asan]), `-fsanitize=thread`
([ThreadSanitizer][tsan]), and `go test -race`. Report the sanitizer and
the command with the result.

## Mutation testing

A mutation tool changes the code in small ways (flips a comparison, swaps
an operator, changes a constant) and reruns the tests; a mutant the tests
do not detect survives. Classify each survivor as a missing test, a weak
assertion, or an equivalent mutant (same behavior; justify it, do not
"fix" it). Use the tool for the ecosystem: [Stryker][stryker] for JS, TS,
and C#, [mutmut][mutmut] for Python, [cargo-mutants][cargo-mutants] for
Rust, and [PIT][pit] for Java. Limit the run to the changed functions or
files; chasing a whole-codebase score wastes time.

[hypothesis]: https://hypothesis.readthedocs.io/en/latest/
[gofuzz]: https://go.dev/doc/security/fuzz/
[libfuzzer]: https://llvm.org/docs/LibFuzzer.html
[asan]: https://clang.llvm.org/docs/AddressSanitizer.html
[tsan]: https://clang.llvm.org/docs/ThreadSanitizer.html
[stryker]: https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/
[mutmut]: https://mutmut.readthedocs.io/
[cargo-mutants]: https://mutants.rs/
[pit]: https://pitest.org/
