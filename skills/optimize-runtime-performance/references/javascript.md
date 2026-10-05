# JavaScript Performance Gotchas

Applies to Node, Bun, and browsers unless a line says otherwise. Profile with `node --cpu-prof`
(open the `.cpuprofile` in DevTools), `node --prof`, `node --trace-deopt`, `node --heap-prof`, and
the DevTools Performance panel. Bun uses JavaScriptCore, not V8, so V8 flags and hidden-class advice
do not carry over to it.

## Contents

- [Measurement](#measurement)
- [Allocation and Strings](#allocation-and-strings)
- [Hidden Classes and Deopts](#hidden-classes-and-deopts)
- [Async and Event Loop](#async-and-event-loop)
- [Browser](#browser)

## Measurement

- Mistake: `console.time` around one call, or a loop whose result is not used. Fix: a harness that
  warms up and reports spread (`mitata` or `tinybench`). V8 eliminates dead code and inlines
  constants, so consume the result (accumulate into an outer variable and print it).
- Mistake: benchmarking a function with one input shape. Fix: call it with the shapes production
  sees. V8 specializes on the types it has seen (inline caches), so a benchmark that stays
  monomorphic overstates the gain for a site that is polymorphic in production.
- Mistake: measuring in a dev build of a bundler or with source maps and devtools open. Fix:
  production build, devtools closed or throttling off, and a fresh profile per browser.
- Mistake: trusting a microbenchmark of `for` versus `forEach`. Fix: the JIT makes them close in
  many cases; look at the profile, and only then change loop form.
- Mistake: optimizing in the main thread a cost that is I/O wait. Fix: a CPU profile shows idle time
  as `(idle)`; if the time is in the event loop waiting, the fix is concurrency, not code.

## Allocation and Strings

- Mistake: `array.map().filter().reduce()` chains over large arrays in a hot path. Fix: one `for`
  loop; each step allocates an array. Keep chains in cold code.
- Mistake: `[...a, x]` or `{...o, k: v}` in a loop (accumulator spread). Fix: `push` to a local
  array or mutate a local object; spreading copies everything each iteration, which is quadratic.
- Mistake: string `+=` assumed slow. Fix: V8 uses ropes and concatenation is usually fine;
  flattening happens on first indexed access. Collect parts in an array and `join` only when the
  profile shows string cost.
- Mistake: `Object.keys(o).forEach` on large dictionaries, or using objects as hash maps with many
  adds and deletes. Fix: `Map` for dynamic keys, `Set` for membership, and never `delete` a property
  on a hot object (it pushes the object to slow dictionary mode); assign `undefined` or use a `Map`.
- Mistake: `array.includes` or `indexOf` inside a loop over big arrays. Fix: build a `Set` once;
  note that `Set` uses SameValueZero (NaN equals NaN) while `indexOf` uses strict equality.
- Mistake: `array.shift()` in a loop to consume a queue. Fix: keep an index, or use two-array or
  ring buffer queues; `shift` is O(n) on large arrays.
- Mistake: `JSON.parse(JSON.stringify(x))` for cloning. Fix: `structuredClone` or build the copy;
  the JSON round trip drops `undefined`, `Date`, `Map`, and cycles, and is slow.
- Mistake: `RegExp` created inside a function or with the `g` flag shared across calls. Fix: hoist a
  literal; a shared `g` or `y` regex keeps `lastIndex` state between `test` and `exec` calls and
  gives wrong results.
- Mistake: holding references that keep large objects alive (closures, caches, `Map` without
  eviction). Fix: take heap snapshots in DevTools or `--heap-prof`, compare two snapshots, and use
  `WeakMap` or an eviction policy.
- Mistake: typed arrays ignored in numeric code. Fix: `Float64Array` or `Uint8Array` avoid
  boxed-number arrays and GC pressure; reuse one buffer, and be careful with `Buffer.allocUnsafe`
  (uninitialized memory, never expose it) and views that share a pooled `ArrayBuffer` (Node small
  `Buffer`s share a pool, so `buf.buffer` is larger than `buf`).

## Hidden Classes and Deopts

- Mistake: adding properties to objects in different orders or after construction. Fix: initialize
  all fields in the constructor in the same order so objects share a hidden class; polymorphic and
  megamorphic sites are slower.
- Mistake: arrays that mix types or holes (`new Array(n)`, `arr[n] =` beyond the length). Fix:
  pre-fill with the right element type; an array transitions from packed `SMI` to double to generic
  elements, and never goes back. Holey arrays are slower. `Array.from({length: n})` or `.fill(0)`
  gives a packed array.
- Mistake: a function that "deoptimizes" assumed from reading code. Fix: run
  `node --trace-deopt --trace-opt script.js` and read the reason (`wrong map`, `not a Smi`); fix the
  type instability it names.
- Mistake: `try`/`catch` and `arguments` assumed to block optimization. Fix: modern V8 (TurboFan)
  optimizes them; do not refactor without a profile.
- Mistake: `eval`, `with`, and dynamic `Function` in hot modules. Fix: avoid them; they defeat
  optimization and static analysis.

## Async and Event Loop

- Mistake: a synchronous CPU loop on the event loop (JSON over big payloads, regex backtracking,
  sync crypto and `fs.*Sync`). Fix: measure the event-loop delay
  (`perf_hooks.monitorEventLoopDelay`), then move the work to a `worker_threads` Worker or chunk it
  (yield with `setImmediate`, not `setTimeout(0)`, in Node).
- Mistake: `await` inside a `for` loop over independent calls. Fix: `Promise.all` over a bounded
  batch; unbounded `Promise.all` over thousands of requests exhausts sockets and memory, so cap
  concurrency with a pool. Keep sequential `await` where order or rate limits matter, and remember
  `Promise.all` rejects on the first error while the others keep running.
- Mistake: passing large objects to a Worker. Fix: `postMessage` structured-clones the data;
  transfer an `ArrayBuffer` in the transfer list (the sender then loses it) or use
  `SharedArrayBuffer` with `Atomics`, which needs cross-origin isolation in browsers.
- Mistake: `async` function per tiny step in a hot loop. Fix: each `await` costs microtask
  scheduling; keep the hot inner function synchronous and await at the boundary.
- Mistake: streams piped with tiny chunks, or `readFileSync` of huge files into memory. Fix: stream
  with a larger `highWaterMark` and use `pipeline`, which handles errors and backpressure; respect
  the `write()` return value.

## Browser

- Mistake: layout thrashing (reading `offsetHeight` after writing styles in a loop). Fix: batch
  reads, then writes; `requestAnimationFrame` for visual updates.
- Mistake: long tasks over 50 ms on the main thread. Fix: find them in the Performance panel; split
  with `scheduler.yield()` (where supported) or `setTimeout`, or move the work to a Worker.
- Mistake: measuring with cached assets. Fix: disable cache and throttle CPU and network in DevTools
  to reflect users; use `performance.mark` and `measure` around the real work.
