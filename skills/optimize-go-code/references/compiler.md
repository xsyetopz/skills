# Compiler constructs

These cards read and influence gc compiler decisions: escape analysis,
inlining, bounds-check elimination, profile-guided optimization, receiver
choice, and defer lowering. Compiler diagnostics in
`sh assets/examples/verify.sh diagnostics` or `pgo` check each claim, and a
benchmark measures it.

Local numbers come from one machine: Apple M1 Max, macOS 27.0,
`go1.27.1 darwin/arm64`, benchstat `-col /impl` over `-count 10
-benchtime 500ms`. Compiler limits quoted from source are pinned to
`go1.27.1`; they change between releases.

## Contents

- Escape analysis report with -gcflags=-m
- Inlining budget with -gcflags=-m=2
- Cold-path outlining to fit the inlining budget
- Bounds-check elimination with a length guard
- Profile-guided optimization with default.pgo
- Pointer receivers for large structs
- Extract the loop body so defer runs per iteration
- Keep defer in small hot functions

## Escape analysis report with -gcflags=-m

**Definition.** `-gcflags=-m` prints the compiler's escape-analysis and
inlining decisions per source position (`escapes to heap`,
`moved to heap: x`, `does not escape`); `-m=2` and `-m=3` add the reasons
([gc-guide][gc-heap]).

**Use when.**

- The heap profile or `allocs/op` points at a function and you need to know
  which expression allocates and why.

**Do not use when.**

- The output comes from a different package or build tags than
  production: decisions depend on inlining, which depends on the whole
  build.
- The "escapes to heap" line is on a cold error path: only lines inside
  measured hot paths matter.

**Example.**

```sh
go build -gcflags=-m . 2>&1 | grep 'escape_'
# ./escape_baseline.go:24:9: &Header{...} escapes to heap
go build -gcflags='-m=2' . 2>&1 | grep -A3 'Header{...} escapes'
```

`-gcflags=all=-m` includes dependencies. The build cache replays the
output, so repeated runs print it again.

Runnable: `assets/examples/constructs/escape_baseline.go` and
`escape_candidate.go`; `sh assets/examples/verify.sh diagnostics`.

**Cost removed.** Guessing which line allocates. Metric: the count of
`escapes to heap` / `moved to heap` lines in the hot function, which must
match the `allocs/op` change.

**Verify.**

1. `sh assets/examples/verify.sh diagnostics` asserts at least one
   `escapes to heap` line in `escape_baseline.go` and none in
   `escape_candidate.go`.
1. The paired allocation oracle (`TestAllocsEscape`) drops 1 -> 0.

## Inlining budget with -gcflags=-m=2

**Definition.** The gc compiler inlines a function whose cost (roughly its
IR node count) is at most `inlineMaxBudget = 80`; a non-inlinable call
inside it adds `inlineExtraCallCost = 57`
(`inline/inl.go` in the [compiler source at go1.27.1][compile-src]).
`-gcflags=-m=2` prints `can inline F with cost N` or
`cannot inline F: function too complex: cost N exceeds budget 80`.

**Use when.**

- A small helper called in a hot loop shows up as its own frame in the
  CPU profile, and the call overhead is large relative to its work.

**Do not use when.**

- The function runs rarely or does heavy work per call: its call
  overhead is noise.
- You would use `//go:noinline` or build flags such as `-l` to "fix" a
  benchmark: production builds do not use them.

**Example.**

```sh
go build -gcflags=-m=2 . 2>&1 | grep 'inline (\*Reader)'
# ./inline.go:18:6: cannot inline (*Reader).Uint16Baseline:
#   function too complex: cost 132 exceeds budget 80
# ./inline.go:38:6: can inline (*Reader).Uint16Candidate with cost 49
```

Runnable: `Uint16Baseline`/`Uint16Candidate` in
`assets/examples/constructs/inline.go`; `sh assets/examples/verify.sh
diagnostics`.

**Cost removed.** Nothing by itself; it shows how far a function is over
budget and which calls cost the most.

**Verify.**

1. `sh assets/examples/verify.sh diagnostics` prints and asserts both
   lines.
1. Check the call site too: `inlining call to (*Reader).Uint16Candidate`
   must appear at the hot caller's line.

## Cold-path outlining to fit the inlining budget

**Definition.** Move expensive, rarely taken work (error formatting,
logging, slow fallbacks) out of a hot function so the rest fits the
inlining budget. In the example, the hot function returns a small error
struct that formats itself lazily in `Error`, instead of calling
`fmt.Errorf`.

**Use when.**

- `-m=2` shows the hot function over budget, with most of the cost in a
  branch that rarely runs.

**Do not use when.**

- Callers inspect the concrete error type: `fmt.Errorf` with `%w` returns
  `*fmt.wrapError`, the candidate returns `*ShortError`. The text and
  `errors.Is(err, ErrShort)` are preserved (`TestInlineEquivalent`), but a
  type switch on the old type would break.
- The move only replaces one non-inlinable call with another: each still
  costs 57, so a fast path plus one outlined call rarely fits under 80
  (locally, three such variants scored 92 to 98).

**Example.**

```go
type ShortError struct{ Off, Len int }

func (e *ShortError) Error() string {
    return fmt.Sprintf("offset %d of %d: %v", e.Off, e.Len, ErrShort)
}

func (e *ShortError) Unwrap() error { return ErrShort }

func (r *Reader) Uint16Candidate() (uint16, error) {
    if r.off+2 > len(r.buf) {
        return 0, &ShortError{Off: r.off, Len: len(r.buf)}
    }
    v := uint16(r.buf[r.off]) | uint16(r.buf[r.off+1])<<8
    r.off += 2
    return v, nil
}
```

Runnable: `ShortError` and `Uint16Candidate` in
`assets/examples/constructs/inline.go`.

**Cost removed.** The call and its register spills per iteration. Local
compiler output: cost 132 -> 49. Local benchstat for `BenchmarkInline`
(4 KiB input, 2,048 calls per op):
`Inline-10 5.293µ ± 3% 2.386µ ± 3% -54.93% (p=0.000 n=10)`. An
intermediate candidate that sliced `b := r.buf[r.off:]` also inlined
(cost 43) but measured 15% slower than the baseline: inlining is not a
speedup until the benchmark shows one.

**Verify.**

1. `go test -run 'TestInlineEquivalent|TestSumUint16Equivalent' .`.
1. `sh assets/examples/verify.sh diagnostics`, then benchstat on
   `BenchmarkInline`: keep the change only with a significant decrease.

## Bounds-check elimination with a length guard

**Definition.** The compiler's prove pass removes index bounds checks it
can prove redundant; `-gcflags=-d=ssa/check_bce/debug=1` prints each check that
remains as `Found IsInBounds` or `Found IsSliceInBounds` (phase list from
`go tool compile -d=ssa/help`).

**Use when.**

- A hot loop indexes a second slice by the first slice's index, and the
  check shows in the CPU profile or disassembly.

**Do not use when.**

- The hint would be `b = b[:len(a)]`: reslicing succeeds up to `cap(b)`
  and silently reads past `len(b)` instead of panicking. This skill's
  equivalence oracle caught exactly that bug.
- You would use `unsafe` pointer arithmetic to drop checks: a wrong index
  then corrupts memory instead of panicking.
- Removing the check does not move the benchmark: on the local M1 Max the
  predictable branch cost nothing measurable (see below). Revert.

**Example.**

```go
func DotCandidate(a, b []int) int {
    if len(b) < len(a) {
        panic("DotCandidate: len(b) < len(a)")
    }
    sum := 0
    for i := range a {
        sum += a[i] * b[i] // proven in range: no check
    }
    return sum
}
```

Runnable: `assets/examples/constructs/bce_baseline.go` and
`bce_candidate.go` (separate files so the per-file diagnostic count is
exact).

**Cost removed.** One compare-and-branch per iteration. Local compiler
output: `./bce_baseline.go:7:18: Found IsInBounds`; nothing for the
candidate. Local benchstat for 4,096 elements:
`BCE-10 1.563µ ± 2% 1.578µ ± 3% ~ (p=1.000 n=10)`: no significant change.

**Verify.**

1. `go test -run TestDotEquivalent .` requires both versions to panic on a
   short `b` that has spare capacity.
1. `sh assets/examples/verify.sh diagnostics` asserts the check count; then
   benchstat decides whether the change is kept.

## Profile-guided optimization with default.pgo

**Definition.** With a CPU pprof profile named `default.pgo` in the main
package directory, `go build` (default `-pgo=auto`, Go 1.21+) uses it to
inline hot calls beyond the normal budget and to devirtualize hot interface
calls. PGO was a preview in Go 1.20 and generally available from Go 1.21;
the Go team reports 2 to 14% improvement for a representative
set of programs as of Go 1.22 ([PGO guide](https://go.dev/doc/pgo),
[Go 1.21 notes](https://go.dev/doc/go1.21)). The hot-call budget is
`inlineHotMaxBudget = 2000`
(`inline/inl.go` in the [compiler source at go1.27.1][compile-src]).

**Use when.**

- You build a binary (a main package) and can collect a representative
  CPU profile, ideally from production via `net/http/pprof`.

**Do not use when.**

- The profile comes from a microbenchmark: the PGO guide says
  microbenchmarks are usually poor candidates.
- The code is a library: `-pgo=auto` reads `default.pgo` from the main
  package directory of the binary being built and rebuilds all packages,
  dependencies included, for that profile (PGO FAQ). The application owns
  the profile, not the library.
- The profile cannot be committed: builds become irreproducible. The
  guide recommends committing `default.pgo`.

**Example.**

```sh
go build -pgo=off -o app ./cmd/app
./app -cpuprofile cmd/app/default.pgo   # or curl /debug/pprof/profile
go build -o app-pgo ./cmd/app          # picks up default.pgo
go version -m app-pgo | grep -- -pgo=  # proves the profile was used
go tool pprof -proto a.pprof b.pprof > merged.pprof  # merge instances
```

Runnable: `assets/examples/constructs/cmd/pgodemo/main.go`;
`verify.sh pgo` generates the profile in the temp copy and never writes
`default.pgo` into the skill.

**Cost removed.** Indirect calls and calls over the inlining budget on hot
paths. Local diagnostics: without a profile `cannot inline
fieldTokenizer.Next: function too complex: cost 100 exceeds budget 80`;
with it `PGO devirtualizing interface call tok.Next to fieldTokenizer.Next`
and `can inline fieldTokenizer.Next with cost 100`. Local end-to-end:
`hyperfine -N -w 2 -r 15 ./nopgo ./withpgo`: 1.456 s ± 0.016 s ->
1.359 s ± 0.011 s (1.07 ± 0.01 times faster).

**Verify.**

1. `sh assets/examples/verify.sh pgo` asserts the `-pgo=` build setting
   and the devirtualization and inlining lines.
1. Measure the application (hyperfine or the service's load test) with and
   without `-pgo=off`; microbenchmarks are not the evidence here.

## Pointer receivers for large structs

**Definition.** A value receiver gets a copy of the value; a pointer
receiver gets its address. The method set of `T` contains only value
methods, while `*T` has both ([spec: method sets][spec-methods]).

**Use when.**

- The struct is large (the example is 520 bytes) and a value-receiver
  method is called on a hot path.
- The method must mutate the receiver.

**Do not use when.**

- The type is small and immutable (a few words): copies are cheap and a
  value is safer to share.
- `T` must keep satisfying an interface that needs the method: after the
  switch only `*T` does.
- You would switch a mutating method the other way: with a value receiver
  the mutation goes to a copy and is lost (`TestReceivers`).

**Example.**

```go
type Stats struct {
    Buckets [64]int64
    Count   int64
}

func (s *Stats) TotalPointer() int64 {
    var t int64
    for _, b := range s.Buckets {
        t += b
    }
    return t + s.Count
}
```

Runnable: `Stats.TotalValue`/`TotalPointer` in
`assets/examples/constructs/dispatch.go`.

**Cost removed.** The receiver copy. Local benchstat:
`Receiver-10 39.76n ± 4% 32.27n ± 4% -18.84% (p=0.000 n=10)`.

**Verify.**

1. `go test -run TestReceivers .` checks totals and mutation semantics.
1. benchstat on `BenchmarkReceiver`.

## Extract the loop body so defer runs per iteration

**Definition.** A deferred call runs when the surrounding function
returns, not at the end of a loop iteration
([spec: defer statements](https://go.dev/ref/spec#Defer_statements)). The
compiler open-codes defers (inlines them at each exit, near-zero overhead
since [Go 1.14](https://go.dev/doc/go1.14)) only when the function has no
defer in a loop, at most 8 defers, and returns times defers at most 15,
and never in race builds
(`walk/stmt.go` and `ssagen/ssa.go` in the
[compiler source at go1.27.1][compile-src]).

**Use when.**

- A `defer` sits inside a `for` loop, usually `defer f.Close()` or
  `defer mu.Unlock()`.

**Do not use when.**

- The intent is to release everything at function exit (rare): make that
  explicit with a slice of cleanups instead.

**Example.**

```go
func ProcessCandidate(h *Handles, n int) int {
    done := 0
    for i := 0; i < n; i++ {
        done += processOne(h)
    }
    return done
}

func processOne(h *Handles) int {
    r := h.Open()
    defer r.Close() // runs at the end of each item; open-coded
    return 1
}
```

Runnable: `ProcessBaseline`/`ProcessCandidate` in
`assets/examples/constructs/deferloop.go`.

**Cost removed.** Resources held until return, and non-open-coded defer
records. Local oracle `TestDeferInLoop`: peak open handles 100 -> 1 for 100
items. With a mutex, the baseline deadlocks on the second iteration.

**Verify.**

1. `go test -run TestDeferInLoop -v .` asserts results, no leak, and the
   peak.
1. Find the pattern with `rg -n -B4 '^\s+defer ' -t go` and inspect hits
   whose preceding lines open a `for`; a semantic fix needs no benchmark.

## Keep defer in small hot functions

**Definition.** Since Go 1.14 most defers are open-coded, which the
release notes describe as "almost zero overhead compared to calling the deferred
function directly" ([Go 1.14 notes](https://go.dev/doc/go1.14)). Replacing
`defer mu.Unlock()` with an explicit unlock gives up panic safety: if the
code between lock and unlock panics, the mutex stays locked.

**Use when.**

- By default: keep `defer` for unlocks and closes.

**Do not use when.**

- A benchmark on your toolchain shows a significant difference and the
  function is one of the non-open-coded cases above (defer in a loop,
  more than 8 defers, many returns). Then restructure, keeping panic
  safety.

**Example.**

```go
func (c *Counter) GetDefer(k string) int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.n[k]
}
```

Runnable: `Counter.GetDefer`/`GetExplicit` in
`assets/examples/constructs/deferloop.go`.

**Cost removed.** None expected; this card prevents a panic-unsafe rewrite.
Local benchstat against the explicit-unlock version:
`DeferHot-10 16.76n ± 2% 16.71n ± 3% ~ (p=0.362 n=10)`.

**Verify.**

1. `go test -run TestDeferInLoop .` also compares `GetDefer` and
   `GetExplicit`.
1. benchstat on `BenchmarkDeferHot` shows `~`; if it does not on your
   toolchain, report the numbers before changing code.

[compile-src]:
  https://github.com/golang/go/tree/go1.27.1/src/cmd/compile/internal

[gc-heap]:
  https://go.dev/doc/gc-guide#Eliminating_heap_allocations
[spec-methods]: https://go.dev/ref/spec#Method_sets
