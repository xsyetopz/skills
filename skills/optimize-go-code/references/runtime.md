# Runtime configuration constructs

These settings change the whole process, not one function. Apply them only
with an application-level measurement, and state the deployment
consequence in the report. The runnable direction checks are in
[`gc_test.go`](../assets/examples/constructs/gc_test.go) (excluded under
`-race`).

Local numbers are machine-specific: Apple M1 Max, macOS 27.0,
`go1.27.1 darwin/arm64`. Since Go 1.26 the Green Tea garbage collector is
the default; the release notes expect a 10 to 40% reduction in GC overhead
for GC-heavy programs ([Go 1.26 notes](https://go.dev/doc/go1.26)), so
re-measure any GC tuning done on an older toolchain.

## Contents

- GOGC
- GOMEMLIMIT soft memory limit
- GOMAXPROCS

## GOGC

**Definition.** `GOGC` (default 100) sets the GC target: the heap may grow
to live heap plus (live heap + GC roots) x GOGC/100 before the next cycle
([runtime](https://pkg.go.dev/runtime#hdr-Environment_Variables),
[gc-guide](https://go.dev/doc/gc-guide)). The guide states: "doubling GOGC
will double heap memory overheads and roughly halve GC CPU cost, and vice
versa." `debug.SetGCPercent` changes it at run time; `GOGC=off` disables
the collector.

**Use when.**

- `gctrace` or the CPU profile (`runtime.gcBgMarkWorker`, `gcAssist`) shows
  significant GC CPU and the process has spare memory.

**Do not use when.**

- Memory is the constraint (containers near their limit): a higher GOGC
  raises peak heap; pair it with GOMEMLIMIT or leave it.
- The allocations can be removed instead: apply the allocation cards
  first; GOGC only trades memory for CPU.
- The code is a library: the setting is process-wide and belongs to the
  application's deployment configuration.

**Example.**

```go
func TestGOGCReducesCycles(t *testing.T) {
    var low, high uint32
    WithGC(50, math.MaxInt64, func() { low, _ = Churn(8<<20, 200_000) })
    WithGC(400, math.MaxInt64, func() { high, _ = Churn(8<<20, 200_000) })
    if high >= low {
        t.Fatalf("GOGC=400 ran %d cycles, GOGC=50 ran %d", high, low)
    }
}
```

Deployment form: `GOGC=200 ./server`.

Runnable: `TestGOGCReducesCycles` in
`assets/examples/constructs/gc_test.go`.

**Cost removed.** GC cycles and their CPU, paid for with heap size. Local
test logs for 200,000 x 1 KiB allocations with 8 MiB live, two runs:
`GOGC=50: 43, GOGC=400: 6` and `GOGC=50: 40, GOGC=400: 5`. Cycle counts
vary between runs; the test asserts only the direction.

**Verify.**

1. `go test -run TestGOGCReducesCycles -v .` (direction only).
1. For the application: `GODEBUG=gctrace=1` cycle count and GC CPU, plus
   peak RSS, before and after; report both sides of the trade.

## GOMEMLIMIT soft memory limit

**Definition.** `GOMEMLIMIT` (Go 1.19+) or `debug.SetMemoryLimit` sets a
soft limit on memory managed by the Go runtime (`Sys - HeapReleased`); the
GC runs more often as usage approaches it, even with `GOGC=off`. It
excludes the binary's mappings, C allocations, and OS memory held for the
process ([SetMemoryLimit](https://pkg.go.dev/runtime/debug#SetMemoryLimit),
[Go 1.19 notes](https://go.dev/doc/go1.19)). The runtime limits GC CPU to
about 50% to avoid thrashing near the limit.

**Use when.**

- The Go program is the only large consumer of a fixed memory reservation
  (a container limit). The gc-guide's rule of thumb is to "leave an
  additional 5-10% of headroom to account for memory sources the Go runtime
  is unaware of" ([gc-guide](https://go.dev/doc/gc-guide)).
- You raise GOGC (or set `GOGC=off`) as well, so the process uses memory
  up to the limit and collects less often while the heap is small.

**Do not use when.**

- The limit is below the program's live heap: the GC runs almost
  continuously (thrashing), as the gc-guide warns.
- The process shares memory with other programs, or its input size is
  unbounded (CLI tools, desktop apps): the guide advises against a limit
  there.
- cgo or `mmap` memory dominates: it is not counted.

**Example.**

```go
func TestMemoryLimitForcesCycles(t *testing.T) {
    var off, limited uint32
    WithGC(-1, math.MaxInt64, func() { off, _ = Churn(8<<20, 100_000) })
    WithGC(-1, 32<<20, func() { limited, _ = Churn(8<<20, 100_000) })
    if off != 0 || limited == 0 {
        t.Fatalf("off=%d limited=%d", off, limited)
    }
}
```

Deployment form: `GOMEMLIMIT=900MiB GOGC=off ./server` for a 1 GiB
container with nothing else in it.

Runnable: `TestMemoryLimitForcesCycles` in
`assets/examples/constructs/gc_test.go`.

**Cost removed.** Out-of-memory kills from an unbounded heap, or GC cycles
when the heap is far below the limit. Local test logs, three runs: 0 cycles
with `GOGC=off`, and 7, 10, and 8 cycles with `GOGC=off` plus a 32 MiB
limit.

**Verify.**

1. `go test -run TestMemoryLimitForcesCycles -v .` (direction only).
1. For the application: the runtime/metrics counter
   `/gc/limiter/last-enabled:gc-cycle` shows whether the CPU limiter
   engaged; RSS stays under the container limit under peak load.

## GOMAXPROCS

**Definition.** `GOMAXPROCS` sets the maximum number of CPUs that can
execute Go code simultaneously. Since Go 1.25, when it is not set, the
default considers the CPU affinity mask and, on Linux, the cgroup CPU
bandwidth limit, and the runtime updates it when those change; setting
`GOMAXPROCS` manually disables both behaviors
([runtime.GOMAXPROCS](https://pkg.go.dev/runtime#GOMAXPROCS),
[Go 1.25 notes](https://go.dev/doc/go1.25)).

**Use when.**

- A service in a CPU-limited container runs a Go version before 1.25: set
  `GOMAXPROCS` to the CPU limit so the scheduler does not run more threads
  than the quota allows; throttling shows up as latency spikes.
- A benchmark needs a fixed value: pass `-cpu N` to `go test`.

**Do not use when.**

- The toolchain is 1.25 or later and the default already matches the
  limit: a hard-coded value disables the automatic updates.
- The container sets only CPU requests: the runtime considers the limit,
  not the request.

**Example.**

```sh
go test -run '^$' -bench BenchmarkCounter -cpu 1,4,10 -count 10 .
GOMAXPROCS=2 ./server   # pre-1.25 container with a 2-CPU limit
```

Runnable: `BenchmarkCounter` in `assets/examples/constructs/bench_test.go`
with `-cpu`.

**Cost removed.** CFS throttling and over-subscription in CPU-limited
containers. Verification tier: not runnable here (macOS has no cgroups);
the benchmark `-cpu` sweep ran locally.

**Verify.**

1. Log `runtime.GOMAXPROCS(0)` at startup in the target environment and
   compare it with the container CPU limit.
1. Compare p99 latency and the container's throttled-time metric before
   and after.
