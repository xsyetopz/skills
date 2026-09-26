# Allocation constructs

Each card removes heap allocations or copies from a measured hot path.
Baseline/candidate pairs live in
[`alloc.go`](../assets/examples/constructs/alloc.go) and
[`dispatch.go`](../assets/examples/constructs/dispatch.go); `equiv_test.go`
proves equivalence and `allocs_test.go` asserts the allocation claim with
`testing.AllocsPerRun`.

Local numbers come from one machine: Apple M1 Max, macOS 27.0,
`go1.27.1 darwin/arm64`. `ALLOCS` lines come from
`sh assets/examples/verify.sh verify`; timing lines come from
`go test -run '^$' -bench . -benchmem -count 10 -benchtime 500ms` summarized
by benchstat `-col /impl` (median, `vs base` with p-value).

## Contents

- Preallocated slice capacity
- Map size hint
- strings.Builder with Grow
- strconv append functions instead of fmt
- bytes.Buffer reused with Reset
- string(b) in map lookups and comparisons
- sync.Pool of pointer-shaped objects
- sync.Pool element type: pointer, not slice
- clear to reuse a map
- Struct map keys instead of concatenated strings
- slices.Sort instead of sort.Slice
- Sorted map keys with a presized slice
- Copying a small sub-slice out of a large buffer
- Return small structs by value
- Generic functions instead of interface slices
- Struct field order and padding

## Preallocated slice capacity

**Definition.** `make([]T, 0, n)` allocates a backing array of capacity `n`
once; `append` then writes in place until `len == cap`. Without it, `append`
reallocates and copies whenever capacity runs out
([spec: appending](https://go.dev/ref/spec#Appending_and_copying_slices)).

**Use when.**

- The final length, or a tight upper bound, is known before the loop
  (`len(input)`, a count from a header).
- `alloc_space` in the heap profile points at `growslice`.

**Do not use when.**

- The bound is far larger than the typical result (a filter that keeps 1%
  of rows): you allocate and zero memory that is never used.
- Callers compare the result to `nil`: `make(..., 0, 0)` is non-nil and
  empty, while a `var out []T` that never appends stays `nil`. The oracle
  `TestPreallocEquivalent` pins this difference.
- The slice you append to is a view that shares spare capacity with
  another owner: `append` overwrites that owner's elements
  (`TestAppendAliasing`). Use `slices.Clip` or copy first.

**Example.**

```go
func SquaresCandidate(values []int) []int {
    out := make([]int, 0, len(values))
    for _, v := range values {
        out = append(out, v*v)
    }
    return out
}
```

Runnable: `SquaresBaseline`/`SquaresCandidate` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** Growth reallocations and copies. Local oracle:
`ALLOCS prealloc-slice: 9 -> 1 per op` for 1,000 ints.
Local benchstat:

```text
Prealloc-10 3.398µ ± 9% 1.677µ ± 20% -50.64% (p=0.000 n=10)
```

**Verify.**

1. `go test -run 'TestPreallocEquivalent|TestAppendAliasing' .`
1. `go test -run TestAllocsPrealloc -v .` prints the ALLOCS line; benchstat
   on `BenchmarkPrealloc` shows lower `allocs/op` and `B/op`.

## Map size hint

**Definition.** `make(map[K]V, n)` sizes the map for about `n` entries so
inserts up to `n` do not trigger incremental growth
([spec: making maps](https://go.dev/ref/spec#Making_slices_maps_and_channels)).

**Use when.**

- The number of distinct keys is known or bounded before insertion.

**Do not use when.**

- The hint is much larger than the typical key count: the map allocates
  the full table up front and never shrinks it
  ([golang/go#20135](https://github.com/golang/go/issues/20135)).

**Example.**

```go
index := make(map[string]int, len(keys))
for i, k := range keys {
    index[k] = i
}
```

Runnable: `IndexBaseline`/`IndexCandidate` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** Map growth rehashing. Local oracle:
`ALLOCS map-size-hint: 17 -> 6 per op` for 1,000 keys.
Local benchstat:

```text
MapHint-10 34.12µ ± 6% 18.29µ ± 4% -46.39% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestMapHintEquivalent .` compares with `maps.Equal`.
1. `go test -run TestAllocsMapHint -v .`; benchstat `BenchmarkMapHint`.

## strings.Builder with Grow

**Definition.** `strings.Builder` appends into one growing `[]byte` and
returns it as a string without copying; `Grow(n)` guarantees space for `n`
more bytes without another allocation
([strings.Builder](https://pkg.go.dev/strings#Builder.Grow)). Repeated
`s += x` allocates a new string for every concatenation.

**Use when.**

- A string is built by concatenation in a loop.
- The final length is cheap to compute (sum of part lengths): call `Grow`.

**Do not use when.**

- The parts are already a `[]string` with one separator: call
  `strings.Join`, which sizes its buffer itself.
- You would copy a non-zero `Builder` value: the docs forbid it, and
  writing to the copy panics.

**Example.**

```go
n := len(sep) * (len(parts) - 1)
for _, p := range parts {
    n += len(p)
}
var b strings.Builder
b.Grow(n)
for i, p := range parts {
    if i > 0 {
        b.WriteString(sep)
    }
    b.WriteString(p)
}
return b.String()
```

Runnable: `JoinBaseline`/`JoinCandidate` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** One string allocation per concatenation. Local oracle:
`ALLOCS strings-builder: 198 -> 1 per op` for 100 parts; the test also
asserts exactly 1 allocation remains after `Grow`.
Local benchstat:

```text
Builder-10 19328.0n ± 5% 954.0n ± 3% -95.06% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestJoinEquivalent .` compares against `strings.Join`
   including empty, Unicode, and empty-separator cases.
1. `go test -run TestAllocsBuilder -v .`.

## strconv append functions instead of fmt

**Definition.** `strconv.AppendInt(dst, v, base)` formats directly into a
caller-owned `[]byte`; `fmt.Sprintf("%d", v)` parses a format string,
boxes `v` into an interface, and allocates a new string
([strconv](https://pkg.go.dev/strconv#AppendInt)).

**Use when.**

- Numbers, booleans, floats, or quoted strings are formatted in a loop.

**Do not use when.**

- The output depends on `fmt` verbs such as `%v` for arbitrary types or
  `%x` of a struct: `strconv` does not reproduce them.
- It is a one-off message or an error path: the readability cost buys
  nothing.

**Example.**

```go
buf := make([]byte, 0, len(values)*21) // 20 digits + sign, 1 comma
for i, v := range values {
    if i > 0 {
        buf = append(buf, ',')
    }
    buf = strconv.AppendInt(buf, int64(v), 10)
}
return string(buf)
```

Runnable: `CSVBaseline`/`CSVCandidate` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** Two allocations per formatted value. Local oracle:
`ALLOCS strconv-append: 408 -> 2 per op` for 200 values.
Local benchstat:

```text
Strconv-10 13.374µ ± 3% 2.607µ ± 2% -80.51% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestCSVEquivalent .` includes `math.MinInt64`,
   `math.MaxInt64`, 0, and -1.
1. `go test -run TestAllocsStrconv -v .`.

## bytes.Buffer reused with Reset

**Definition.** `buf.Reset()` sets the length to zero and keeps the
capacity, so an owner that renders repeatedly reuses the same storage
([bytes.Buffer.Reset](https://pkg.go.dev/bytes#Buffer.Reset)).

**Use when.**

- One goroutine renders many messages sequentially (an encoder, a logger
  writer, a response builder) and consumes each result before the next.

**Do not use when.**

- The caller keeps the returned `[]byte` after the next call: it aliases
  the reused buffer and is overwritten (`TestRenderEquivalentAndAliasing`).
  Document "valid until the next call" or return a copy.
- The owner is shared between goroutines without a lock.
- One rare huge message would pin a huge buffer for the owner's
  lifetime.

**Example.**

```go
type Renderer struct{ buf bytes.Buffer }

// Render's result is valid until the next Render call.
func (r *Renderer) Render(rows []string) []byte {
    r.buf.Reset()
    for _, row := range rows {
        r.buf.WriteString(row)
        r.buf.WriteByte('\n')
    }
    return r.buf.Bytes()
}
```

Runnable: `RenderBaseline`/`Renderer.Render` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** The buffer's growth allocations per call. Local oracle:
`ALLOCS buffer-reset: 5 -> 0 per op`; the test also asserts 0.
Local benchstat:

```text
BufferReuse-10 977.1n ± 3% 574.8n ± 2% -41.18% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestRenderEquivalentAndAliasing .` checks output and
   proves the aliasing hazard exists.
1. `go test -run TestAllocsBufferReuse -v .`.

## string(b) in map lookups and comparisons

**Definition.** The gc compiler does not allocate for `m[string(b)]` when
`m` is a `map[string]T` and `b` is a `[]byte`, nor for `string(b)` used
only in a comparison, nor for `[]byte(s)` used only as a `range`
expression ([compiler optimizations wiki][wiki-opt]).
The spec itself says a conversion yields a new value; these are compiler
optimizations, not language guarantees
([spec: conversions][spec-conv]).

**Use when.**

- Bytes read from I/O are looked up in a string-keyed map or compared to a
  string constant.

**Do not use when.**

- The converted string is stored, returned, or passed on (the baseline's
  `keep(key)`): the string must exist, so it allocates. Convert once and
  reuse the string instead of converting twice.
- You would use `unsafe.String` to avoid the copy: the string then aliases
  mutable memory and breaks when `b` changes.
- The code counts characters: `len(s)` counts bytes and
  `utf8.RuneCountInString` counts runes; do not swap them while
  optimizing.

**Example.**

```go
for _, w := range words {
    total += m[string(w)] // no allocation for the lookup
}
```

Runnable: `LookupBaseline`/`LookupCandidate` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** One string allocation per lookup. Local oracle with
keys longer than 32 bytes: `ALLOCS map-string-bytes: 100 -> 0 per op`.
Keys up to 32 bytes that do not escape may already use a stack buffer, so
test with realistic key lengths.
Local benchstat:

```text
Conversion-10 2.900µ ± 4% 1.447µ ± 4% -50.11% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestLookupEquivalent .` includes a missing key and `nil`.
1. `go test -run TestAllocsConversion -v .` asserts 0 for the candidate.

## sync.Pool of pointer-shaped objects

**Definition.** `sync.Pool` caches temporary objects for reuse across
goroutines. The runtime may drop any pooled item at any time; the docs
aim pools at objects shared by many independent concurrent clients, not
at free lists inside short-lived objects
([sync.Pool](https://pkg.go.dev/sync#Pool)).

**Use when.**

- A temporary buffer or encoder state is allocated per request on a
  concurrent hot path, and `alloc_space` shows it.

**Do not use when.**

- The object carries state between uses and is not reset: the next user
  sees stale or secret data. Call `Reset` after `Get`.
- The result aliases the pooled object after `Put` (for example returning
  `buf.Bytes()`): copy out first (`buf.String()`).
- Buffers can grow without bound: put back only below a size cap, or a
  single large request pins memory in the pool.
- The object must persist (a cache, a connection pool): the GC drops pool
  contents.

**Example.**

```go
var bufPool = sync.Pool{New: func() any { return new(bytes.Buffer) }}

func EncodeCandidate(fields []string) string {
    buf := bufPool.Get().(*bytes.Buffer)
    buf.Reset()
    for _, f := range fields {
        buf.Write(strconv.AppendQuote(buf.AvailableBuffer(), f))
        buf.WriteByte(' ')
    }
    s := buf.String() // copy before Put
    if buf.Cap() <= 64<<10 {
        bufPool.Put(buf)
    }
    return s
}
```

Runnable: `EncodeBaseline`/`EncodeCandidate` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** The per-call buffer allocation. Local oracle:
`ALLOCS sync-pool-buffer: 2 -> 1 per op` (the remaining one is the result
string). The oracle asserts "fewer", never zero, because the GC may empty
the pool.
Local benchstat:

```text
PoolBuffer-10 1.447µ ± 3% 1.309µ ± 3% -9.51% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestPoolEquivalent .` calls the candidate three times per
   input to prove reuse does not leak previous contents.
1. `go test -run TestAllocsPool -v .`; `TestPoolConcurrent` runs eight
   goroutines against the pool, and `sh assets/examples/verify.sh race`
   runs it under the race detector.

## sync.Pool element type: pointer, not slice

**Definition.** Putting a non-pointer value such as a `[]byte` into a pool
converts it to `any`, which heap-allocates a copy of the slice header;
storing `*[]byte` avoids it
([staticcheck SA6002](https://staticcheck.dev/docs/checks/#SA6002)).

**Use when.**

- A pool holds slices, or any non-pointer value.

**Do not use when.**

- The value is already a pointer (`*bytes.Buffer`, `*T`): nothing to fix.

**Example.**

```go
var ptrPool = sync.Pool{New: func() any {
    b := make([]byte, 0, 512)
    return &b
}}

func ChecksumPtrPool(data []byte) uint32 {
    p := ptrPool.Get().(*[]byte)
    buf := append((*p)[:0], data...)
    sum := fold(buf)
    *p = buf // keep grown capacity
    ptrPool.Put(p)
    return sum
}
```

Runnable: `ChecksumSlicePool`/`ChecksumPtrPool` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** One allocation per `Put`. Local oracle:
`ALLOCS sync-pool-pointer: 1 -> 0 per op`.
Local benchstat:

```text
PoolPointer-10 473.1n ± 2% 428.5n ± 2% -9.44% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestPoolEquivalent .`.
1. `go test -run TestAllocsPool -v .`. `staticcheck ./...` documents
   SA6002 for this pattern; it was not run for this skill.

## clear to reuse a map

**Definition.** `clear(m)` (Go 1.21+) deletes all entries of a map, leaving
it empty; for a slice it zeroes elements up to `len`
([spec: Clear](https://go.dev/ref/spec#Clear)). Reusing a cleared map
avoids reallocating its table for the next batch.

**Use when.**

- A scratch map is rebuilt for every batch or request in a loop owned by
  one goroutine.

**Do not use when.**

- One batch can be far larger than the rest: the cleared map keeps its
  largest size, because maps do not shrink
  ([golang/go#20135](https://github.com/golang/go/issues/20135)).
- Another owner still reads the map.
- The module's `go` directive is below 1.21.

**Example.**

```go
seen := make(map[string]struct{})
for _, batch := range batches {
    clear(seen)
    for _, s := range batch {
        seen[s] = struct{}{}
    }
    distinct += len(seen)
}
```

Runnable: `BatchCountsBaseline`/`BatchCountsCandidate` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** Table allocation and growth per batch. Local oracle for
3 batches of 200 words: `ALLOCS clear-map: 27 -> 9 per op` (the remaining
allocations are the first batch's growth).
Local benchstat:

```text
Clear-10 17.32µ ± 4% 11.19µ ± 3% -35.42% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestClearEquivalent .` includes an empty batch between
   non-empty ones.
1. `go test -run TestAllocsClear -v .`.

## Struct map keys instead of concatenated strings

**Definition.** Any comparable struct can be a map key
([spec: map types](https://go.dev/ref/spec#Map_types)). A struct key hashes
its fields directly; `m[a+" "+b]` builds a new string per lookup.

**Use when.**

- A map is keyed by two or more fields joined into a string.

**Do not use when.**

- The key is persisted or sent over the wire as a string: keep the string
  form at that boundary.
- A field is a slice, map, or function: the struct is not comparable and
  does not compile as a key.

**Example.**

```go
type routeKey struct{ method, path string }

func RouteCandidate(m map[routeKey]int, method, path string) (int, bool) {
    v, ok := m[routeKey{method, path}]
    return v, ok
}
```

Runnable: `RouteBaseline`/`RouteCandidate` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** One string allocation per lookup, and key ambiguity:
`("GET /b", "c")` and `("GET", "/b c")` concatenate to the same string, and
`TestStructKeysEquivalentAndUnambiguous` shows the baseline returning a
false hit. Local oracle with a 42-byte key:
`ALLOCS struct-key: 1 -> 0 per op`. Keys of 32 bytes or less may already
build in a stack buffer and show 0 in the baseline.
Local benchstat:

```text
StructKey-10 41.13n ± 3% 18.12n ± 2% -55.94% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestStructKeysEquivalentAndUnambiguous .`.
1. `go test -run TestAllocsStructKey -v .`.

## slices.Sort instead of sort.Slice

**Definition.** `slices.Sort` (Go 1.21+) is a generic sort for ordered
element types; `sort.Slice` takes `any` plus a `less` closure and swaps
through `reflectlite.Swapper` (`src/sort/slice.go`)
([slices](https://pkg.go.dev/slices#Sort),
[sort.Slice](https://pkg.go.dev/sort#Slice)).

**Use when.**

- Elements are `cmp.Ordered` (use `slices.Sort`) or you have a comparison
  (use `slices.SortFunc(xs, func(a, b T) int)`).

**Do not use when.**

- You need a stable sort: use `slices.SortStableFunc`; `slices.Sort` is not
  stable, like `sort.Slice`.
- Elements are floats that can be NaN: `slices.Sort` orders NaNs before
  other values, while `sort.Slice` with `a < b` leaves them wherever the
  algorithm happens to put them, so the outputs can differ.

**Example.**

```go
func SortCandidate(xs []int) { slices.Sort(xs) }
```

Runnable: `SortBaseline`/`SortCandidate` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** Reflection-based swapping and the interface and
closure allocations. Local oracle: `ALLOCS slices-sort: 2 -> 0 per op` for 500
ints.
Local benchstat:

```text
Sort-10 15.525µ ± 3% 5.018µ ± 2% -67.68% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestSortEquivalent .` checks `slices.IsSorted` and equality.
1. `go test -run TestAllocsSort -v .`.

## Sorted map keys with a presized slice

**Definition.** Map iteration order is unspecified and changes between
iterations ([spec: for range](https://go.dev/ref/spec#For_range),
[maps.Keys](https://pkg.go.dev/maps#Keys)), so deterministic output needs
sorted keys. `slices.Sorted(maps.Keys(m))` collects
from an iterator without knowing the size; collecting into
`make([]K, 0, len(m))` and calling `slices.Sort` allocates once.

**Use when.**

- Keys are sorted on a hot path (serialization, canonical hashing,
  diff output).

**Do not use when.**

- It is not hot: `slices.Sorted(maps.Keys(m))` is clearer.
- Callers distinguish `nil` from empty: `slices.Sorted` returns `nil` for
  an empty map, and the presized form returns an empty non-nil slice
  (`TestSortedKeysEquivalent` pins this).

**Example.**

```go
keys := make([]string, 0, len(m))
for k := range m {
    keys = append(keys, k)
}
slices.Sort(keys)
```

Runnable: `SortedKeysBaseline`/`SortedKeysCandidate` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** Growth reallocations while collecting. Local oracle for
500 keys: `ALLOCS sorted-keys: 13 -> 1 per op`.
Local benchstat:

```text
SortedKeys-10 43.43µ ± 3% 41.43µ ± 4% -4.59% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestSortedKeysEquivalent .` repeats five times because map
   order changes between iterations.
1. `go test -run TestAllocsSortedKeys -v .`.

## Copying a small sub-slice out of a large buffer

**Definition.** A sub-slice shares the backing array of the original, so
keeping `packet[:8]` keeps the whole packet reachable. `bytes.Clone` or
`slices.Clone` copies the small part into its own array
([bytes.Clone](https://pkg.go.dev/bytes#Clone)).

**Use when.**

- A small part of a large read buffer is retained (cached, stored in a
  map, sent to another goroutine) and `inuse_space` shows the large
  buffers alive.

**Do not use when.**

- The sub-slice is consumed immediately: the copy adds one allocation and
  removes nothing.
- The caller relies on seeing later writes through the view.

**Example.**

```go
func HeaderCandidate(packet []byte) []byte {
    return bytes.Clone(packet[:8])
}
```

Runnable: `HeaderBaseline`/`HeaderCandidate` in
`assets/examples/constructs/alloc.go`.

**Cost removed.** Retained memory, at the price of one extra allocation.
The oracle `TestHeaderRetention` asserts `cap` 1 MiB for the baseline view
and under 1 KiB for the clone, and that the clone does not see later writes.

**Verify.**

1. `go test -run TestHeaderRetention .`.
1. For the real program: `go tool pprof -sample_index=inuse_space` before
   and after; the large buffer's allocation site shrinks.

## Return small structs by value

**Definition.** Escape analysis moves a variable to the heap when the
compiler cannot prove it does not outlive its frame; a non-inlined
function that returns `&T{}` makes the value escape
([gc-guide][gc-heap]).
Returning `T` by value lets the caller keep it on its stack.

**Use when.**

- `-gcflags=-m` reports `&T{...} escapes to heap` for a small struct that
  callers only read.

**Do not use when.**

- Callers need shared identity or mutation through the pointer.
- The struct is large (hundreds of bytes) and copied many times: measure
  the copy cost.
- `nil` is part of the API: replace it with an explicit `ok bool` (the
  example does) and update every caller.

**Example.**

```go
func ParseHeaderCandidate(line string) (Header, bool) {
    name, value, ok := strings.Cut(line, ":")
    if !ok {
        return Header{}, false
    }
    // ... validation as in the baseline ...
    return Header{Name: name, Value: value, Size: len(line)}, true
}
```

Runnable: `ParseHeaderBaseline`/`ParseHeaderCandidate` in
`assets/examples/constructs/escape_baseline.go` and `escape_candidate.go`.

**Cost removed.** One heap allocation per call. Local compiler output:
`./escape_baseline.go:24:9: &Header{...} escapes to heap`; none for the
candidate. Local oracle: `ALLOCS return-by-value: 1 -> 0 per op`.
Local benchstat:

```text
Escape-10 45.87n ± 7% 32.41n ± 2% -29.33% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestHeaderParseEquivalent .`.
1. `sh assets/examples/verify.sh diagnostics` asserts the escape lines;
   `go test -run TestAllocsEscape -v .`.

## Generic functions instead of interface slices

**Definition.** Converting a non-pointer value to an interface stores a
pointer to a copy of it, which usually heap-allocates; a generic function
instantiated on a concrete type works on the values directly
([spec: interface types](https://go.dev/ref/spec#Interface_types),
[type parameters](https://go.dev/ref/spec#Type_parameter_declarations)).

**Use when.**

- A hot loop builds `[]Iface` or `[]any` from concrete values only to call
  one method.

**Do not use when.**

- The slice really mixes dynamic types.
- A `nil` check on the interface was the point: an interface holding a
  typed nil pointer is not `nil` (`TestInterfaceEquivalentAndTypedNil`);
  keep the nil semantics identical.

**Example.**

```go
type Areas[S Shape] []S

func (a Areas[S]) Total() float64 {
    total := 0.0
    for _, s := range a {
        total += s.Area()
    }
    return total
}
```

`AreaCandidate` in `dispatch.go` converts the `[]Rect` to `Areas` of
`Rect` and calls `Total`; the conversion copies no elements.

Runnable: `AreaBaseline`/`AreaCandidate` in
`assets/examples/constructs/dispatch.go`.

**Cost removed.** One allocation per boxed element, plus the interface
slice. Local oracle for 200 rects: `ALLOCS generic-no-boxing: 201 -> 0 per
op`.
Local benchstat:

```text
Boxing-10 9.546µ ± 19% 1.716µ ± 17% -82.03% (p=0.000 n=10)
```

**Verify.**

1. `go test -run TestInterfaceEquivalentAndTypedNil .`.
1. `go test -run TestAllocsBoxing -v .`.

## Struct field order and padding

**Definition.** A struct's alignment is the largest alignment of its
fields ([spec: size and alignment][spec-size]),
and the compiler pads between fields to satisfy each field's alignment.
Ordering fields from largest to smallest alignment removes interior
padding. Separately, the GC stops scanning a value at its last pointer,
so putting pointer fields first can reduce scan work when GC cost is the
metric
([gc-guide](https://go.dev/doc/gc-guide)).

**Use when.**

- Many instances live at once (large slices, caches) and `inuse_space` or
  RSS is the metric.

**Do not use when.**

- The struct is serialized by memory layout (`encoding/binary` on the
  struct, cgo, `unsafe` offsets): reordering changes the layout.
- Field order documents meaning and only a few instances exist.

**Example.**

```go
type EventPadded struct { // 32 bytes on 64-bit
    Active  bool
    ID      int64
    Retries uint8
    Offset  int32
    Urgent  bool
}

type EventPacked struct { // 16 bytes on 64-bit
    ID      int64
    Offset  int32
    Retries uint8
    Active  bool
    Urgent  bool
}
```

Runnable: `EventPadded`/`EventPacked` in
`assets/examples/constructs/dispatch.go`.

**Cost removed.** Padding bytes per instance. Local test log:
`EventPadded 32 B, EventPacked 16 B` (darwin/arm64).

**Verify.**

1. `go test -run TestPadding -v .` asserts the packed type is smaller.
1. Compare `unsafe.Sizeof(T{})` before and after, and multiply by the live
   instance count to predict the `inuse_space` change.

[wiki-opt]: https://go.dev/wiki/CompilerOptimizations
[spec-conv]:
  https://go.dev/ref/spec#Conversions_to_and_from_a_string_type
[gc-heap]:
  https://go.dev/doc/gc-guide#Eliminating_heap_allocations
[spec-size]:
  https://go.dev/ref/spec#Size_and_alignment_guarantees
