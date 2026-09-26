# Browser rendering constructs

Browser only: node and bun have no DOM or rendering. The runnable page is
[`rendering.html`](../assets/examples/browser/rendering.html); it writes
its results to `window.results` and the `#out` element.

Verification tier: **Executed** once in this session in headless Chrome
154 (`HeadlessChrome/154.0.0.0`, macOS arm64) driven by the
`agent-browser` CLI; not part of `verify.sh`, which has no browser. The
commands were:

```sh
agent-browser open "file://$PWD/assets/examples/browser/rendering.html"
agent-browser eval "JSON.stringify(window.results)"
agent-browser close
```

Any browser works: open the file and read `#out`. Headless numbers are
machine- and mode-specific; take frame timing from the DevTools
Performance panel on a real display.

## Contents

- Batch DOM reads before writes
- requestAnimationFrame for visual updates
- scheduler.yield in long tasks

## Batch DOM reads before writes

**Definition.** Reading a layout property (`offsetWidth`, `offsetHeight`,
`getBoundingClientRect()`) after a style write forces the browser to run
style and layout synchronously. Alternating read/write in a loop repeats
that per iteration ("layout thrashing"); reading everything first and
writing afterwards needs at most one layout
([web.dev][web-dev]).

**Use when.**

- A DevTools Performance recording shows "Forced reflow" warnings or long
  purple Layout blocks inside a script task.
- Code loops over elements reading geometry and writing styles.

**Do not use when.**

- A write must see the layout produced by the previous write (a true
  dependency): restructure the computation or use CSS instead.

**Example.**

```javascript
function batched(boxes) {
  const read = boxes.map((el) => el.offsetWidth); // all reads
  boxes.forEach((el, i) => (el.style.width = `${read[i] + 1}px`));
}
```

Runnable: `interleaved` / `batched` in `rendering.html`.

**Cost removed.** One forced layout per element. Local headless Chrome 154,
400 elements: interleaved 33.8-49.6 ms → batched 0.2-0.3 ms.

**Verify.**

1. `window.results.sameWidths` is `true` (both produce identical final
   styles).
1. `interleavedMs` > `batchedMs`; in DevTools, the "Forced reflow" insight
   disappears for the candidate.

## requestAnimationFrame for visual updates

**Definition.** [`requestAnimationFrame(cb)`][requestanimationframe-cb]
runs `cb` before the next repaint; it is one-shot and paused in background
tabs. Recording the latest value per event and writing it once per frame
turns many events into one style write.

**Use when.**

- Handlers for high-rate events (`scroll`, `pointermove`, `input`,
  WebSocket messages) write styles or DOM on every event.

**Do not use when.**

- Every event must produce a visible or logged effect.
- Work must continue in background tabs (rAF pauses there); use a timer or
  worker for non-visual work.

**Example.**

```javascript
let pending = null;
function onInput(v) {
  if (pending === null) {
    requestAnimationFrame(() => {
      host.style.opacity = pending; // latest value only
      pending = null;
    });
  }
  pending = v;
}
```

Runnable: `makeEager` / `makeFramed` in `rendering.html`.

**Cost removed.** Style writes (and the style/layout work they trigger)
beyond one per frame. Local: 100 synchronous events → 100 writes eager, 1
write framed; `sameOpacity` true.

**Verify.**

1. `window.results.sameOpacity` is `true` (final state identical).
1. `eagerWrites` = 100 and `framedWrites` = 1.

## scheduler.yield in long tasks

**Definition.** [`scheduler.yield()`][scheduler-yield]
returns a promise that resolves in a new task whose continuation is
prioritized, so input and rendering can run between chunks of a long task.
MDN marks it "Limited availability" (not Baseline); feature-detect and
fall back to a macrotask.

**Use when.**

- The Performance panel shows [long tasks][long-tasks]
  (50 ms or more) during interactions,
  and the work can be split into chunks.

**Do not use when.**

- The work needs no DOM access: move it to a Web Worker, which removes it
  from the main thread instead of interleaving it.
- State read before a yield can change during the yield and the code does
  not re-validate it.

**Example.**

```javascript
const yieldNow = () => globalThis.scheduler?.yield
  ? globalThis.scheduler.yield()
  : new Promise((r) => setTimeout(r, 0));
for (const chunk of chunks) {
  process(chunk);
  await yieldNow();
}
```

Runnable: `yieldNow` and `framesDuring` in `rendering.html`.

**Cost removed.** Main-thread blocking during a long task. Local headless
Chrome 154 (`schedulerYield: true`): 0 animation frames during one 200 ms
task, 1 during twenty 10 ms chunks. Headless frame delivery is not
representative; measure Interaction to Next Paint in a real browser.

**Verify.**

1. Results of the chunked work equal the unchunked work (compare outputs in
   a unit test).
1. `framesDuringChunks` > `framesDuringLongTask`, and the DevTools
   Performance panel shows no task above 50 ms for the candidate.

[web-dev]:
  https://web.dev/articles/avoid-large-complex-layouts-and-layout-thrashing
[requestanimationframe-cb]:
  https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame
[scheduler-yield]:
  https://developer.mozilla.org/en-US/docs/Web/API/Scheduler/yield
[long-tasks]:
  https://developer.mozilla.org/en-US/docs/Web/API/PerformanceLongTaskTiming
