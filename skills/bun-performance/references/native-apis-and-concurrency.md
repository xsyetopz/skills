# Native data paths and bounded concurrency

Research: 2026-09-09; Bun 1.4.2.

## File and byte ownership

```ts
import { mkdir } from "node:fs/promises";
await mkdir("out", { recursive: true });
const source = Bun.file("fixtures/input.bin");
const written = await Bun.write("out/copy.bin", source);
console.log({ written });
```

`Bun.file` creates a lazy Blob-like reference; constructing one does not read
the bytes or establish existence. `.text()` decodes text, `.bytes()`
materializes bytes, `.stream()` supports incremental consumers. `Bun.write`
returns a byte count and can select native copy operations. Use `node:fs` for
directories. Handle read/write errors at the operation, including after an
existence check. [File I/O](https://bun.com/docs/runtime/file-io).

For many small writes, own a `FileSink`, write chunks, await `flush()` when
necessary and await `end()` in cleanup. `unref()` permits process exit; it does
not flush or establish persistence. Use atomic replacement and fsync where state
durability requires them.

Pass bytes through the path without string conversion when encoding is
irrelevant. Use `subarray()` only while the backing buffer's lifetime is
acceptable; make an explicit copy for a tiny long-lived fragment of a huge
payload. Scratch storage belongs to one active consumer or needs
synchronization. Test partial input, non-ASCII strings and cancellation when
changing these paths.

## HTTP and streaming

```ts
const server = Bun.serve({
  hostname: "127.0.0.1",
  port: 0,
  async fetch(req) {
    if (new URL(req.url).pathname !== "/fixture")
      return new Response("Missing", { status: 404 });
    const file = Bun.file("fixtures/output.bin");
    if (!(await file.exists())) return new Response("Missing", { status: 404 });
    return new Response(file);
  },
});
console.log(server.url);
```

The route serves a fixed fixture. Validate any added request-derived paths
before file access. Serving a Blob avoids full-file decoding. Preserve content
types, cache headers, ranges and access checks required by the real route. A
request/response stream body has consumption ownership; do not reuse a consumed
response across requests. Current routes require 1.2.3+, while a `fetch` handler
supports older versions. `await server.stop()` drains active connections;
`stop(true)` closes them. Long-lived WebSockets need an explicit shutdown plan.
[Server contracts][ref-1].

Bound stream production by consumer demand and stop upstream work on disconnect.
Current server inactivity timeout can close a quiet in-flight response; use a
per-request timeout for a deliberate long-lived stream rather than disabling
protection globally. HTTP/2 and HTTP/3 server modes are labelled experimental in
the researched docs and are not the default optimization path.

## Workers and queues

Bun's Web Worker API remains **experimental**, especially termination. For CPU
work large enough to amortize startup and message costs:

```ts
const worker = new Worker(new URL("./worker.ts", import.meta.url).href);
worker.addEventListener("message", (event) => consumeResult(event.data));
worker.addEventListener("error", (event) => failPending(event.message));
worker.postMessage({ id: 1, input: "payload" });
```

`consumeResult` and `failPending` are application-owned callbacks. In the
worker, install `self.onmessage` before any top-level await; static imports that
await can also delay handler installation and lose messages. Messages use
structured cloning. `node:worker_threads` queues on `parentPort` until a
listener is attached, which can suit async initialization. `unref()` changes
process lifetime; it does not cancel work. `{ smol: true }` trades worker
performance for a smaller JSC heap. [Worker contracts][ref-2].

Maintain a fixed worker pool, request IDs, a maximum in-flight count and bounded
pending queue. On saturation, reject or delay admission according to the
application's contract. Ignore canceled/stale result IDs, reject pending callers
on worker failure, and stop accepting work before shutdown. For I/O, use bounded
promises and size admission limits to downstream capacity. Measure queue wait,
p95/p99 latency, throughput and RSS, including payload cloning and
initialization. Never transfer buffer ownership while another operation still
needs those bytes.

[ref-1]: https://bun.com/docs/runtime/http/server
[ref-2]: https://bun.com/docs/runtime/workers
