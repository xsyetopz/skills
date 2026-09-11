# Bun performance evaluation

Evaluated 2026-09-12 on Bun 1.4.2, macOS arm64. Replaced `bun-performance` with
explicit-only `optimize-bun-code`; consolidated eight inherited fragments into
two references covering measurement/memory and native APIs/concurrency.

## Verified interfaces and examples

Rechecked official Bun profiling, file I/O, heap snapshot, debugger, HTTP server
and worker documentation linked from the references. Removed incomplete worker
scaffolding and an unconditional pool framework. Worker admission and ownership
remain conditional on a recurring parallel workload.

Actual CPU profiling generated JSON and Markdown. With both CPU formats, the
configured `workload.cpuprofile` name yielded `workload.cpuprofile.cpuprofile`
and `workload.cpuprofile.md`; single-format output used the configured name. The
JSON contained samples and timing fields. Exit-time heap profiling produced a
full V8-format snapshot with 43,573 nodes, not allocation sampling. The accepted
but unused heap interval flag is explicitly distinguished from Node's sampling
behavior.

Extracted TypeScript examples ran in `/tmp/bun-native-evidence`:

- File copy returned 4,108 bytes; `cmp` proved exact binary preservation.
- Loopback HTTP preserved all binary bytes; unknown route and missing fixture
  returned 404. The test stopped the server afterward.
- `heapStats`, `process.memoryUsage` and `writeHeapSnapshot` ran; the snapshot
  parsed with 3,972 nodes.

These checks do not prove durability, disconnect handling, HTTP load
performance, worker termination, or debugger attachment. No such runtime claims
are made.

## Independent optimization evaluation

A fresh-context evaluator received a sales aggregation implementation, frozen
input tests and a contract preserving totals, insertion order and ownership. The
evaluator removed repeated whole-map cloning by mutating one local map, without
adding workers, caching, dependencies or changing the runtime.

On 6,000 rows with 5,000 distinct customer IDs, six alternating processes each
performed two warm-up calls and five measured calls. Median process medians were
114.543 ms baseline and 0.265 ms candidate; individual samples ranged from
109.008–147.108 ms and 0.225–0.325 ms respectively. Result consumption and sum
checking were inside the measured interval. This is roughly 432 times faster for
this synthetic high-cardinality workload, not a general Bun speedup.

Both baseline and candidate passed the two original behavior tests. Integration
inspected the benchmark and candidate and ran 200 deterministic differential
cases with frozen inputs, repeated keys, signed amounts and Unicode keys; all
matched the baseline's complete ordered entries. Allocation reductions follow
from eliminating explicit clones; allocation counts were not measured.

Artifacts: `/tmp/bun-opt-forward-work.5IHV6Y` and
`/tmp/bun-opt-forward-result.md`. The measurements exclude process startup,
input construction, I/O and memory profiling; only one host/runtime was tested.

## Validation and remaining intake

Both official skills-ref and skill-creator validation passed. Strict Markdown
passed for the package. Dependency inventory metadata and sample rows were
inspected, but the inventory is not fully consumed. Its restricted-package
labels and unsupported performance ratios were not imported as policy. Further
source intake remains part of the full repository goal.
