# Go Performance Gotchas

Measure with `go test -run '^$' -bench X -benchmem -count 10`, compare with
`benchstat old.txt new.txt`, and attribute cost with `-cpuprofile`, `-memprofile`
(`go tool pprof -sample_index=alloc_space -top`), and `GODEBUG=gctrace=1` (PowerShell:
`$env:GODEBUG='gctrace=1'`). Keep the module's `go` directive; do not raise it to reach a newer
construct unless asked.

## Contents

- [Measurement](#measurement)
- [Allocation](#allocation)
- [Compiler](#compiler)
- [Concurrency and I/O](#concurrency-and-io)
- [Runtime Settings](#runtime-settings)

## Measurement

- Mistake: `for i := 0; i < b.N; i++` whose result is unused, or a `b.Loop` on a module below Go
  1.24. Fix: on 1.24+ write `for b.Loop()` (it keeps call arguments and results alive and runs setup
  once); below that, keep `b.N` and assign the result to a package-level sink. Do not use both in
  one function, and do not write `b.Loop()` in any other loop form, because only that exact form
  gets the keep-alive handling. Before Go 1.26 the `b.Loop` body was not inlined, so tiny functions
  can show extra allocations there.
- Mistake: one `-count 1` run or rerunning until benchstat reports a difference. Fix: `-count 10` on
  a quiet machine with the same `GOMAXPROCS`; keep a change only when benchstat shows the target
  metric moved (p < 0.05) and nothing else regressed. A `~` means revert.
- Mistake: `testing.AllocsPerRun` assertions under `-race`, or asserting exactly zero for code that
  uses `sync.Pool`. Fix: tag them `//go:build !race` and assert an upper bound.
- Mistake: example inputs that do not allocate. Fix: `strconv.Itoa` of 0..99, short non-escaping
  strings, and small boxed values take allocation-free paths and make the baseline look free. Use
  realistic values.
- Mistake: comparing baseline and candidate from two separate runs on different days. Fix: put both
  as `impl=baseline` and `impl=candidate` sub-benchmarks and compare with `benchstat -col /impl`.
- Mistake: profiling a benchmark and assuming it matches production. Fix: capture a CPU profile from
  the real binary under production-like load (`net/http/pprof` on an internal-only listener;
  profiling production needs the user's approval) for PGO and for checking that the benchmark covers
  the hot path.

## Allocation

- Mistake: `make([]T, 0, n)` with an oversized bound. Fix: presize only when the bound is close to
  the typical result; a filter that keeps 1% of rows allocates and zeroes the rest for nothing.
  Callers that compare the result to `nil` observe `make(..., 0, 0)` as non-nil, unlike a
  `var out []T` that never appends.
- Mistake: appending to a sub-slice that shares spare capacity with another owner. Fix:
  `slices.Clip` or copy first; `append` overwrites the owner's elements.
- Mistake: a large map size hint or `clear(m)` for a map that once held a huge batch. Fix: maps
  never shrink ([golang/go#20135](https://github.com/golang/go/issues/20135)); allocate a new map
  when batch sizes vary widely. `clear` needs Go 1.21.
- Mistake: copying a `strings.Builder` value, or using a Builder when the parts are already a
  `[]string` with one separator. Fix: pass a pointer and call `Grow`; use `strings.Join`, which
  sizes its own buffer. Writing to a copied non-zero Builder panics.
- Mistake: `fmt.Sprintf("%d", n)` in a loop. Fix: `strconv.AppendInt(buf, n, 10)` into a reused
  buffer. Keep `fmt` when verbs such as `%v` or `%x` of a struct define the output.
- Mistake: reusing a `bytes.Buffer` and returning `buf.Bytes()`. Fix: the slice aliases the buffer
  and is overwritten on the next call; return a copy or document "valid until next call". Unbounded
  growth from one huge message pins memory for the owner's lifetime.
- Mistake: `string(b)` in a map lookup assumed to allocate. Fix: the compiler skips the copy for
  `m[string(b)]` and comparisons; do not convert once into a variable first. If the string is stored
  or returned, it must be allocated. Never use `unsafe.String` over memory that can change.
- Mistake: `sync.Pool` of slices or pooled objects that carry state. Fix: pool pointers
  (`*bytes.Buffer`, `*T`), because putting a slice value allocates on every `Put`; `Reset` after
  `Get`; copy out before `Put`; put back only below a size cap. The GC empties pools, so never use
  one as a cache.
- Mistake: map keys built as `a + ":" + b`. Fix: a comparable struct key. Keep the string form where
  the key is persisted or sent. A struct with a slice, map, or func field is not comparable.
- Mistake: small sub-slices keeping a big buffer alive. Fix: `slices.Clone` or `bytes.Clone` the
  small part (visible as `inuse_space`).
- Mistake: `sort.Slice` in hot code. Fix: `slices.Sort` or `slices.SortFunc` (Go 1.21) avoid
  reflection-based swaps and interface calls.
- Mistake: `[]any` built from concrete values in hot code. Fix: a generic function; boxing allocates
  for values that are not pointer shaped or small constants.
- Mistake: iterating a map and expecting deterministic output after optimizing. Fix: sort keys into
  a presized slice when output order is observable.
- Mistake: reordering struct fields without checking users. Fix: order by decreasing alignment only
  for types with many live instances; unsafe offset users and `encoding/binary` layouts break.

## Compiler

- Mistake: guessing what escapes. Fix: read `go build -gcflags=-m` (escape) and `-gcflags=-m=2`
  (inlining budget of 80 nodes); `&T{...} escapes to heap` for small structs often disappears by
  returning by value.
- Mistake: adding `_ = s[n-1]` hints blindly. Fix: check `-gcflags=-d=ssa/check_bce/debug=1` for
  `Found IsInBounds` before and after; a rewrite that leaves the count unchanged measures as `~`.
- Mistake: a `defer` inside a `for` loop. Fix: defers run at function exit, not per iteration;
  extract the loop body into a function. Conversely, keep `defer mu.Unlock()` in small hot
  functions: open-coded defers are cheap, and removing it risks a lock leaking on panic.
- Mistake: value receivers on large structs called in loops. Fix: pointer receivers, unless method
  sets matter for interfaces or the copy is needed for safety.
- Mistake: adopting PGO without a representative profile. Fix: put a merged production CPU profile
  at `default.pgo` in the main package directory (Go 1.21+), rebuild, and measure end to end; it
  changes the whole binary and can shift inlining elsewhere.

## Concurrency and I/O

- Mistake: one goroutine per item for a large input. Fix: a bounded worker pool (`errgroup.SetLimit`
  or N workers on a channel); confirm the goroutines exit with the goroutine profile after errors or
  cancel.
- Mistake: one channel send per small item. Fix: send batches (slices) of items; a channel operation
  costs a lock and possibly a park.
- Mistake: a mutex around one counter. Fix: `atomic.Int64` (Go 1.19). For many workers updating a
  shared map, aggregate per worker and merge at the end.
- Mistake: many small `Write` calls to a file or socket, or byte-at-a-time reads. Fix:
  `bufio.Writer` (and `Flush` before close or error exit) and `bufio.Scanner`; raise
  `Scanner.Buffer` for lines over 64 KiB or it fails with `token too long`.

## Runtime Settings

- Mistake: raising `GOGC` without a memory ceiling. Fix: pair `GOGC` with `GOMEMLIMIT` (a soft limit
  that makes the GC work harder near it) inside containers, and read `gctrace` output to confirm GC
  CPU dropped. Setting `GOMEMLIMIT` near the container limit with `GOGC=off` can cause GC thrash
  instead of OOM.
- Mistake: default `GOMAXPROCS` inside a CPU-limited container on older Go versions. Fix: Go 1.25
  made it respect cgroup CPU limits; on earlier versions set it explicitly or use `automaxprocs`.
  Throttling shows as latency spikes with low average CPU.
