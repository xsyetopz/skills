# Execute the Rust performance fixtures

The bundled fixtures are small programs that expose one semantic failure at a
time. Use them to study the skill and to test the fixture runner. Do not treat
their pass as evidence for target repository code or their smoke execution as a
benchmark.

## Run the fixtures

1. Provision the project-declared Rust toolchain. Do not install a newer
   compiler/runtime silently.
1. Copy `assets/examples/` to a work directory if you need to change it.
1. From the copied directory, run:

```sh
sh verify.sh comparisons
sh verify.sh correctness 1
sh verify.sh reproduction
```

The incorrect variant must exit nonzero with its documented contract marker. The
corrected variant must exit zero under the same independent oracle. A
compiler/import/setup failure is not the expected failure. Unknown modes and
case identifiers must fail rather than report a skip as success.

## Adapt the code to a real measurement

Use the repository harness. For Rust, the intended mechanism is Criterion or the
repository cargo benchmark with matched profiles/features, warmup/samples,
stable inputs, and black-boxed outputs. A representative command sequence is:

```sh
cargo test --all-targets --all-features
cargo bench --bench target
perf record -g -- target/release/app fixture.bin && perf report
```

Confirm the exact options against the installed tool. Capture raw output,
toolchain/runtime identity, environment, repetitions, and validity checks. The
cost reduced must appear in perf, samply, Instruments or the target profiler
plus compiler/LLVM diagnostics when they answer the hypothesis; the application
metric must also move when that cost is material. If either signal does not
move, report the candidate as unconfirmed rather than inventing a speedup.
