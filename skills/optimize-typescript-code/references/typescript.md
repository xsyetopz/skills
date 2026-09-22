# TypeScript runtime performance

Identify the actual runtime: browser and version, Node.js, Bun, or another
engine. TypeScript types are erased; a type-only rewrite is not a runtime
optimization. Keep bundler, transpilation target, source maps, minification, and
development/production modes explicit.

For browser work, distinguish scripting, rendering/layout, painting, network,
and main-thread scheduling. Profile the real interaction before optimizing a
function that contributes little to it. For server work, separate CPU from
event-loop delay, asynchronous I/O, allocation, and downstream latency. Compare
tail latency under representative concurrency, not only an isolated loop.

Use the runtime's profiler and existing benchmark framework. Warmup, JIT
tiering, constant folding, and garbage collection can distort small
measurements; retain enough repetitions and output consumption. Do not transfer
engine-specific “hidden class” or inline-cache folklore without checking the
actual engine and call site.

Investigate repeated parsing, serialization, cloning, intermediate arrays,
string construction, and redundant DOM work where measured. Preserve order,
sparse-array behavior, coercion, observable getters, and promise/error semantics
when replacing collection methods or restructuring async code.

Reduce retained object graphs and release listeners/timers/resources at their
owner boundary. Adding a cache requires an actual key, invalidation/lifetime
policy, and bound justified by the workload. Worker transfer can avoid copies
for transferable objects but changes ownership; verify buffer detachment and
cancellation behavior.

Sources: [Node.js profiling][node-js-profiling], [Node performance
hooks][ref-node-performance-hooks], [Chrome DevTools
performance][chrome-devtools-performance].

## Executable fixtures

The fixture uses Node.js 22.6+ with `--experimental-strip-types` and POSIX `sh`
for runtime checks. Type checks additionally require the declared TypeScript
compiler and Node types; runtime stripping does not check types.

Read [the fixture execution contract][ref-the-fixture-execution-contract] before
running these examples. It defines disposal, supported modes, same-check
defective/corrected implementation checks, and the distinction between
correctness and timing.

From the skill root:

```sh
sh assets/examples/verify.sh
sh assets/examples/verify.sh correctness 1
```

The complete project and its native configuration are in
[the TypeScript examples](../assets/examples). Copy that directory intact when
adapting a fixture. Run only this language; the target project keeps its own
toolchain.

### Semantic regression cases

Source: [semantics.ts][ref-semantics-ts].

| Case | Required contract |
| --- | --- |
| 1 | SameValueZero membership for NaN |
| 2 | Sparse versus dense arrays |
| 3 | Awaiting asynchronous work |
| 4 | Bounded concurrent work |
| 5 | Structured clone versus lossy JSON roundtrip |
| 6 | Copy versus buffer transfer/detachment |
| 7 | Independent rows versus shared row |
| 8 | Runtime validation versus an erased type assertion |

## Baseline and candidate

Use [the comparison sources][ref-the-comparison-sources] and their
expected-result checks. The [shared contract][fixture-contract] explains
input-domain limits and why these programs are not speed claims.

## Benchmark fixture

Work in a copy of [the javascript asset directory](../assets/examples). Run the
following commands relative to that copied directory.

Use the project's existing JavaScript benchmark harness; do not turn the
comparison CLI into a home-made timing library. The bundled comparison programs
test equivalence and expose callable functions, not speedup claims. Run
`sh verify.sh comparisons` from its root first.

Keep the actual browser/Node/Bun runtime fixed. Await each complete async
operation; do not time promise construction alone. Keep a result sink and
bounded concurrency. Profile event-loop stalls and GC separately. A Node fixture
cannot establish browser DOM or Bun performance.

Integrate the selected baseline and candidate functions into the native
benchmark framework already used by the target repository. Record its exact
version and configuration; retain its result format, warmups/forks, parameters
and native controls. Test an independent expected result before measurement.
Keep one source of benchmark configuration instead of a separate skill_config
file. Declare any new package installation before performing it. Provision the
target benchmark dependencies explicitly; the example alone does not demonstrate
a performance gain.

Source: [source][source]

## Failure reproduction

Source: [the isolated reproducer][ref-the-isolated-reproducer]. From the skill
root, run `sh assets/examples/verify.sh reproduction`. Direct commands below
assume a clean copy of the reproduction directory.

Expected: both callbacks complete before the operation returns.

Actual: `forEach` does not await async callbacks, so the immediate count is
zero. The top-level verifier copies the assets and runs `repro.ts` with Node and
`--experimental-strip-types` in a temporary directory.

[node-js-profiling]: https://nodejs.org/en/learn/getting-started/profiling
[chrome-devtools-performance]:
  https://developer.chrome.com/docs/devtools/performance
[source]: https://nodejs.org/api/perf_hooks.html
[ref-node-performance-hooks]: https://nodejs.org/api/perf_hooks.html
[ref-the-fixture-execution-contract]:
  typescript-runtime-performance-executable-performance-fixtures.md
[fixture-contract]:
  typescript-runtime-performance-executable-performance-fixtures.md
[ref-semantics-ts]: ../assets/examples/correctness/semantics.ts
[ref-the-comparison-sources]: ../assets/examples/comparisons
[ref-the-isolated-reproducer]: ../assets/examples/reproduction

## Type checking

In a disposable copy of `assets/examples/`, provision the declared development
dependencies using the project's package manager, then run:

```sh
tsc --project tsconfig.json
sh verify.sh
```

The first command checks types without emitting code; the second executes
behavior. Preserve both results. Do not claim that one substitutes for the
other, or that Node fixture execution proves browser or Bun behavior.
