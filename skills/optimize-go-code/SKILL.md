---
name: optimize-go-code
description: >-
  Profiles and optimizes Go CPU time, latency, and allocations with testing.B,
  benchstat, pprof, and compiler diagnostics. Use when a Go benchmark or
  profile shows the cost. Not for style edits.
---

# Optimize Go Code

Make a measured Go hot path cheaper without changing observable behavior.
Each change applies one reference card to a cost that a profile attributes,
is proven equivalent by a test oracle, and is kept only if the metric the
card names improves. The cards record preconditions and traps that are easy
to get wrong from memory, so read the card before applying a construct.

## Workflow

1. Record the target: `go version`, `go env GOOS GOARCH GOAMD64 GOARM64`,
   the `go` and `toolchain` lines of `go.mod`, build tags, and any
   `GOGC`, `GOMEMLIMIT`, `GOMAXPROCS`, or `GOEXPERIMENT` in the deployment.
   Keep the module's Go version; do not raise the `go` directive to reach
   a construct unless the user asked.
1. Reproduce the workload with a `testing.B` benchmark or the real binary.
   Pick the metric the user cares about: ns/op, tail latency, throughput,
   allocs/op, B/op, live heap, GC CPU, or RSS.
1. Attribute the cost before editing
   ([measurement](references/measurement.md)):
   - CPU: `go test -run '^$' -bench X -cpuprofile cpu.pprof` then
     `go tool pprof -top`;
   - allocations or GC: `-benchmem`, `-memprofile` with
     `-sample_index=alloc_space`, `GODEBUG=gctrace=1`;
   - waiting, contention, scheduling: block/mutex profiles, `go test -trace`.
1. Choose one construct from the routing table whose **Use when** matches
   the evidence and whose **Do not use when** does not.
1. Write the oracle first: keep the old code as `xBaseline` in a test and
   compare it with the candidate on empty, boundary, error, aliasing, and
   ordering cases. Add a `testing.AllocsPerRun` assertion for allocation
   cards, in a file tagged `//go:build !race`.
1. Apply the change and check the compiler's view where the card says so:
   `go build -gcflags=-m` (escape), `-gcflags=-m=2` (inlining),
   `-gcflags=-d=ssa/check_bce/debug=1` (bounds checks).
1. Measure: `go test -run '^$' -bench X -benchmem -count 10`, with
   baseline and candidate as `impl=baseline` / `impl=candidate`
   sub-benchmarks or as two revisions, then
   `benchstat -col /impl bench.txt` or `benchstat old.txt new.txt`. Keep the
   change only if the target metric moved with p < 0.05 and nothing else
   regressed; run `go test -race` on the changed package.
1. Re-run the application-level workload, then report using
   [the report template](assets/performance-report.md).

## Route evidence to a construct

| Evidence | Card |
| --- | --- |
| `growslice` in `alloc_space`, append in a loop | [Preallocation](references/allocation.md#preallocated-slice-capacity) |
| Map growth while filling a map of known size | [Map size hint](references/allocation.md#map-size-hint) |
| `s +=` string concatenation in loops | [strings.Builder](references/allocation.md#stringsbuilder-with-grow) |
| `fmt.Sprintf`/`Sprint` formatting numbers in loops | [strconv append](references/allocation.md#strconv-append-functions-instead-of-fmt) |
| New `bytes.Buffer` per message in one goroutine | [Buffer Reset](references/allocation.md#bytesbuffer-reused-with-reset) |
| `string(b)` conversions before map lookups | [string(b) lookups](references/allocation.md#stringb-in-map-lookups-and-comparisons) |
| Per-request temporary buffers across goroutines | [sync.Pool](references/allocation.md#syncpool-of-pointer-shaped-objects), [pool element type](references/allocation.md#syncpool-element-type-pointer-not-slice) |
| Scratch map rebuilt per batch | [clear](references/allocation.md#clear-to-reuse-a-map) |
| Keys built as `a + ":" + b` | [Struct keys](references/allocation.md#struct-map-keys-instead-of-concatenated-strings) |
| `sort.Slice` in hot code | [slices.Sort](references/allocation.md#slicessort-instead-of-sortslice) |
| Map iteration must be deterministic | [Sorted keys](references/allocation.md#sorted-map-keys-with-a-presized-slice) |
| Small sub-slices keep big buffers alive (`inuse_space`) | [Clone sub-slice](references/allocation.md#copying-a-small-sub-slice-out-of-a-large-buffer) |
| `&T{...} escapes to heap` on a small struct | [Return by value](references/allocation.md#return-small-structs-by-value), [escape report](references/compiler.md#escape-analysis-report-with--gcflags-m) |
| `[]any` / `[]Iface` built from concrete values | [Generics](references/allocation.md#generic-functions-instead-of-interface-slices) |
| Many live instances of a struct with mixed field sizes | [Field order](references/allocation.md#struct-field-order-and-padding) |
| Small hot helper appears as its own frame | [Inlining budget](references/compiler.md#inlining-budget-with--gcflags-m2), [cold-path outlining](references/compiler.md#cold-path-outlining-to-fit-the-inlining-budget) |
| `Found IsInBounds` in a hot loop | [BCE](references/compiler.md#bounds-check-elimination-with-a-length-guard) |
| Binary with a representative CPU profile | [PGO](references/compiler.md#profile-guided-optimization-with-defaultpgo) |
| Large struct with value-receiver methods | [Pointer receivers](references/compiler.md#pointer-receivers-for-large-structs) |
| `defer` inside a `for` loop | [Extract loop body](references/compiler.md#extract-the-loop-body-so-defer-runs-per-iteration) |
| Plan to remove `defer mu.Unlock()` for speed | [Keep defer](references/compiler.md#keep-defer-in-small-hot-functions) |
| One goroutine per item for large inputs | [Worker pool](references/concurrency-io.md#bounded-worker-pool) |
| `chansend`/`chanrecv` per small item | [Batching](references/concurrency-io.md#batching-channel-sends) |
| Producer and consumer park on every item of an unbuffered channel | [Buffered channel](references/concurrency-io.md#buffered-channel-between-producer-and-consumer) |
| Mutex around a single counter | [atomic.Int64](references/concurrency-io.md#atomicint64-instead-of-a-mutex-guarded-counter) |
| Shared map/lock updated per item by workers | [Per-worker aggregation](references/concurrency-io.md#per-worker-aggregation) |
| Many small writes to a file or socket | [bufio.Writer](references/concurrency-io.md#bufiowriter-for-many-small-writes) |
| Byte-at-a-time or unbuffered reads | [bufio.Scanner](references/concurrency-io.md#bufioscanner-for-line-input) |
| GC CPU high, memory to spare | [GOGC](references/runtime.md#gogc) |
| Container memory limit, OOM kills | [GOMEMLIMIT](references/runtime.md#gomemlimit-soft-memory-limit) |
| CPU-limited container, throttling | [GOMAXPROCS](references/runtime.md#gomaxprocs) |
| Goroutines never finish after a change | [Leak profile](references/measurement.md#goroutine-leak-profile) |

## Rules

- Same machine, toolchain, inputs, `GOMAXPROCS`, and power state for
  baseline and candidate; at least `-count 10`; compare with benchstat.
  Never rerun until the result becomes significant.
- One construct per measured change, so each result is attributable.
  Revert a change whose metric shows `~`: a plausible rewrite can measure
  as no change (the BCE card's own run did), and keeping it adds risk with
  no benefit.
- A candidate that does less work (skips validation, different input,
  cached result, dead code the compiler removed) is invalid even if faster.
  Every benchmark consumes its result through `b.Loop` or a typed sink.
- Preserve the observable contract: results, error text and `errors.Is`
  identity, panics, nil versus empty slices and maps, ordering, aliasing of
  returned slices, and goroutine completion. The cards list each
  construct's traps.
- Allocation assertions never run under `-race`, and never assert exactly
  zero for code that uses `sync.Pool`.
- `GOGC`, `GOMEMLIMIT`, `GOMAXPROCS`, and PGO change the whole binary.
  Apply them only with an application-level measurement and state the
  deployment consequence.
- Choose example inputs that really allocate: `strconv.Itoa` of 0..99,
  strings of 32 bytes or less that do not escape, and small boxed values
  can take allocation-free paths and make a baseline look free.

## Bundled tools

- `assets/examples/verify.sh MODE` works in a temp copy of the example
  module (needs Go 1.25+). Modes: `verify`
  (vet, equivalence and allocation oracles), `race`, `diagnostics`
  (escape, inlining, BCE assertions), `benchmark` (smoke, 1 iteration),
  `measure` (`-count 10` plus benchstat when found or given in the
  `BENCHSTAT` variable), `profile` (CPU, heap, trace), `pgo`.
- `assets/performance-report.md`: the report skeleton.

## References

- [Measurement](references/measurement.md): b.Loop and b.N benchmarks,
  RunParallel, AllocsPerRun, oracles, benchstat, pprof, traces, gctrace,
  goroutine leaks.
- [Allocation](references/allocation.md): preallocation, builders,
  strconv, buffers, conversions, pools, clear, keys, sorting, retention,
  escape, boxing, padding.
- [Compiler](references/compiler.md): escape analysis, inlining, BCE, PGO,
  receivers, defer.
- [Concurrency and I/O](references/concurrency-io.md): worker pools,
  batching, channel buffering, atomics, aggregation, bufio.
- [Runtime configuration](references/runtime.md): GOGC, GOMEMLIMIT,
  GOMAXPROCS.

## Completion evidence

The final report contains:

- Go version, GOOS/GOARCH, CPU model, `go` directive, and runtime settings;
- the profile or benchmark output that attributed the cost;
- the construct applied, with its **Use when** conditions checked;
- the oracle command and result, including edge cases and `-race`;
- benchstat output for baseline and candidate with n, p-values, and
  allocs/op, plus the application-level result;
- anything not run (other GOOS/GOARCH, production profiles, container
  limits) stated as not verified.
