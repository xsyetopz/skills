# Async, event-loop, worker, and stream constructs

Baseline and candidate pairs live in
[`async.mjs`](../assets/examples/constructs/async.mjs), `cpu-worker.mjs`,
and `bun-io.mjs`. Every oracle awaits all work it starts.

Local numbers are machine-specific: Apple M1 Max, macOS arm64, node 26.8.2,
bun 1.4.2, from `TIME`, `TICKS`, `RENDERS`, and `PEAK` lines of
`sh assets/examples/verify.sh verify`.

## Contents

- Promise.all for independent awaits
- for...of with await instead of forEach(async)
- Bounded concurrency
- Drop redundant async wrappers and then chains
- return await inside try
- Coalesce notifications into one microtask
- Yield inside long synchronous loops
- worker_threads for CPU-bound work
- Transfer ArrayBuffers instead of copying
- stream.pipeline for backpressure
- Bun.file and Bun.write for file copies

## Promise.all for independent awaits

**Definition.** `for (...) await load(id)` starts each operation after the
previous one settles; `Promise.all(ids.map(load))` starts all of them, then
resolves with results in input order, or rejects with the first
rejection.

**Use when.**

- Awaited operations in a loop are independent and the downstream accepts
  them concurrently.

**Do not use when.**

- Side effects must happen in order (sequential writes).
- The list is large or unbounded: use bounded concurrency.
- Callers need every outcome: use `Promise.allSettled`. `Promise.all`
  rejects on the first failure while the other operations keep running
  unobserved.

**Example.**

```javascript
export const candidateFetchAll = (ids, load) =>
  Promise.all(ids.map((id) => load(id))); // all in flight, order kept
```

Runnable: `baselineFetchAll` / `candidateFetchAll` in `async.mjs`.

**Cost removed.** Serialized waiting. Local (5 loads of 20 ms): 105 → 21
ms on node and bun.

**Verify.**

1. `verify` compares results and order, and asserts the rejection case.
1. `verify` asserts concurrent time x 2.5 < sequential time.

## for...of with await instead of forEach(async)

**Definition.** `Array.prototype.forEach` ignores its callback's return
value, so `items.forEach(async (x) => { await save(x); })` returns before
any save finishes and drops rejections into unhandled-rejection handling.

**Use when.**

- Any `forEach(async` appears in code whose caller expects the work to be
  done (grep: `rg -n 'forEach\(async'`).

**Do not use when.**

- Never keep `forEach(async` for awaited work. For concurrency, use
  `Promise.all(items.map(...))` or the bounded pool below.

**Example.**

```javascript
export async function fixedSaveAll(items, save) {
  for (const item of items) await save(item);
}
```

Runnable: `brokenSaveAll` / `fixedSaveAll` in `async.mjs`.

**Cost removed.** A correctness bug that looks like a speedup: the broken
version "finishes" in 0 ms because it does not wait.

**Verify.**

1. `verify` asserts 0 saves complete when `brokenSaveAll` resolves and 2
   when `fixedSaveAll` resolves.
1. Benchmarks of async code must await the full operation; reject any
   candidate whose speedup comes from not awaiting.

## Bounded concurrency

**Definition.** A fixed number of async "lanes" pull the next index from a
shared counter until the input is exhausted, so at most `limit`
operations are in flight and results keep input order.

**Use when.**

- `Promise.all` over a large list overloads a downstream (connection
  pool, rate limit, file descriptors, memory).

**Do not use when.**

- The downstream already queues and limits (a database pool with its own
  queue) and the list is small.
- Operations must run strictly in order: use `limit = 1` or a loop.

**Example.**

```javascript
export async function mapLimit(items, limit, fn) {
  const results = new Array(items.length);
  let next = 0;
  async function lane() {
    while (next < items.length) {
      const index = next++;
      results[index] = await fn(items[index], index);
    }
  }
  const lanes = Math.min(limit, items.length);
  await Promise.all(Array.from({ length: lanes }, lane));
  return results;
}
```

Runnable: `mapLimit` in `async.mjs`.

**Cost removed.** Unbounded in-flight work (memory, downstream errors);
overlap stays. Observe the peak number of in-flight operations.

**Verify.**

1. `verify` asserts results in input order for out-of-order completion
   times, peak in-flight = 2 for `limit = 2`, and `[]` for empty input.
1. In the target system, record the downstream's concurrency or error rate
   before and after.

## Drop redundant async wrappers and then chains

**Definition.** Since V8 7.2, `await` on a native promise takes one
microtask tick instead of at least three
([fast async](https://v8.dev/blog/fast-async)). But an `async` function
that *returns* a promise resolves its own promise through
NewPromiseResolveThenableJob
([ECMA-262](https://tc39.es/ecma262/#sec-newpromiseresolvethenablejob)),
which adds ticks, and each `.then` adds one.

**Use when.**

- A hot path wraps a promise-returning call in `async () => call()` or
  adds identity `.then((v) => v)` steps with no transformation.

**Do not use when.**

- The wrapper exists to convert synchronous throws into rejections, or
  contains a `try` (see the next card).
- A profile of the real workload does not show the ticks; they matter
  only at very high promise rates.

**Example.**

```javascript
export const getValue = () => Promise.resolve(42);
export async function wrappedValue() {
  return getValue(); // resolving with a promise adds thenable-job ticks
}
// Call getValue() directly where the wrapper adds nothing.
```

Runnable: `getValue`, `wrappedValue`, `chainedValue`, and `ticksToSettle`
in `async.mjs`.

**Cost removed.** Microtask ticks per call. Local, node and bun: direct 1
tick, async wrapper 3, two identity `.then` steps 3, `return await` 2.

**Verify.**

1. `verify` asserts equal values and `direct < wrapped`, `direct <
   chained` using `ticksToSettle`.
1. The `TICKS` line prints the counts for each form.

## return await inside try

**Definition.** Inside `try`, `return promise` returns before the promise
settles, so a rejection bypasses the `catch`; `return await promise`
settles it inside the `try`. The
[await](https://tc39.es/ecma262/#await) step uses PromiseResolve, which
returns native promises unchanged.

**Use when.**

- An `async` function returns a promise from inside `try`/`catch` or
  `try`/`finally` and must handle its rejection or run cleanup after it.

**Do not use when.**

- Never drop the `await` from `return await` inside `try` as an
  "optimization". Outside `try` both forms are correct; locally `return
  await` took 2 ticks and `return promise` 3.

**Example.**

```javascript
export async function returnAwait() {
  try {
    return await failing(); // rejection is caught here
  } catch {
    return "handled";
  }
}
```

Runnable: `returnAwait` / `returnWithoutAwait` in `async.mjs`.

**Cost removed.** An escaped rejection (behavior bug) and one tick.

**Verify.**

1. `verify` asserts `returnAwait()` resolves `"handled"` and
   `returnWithoutAwait()` rejects.
1. The `TICKS` line shows `returnAwait` at 2.

## Coalesce notifications into one microtask

**Definition.** A setter records the change and schedules one
`queueMicrotask` flush if none is pending; all synchronous writes in the
same turn produce one notification with the final state.

**Use when.**

- A store, observer, or renderer is notified per write and writes arrive
  in synchronous bursts.

**Do not use when.**

- Listeners need every intermediate value (audit logs, undo history).
- Callers read derived state synchronously after a write: with batching
  it updates only after the current task.

**Example.**

```javascript
set(key, value) {
  state[key] = value;
  if (scheduled) return;
  scheduled = true;
  queueMicrotask(() => {
    scheduled = false;
    onChange({ ...state }); // one render per synchronous burst
  });
},
```

Runnable: `eagerStore` / `batchedStore` in `async.mjs`.

**Cost removed.** Redundant notifications (renders, recomputations).
Local: 3 writes → renders 3 → 1.

**Verify.**

1. `verify` asserts 0 renders before the microtask, 1 after, and the same
   final state as the eager store.
1. The `RENDERS` line prints both counts.

## Yield inside long synchronous loops

**Definition.** Splitting a long loop into chunks and awaiting
`setImmediate` between them lets timers, I/O callbacks, and other
requests run. Node's `timersPromises.scheduler.yield()` is "equivalent to
calling `timersPromises.setImmediate()`" and is Experimental
([timers](https://nodejs.org/api/timers.html)).

**Use when.**

- One request's CPU work blocks others (event-loop delay spikes in
  `perf_hooks.monitorEventLoopDelay`, timeouts during batch jobs).

**Do not use when.**

- Total CPU time is the metric: chunking adds scheduling overhead
  without reducing work. Use a worker to run it in parallel.
- Shared state can be mutated by other callbacks between chunks.

**Example.**

```javascript
export async function hashYielding(n, chunk = 200_000) {
  let h = 0;
  for (let start = 0; start < n; start += chunk) {
    const end = Math.min(n, start + chunk);
    for (let i = start; i < end; i++) h = mix(h, i);
    await new Promise((resolve) => setImmediate(resolve)); // let I/O run
  }
  return h;
}
```

Runnable: `hashBlocking` / `hashYielding` in `async.mjs`.

**Cost removed.** Event-loop blocking. Local (30,000,000 iterations, a 2
ms interval timer): 0 timer callbacks during the blocking loop; 138-140
(node) and 22 (bun) during the chunked loop.

**Verify.**

1. `verify` asserts the chunked result equals the blocking result.
1. `verify` asserts 0 ticks while blocking and > 0 while chunked.

## worker_threads for CPU-bound work

**Definition.** A `Worker` runs JavaScript on another thread with its own
event loop; data crosses via `postMessage` (structured clone or
transfer). Node's docs: workers are useful for CPU-intensive JavaScript
and "do not help much with I/O-intensive work", and recommend a pool over
a worker per task
([worker_threads](https://nodejs.org/api/worker_threads.html)). Bun
implements `node:worker_threads` and marks its `Worker` API experimental
([bun workers](https://bun.com/docs/runtime/workers)).

**Use when.**

- A CPU-bound task (hashing, parsing, compression, image work) blocks the
  main thread for tens of milliseconds or more.

**Do not use when.**

- The work is I/O: the async I/O APIs are already off-thread.
- The task is short: worker startup and message cloning can cost more.
- Inputs are large and not transferable: cloning costs a copy each way.

**Example.**

```javascript
const worker = new Worker(new URL("./cpu-worker.mjs", import.meta.url), {
  workerData: n,
});
const result = await new Promise((resolve, reject) => {
  worker.once("message", resolve);
  worker.once("error", reject);
});
```

Runnable: `hashInWorker` in `async.mjs` and `cpu-worker.mjs`.

**Cost removed.** Main-thread blocking. Local (30,000,000 iterations): 0
timer callbacks during the blocking loop; 24-36 (node) and 22-23 (bun)
while the worker ran it.

**Verify.**

1. `verify` asserts the worker result equals the in-thread result.
1. `verify` asserts more timer ticks with the worker than while blocking.

## Transfer ArrayBuffers instead of copying

**Definition.** `postMessage(buffer, [buffer])` moves ownership: the
receiver gets the memory and the sender's `byteLength` becomes 0.
Without the transfer list the buffer is cloned (copied)
([worker_threads](https://nodejs.org/api/worker_threads.html);
[MDN structuredClone transfer][mdn-structuredclone-transfer]).

**Use when.**

- Large binary data (MiBs) is sent to a worker or port and the sender
  does not need it afterwards.

**Do not use when.**

- The sender still reads the buffer: after transfer it is detached
  (length 0), and any view over it throws or reads nothing.
- The buffer is a `SharedArrayBuffer`: it is shared, not transferred.

**Example.**

```javascript
port.postMessage(buffer, [buffer]); // buffer.byteLength === 0 afterwards
```

Runnable: `send` in `async.mjs`.

**Cost removed.** A full copy per message. Local (32 MiB, time includes
allocating and filling the buffer): node 9.6-11.2 → 1.8 ms; bun
10.0-12.4 → 3.4-4.1 ms.

**Verify.**

1. `verify` asserts the copied sender keeps 1 MiB, the transferred sender
   has length 0, and both receivers got identical bytes.
1. The `TIME postMessage` line prints copy vs transfer.

## stream.pipeline for backpressure

**Definition.** `writable.write()` returns `false` when the buffer reaches
`highWaterMark`; the producer must wait for `'drain'`.
`pipeline()` from `node:stream/promises` (added in node 15.0.0) does that,
forwards errors, and
destroys all streams on failure ([stream](https://nodejs.org/api/stream.html)).
The default `highWaterMark` for byte streams became 64 KiB in node 22.0.0
([PR #52037](https://github.com/nodejs/node/pull/52037)); `new
Writable().writableHighWaterMark` is 65536 on node 26.8.2 and bun 1.4.2.

**Use when.**

- Code pipes with `on("data", (c) => dest.write(c))`, ignores the return
  value of `write()`, or hand-wires `error` handlers on each stream.

**Do not use when.**

- Data is small and already in memory: write it once.

**Example.**

```javascript
import { pipeline } from "node:stream/promises";
await pipeline(source, transform, destination); // waits, propagates errors
```

Runnable: `baselineCopy` / `candidateCopy` in `async.mjs`.

**Cost removed.** Unbounded buffering in the slow consumer. Local (200
chunks of 1 KiB, sink `highWaterMark` 4 KiB): peak `writableLength`
203,776 → 3,072 bytes on node and bun.

**Verify.**

1. `verify` asserts the same byte count for both and the pipeline peak <=
   the sink's `highWaterMark`.
1. The `PEAK` line prints both peaks; in production, compare RSS under the
   same input.

## Bun.file and Bun.write for file copies

**Definition.** `Bun.file(path)` returns a lazy `BunFile`; `Bun.write(dest,
Bun.file(src))` copies file to file with platform syscalls. Bun's docs list
`copy_file_range`, `sendfile`, and `splice` on Linux and `clonefile` and
`fcopyfile` on macOS ([file I/O](https://bun.com/docs/api/file-io)). Bun
only.

**Use when.**

- Bun code copies files with `readFile` + `writeFile` (whole file through
  the JS heap).

**Do not use when.**

- The code must also run on node: keep `node:fs` (`fs.copyFile` is the
  portable equivalent) or branch on `globalThis.Bun`.
- The data must be transformed in between: use streams.

**Example.**

```javascript
export async function candidateCopy(src, dest) {
  await Bun.write(dest, Bun.file(src)); // file-to-file, no JS buffer
}
```

Runnable: `bun-io.mjs` (bun only).

**Cost removed.** Reading the file into memory and writing it back. Local
(32 MiB on APFS, median of 5): 9.2-9.6 → 0.3 ms. APFS supports
`clonefile`; other file systems will differ.

**Verify.**

1. `bun assets/examples/constructs/bun-io.mjs` (run by `verify.sh verify`)
   compares the copied bytes and `Bun.file(src).size`.
1. It asserts the `Bun.write` median is below the baseline median.

[mdn-structuredclone-transfer]:
  https://developer.mozilla.org/en-US/docs/Web/API/Window/structuredClone
