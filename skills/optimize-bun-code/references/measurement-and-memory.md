# CPU, JSC and memory diagnosis

Reviewed 2026-09-12 against Bun 1.4.2 and linked primary documentation. Verify
runtime-specific behavior when the target binary differs.

## Collect an interpretable baseline

Choose startup, steady-state throughput, latency or retained memory before
measuring. For a CLI, time the actual process including initialization. For a
hot function, prepare inputs outside the interval and consume results; use
`performance.now()` or an existing benchmark harness. Include realistic object
shapes, sizes, failures and cache misses. Report cold and warmed runs separately
to expose JSC warm-up and tiering.

Run repeated baseline and candidate measurements with the same binary, workload
and hardware conditions. Alternate order where thermal/cache drift matters.
Report median, spread, errors, and dropped requests. For HTTP, use the real
application protocol and a load generator with spare capacity, measuring
achieved throughput and latency distribution. A microbenchmark does not
establish server latency.

## CPU profile workflow

```sh
mkdir -p profiles
bun --cpu-prof --cpu-prof-dir ./profiles --cpu-prof-name baseline.cpuprofile \
  ./bench/workload.ts
bun --cpu-prof-md ./bench/workload.ts
```

Let the process exit normally so the profile is written. Load `.cpuprofile` in
Chrome's Performance tools or VS Code's CPU profile viewer. Inspect
total/inclusive time to locate expensive call paths, then self time to find work
performed in the function itself. High total time in a dispatcher may belong to
its callees. Idle network waits require request timing, not only JS CPU samples.
Markdown output supports text inspection; CPU JSON and Markdown can be requested
together. In Bun 1.4.2, requesting both formats treats the configured name as a
base: `workload.cpuprofile` produced `workload.cpuprofile.cpuprofile` and
`workload.cpuprofile.md` in a controlled run. Inspect actual output names rather
than assuming a path from the flag alone. These flags profile a script
invocation; do not infer that every `bun test` mode emits them.
[Profiling commands](https://bun.com/docs/project/benchmarking).

Use `bun --inspect-brk ./bench/workload.ts` for a startup breakpoint;
`--inspect-wait` waits for an attachment without that injected breakpoint. Bun
uses the WebKit Inspector Protocol. Debugger pauses and profiling overhead
invalidate normal latency comparisons, so time the final comparison separately.
[Debugger](https://bun.com/docs/runtime/debugger).

## Distinguish retention from allocation

At equivalent quiescent checkpoints, capture the heap before work, after
repeated work, and after cleanup:

```ts
import { writeHeapSnapshot } from "node:v8";
import { heapStats } from "bun:jsc";
console.log({ memory: process.memoryUsage(), heap: heapStats() });
writeHeapSnapshot("after-cleanup.heapsnapshot");
```

Load snapshots in Chrome Memory, compare surviving objects, and follow retainers
to a cache, listener, closure or queue owner. Remove that unwanted ownership,
then repeat the same lifecycle. Use snapshots for retained relationships. Use
allocation profiling for transient churn.
[V8-format snapshots](https://bun.com/guides/runtime/heap-snapshot).

Current `--heap-prof` writes a **full snapshot** at exit with a `.heapprofile`
filename; it is not Node's sampled allocation profile. Import using All Files or
rename to `.heapsnapshot`. `--heap-prof-interval` is accepted but unused;
selecting an interval does not produce allocation sampling. `--heap-prof-md`
chooses Markdown, including when both heap flags are supplied.
[Current heap-profile semantics](https://bun.com/docs/project/benchmarking).

Compare process RSS, JS heap, and external/native memory. Do not sum overlapping
counters. Stable JS object counts with growing RSS can indicate buffers, native
resources, allocator retention or fragmentation. Use OS allocation tools when JS
retainers do not explain growth. `Bun.gc(true)` can make an investigative
checkpoint more comparable, but forced GC is not a production leak fix. A peak
that plateaus after bounded caching differs from growth on every completed
request.

Profile object-shape changes, temporary arrays, and working-set size before
changing loops or representations. A small typed-array view can retain its
entire backing allocation. `--smol` trades runtime performance for memory;
evaluate both sides under the deployment workload. Do not apply V8-specific JIT
flags or call JS warm-up native PGO. For I/O and parallel work, use
[native APIs and concurrency](native-apis-and-concurrency.md).

A curated dependency inventory is a discovery aid, not performance evidence.
Verify current maintenance and the actual API/compatibility needs before
choosing a smaller alternative. Package size, dependency count and runtime
throughput are different measurements. Do not replace an existing
CLI/parser/logger merely because an inventory marks it restricted or assigns an
unmeasured speed ratio.

### RED — DO NOT: claim speed from dependency count

**Deciding condition:** The user requested runtime performance, and no profile
identifies the dependency as a limiting path.

```text
Replace the maintained parser with a local parser because zero dependencies is
faster and uses less memory.
```

Why RED:

- dependency count does not measure CPU time, retained memory, or package load;
- the replacement can lose syntax, diagnostics, and security maintenance;
- no representative workload or correctness comparison supports the claim.

### GREEN — DO: optimize only an observed limiting path

```text
Baseline: parser accounts for 3% of request CPU and is absent from the retained
heap after startup. Decision: keep it and investigate the 61% transform path.
```

Why GREEN:

- the profile identifies where improvement can affect the requested metric;
- retaining the parser preserves its established contract;
- the next experiment has an explicit baseline and target.

Check:

- repeat the representative workload before and after the candidate change and
  report distribution, errors, memory, and runtime version.
