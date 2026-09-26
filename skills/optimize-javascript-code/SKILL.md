---
name: optimize-javascript-code
description: >-
  Profiles and optimizes JavaScript CPU time, allocations, and event-loop
  latency on Node, Bun, and browsers with CPU profiles and deopt traces. Use
  when a JavaScript benchmark or profile shows the cost. Not for runtime
  migration or type-check speed.
---

# Optimize JavaScript Code

Make a measured JavaScript hot path cheaper on the runtime the project
ships (node, bun, or a browser) without changing observable behavior. Each
change applies one reference card to a cost that a profile attributes, is
checked by an equivalence oracle, and is kept only if the metric the card
names improves. The cards record where the common advice measured in the
wrong direction, so read the card before applying a construct.

## Workflow

1. Record the target: runtime and version (`node --version`,
   `bun --version`, or the browser build), module format, bundler and
   transpile target, and production flags. Keep them fixed; changing the
   runtime is a separate, authorized decision.
1. Reproduce the workload with representative input and pick the metric
   the user cares about: CPU time per operation, request latency (p50,
   p99), throughput, allocation rate or GC pauses, retained memory,
   event-loop delay, or frame time.
1. Attribute the cost before editing
   ([measurement](references/measurement.md)):
   - CPU: `node --cpu-prof` or `bun --cpu-prof`, then read inclusive
     samples per frame;
   - garbage and GC pauses: `--trace-gc` counts, then a sampling
     allocation profile that includes collected objects;
   - retained memory: `--heap-prof` or two heap snapshots;
   - suspected deopts: `node --trace-opt --trace-deopt`;
   - event-loop stalls: `perf_hooks.monitorEventLoopDelay`;
   - browsers: the DevTools Performance panel.
1. Choose one construct from the routing table whose **Use when** matches
   the evidence and whose **Do not use when** does not.
1. Write the oracle first: baseline and candidate on the same inputs,
   including empty, boundary, `NaN`/`-0`, holes, Unicode, error, and
   rejection cases. Await every promise the code starts.
1. Apply the change with a short comment naming the invariant it relies
   on (shared `lastIndex`, detached buffers, bounded cache keys, shared
   subtrees that must not be mutated).
1. Verify with the card's **Verify** steps: behavior first, then the named
   metric, on every runtime the project supports. Measure baseline and
   candidate in separate processes when they share code.
1. Re-run the application-level workload. Keep the change only if the
   target metric moved beyond run-to-run noise and nothing else regressed;
   revert it otherwise.
1. Report with [the report template](assets/performance-report.md).

## Route evidence to a construct

| Evidence | Card |
| --- | --- |
| Need ns/op for one function, no harness | [Timing harness](references/measurement.md#timing-harness-with-warmup-and-a-result-sink), [mitata](references/measurement.md#mitata) |
| Results flip when order of runs is swapped | [One process per variant](references/measurement.md#one-process-per-variant) |
| Unknown hot function | [--cpu-prof](references/measurement.md#cpu-profile-with---cpu-prof) |
| Many scavenges, GC time in profile | [--trace-gc](references/measurement.md#gc-trace-with---trace-gc), [Allocation profile](references/measurement.md#sampling-allocation-profile-including-collected-objects) |
| Memory grows over time | [--heap-prof](references/measurement.md#live-heap-profile-with---heap-prof), [Heap snapshots](references/measurement.md#heap-snapshots) |
| Hot function keeps deoptimizing | [Deopt trace](references/measurement.md#optimization-and-deoptimization-trace) |
| Need proof of shapes, holes, ropes, tiers | [V8 natives](references/measurement.md#v8-natives-with---allow-natives-syntax-test-only), [bun:jsc](references/measurement.md#javascriptcore-probes-with-bunjsc) |
| Allocation claim needs a CI check | [Allocation oracle](references/measurement.md#allocation-oracle-with---expose-gc-and-heapused) |
| Same type built with different field orders | [Constructor init](references/shapes-and-collections.md#initialize-every-field-in-the-constructor) |
| `delete obj.field` on hot objects | [Assign undefined](references/shapes-and-collections.md#assign-undefined-instead-of-delete) |
| Hot reader sees objects of many shapes | [Monomorphic sites](references/shapes-and-collections.md#monomorphic-call-sites) |
| `new Array(n)` or out-of-order writes | [Packed arrays](references/shapes-and-collections.md#packed-arrays-instead-of-holey-arrays) |
| `null`/`-0`/strings mixed into numbers | [One elements kind](references/shapes-and-collections.md#one-elements-kind-per-array) |
| Many small numeric records | [Typed arrays](references/shapes-and-collections.md#typed-arrays-for-numeric-records) |
| Object used as a growing dictionary | [Map](references/shapes-and-collections.md#map-for-dynamic-keys) |
| `includes`/`indexOf` inside a loop | [Set](references/shapes-and-collections.md#set-for-repeated-membership-tests) |
| `filter().map().reduce()` in a hot path | [Fuse chains](references/allocation-and-strings.md#fuse-mapfilterreduce-chains-into-one-loop) |
| Fresh capturing callback per call | [Hoist closures](references/allocation-and-strings.md#hoist-closures-out-of-hot-calls) |
| Hot `forEach` callback | [for loop](references/allocation-and-strings.md#indexed-for-loop-instead-of-foreach) |
| `arr = arr.concat([x])` or `[...arr, x]` in a loop | [push](references/allocation-and-strings.md#push-instead-of-concat-in-a-loop) |
| Pieces pushed only to `join` | [String +=](references/allocation-and-strings.md#string--instead-of-array-join) |
| Regex literal or `new RegExp` per call | [Hoist regex](references/allocation-and-strings.md#hoist-regular-expression-literals), [Regex cache](references/allocation-and-strings.md#cache-regexp-objects-built-from-strings) |
| Lexer uses `exec(text.slice(pos))` | [Sticky regex](references/allocation-and-strings.md#sticky-regex-for-positional-tokenizing) |
| Deep clone to change a few fields | [Copy changed path](references/allocation-and-strings.md#copy-the-changed-path-instead-of-deep-cloning) |
| JSON round trip loses `Date`/`undefined`/`NaN` | [structuredClone](references/allocation-and-strings.md#structuredclone-instead-of-a-json-round-trip) |
| Proposal to hoist try/catch for speed | [try/catch](references/allocation-and-strings.md#trycatch-inside-hot-functions) |
| Independent awaits in a loop | [Promise.all](references/async-and-concurrency.md#promiseall-for-independent-awaits), [Bounded](references/async-and-concurrency.md#bounded-concurrency) |
| `forEach(async ...)` | [for...of await](references/async-and-concurrency.md#forof-with-await-instead-of-foreachasync) |
| `async` wrappers, identity `.then` | [Drop wrappers](references/async-and-concurrency.md#drop-redundant-async-wrappers-and-then-chains), [return await](references/async-and-concurrency.md#return-await-inside-try) |
| One render per write in a burst | [Coalesce microtasks](references/async-and-concurrency.md#coalesce-notifications-into-one-microtask) |
| Timeouts or stalls while CPU work runs | [Loop delay](references/measurement.md#event-loop-delay-with-monitoreventloopdelay) |
| Event-loop delay from CPU work | [Yield](references/async-and-concurrency.md#yield-inside-long-synchronous-loops), [Workers](references/async-and-concurrency.md#worker_threads-for-cpu-bound-work), [Transfer](references/async-and-concurrency.md#transfer-arraybuffers-instead-of-copying) |
| Memory grows while piping streams | [pipeline](references/async-and-concurrency.md#streampipeline-for-backpressure) |
| Bun copies files through memory | [Bun.write](references/async-and-concurrency.md#bunfile-and-bunwrite-for-file-copies) |
| Forced reflow, per-event style writes, long tasks | [Batch reads](references/browser.md#batch-dom-reads-before-writes), [rAF](references/browser.md#requestanimationframe-for-visual-updates), [scheduler.yield](references/browser.md#scheduleryield-in-long-tasks) |

## Rules

- Same machine, runtime version, flags, input, and build mode for baseline
  and candidate. Warm up, keep results in a sink, and report median plus a
  spread (p90 or min/max) with units.
- One construct per measured change, so each result is attributable.
  Revert changes whose metric does not move; do not keep "harmless"
  rewrites.
- A candidate that does less work is invalid even if faster: skipped
  awaits (`forEach(async`), dropped validation, cached results, smaller
  input, or a shared object where the baseline made copies.
- A node result is not a bun or browser result: the Map counting card
  measured opposite directions on node and bun. Verify on every shipped
  runtime.
- Folklore is not evidence: the cards measured `+=` faster than `join`
  and `structuredClone` slower than a JSON round trip. Follow the card's
  measured direction and re-measure on the target.
- Never change coercion, `NaN`/`-0` handling, hole semantics, key order,
  prototype-key behavior, error types, rejection timing, or ordering of
  side effects without the user's approval. The cards list each trap.
- `%` natives, `--expose-gc`, and `bun:jsc` probes belong in tests and
  investigation scripts only, never in shipped code.
- Timing an async function's synchronous part measures promise creation;
  time the awaited operation end to end.
- TypeScript types are erased: a type-only rewrite is not a runtime
  optimization.

## Bundled tools

- `assets/examples/verify.sh verify|benchmark|measure|profile|mitata`:
  copies `assets/examples/constructs/` to a temporary directory and runs
  it there. `verify` runs every oracle and benefit assertion on node and
  bun plus the V8/JSC probes and the deopt trace; `benchmark` is a harness
  smoke (no timing claim); `measure` times each pair side in its own
  process (`BENCH_FILTER` narrows it); `profile` checks CPU, heap,
  snapshot, and allocation profiles; `mitata` installs `mitata@1.0.34`
  (network) and runs the pairs through it. A missing bun prints `SKIP`.
- `assets/examples/browser/rendering.html`: browser-only pairs; open it in
  a browser and read `#out`.
- `assets/performance-report.md`: the report skeleton.

## References

- [Measurement](references/measurement.md): timing, profiles, heap
  tools, traces, and engine probes.
- [Shapes and collections](references/shapes-and-collections.md): hidden
  classes, elements kinds, typed arrays, Map, and Set.
- [Allocation and strings](references/allocation-and-strings.md): loops,
  closures, strings, regexes, cloning, and try/catch.
- [Async and concurrency](references/async-and-concurrency.md): promises,
  microtasks, the event loop, workers, streams, and Bun I/O.
- [Browser](references/browser.md): layout, frames, and long tasks.

## Completion evidence

The final report contains:

- runtime name and version, OS/CPU, flags, bundler/transpile target;
- the profile, trace, or counter output that attributed the cost;
- the construct applied, with its **Use when** and **Do not use when**
  conditions checked against the code;
- the oracle command and result, including edge and error cases;
- baseline and candidate numbers with units and spread from the same
  machine and runtime (separate processes when code is shared), plus the
  application-level result;
- every supported runtime not measured (bun, browsers, older node) stated
  as not verified.
