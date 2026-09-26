# Measurement constructs

Each card locates time or memory before a change and proves the change
moved the metric. Runnable sources live in
`assets/examples/constructs/`; `sh assets/examples/verify.sh <mode>` runs
them in a temporary copy.

Local numbers in this file are machine-specific: Apple M1 Max, macOS arm64,
node 26.8.2 (V8 14.6.202.34-node.28), bun 1.4.2. Timings are medians of
`sh assets/examples/verify.sh measure`; they do not transfer to other
machines, runtimes, or inputs.

## Contents

- Timing harness with warmup and a result sink
- One process per variant
- Event-loop delay with monitorEventLoopDelay
- performance.now in browsers
- mitata
- CPU profile with --cpu-prof
- Live-heap profile with --heap-prof
- Sampling allocation profile including collected objects
- Heap snapshots
- Allocation oracle with --expose-gc and heapUsed
- GC trace with --trace-gc
- Optimization and deoptimization trace
- V8 natives with --allow-natives-syntax (test-only)
- JavaScriptCore probes with bun:jsc

## Timing harness with warmup and a result sink

**Definition.** A loop that runs the function until the JIT has tiered up
(warmup), then records several fixed-duration samples with the monotonic
nanosecond clock
[`process.hrtime.bigint()`][process-hrtime-bigint]
and stores every result in a module-level sink so the engine cannot drop
the call as dead code.

**Use when.**

- The project has no benchmark harness and you need ns/op for one function.
- The cost is CPU in a synchronous function; the profile already names it.

**Do not use when.**

- The project already uses mitata, tinybench, or Benchmark.js: use that
  harness so results stay comparable with its history.
- The code is asynchronous: timing the synchronous call measures promise
  creation, not the work. Time the awaited operation end to end instead.
- You need allocation or GC numbers: time does not show them; use the
  allocation oracle or a profile.

**Example.**

```javascript
const now = () => process.hrtime.bigint(); // monotonic ns
let sink;
function runFor(fn, ms) {
  const budget = BigInt(ms * 1e6);
  const start = now();
  let n = 0;
  let elapsed = 0n;
  do {
    for (let i = 0; i < 64; i++) sink = fn(n + i);
    n += 64;
    elapsed = now() - start;
  } while (elapsed < budget);
  return Number(elapsed) / n; // ns/op
}
runFor(fn, 300); // warmup: discard
const samples = Array.from({ length: 20 }, () => runFor(fn, 50));
```

Runnable: `assets/examples/constructs/bench.mjs` (`measure`, `report`).

**Cost removed.** Measurement error from cold-start timing (interpreter
and baseline tiers) and from dead-code elimination. Read the median and
p90 ns/op from `report`; a p90 far above the median means GC or tier-up
landed inside samples.

**Verify.**

1. `sh assets/examples/verify.sh benchmark`: every pair runs once through
   the harness on node and bun and prints `SMOKE PASSED`.
1. `sh assets/examples/verify.sh measure` with `BENCH_FILTER=fuse-chain`
   prints baseline and candidate medians; compare only rows from the same
   runtime and machine.

## One process per variant

**Definition.** V8 and JavaScriptCore record type feedback per function. If
baseline and candidate share a helper, whichever runs first shapes the
feedback the other sees. Run each side in its own process.

**Use when.**

- Baseline and candidate call the same function with different inputs
  (object shapes, array kinds, argument types).
- Results change when you swap the order of the two measurements.

**Do not use when.**

- The comparison is about startup or module loading: measure whole
  processes with `hyperfine` instead.

**Example.**

```javascript
import { spawnSync } from "node:child_process";
for (const side of ["baseline", "candidate"]) {
  spawnSync(process.execPath, [script, "measure-one", name, side], {
    stdio: "inherit",
  });
}
```

Runnable: `measure` and `measure-one` in `assets/examples/constructs/run.mjs`;
the failure it prevents is reproduced by `shared-feedback.mjs`.

**Cost removed.** Cross-contamination of type feedback. Local:
`node shared-feedback.mjs` (one `sumAll` over 4,096 elements, holey array
measured first, packed second, same process) printed 7,721.9 vs 29,210.9
ns; `BENCH_FILTER="packed-array read" sh assets/examples/verify.sh
measure` (separate processes) printed 7,717.2 vs 7,674.0 ns on node and
2,533.5 vs 2,535.1 ns on bun. The 4x gap was an artifact of shared
feedback, not of the elements kind.

**Verify.**

1. Swap the order of baseline and candidate; in-process results that flip
   mean shared feedback.
1. `sh assets/examples/verify.sh measure` runs every side in a child
   process (`process.execPath` works for node and bun).

## Event-loop delay with monitorEventLoopDelay

**Definition.** [`perf_hooks.monitorEventLoopDelay({ resolution })`][eld]
(node 11.10.0+) samples how late a timer fires and records the delays in
a histogram whose values are nanoseconds (`min`, `max`, `mean`,
`percentile(p)`). Bun 1.4.2 also provides it (local). A long synchronous
task shows up as a large `max`.

**Use when.**

- Requests time out or health checks fail while CPU work runs, and you
  must show which change reduces the stall.

**Do not use when.**

- You need to know which function blocks: the histogram has no stacks;
  pair it with `--cpu-prof`.
- You measure a stall shorter than `resolution` (default 10 ms).

**Example.**

```javascript
import { monitorEventLoopDelay } from "node:perf_hooks";
const histogram = monitorEventLoopDelay({ resolution: 1 });
histogram.enable(); // do not reset() right before the work (see below)
await sleep(5);
await work();
await sleep(5); // let the sampler record the last delay
histogram.disable();
const maxMs = histogram.max / 1e6;
```

Runnable: `maxLoopDelayMs` in `assets/examples/constructs/async.mjs`.

**Cost removed.** Unmeasured event-loop stalls. Local `DELAY` line
from two `verify` runs: 30,000,000-iteration hash blocking 35.2-35.8 ms →
3.1-6.6 ms when chunked (node); 41.9-49.4 ms → 1.5-1.7 ms (bun). On node
26.8.2, calling `histogram.reset()` just before the blocking work made
`max` about 1.1 ms and hid the stall, so the example does not reset.

**Verify.**

1. `sh assets/examples/verify.sh verify` asserts the chunked run's max
   delay is below half of the blocking run's.
1. In a server, record `percentile(99)` over the same load before and
   after the change.

## performance.now in browsers

**Definition.** [`performance.now()`][performance-now]
returns a monotonic millisecond `DOMHighResTimeStamp`. Browsers coarsen it:
MDN lists 100 µs resolution in non-isolated contexts and 5 µs in
cross-origin isolated contexts.

**Use when.**

- The code runs in a browser or must run unchanged in node, bun, and
  browsers (all three provide `performance.now()`).
- The measured interval is much longer than the resolution (milliseconds).

**Do not use when.**

- Individual operations take less than the resolution: time a batch of
  calls and divide, or use the DevTools Performance panel.
- You need wall-clock timestamps for logs: use `Date.now()`.

**Example.**

```javascript
const start = performance.now();
for (let i = 0; i < 10_000; i++) sink = work(i);
const msPerOp = (performance.now() - start) / 10_000;
```

Runnable: `assets/examples/browser/rendering.html` (`time`).

**Cost removed.** False precision: a per-call timing below the browser's
resolution reports 0 or one tick, and repeated single calls return
multiples of the resolution.

**Verify.**

1. Check `crossOriginIsolated` in the page before relying on 5 µs.
1. Report the batch size and the per-op division with every result.

## mitata

**Definition.** [mitata](https://github.com/evanwashere/mitata) is a
microbenchmark library that handles warmup, sampling, and statistics, and
reports allocation per iteration on node. Bun's
[benchmarking guide](https://bun.com/docs/project/benchmarking) recommends
it for microbenchmarks. `do_not_optimize(value)` is its result sink.

**Use when.**

- You want percentiles and a summary ("N.NNx faster") without writing a
  harness, on node and bun with one file.
- A dependency is acceptable in the benchmark project (not in production).

**Do not use when.**

- Installing packages is not authorized: use `bench.mjs` instead.
- The project already standardizes on another harness.

**Example.**

```javascript
import { bench, do_not_optimize, run, summary } from "mitata";
summary(() => {
  bench("baseline", () => do_not_optimize(baseline(data)));
  bench("candidate", () => do_not_optimize(candidate(data)));
});
await run({ colors: false });
```

Runnable: `assets/examples/constructs/mitata-bench.mjs`.

**Cost removed.** Hand-written statistics. Local (mitata 1.0.34,
`BENCH_FILTER=regex-cache`): node 182.06 → 21.23 ns/iter, bun 46.65 →
19.21 ns/iter.

**Verify.**

1. `BENCH_FILTER=regex-cache sh assets/examples/verify.sh mitata` installs
   `mitata@1.0.34` with `bun add` in a temporary copy (network required)
   and runs on node and bun.
1. Check that the `summary` block names the candidate as faster and that
   the p99 column does not overlap the other row's average.

## CPU profile with --cpu-prof

**Definition.** [`--cpu-prof`](https://nodejs.org/api/cli.html#--cpu-prof)
starts the V8 sampling CPU profiler at startup and writes a `.cpuprofile`
(Chrome DevTools format) on exit. `--cpu-prof-dir`, `--cpu-prof-name`, and
`--cpu-prof-interval` (default 1000 µs) configure it; added in node 12.0.0
and marked stable in 22.4.0. Bun 1.4 accepts the same flags (`bun --help`)
and also `--cpu-prof-md`.

**Use when.**

- A workload is slow and you do not yet know which function dominates.
- You need the same evidence on node and bun.

**Do not use when.**

- The process never exits normally (servers): use `--inspect` and record
  from DevTools, or stop via a signal handler that exits cleanly.
- The cost is waiting (I/O, timers): a CPU profile shows only idle time.

**Example.**

```sh
node --cpu-prof --cpu-prof-dir=prof workload.mjs
bun --cpu-prof --cpu-prof-dir=prof workload.mjs
node check-profiles.mjs prof   # self and inclusive samples per frame
```

Runnable: `assets/examples/constructs/workload.mjs` and
`check-profiles.mjs`.

**Cost removed.** Guessing. The profile's `nodes[].hitCount` gives
self samples; summing a subtree gives inclusive samples. Local: node
reported 185 of 255 samples inclusive (139 self) in `baselineEvenSquares`;
bun reported 211 of 241 inclusive but only 1 self, because JSC attributes
time to inlined callees. Read inclusive time on bun.

**Verify.**

1. `sh assets/examples/verify.sh profile` asserts the hot frame holds at
   least half of all samples inclusive, on node and bun.
1. After a change, the same command must show a smaller inclusive share
   for the frame, and the end-to-end metric must move too.

## Live-heap profile with --heap-prof

**Definition.** [`--heap-prof`](https://nodejs.org/api/cli.html#--heap-prof)
starts the V8 sampling heap profiler and writes a `.heapprofile` on exit
(average sampling interval `--heap-prof-interval`, default 512 KiB). The
sampling profiler reports "only objects which are still alive when the
profile is returned"
([HeapProfiler.startSampling][heapprofiler-startsampling]).

**Use when.**

- Retained memory grows (leaks, caches, large live structures) and you
  need the allocating stacks.

**Do not use when.**

- The problem is short-lived garbage (GC pressure): this profile omits
  collected objects. Use the sampling allocation profile below.

**Example.**

```sh
node --heap-prof --heap-prof-dir=prof workload.mjs
```

**Cost removed.** Attributes retained bytes to stacks. Local: 9,304,656
of 9,829,008 sampled bytes were attributed to `retainRows`, which keeps
100,000 rows alive; the 300 ms of garbage from `baselineEvenSquares` in the
same run did not appear.

**Verify.**

1. `sh assets/examples/verify.sh profile` asserts `retainRows` owns sampled
   live bytes.
1. After a fix, a profile of the same workload shows fewer bytes for the
   frame.

## Sampling allocation profile including collected objects

**Definition.** The inspector method `HeapProfiler.startSampling` accepts
`includeObjectsCollectedByMinorGC` and `includeObjectsCollectedByMajorGC`
([protocol][protocol]),
so the profile also attributes garbage. `node:inspector/promises` (added
in node 19.0.0, Experimental, per [inspector][node-inspector]) reaches it
in-process.

**Use when.**

- `--trace-gc` shows frequent scavenges and you need the functions that
  allocate the temporary objects.

**Do not use when.**

- You need retained memory: use `--heap-prof` or a heap snapshot.
- The runtime is bun: `node:inspector` sessions are not available there;
  `bun --heap-prof` exists (`bun --help`) but whether it keeps collected
  objects was not verified here.

**Example.**

```javascript
import { Session } from "node:inspector/promises";
const session = new Session();
session.connect();
await session.post("HeapProfiler.startSampling", {
  samplingInterval: 4096,
  includeObjectsCollectedByMinorGC: true,
  includeObjectsCollectedByMajorGC: true,
});
runWorkload();
const { profile } = await session.post("HeapProfiler.stopSampling");
```

Runnable: `assets/examples/constructs/alloc-profile.mjs`.

**Cost removed.** Unattributed temporary allocation. Local: 45,253,304
sampled bytes inclusive under `baselineEvenSquares` vs 4,488 under
`candidateEvenSquares` for 20,000 calls each (sampled, so approximate).

**Verify.**

1. `node alloc-profile.mjs` (run by `verify.sh profile`) exits 1 unless the
   candidate's sampled bytes are below a tenth of the baseline's.
1. Keep the same sampling interval for both sides.

## Heap snapshots

**Definition.** A heap snapshot is the full object graph at one moment.
[`v8.writeHeapSnapshot()`][v8-writeheapsnapshot] writes one synchronously;
it "blocks the event loop" and "requires memory about twice the size of the
heap". [`--heapsnapshot-signal`][heapsnapshot-signal] writes one on a
signal; `--heapsnapshot-near-heap-limit` writes one near the heap limit.
Bun provides `Bun.generateHeapSnapshot()` (viewable in WebKit/Safari
tools, per the [bun guide][bun-guide]).

**Use when.**

- Memory grows over time: take two snapshots and compare retained sizes
  in the DevTools "Comparison" view to find what accumulates and what
  retains it.

**Do not use when.**

- The process is near its memory limit and doubling the heap would crash
  it, unless the crash is acceptable (then use
  `--heapsnapshot-near-heap-limit`).
- The question is CPU time or short-lived garbage.

**Example.**

```sh
node --heapsnapshot-signal=SIGUSR2 server.mjs &
kill -USR2 "$!"            # writes a .heapsnapshot file in the cwd
node -e 'require("v8").writeHeapSnapshot("app.heapsnapshot")'
```

**Cost removed.** Unknown retainers of leaked objects. Compare the node
count and retained size of the suspect constructor between two snapshots.

**Verify.**

1. `sh assets/examples/verify.sh profile` writes a snapshot and checks
   `snapshot.node_count > 0` (local: 58,668 nodes for an empty script).
1. After a leak fix, the second-minus-first snapshot delta for the
   constructor is zero under the same workload.

## Allocation oracle with --expose-gc and heapUsed

**Definition.** With `node --expose-gc`, calling `gc()` and then reading
[`process.memoryUsage()`][process-memoryusage]
`heapUsed + arrayBuffers` before and after N calls gives bytes allocated
per call, if no GC runs inside the window.

**Use when.**

- A card claims fewer allocations and you need a pass/fail test in CI.
- The runtime is node (V8).

**Do not use when.**

- The runtime is bun: `process.memoryUsage().heapUsed` and
  `bun:jsc.heapStats()` did not change across these windows on bun 1.4.2
  (local), so the oracle prints `SKIP alloc` there.
- The workload allocates more than the young generation per window: a
  scavenge inside the window invalidates the delta.
- The pair's allocation varies with JIT tier (observed for string `+=` vs
  `join`): report it as unstable instead of asserting.

**Example.**

```javascript
function allocatedBytes(fn, iterations = 200) {
  for (let i = 0; i < 5_000; i++) sink = fn(i); // tier up first
  let best = Infinity;
  for (let w = 0; w < 5; w++) {
    gc();
    const m0 = process.memoryUsage();
    for (let i = 0; i < iterations; i++) sink = fn(i);
    const m1 = process.memoryUsage();
    const d = m1.heapUsed + m1.arrayBuffers - m0.heapUsed - m0.arrayBuffers;
    if (d >= 0) best = Math.min(best, d);
  }
  return best / iterations;
}
```

Runnable: `allocatedBytes` and `allocatesLess` in
`assets/examples/constructs/check.mjs`.

**Cost removed.** An unmeasured "fewer allocations" claim. The minimum
over windows discards windows where a scavenge freed memory mid-window.

**Verify.**

1. `sh assets/examples/verify.sh verify` prints `ALLOC <construct>: X B/call
   -> Y B/call` lines and fails if Y exceeds the ratio the pair declares.
1. Run twice; B/call must match within a few bytes for a stable pair.

## GC trace with --trace-gc

**Definition.** The V8 flag `--trace-gc` (listed by `node --v8-options`)
prints one line per collection: kind (`Scavenge` for young generation,
`Mark-Compact` for full), heap size before and after, and pause time.
Node's `PerformanceObserver` with `type: "gc"`
([perf_hooks](https://nodejs.org/api/perf_hooks.html)) exposes the same
events in-process with `detail.kind` (`NODE_PERFORMANCE_GC_MINOR`,
`..._MAJOR`, `..._INCREMENTAL`, `..._WEAKCB`).

**Use when.**

- Latency spikes or CPU profiles show `(garbage collector)` time and you
  need collection counts and pauses per workload.

**Do not use when.**

- You need to know which function allocates: GC traces have no stacks.

**Example.**

```sh
node --trace-gc workload.mjs | grep -c Scavenge
```

Local output line shape (node 26.8.2): `Scavenge 4.5 (5.4) -> 4.2 (6.1)
MB, pooled: 0.0 MB, 0.44 / 0.00 ms ... allocation failure;`.

**Cost removed.** Uncounted collections. After an allocation fix, the
`Scavenge` count for the same workload must fall.

**Verify.**

1. Run baseline and candidate workloads with the same input and count
   `Scavenge` lines.
1. Confirm the candidate count is lower and total pause time dropped.

## Optimization and deoptimization trace

**Definition.** V8's `--trace-opt` logs when a function is marked and
compiled by Maglev or TurboFan; `--trace-deopt` logs each bailout with its
reason (for example `reason: not a Smi`). Both are V8 flags, listed by
`node --v8-options`; their output format is not a stable interface.

**Use when.**

- A hot function is slower than expected and the profile shows it in the
  interpreter, or it keeps recompiling.

**Do not use when.**

- The runtime is bun: use `bun:jsc` probes (`numberOfDFGCompiles`,
  `reoptimizationRetryCount`).
- A single deopt at startup is the only event: it is normal feedback
  collection, not a cost.

**Example.**

```javascript
function add(a, b) {
  return a + b;
}
for (let i = 0; i < 200_000; i++) add(i, 1); // optimized for Smis
add("x", "y"); // bailout: reason: not a Smi
```

Runnable: `assets/examples/constructs/deopt.mjs` (pass `stable` to route
strings through a separate function).

**Cost removed.** Repeated deoptimize/reoptimize cycles at a hot site.
Count the `bailout ... <JSFunction name` lines.

**Verify.**

1. `node --trace-deopt deopt.mjs | grep 'reason: not a Smi'` finds the
   bailout; `node --trace-deopt deopt.mjs stable` has no bailout in `add`.
1. `sh assets/examples/verify.sh verify` asserts both.

## V8 natives with --allow-natives-syntax (test-only)

**Definition.** `node --allow-natives-syntax` enables `%Name(...)` calls to
V8 test intrinsics declared in `FOR_EACH_INTRINSIC_TEST` in
[src/runtime/runtime.h][src-runtime-runtime-h]:
`%HaveSameMap`, `%HasFastProperties`, `%HasHoleyElements`,
`%HasSmiElements`, `%HasDoubleElements`, `%HasObjectElements`,
`%StringIsFlat`, `%PrepareFunctionForOptimization`,
`%OptimizeFunctionOnNextCall`, `%GetOptimizationStatus`. Bit 5 of the
status is `kTurboFanned` (enum `OptimizationStatus` in the same file).

**Use when.**

- A test must prove an engine-internal fact the card claims (same hidden
  class, packed elements, rope string, optimized function).

**Do not use when.**

- The code is production or library code: `%` is a syntax error without
  the flag, and always in bun. Keep probes in a separate file.
- The V8 version differs and names and status bits were not re-checked;
  they were confirmed only on node 26.8.2 (V8 14.6).

**Example.**

```javascript
%PrepareFunctionForOptimization(f);
f(a);
f(b);
%OptimizeFunctionOnNextCall(f);
f(c);
const TURBOFANNED = 1 << 5;
if (!(%GetOptimizationStatus(f) & TURBOFANNED)) throw new Error("not opt");
```

Runnable: `assets/examples/constructs/v8-probes.mjs`.

**Cost removed.** Folklore about engine internals: each construct gets a
checked fact.

**Verify.**

1. `node --allow-natives-syntax assets/examples/constructs/v8-probes.mjs`
   prints `PASS v8-probes` (run by `verify.sh verify`).

## JavaScriptCore probes with bun:jsc

**Definition.** Bun's `bun:jsc` module exposes JSC internals, including
`describe(value)` (structure ID and transition kind), `isRope(string)`,
`numberOfDFGCompiles(fn)`, `heapStats()`, and `optimizeNextInvocation(fn)`
(names enumerated locally with
`bun -e 'import * as j from "bun:jsc"; console.log(Object.keys(j))'` on
bun 1.4.2). `heapStats()` is documented in the
[bun benchmarking guide](https://bun.com/docs/project/benchmarking).

**Use when.**

- A card's claim must also hold on bun (shapes, ropes, try/catch
  compilation).

**Do not use when.**

- You need allocation bytes per call: `heapStats()` did not reflect
  unswept allocations in local windows.
- You need holey vs packed evidence: `describe` printed `ArrayWithInt32`
  for both `new Array(3)` filled and `[1, 2, 3]` locally.

**Example.**

```javascript
import { describe, isRope, numberOfDFGCompiles } from "bun:jsc";
const id = (o) => describe(o).match(/StructureID: (\d+)/)[1];
isRope(built); // true for an unflattened += result
```

Runnable: `assets/examples/constructs/jsc-probes.mjs`.

**Cost removed.** Same as the V8 probes, for JavaScriptCore.

**Verify.**

1. `bun assets/examples/constructs/jsc-probes.mjs` prints
   `PASS jsc-probes` (run by `verify.sh verify`).

[process-hrtime-bigint]: https://nodejs.org/api/process.html#processhrtimebigint
[performance-now]:
  https://developer.mozilla.org/en-US/docs/Web/API/Performance/now
[heapprofiler-startsampling]:
  https://chromedevtools.github.io/devtools-protocol/tot/HeapProfiler/#method-startSampling
[protocol]:
  https://chromedevtools.github.io/devtools-protocol/tot/HeapProfiler/#method-startSampling
[v8-writeheapsnapshot]:
  https://nodejs.org/api/v8.html#v8writeheapsnapshotfilenameoptions
[heapsnapshot-signal]:
  https://nodejs.org/api/cli.html#--heapsnapshot-signalsignal
[bun-guide]: https://bun.com/docs/project/benchmarking
[process-memoryusage]: https://nodejs.org/api/process.html#processmemoryusage
[src-runtime-runtime-h]:
  https://github.com/v8/v8/blob/main/src/runtime/runtime.h
[eld]: https://nodejs.org/api/perf_hooks.html#perf_hooksmonitoreventloopdelayoptions
[node-inspector]: https://nodejs.org/api/inspector.html
