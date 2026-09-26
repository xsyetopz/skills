# Measurement constructs

These cards produce the baseline, the oracle, and the evidence that every
other card relies on. Runnable code is in
[`assets/examples/constructs`](../assets/examples/constructs); run it through
[`verify.sh`](../assets/examples/verify.sh), which always works in a temporary
copy.

Local measurements in this skill come from one machine: Apple M1 Max,
macOS 27.0, `go version go1.27.1 darwin/arm64`, `GOTOOLCHAIN=local`.
Allocation counts from `testing.AllocsPerRun` are deterministic for a given
toolchain and input; timings do not transfer to other machines.

## Contents

- Benchmark with b.Loop
- Benchmark with a b.N loop
- ReportAllocs and -benchmem
- Parallel benchmark with RunParallel
- AllocsPerRun allocation oracle
- Equivalence oracle test
- benchstat comparison
- CPU profile from go test
- Heap profile with alloc_space and inuse_space
- Block and mutex profiles
- Execution trace
- GC trace with GODEBUG=gctrace=1
- Goroutine leak profile

## Benchmark with b.Loop

**Definition.** `for b.Loop() { ... }` (Go 1.24+) runs the body until the
benchmark has enough samples. The first call resets the timer, so setup
before the loop is not timed, and the benchmark function runs once per
`-count`. The compiler keeps alive the arguments and results of calls
written inside the loop, so it cannot delete the measured work
([testing.B.Loop](https://pkg.go.dev/testing#B.Loop),
[Go 1.24 notes](https://go.dev/doc/go1.24)). Since Go 1.26, `B.Loop`
no longer prevents inlining in the loop body
([Go 1.26 notes](https://go.dev/doc/go1.26)).

**Use when.**

- The module's `go` directive is 1.24 or later (`go.mod`).
- Setup is expensive or must run once (fixtures, maps, files).

**Do not use when.**

- The module supports Go below 1.24: `b.Loop` does not exist there; use the
  [b.N card](#benchmark-with-a-bn-loop). Do not raise the `go` directive
  just for it.
- The same function also has a `b.N` loop: the docs say to use one or the
  other.
- The loop condition is not written exactly `b.Loop()` (for example
  `for ok := b.Loop(); ok; ok = b.Loop()`): the keep-alive transformation
  applies only to that exact form.
- The toolchain is 1.24 or 1.25 and the measured call is tiny: before
  Go 1.26 the body was not inlined, which can add allocations the
  production call site does not have. Compare against a `b.N` version on
  those toolchains.

**Example.**

```go
func BenchmarkBuilder(b *testing.B) {
    w := words(100) // setup: not timed
    b.Run("impl=baseline", func(b *testing.B) {
        b.ReportAllocs()
        for b.Loop() {
            benchStr = JoinBaseline(w, ",")
        }
    })
    b.Run("impl=candidate", func(b *testing.B) {
        b.ReportAllocs()
        for b.Loop() {
            benchStr = JoinCandidate(w, ",")
        }
    })
}
```

Runnable: `compare` in `assets/examples/constructs/bench_test.go`. The
`impl=` sub-benchmark names let benchstat put baseline and candidate in
columns of one table.

**Cost removed.** Setup time counted as work, setup repeated per `b.N`
round, and dead-code-eliminated loops that report near-zero ns/op.
benchstat's `±` column shows ns/op stability across `-count` runs.

**Verify.**

1. `sh assets/examples/verify.sh benchmark` runs each benchmark once
   (`-benchtime 1x`) and must print `SMOKE PASSED`.
1. Grep the target: `rg -n 'b\.Loop\(\)' -g '*_test.go'` and confirm no
   function also contains `b.N`.
1. Compare ns/op with the plausible cost of the work: a result far below
   it (a map build in single-digit ns) means the compiler removed the
   work; inspect it before trusting any comparison.

## Benchmark with a b.N loop

**Definition.** The pre-1.24 form: the framework calls the benchmark
function repeatedly with a growing `b.N`, and the function runs the body
`b.N` times. `b.ResetTimer` zeroes elapsed time and allocation counters after
setup ([testing.B.ResetTimer](https://pkg.go.dev/testing#B.ResetTimer)).

**Use when.**

- The module supports Go versions before 1.24.
- You need `b.StopTimer`/`b.StartTimer` around per-iteration setup (rarely
  correct; see below).

**Do not use when.**

- The body's result is unused: the compiler may delete the call. Assign it
  to a package-level sink variable of a concrete type (a `var sink any`
  boxes and allocates by itself).
- Setup precedes the loop without `b.ResetTimer()`: setup is timed, and it
  reruns for every `b.N` round.
- Per-iteration `StopTimer`/`StartTimer` wraps a body of a few hundred ns:
  the timer calls dominate; restructure so setup runs once.

**Example.**

```go
func BenchmarkJoinLegacyN(b *testing.B) {
    w := words(100)
    b.ReportAllocs()
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        benchStr = JoinCandidate(w, ",") // package-level string sink
    }
}
```

Runnable: `BenchmarkJoinLegacyN` in `assets/examples/constructs/bench_test.go`.

**Cost removed.** As in the b.Loop card: timed setup and eliminated work.

**Verify.**

1. Every `b.N` benchmark assigns its result to a sink or otherwise consumes
   it, and calls `b.ResetTimer()` after non-trivial setup.
1. `go test -run '^$' -bench BenchmarkJoinLegacyN -benchmem` reports the
   same `allocs/op` as the `b.Loop` candidate (both 1 locally).

## ReportAllocs and -benchmem

**Definition.** `b.ReportAllocs()` enables malloc statistics for one
benchmark; `-benchmem` enables them for all. The output gains `B/op` and
`allocs/op` columns
([testing.B.ReportAllocs](https://pkg.go.dev/testing#B.ReportAllocs)).

**Use when.**

- Any allocation card is being applied: `allocs/op` is its primary metric.

**Do not use when.**

- You need retained (live) memory: `B/op` counts allocated bytes, not
  bytes that stay reachable. Use the [heap profile][heap-card] with
  `-sample_index=inuse_space`.
- The benchmark runs under `-race`: the race runtime changes allocation.

**Example.** `b.ReportAllocs()` inside `compare` in `bench_test.go`;
command line:

```sh
go test -run '^$' -bench 'BenchmarkBuilder' -benchmem -count 10 .
```

Runnable: `compare` in `assets/examples/constructs/bench_test.go`.

**Cost removed.** Nothing by itself; it exposes the allocation cost. Local
row: `BenchmarkJoinLegacyN-10 ... 1024 B/op 1 allocs/op`.

**Verify.**

1. The output lines contain `B/op` and `allocs/op` for the benchmarks you
   compare.
1. The candidate's `allocs/op` agrees with the `testing.AllocsPerRun`
   oracle for the same input. The two can differ slightly: locally
   `BenchmarkMapHint` reported 15 -> 5 allocs/op while AllocsPerRun
   reported 17 -> 6. Compare benchmark with benchmark and oracle with
   oracle.

## Parallel benchmark with RunParallel

**Definition.** `b.RunParallel(func(pb *testing.PB))` runs the body in
`GOMAXPROCS` goroutines (scaled by `b.SetParallelism`) and distributes
`b.N` iterations among them while `pb.Next()` returns true
([testing.B.RunParallel](https://pkg.go.dev/testing#B.RunParallel)).

**Use when.**

- The cost under test is contention: locks, atomics, pools, shared maps.

**Do not use when.**

- The code is single-threaded in production: parallel numbers measure
  something it never does.
- The body calls `b.StartTimer`, `b.StopTimer`, or `b.ResetTimer`: the docs
  forbid them inside RunParallel.

**Example.**

```go
b.Run("impl=candidate", func(b *testing.B) {
    var c AtomicCounter
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            c.Inc()
        }
    })
})
```

Runnable: `BenchmarkCounter` in `assets/examples/constructs/bench_test.go`.

**Cost removed.** Exposes lock and cache-line contention that sequential
benchmarks hide. Vary parallelism with `-cpu 1,4,10`.

**Verify.**

1. `go test -run '^$' -bench BenchmarkCounter -cpu 1,4,10 -count 10`.
1. benchstat rows per `-cpu` value show how the cost scales.

## AllocsPerRun allocation oracle

**Definition.** `testing.AllocsPerRun(runs, f)` calls `f` once as warm-up,
then returns the average number of heap allocations per call over `runs`
calls. It sets `GOMAXPROCS` to 1 while measuring
([testing.AllocsPerRun](https://pkg.go.dev/testing#AllocsPerRun)).

**Use when.**

- A card claims fewer allocations: assert the claim in a test so a
  regression fails it.

**Do not use when.**

- The test binary runs with `-race`: counts change. Guard the file with
  `//go:build !race`.
- The input hits an allocation-free runtime fast path, so a zero proves
  nothing. Local examples: `strconv.Itoa` of 0..99, strings converted into
  32-byte stack buffers, and small values boxed into interfaces.
- The code uses `sync.Pool`: the GC may empty the pool at any time, so
  assert "fewer than baseline", never "exactly zero".

**Example.**

```go
func fewer(t *testing.T, name string, baseline, candidate func()) {
    t.Helper()
    b := testing.AllocsPerRun(100, baseline)
    c := testing.AllocsPerRun(100, candidate)
    t.Logf("ALLOCS %s: %.0f -> %.0f per op", name, b, c)
    if c >= b {
        t.Fatalf("%s: candidate %.0f, baseline %.0f", name, c, b)
    }
}
```

Runnable: `fewer` in `assets/examples/constructs/allocs_test.go`.

**Cost removed.** Unverified allocation claims. Local oracle output for
every allocation card is quoted in [allocation](allocation.md).

**Verify.**

1. `sh assets/examples/verify.sh verify` prints one `ALLOCS name: B -> C`
   line per pair, and the test fails if C is not below B.
1. `sh assets/examples/verify.sh race` must still pass: the build tag
   removes the allocation file under `-race`.

## Equivalence oracle test

**Definition.** A test that runs baseline and candidate on the same
inputs, including empty, boundary, error, and aliasing cases, and fails on
any observable difference: result, error text and identity (`errors.Is`),
panic, nil versus empty, ordering, or mutation of caller data.

**Use when.**

- Always, before measuring: a faster candidate that computes something
  else is not a result.

**Do not use when.**

- Never skip it. If the old code has no tests, keep the old function as
  `xBaseline` in a test file until the comparison passes.

**Example.**

```go
func TestDotEquivalent(t *testing.T) {
    a, b := ints(100), ints(120)
    if DotBaseline(a, b) != DotCandidate(a, b) {
        t.Fatal("dot differs")
    }
    for _, f := range []func([]int, []int) int{DotBaseline, DotCandidate} {
        func() {
            defer func() {
                if recover() == nil {
                    t.Fatal("short b must panic in both")
                }
            }()
            f(a, b[:50])
        }()
    }
}
```

Runnable: `TestDotEquivalent` in
`assets/examples/constructs/equiv_test.go`. This test caught a real bug
while the skill was written: the reslice `b = b[:len(a)]` succeeded within
`cap(b)` and read past `len(b)` instead of panicking.

**Cost removed.** Rework after a semantic change ships as a speedup.

**Verify.**

1. `go test -count 1 -run 'Equivalent|Aliasing' ./...` passes.
1. Mutate the candidate (for example drop a boundary check) and confirm the
   oracle fails; an oracle that never fails proves nothing.

## benchstat comparison

**Definition.** `benchstat` from `golang.org/x/perf/cmd/benchstat` reads
`go test -bench` output and reports medians, 95% confidence intervals, and,
for A/B comparisons, p-values from the Mann-Whitney U-test; `~` marks no
statistically significant difference. Run each benchmark at least 10 times
([benchstat](https://pkg.go.dev/golang.org/x/perf/cmd/benchstat)).

**Use when.**

- Any timing or allocation claim is reported.

**Do not use when.**

- You would rerun until the difference becomes significant: the benchstat
  docs call that statistical bias.
- Baseline and candidate ran on different machines, toolchains, power
  states, or with different `GOMAXPROCS`.

**Example.**

```sh
go test -run '^$' -bench . -benchmem -count 10 . > bench.txt
go run golang.org/x/perf/cmd/benchstat@latest -col /impl bench.txt
# Two revisions instead of two sub-benchmarks:
go run golang.org/x/perf/cmd/benchstat@latest old.txt new.txt
```

`-col /impl` compares the `impl=baseline` and `impl=candidate`
sub-benchmark keys in one file. Local output lines are quoted in each card.

Runnable: `sh assets/examples/verify.sh measure`.

**Cost removed.** False speedups from noise. Metric: the `vs base`
column, a percentage with `p=` below 0.05, or `~`.

**Verify.**

1. `BENCHSTAT='go run golang.org/x/perf/cmd/benchstat@latest'
   sh assets/examples/verify.sh measure` writes `bench-results/bench.txt`
   and prints the table.
1. A claimed change has a non-`~` entry with `n=10` samples on both sides.

## CPU profile from go test

**Definition.** `go test -cpuprofile cpu.pprof` samples on-CPU stacks while
the tests and benchmarks run; `go tool pprof` reports flat (self) and cum
(inclusive) time per function
([diagnostics](https://go.dev/doc/diagnostics)).

**Use when.**

- CPU time or latency is the complaint and no hot function is known yet.
- After a change, to confirm the cost left the named function instead of
  moving into a callee.

**Do not use when.**

- The program is waiting, not computing (I/O, locks, channels): on-CPU
  samples miss blocked time. Use the
  [block and mutex profiles](#block-and-mutex-profiles) or the
  [execution trace](#execution-trace).
- Another profiler runs at the same time: the diagnostics page warns
  that profilers interfere with each other.

**Example.**

```sh
go test -run '^$' -bench 'BenchmarkInline' -cpuprofile cpu.pprof \
    -o pkg.test .
go tool pprof -top -nodecount 15 pkg.test cpu.pprof
go tool pprof -list 'SumUint16Baseline' pkg.test cpu.pprof
go tool pprof -http=:8080 pkg.test cpu.pprof  # flame graph
```

Run it in a scratch copy: `-cpuprofile` also writes the test binary to
the current directory. Verification tier: `-top` executed through
`verify.sh profile`; `-list` and `-http` were not run in this skill's
verification.

Runnable: `sh assets/examples/verify.sh profile`.

**Cost removed.** Guessing. Metric: the target function's flat/cum
percentage before and after the change.

**Verify.**

1. `sh assets/examples/verify.sh profile` prints `pprof -top` for CPU.
1. After the change, the same command shows the target's `flat%` reduced
   and no new function taking its place.

## Heap profile with alloc_space and inuse_space

**Definition.** `go test -memprofile mem.pprof` writes the heap profile.
`-sample_index=alloc_space` (or `alloc_objects`) shows everything allocated
since start; the default `inuse_space` shows live objects as of the last
GC ([runtime/pprof](https://pkg.go.dev/runtime/pprof#Profile)). The
profile samples allocations; `-memprofilerate=1` records every one, at a
large cost.

**Use when.**

- `allocs/op` or GC CPU is high: use `alloc_space` to find the site.
- Resident memory grows: use `inuse_space` to find what is retained.

**Do not use when.**

- You would judge allocation churn from `inuse_space`, or a leak from
  `alloc_space`: each answers the other question.

**Example.**

```sh
go test -run '^$' -bench 'BenchmarkStrconv' -benchmem \
    -memprofile mem.pprof -o pkg.test .
go tool pprof -top -sample_index=alloc_space pkg.test mem.pprof
go tool pprof -top -sample_index=inuse_space pkg.test mem.pprof
```

Runnable: `sh assets/examples/verify.sh profile`.

**Cost removed.** Attribution of allocation to the wrong site. Metric: the
`alloc_space` share of the target function, and `B/op` in the benchmark.

**Verify.**

1. `sh assets/examples/verify.sh profile` prints the `alloc_space` top list.
1. After the change, the function no longer appears in the top entries,
   and the benchmark's `allocs/op` matches the AllocsPerRun oracle.

## Block and mutex profiles

**Definition.** The block profile records where goroutines wait on
synchronization (channels, `sync` primitives); the mutex profile records
the holders of contended mutexes. Both are off by default and enabled with
`runtime.SetBlockProfileRate` and `runtime.SetMutexProfileFraction`, or by
`go test -blockprofile` and `-mutexprofile`
([diagnostics](https://go.dev/doc/diagnostics)).

**Use when.**

- Wall time is high but the CPU profile is flat or mostly idle.
- Throughput stops scaling with `-cpu` in a RunParallel benchmark.

**Do not use when.**

- You would leave `SetBlockProfileRate(1)` on in production without
  measuring its overhead: it records every blocking event.

**Example.**

```sh
go test -run '^$' -bench 'BenchmarkSharded' -cpu 10 \
    -mutexprofile mutex.pprof -blockprofile block.pprof -o pkg.test .
go tool pprof -top pkg.test mutex.pprof
```

Runnable: `BenchmarkSharded` in `assets/examples/constructs/bench_test.go`.

**Cost removed.** Contention misread as CPU cost. Metric: contention
delay attributed to the lock site, before and after
[per-worker aggregation](concurrency-io.md#per-worker-aggregation).
Local run of the command above (one profile covering both
sub-benchmarks): `CountWordsBaseline.func1` cum 572.34ms (60.76%),
`CountWordsCandidate.func1` cum 352.26ms (37.40%). The candidate still
contends while it merges its local maps.

**Verify.**

1. The baseline's mutex profile names the lock site
   (`CountWordsBaseline.func1` with go1.27.1; closure names can change
   between releases).
1. After the change, that site's delay drops; the lock-acquisition oracle in
   `TestShardedAggregation` goes from 650 to 4.

## Execution trace

**Definition.** `runtime/trace` (or `go test -trace trace.out`) records
scheduler, syscall, GC, and goroutine events; `go tool trace` renders them.
The diagnostics page recommends it for latency and poor parallelism, not
for finding CPU hot spots
([diagnostics](https://go.dev/doc/diagnostics)). Go 1.25
adds `trace.FlightRecorder`, an in-memory ring buffer that snapshots the
last few seconds on demand
([Go 1.25 notes](https://go.dev/doc/go1.25)).

**Use when.**

- Worker pools, channels, or GC pauses are suspected of idling CPUs.
- Tail latency is the metric and it is not explained by CPU samples.

**Do not use when.**

- You need a hot-function ranking: use the CPU profile.
- You would trace a long production run continuously: use the flight
  recorder.

**Example.**

```sh
go test -run '^$' -bench 'BenchmarkWorkerPool' -benchtime 100x \
    -trace trace.out .
go tool trace trace.out
```

Runnable: `sh assets/examples/verify.sh profile`.

**Cost removed.** Idle processors and scheduling gaps that no profile
shows. Metric: goroutine analysis and processor utilization views.

**Verify.**

1. `sh assets/examples/verify.sh profile` writes `bench-results/trace.out`
   (executed).
1. `go tool trace` opens it in a browser; compare processor utilization
   for the baseline and candidate sub-benchmarks (the UI was not opened in
   this skill's verification).

## GC trace with GODEBUG=gctrace=1

**Definition.** `GODEBUG=gctrace=1` makes the runtime print one line per GC
cycle to stderr with heap sizes, CPU time, and pause times
([gc-guide](https://go.dev/doc/gc-guide),
[runtime](https://pkg.go.dev/runtime#hdr-Environment_Variables)).

**Use when.**

- Deciding whether allocation work or [GOGC/GOMEMLIMIT](runtime.md)
  tuning matters: count cycles and GC CPU on the real workload.

**Do not use when.**

- Production tooling would parse its format: use `runtime/metrics`,
  whose names are stable.

**Example.**

```sh
GODEBUG=gctrace=1 ./server 2>gctrace.log
grep -c '^gc ' gctrace.log   # GC cycles during the run
```

Runnable: `GODEBUG=gctrace=1 go test -run TestGOGCReducesCycles .` in
`assets/examples/constructs/`.

**Cost removed.** Tuning the GC without knowing how often it runs. Metric:
cycle count and the `% CPU` field per line.

**Verify.**

1. The log contains `gc N @...` lines.
1. After an allocation card or a GOGC change, the same workload logs fewer
   cycles (the runnable `TestGOGCReducesCycles` shows the direction).

## Goroutine leak profile

**Definition.** The `goroutineleak` profile (general availability in Go
1.27, experimental in 1.26) reports goroutines blocked on a primitive that
no runnable goroutine can reach, so they can never wake. It is available
through `runtime/pprof` and as `/debug/pprof/goroutineleak` in
`net/http/pprof` ([Go 1.27 notes](https://go.dev/doc/go1.27)).

**Use when.**

- A concurrency change (worker pools, batching, pipelines) could leave
  senders or receivers blocked forever.
- Goroutine counts grow over time in production.

**Do not use when.**

- The toolchain is older than 1.27 (1.26 needs `GOEXPERIMENT`): use the
  `goroutine` profile and compare counts before and after instead.

**Example.**

```go
func TestNoLeakedGoroutines(t *testing.T) {
    before := leakCount(t) // "goroutineleak profile: total N"
    HashAllCandidate(ints(100), 4)
    SumViaChannelCandidate(ints(100), 16)
    if after := leakCount(t); after != before {
        t.Fatalf("leak profile changed: %q -> %q", before, after)
    }
}
```

Runnable: `assets/examples/constructs/leak_test.go`. `leakCount` calls
`pprof.Lookup("goroutineleak").WriteTo(&buf, 1)` and returns the header
line. `TestLeakProfileDetectsLeak` leaks one goroutine on purpose and
polls until the profile's total increases, which proves the oracle can
fail. Detection runs during GC, so it misses a goroutine that has not yet
reached its blocking operation.

**Cost removed.** Leaked goroutines and the memory their stacks pin.
Metric: the `total N` header of the profile before and after the workload.

**Verify.**

1. `go test -count 3 -shuffle on -run Leak -v .` passes; the log shows
   `total 0 -> total 1` for the deliberate leak.
1. After a concurrency change, the leak total for the workload does not
   increase.

[heap-card]: #heap-profile-with-alloc_space-and-inuse_space
