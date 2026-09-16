# Run software performance and correctness examples

These are executable software examples. A fixture supplies input and setup; a
mutant is a deliberately defective implementation. A correction implements the
intended behavior. The same independent expected-result check is applied to
both. A performance baseline and candidate must instead be behaviorally
equivalent.

Read this before running a bundled performance fixture for the first time. Read
the language reference for its prerequisites, eight semantic cases, native
benchmark commands, and expected reproduction failure.

## Execution boundary

Run the selected `assets/examples/verify.sh` from any working directory with
POSIX `sh`; it resolves its own directory. The native source/projects can also
be used directly on their supported platforms. Copy examples to a work area
before changing or building them. Do not edit the installed skill.

The runner works in its own temporary copy and removes only that copy. It does
not install packages, regenerate lockfiles, or delete caller-owned build output.
Missing toolchains are failures, not skipped success. Scala CLI and Rust
managers may contact native registries when their toolchains/dependencies are
not provisioned; provision them first when execution must be offline. Unknown
modes, extra arguments, and invalid case numbers return errors.

From the examples directory, these are the supported modes:

```sh
sh verify.sh                # comparisons, all semantic pairs, reproduction
sh verify.sh comparisons
sh verify.sh correctness 1  # selected case: mutant then correction
sh verify.sh reproduction
```

The original repository also calls `verify.sh benchmark`. This retained mode
runs baseline/candidate execution checks and explicitly reports a smoke result;
it does not produce timing or allocation measurements. It exists for that
inspected command consumer, not as a recommended name for a new benchmark.

The convenience runner does not run timed benchmarks. Use the language's native
benchmark instructions and retain the benchmark framework's own configuration,
command-line controls, and result formats.

## Semantic checks

Each case applies the same independent observable condition to an incorrect
implementation and its correction. Red must exit 1 with the case's `CONTRACT ...
FAIL` marker; green must exit 0 with its `PASS` marker. Compiler, import, or
setup failures cannot satisfy the expected-failure check. A test that always
fails is not an independent expected-result check. These fixtures test behavior,
not performance, and do not prove correctness beyond the condition exercised.

## Baseline and candidate

The selected `comparisons/` directory contains executable baseline/candidate
functions with differential and expected-result checks. Inspect each input
domain before reuse: integer checksums do not establish floating-point,
culture-sensitive string, or user-defined equality equivalence. A candidate is a
hypothesis, not a measured winner. Input size, setup, allocation, data
representation, and runtime optimizations can reverse a result.

The inspection CLI prints results. Timing that CLI includes startup, setup,
formatting, and printing; it does not establish a warmed in-process speedup.
Adapt the actual functions into the target's native benchmark framework instead
of building a parallel timing framework. Reproduction success establishes only
the named failure, not an optimization result.
