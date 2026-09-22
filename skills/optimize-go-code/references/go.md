# Profile and optimize Go programming-language code

Record Go version, GOOS/GOARCH, build tags, runtime settings, workload, and
concurrency. Use the repository's `go test` benchmarks and profiles. `-benchmem`
reports benchmark allocation metrics; a heap profile answers a different
question. Preserve raw runs and use the established `benchstat` tool when
comparing repeated benchmark results.

Separate CPU profiles, heap/allocation profiles, blocking/mutex profiles, and
execution traces. Contention, scheduling delay, GC, and network waits need
different observations. A CPU profile alone can miss the reason elapsed time is
high.

Inspect escape analysis when a suspected allocation matters, using the selected
compiler's diagnostics; do not assume every pointer escapes or every value stays
on the stack. Check interface boxing, closure capture, conversions, append
growth, map access, and data layout on the actual hot path. A reslice can retain
a large backing array; a small copy can reduce retained memory while increasing
immediate allocation.

Treat `sync.Pool` as a temporary reuse mechanism, not a lifetime or durable
cache guarantee. Reset reusable objects correctly and never access them after
return. Bound goroutine creation and channel queues according to the workload;
more goroutines are not automatically faster.

Use the race detector and correctness tests separately from release timing.
Preserve cancellation and error propagation when changing concurrency. Go
runtime/compiler behavior is version-sensitive; verify closure and loop-variable
semantics against the project's language/toolchain version rather than repeating
pre-change folklore.

Sources: [Go diagnostics](https://go.dev/doc/diagnostics),
[testing package](https://pkg.go.dev/testing), [benchstat][ref-benchstat],
[sync.Pool](https://pkg.go.dev/sync#Pool).

## Executable fixtures

Requires Go 1.23 or newer (local toolchain; no automatic upgrade) and POSIX `sh`
for the convenience runner.

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
[the go assets](../assets/examples). Copy that directory intact when adapting a
fixture. Run only the selected language, not all toolchains.

### Semantic regression cases

Source: [go.mod](../assets/examples/correctness/go.mod).

| Case | Required contract |
| --- | --- |
| 1 | append and shared backing arrays |
| 2 | Capacity retention versus a compact result |
| 3 | Typed nil inside an interface |
| 4 | Canonical ordering independent of traversal order |
| 5 | Unicode scalar count versus bytes |
| 6 | Value receiver versus authoritative state |
| 7 | Snapshot versus shared byte slice |
| 8 | Worker cancellation and completion handshake |

## Baseline and candidate

Use [the comparison sources](../assets/examples/comparisons) and their
expected-result checks. The
[shared contract](go-runtime-performance-executable-performance-fixtures.md)
explains input-domain limits and why these programs are not speed claims.

## Benchmark fixture

Work in a copy of [the go asset directory](../assets/examples). Run the
following commands relative to that copied directory.

The actual benchmark source is `comparisons/benchmark_test.go`; there is no
second wrapper or custom result format. With the selected Go toolchain:

```sh
cd comparisons
go test ./...
go test -run '^$' -bench . -benchmem -count 10 > baseline.txt
# Repeat with the candidate revision, otherwise identical, into candidate.txt.
# With the project's provisioned golang.org/x/perf/cmd/benchstat:
benchstat baseline.txt candidate.txt
```

The fixture uses `b.N` so it remains usable on the declared Go 1.23 baseline.
Use `B.Loop` in projects whose supported Go version provides it; do not silently
raise a project's minimum version for an example. Inspect setup and sink
placement before interpreting measurements. Run race detection separately from
timing. Allocation counts do not establish retained heap or absence of native
allocation. CPU/profile commands and heap interpretation are in the language
reference.

Sources: [source][source] and [source][source-2]

## Failure reproduction

Source: [the isolated reproducer](../assets/examples/reproduction). From the
skill root, run `sh assets/examples/verify.sh reproduction`. Direct commands
below assume a clean copy of the reproduction directory.

Expected: the saved view remains `[1 2]` after the owner grows.

Actual: both slices share spare capacity and the owner overwrites the second
element. The verifier copies and runs `repro.go` in a temporary directory.

[source]: https://pkg.go.dev/testing
[source-2]: https://pkg.go.dev/golang.org/x/perf/cmd/benchstat
[ref-benchstat]: https://pkg.go.dev/golang.org/x/perf/cmd/benchstat
[ref-the-fixture-execution-contract]:
  go-runtime-performance-executable-performance-fixtures.md
