# Concurrency and I/O constructs

Each card reduces goroutine, synchronization, or system-call cost without
changing results, ordering, or completion semantics. Pairs live in
[`concurrency.go`](../assets/examples/constructs/concurrency.go) and
[`io.go`](../assets/examples/constructs/io.go). Every oracle also runs under
`sh assets/examples/verify.sh race`.

Local numbers come from one machine: Apple M1 Max (10 cores, so
`GOMAXPROCS=10`), macOS 27.0, `go1.27.1 darwin/arm64`, benchstat
`-col /impl` over `-count 10 -benchtime 500ms`.

## Contents

- Bounded worker pool
- Batching channel sends
- Buffered channel between producer and consumer
- atomic.Int64 instead of a mutex-guarded counter
- Per-worker aggregation
- bufio.Writer for many small writes
- bufio.Scanner for line input

## Bounded worker pool

**Definition.** A fixed number of goroutines receive work from a channel
and exit when it closes; a `sync.WaitGroup` joins them.
`WaitGroup.Go` (Go 1.25+) starts a goroutine and counts it in one call
([sync.WaitGroup.Go](https://pkg.go.dev/sync#WaitGroup.Go)).

**Use when.**

- Code starts one goroutine per item for many items, and the goroutine
  count, scheduler time, or memory grows with input size.

**Do not use when.**

- Items are few and each blocks on I/O: the extra goroutines are cheap and
  a pool only adds queueing.
- Result order matters and workers append to a shared slice: the order
  changes between runs. Write by index, as the example does.
- The caller treats "all sent" as "all done": completion is `wg.Wait()`
  after `close(jobs)`, not the last send. The function must not return
  before its workers are joined.
- The module's `go` directive is below 1.25: use `wg.Add(1)` and
  `go func() { defer wg.Done(); ... }()`.

**Example.**

```go
out := make([]int, len(items))
jobs := make(chan int, workers)
var wg sync.WaitGroup
for range workers {
    wg.Go(func() {
        for i := range jobs {
            out[i] = hash(items[i])
        }
    })
}
for i := range items {
    jobs <- i
}
close(jobs) // workers leave their range loops
wg.Wait()   // done means joined, not scheduled
```

Runnable: `HashAllBaseline`/`HashAllCandidate` in
`assets/examples/constructs/concurrency.go`.

**Cost removed.** Goroutine creation and scheduling per item. The oracle
asserts goroutines started 500 -> 4 for 500 items and 4 workers. Local
benchstat for 2,000 items and 8 workers
(`BENCH_FILTER='Counter|WorkerPool' sh assets/examples/verify.sh measure`,
default benchtime):

```text
WorkerPool-10 911.9µ ± 3% 886.3µ ± 9% -2.81% (p=0.001 n=10)
WorkerPool-10 156.64Ki ± 0% 16.89Ki ± 0% -89.22% (p=0.000 n=10) B/op
WorkerPool-10 4002.00 ± 0% 19.00 ± 0% -99.53% (p=0.000 n=10) allocs/op
```

The time gain is small because each hash is cheap; memory and goroutine
count are the main effect. Decide by the metric you target.

**Verify.**

1. `go test -run TestWorkerPool -v .` checks equal ordered results and
   the goroutine count; `verify.sh race` checks races.
1. `TestNoLeakedGoroutines` checks the goroutineleak profile; benchstat on
   `BenchmarkWorkerPool`; the execution trace shows processor use.

## Batching channel sends

**Definition.** Each channel send and receive synchronizes the sender and
receiver; sending a slice of items per operation divides that cost by the
batch size. A buffered channel lets the sender run ahead by `cap` elements
before blocking ([spec: channel types](https://go.dev/ref/spec#Channel_types)).

**Use when.**

- A producer sends many small items (ints, small structs) and the profile
  shows `runtime.chansend`/`chanrecv` or the trace shows constant
  goroutine hand-offs.

**Do not use when.**

- Per-item latency matters: a batch waits until it is full or a timer
  flushes it. Add a time-bound flush if items trickle in.
- The producer reuses or mutates the batch slice after sending: the
  receiver sees the change. Send a fresh slice, or a read-only view of
  immutable data as the example does.

**Example.**

```go
ch := make(chan []int, 4)
go func() {
    for start := 0; start < len(items); start += batch {
        end := min(start+batch, len(items))
        ch <- items[start:end] // read-only view
    }
    close(ch)
}()
for chunk := range ch {
    for _, v := range chunk {
        sum += v
    }
}
```

Runnable: `SumViaChannelBaseline`/`SumViaChannelCandidate` in
`assets/examples/constructs/concurrency.go`.

**Cost removed.** Channel operations: the oracle asserts 1,000 sends ->
8 for 1,000 items and batch 128. Local benchstat for 10,000 items:
`Batching-10 351.09µ ± 3% 14.09µ ± 5% -95.99% (p=0.000 n=10)`.

**Verify.**

1. `go test -run TestBatching .` checks equal sums and send counts for 0,
   1, and 1,000 items.
1. benchstat on `BenchmarkBatching`.

## Buffered channel between producer and consumer

**Definition.** `make(chan T, n)` creates a channel whose sends succeed
without blocking while fewer than `n` elements are queued; with `n == 0`
every send waits for a receiver
([spec: channel types](https://go.dev/ref/spec#Channel_types)). The memory
model guarantees for an unbuffered channel that "a receive from an
unbuffered channel is synchronized before the completion of the
corresponding send"; for capacity C, only that the kth receive is
synchronized before the completion of the k+Cth send
([memory model](https://go.dev/ref/mem#chan)).

**Use when.**

- A producer and a consumer alternate in lockstep on an unbuffered channel
  and the trace or profile shows them parking on every item.
- Production and consumption are bursty and a bounded queue smooths them.

**Do not use when.**

- The code relies on the synchronous hand-off, "the send returned, so the
  receiver has the item" (a done signal, an ownership transfer, a
  rendezvous): with a buffer, the send returns before any receive.
- The size is a guess at "large enough to never block": a full buffer
  still blocks, and a buffer nobody drains hides a stalled consumer. Size
  it to a stated bound (burst size, worker count).
- The cost is the number of channel operations: buffering does not reduce
  them; [batch](#batching-channel-sends) instead.

**Example.**

```go
func SumBuffered(items []int, capacity int) int {
    return sumVia(make(chan int, capacity), items)
}

func sumVia(ch chan int, items []int) int {
    go func() {
        for _, v := range items {
            ch <- v
        }
        close(ch)
    }()
    sum := 0
    for v := range ch {
        sum += v
    }
    return sum
}
```

Runnable: `SumUnbuffered`/`SumBuffered` in
`assets/examples/constructs/concurrency.go`.

**Cost removed.** Goroutine park/unpark per item. Local benchstat for
10,000 items, capacity 128:

```text
ChannelBuffer-10 2056.1µ ± 14% 655.5µ ± 17% -68.12% (p=0.000 n=10)
ChannelBuffer-10 160.0 ± 1% 1200.0 ± 0% +650.00% (p=0.000 n=10) B/op
```

The buffer's memory is the price (1,200 B/op here).

**Verify.**

1. `go test -run TestChannelBuffering .` compares sums for 0, 1, and
   1,000 items; `verify.sh race`.
1. benchstat on `BenchmarkChannelBuffer`; review every send on the
   changed channel for code that assumes the receiver already has the item.

## atomic.Int64 instead of a mutex-guarded counter

**Definition.** `atomic.Int64` (Go 1.19+) provides `Add`, `Load`, `Store`,
and `CompareAndSwap` on one value without a lock; operations on it are
sequentially consistent under the memory model
([sync/atomic](https://pkg.go.dev/sync/atomic#Int64),
[memory model](https://go.dev/ref/mem#atomic)).

**Use when.**

- A lock protects exactly one integer or pointer that changes
  independently of other state (counters, gauges, generation numbers).

**Do not use when.**

- Two or more fields must change together (a count and a sum, a map and
  its size): separate atomics let readers see a torn state. Keep the lock.
- Many goroutines update the same counter at very high rates: the cache
  line still bounces; shard per worker and sum on read instead.

**Example.**

```go
type AtomicCounter struct{ n atomic.Int64 }

func (c *AtomicCounter) Inc()        { c.n.Add(1) }
func (c *AtomicCounter) Load() int64 { return c.n.Load() }
```

Runnable: `MutexCounter`/`AtomicCounter` in
`assets/examples/constructs/concurrency.go`.

**Cost removed.** Lock acquire and release per update. Local benchstat
with `RunParallel` on 10 procs:
`Counter-10 138.70n ± 7% 57.05n ± 12% -58.86% (p=0.000 n=10)`.

**Verify.**

1. `go test -run TestCounters .` and `verify.sh race` check that no update
   is lost (8 goroutines x 1,000).
1. `go test -run '^$' -bench BenchmarkCounter -cpu 1,4,10 -count 10`
   and benchstat.

## Per-worker aggregation

**Definition.** Each worker accumulates into state it owns alone and
merges into the shared result once, under the lock, when it finishes: one
lock acquisition per worker instead of one per item.

**Use when.**

- The mutex profile or a RunParallel benchmark shows contention on a
  shared map or counter updated per item.

**Do not use when.**

- Readers need live partial results during processing.
- Per-worker state is large (a full copy of a big map per worker): memory
  grows with the worker count. Locally the candidate took less time but
  allocated more (`Sharded-10` allocs/op 27 -> 87, B/op 53.51Ki ->
  265.05Ki).

**Example.**

```go
wg.Go(func() {
    local := make(map[string]int)
    for _, w := range shard {
        local[w]++
    }
    mu.Lock()
    for w, n := range local {
        counts[w] += n
    }
    mu.Unlock()
})
```

Runnable: `CountWordsBaseline`/`CountWordsCandidate` in
`assets/examples/constructs/concurrency.go`.

**Cost removed.** Lock acquisitions: the oracle asserts 650 -> 4 for four
shards. Local benchstat:
`Sharded-10 603.2µ ± 3% 220.9µ ± 10% -63.38% (p=0.000 n=10)`.

**Verify.**

1. `go test -run TestShardedAggregation .` compares the maps and the lock
   counts; `verify.sh race`.
1. benchstat on `BenchmarkSharded`, and the mutex profile before and after.

## bufio.Writer for many small writes

**Definition.** `bufio.NewWriter(w)` collects writes in a 4,096-byte buffer
(`defaultBufSize` in `src/bufio/bufio.go`) and calls the underlying
`Write` only when the buffer fills or on `Flush`
([bufio.Writer](https://pkg.go.dev/bufio#Writer)).

**Use when.**

- Code writes many small pieces to a file, socket, or pipe, and the
  profile shows `syscall.write`, or the writer is an `*os.File`.

**Do not use when.**

- `Flush` is not guaranteed on every path, including errors: the tail of
  the output is silently lost. Check the error from `Flush`.
- Each write must reach the peer immediately (interactive protocols):
  flushing per message removes the benefit.
- Each `Write` on the destination is already cheap, as with in-memory
  or no-op writers (`bytes.Buffer`, `strings.Builder`, `io.Discard`):
  `bufio` only adds a copy. Locally, against `io.Discard`, the buffered
  version was 12% slower; against `os.DevNull`, where each write is a
  syscall, it was far faster.

**Example.**

```go
bw := bufio.NewWriter(w)
var tmp [24]byte
for _, v := range values {
    line := append(strconv.AppendInt(tmp[:0], int64(v), 10), '\n')
    if _, err := bw.Write(line); err != nil {
        return err
    }
}
return bw.Flush()
```

Runnable: `WriteLinesBaseline`/`WriteLinesCandidate` in
`assets/examples/constructs/io.go`.

**Cost removed.** Write calls: the oracle asserts at most
`bytes/4096 + 1` calls; local log `write calls 2000 -> 4`. Local benchstat
writing 2,000 lines to `os.DevNull`:
`Writer-10 2477.37µ ± 5% 34.72µ ± 3% -98.60% (p=0.000 n=10)`.

**Verify.**

1. `go test -run TestBufferedWriter -v .` compares the bytes written and
   logs the call counts.
1. benchstat on `BenchmarkWriter`; for a real program, count `write`
   syscalls with the OS tracer you have (for example `strace -c` on Linux).

## bufio.Scanner for line input

**Definition.** `bufio.Scanner` reads the source in large chunks and
splits them into tokens (lines by default). Tokens larger than
`MaxScanTokenSize` (64 KiB) stop the scan with `bufio.ErrTooLong` unless
`Scanner.Buffer` raises the limit
([bufio.Scanner](https://pkg.go.dev/bufio#Scanner)).

**Use when.**

- Input is read with tiny `Read` calls (byte at a time) or through an
  unbuffered reader in a loop.

**Do not use when.**

- Lines can exceed 64 KiB and the code does not call
  `sc.Buffer(buf, max)`: the candidate fails where the old code worked
  (`TestBufferedReader` proves the `ErrTooLong` case).
- The code ignores `sc.Err()` after the loop: read errors disappear.
- The code keeps `sc.Bytes()` after the next `Scan`: the slice is
  overwritten. Use `sc.Text()` or copy.

**Example.**

```go
sc := bufio.NewScanner(r)
for sc.Scan() {
    n, err := strconv.Atoi(sc.Text())
    if err != nil {
        return 0, err
    }
    sum += n
}
return sum, sc.Err()
```

Runnable: `SumLinesBaseline`/`SumLinesCandidate` in
`assets/examples/constructs/io.go`.

**Cost removed.** Read calls: the oracle asserts at least a 100x reduction
(one per byte versus one per 4 KiB chunk); local log
`read calls 11557 -> 4`. Local benchstat over 2,000 lines from a
`strings.Reader`:
`Reader-10 63.20µ ± 9% 43.13µ ± 5% -31.76% (p=0.000 n=10)`.

**Verify.**

1. `go test -run TestBufferedReader -v .` checks empty input, a missing
   final newline, a long input, and `ErrTooLong`.
1. benchstat on `BenchmarkReader`.
