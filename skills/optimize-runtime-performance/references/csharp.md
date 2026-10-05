# C# and .NET Performance Gotchas

Benchmark with BenchmarkDotNet, find allocation and GC cost with `dotnet-counters` and
`dotnet-trace`, and read JIT output with `DOTNET_JitDisasm` (release runtime builds support it since
.NET 7).

## Contents

- [Measurement](#measurement)
- [Allocation](#allocation)
- [JIT and Runtime Configuration](#jit-and-runtime-configuration)
- [Concurrency and Interop](#concurrency-and-interop)

## Measurement

- Mistake: timing with `Stopwatch` in a console app, or running BenchmarkDotNet from a Debug build
  or with a debugger attached. Fix: `dotnet run -c Release` with the BenchmarkDotNet runner; it
  refuses non-optimized builds by default and handles warmup, pilot runs, and outlier detection.
- Mistake: a benchmark method that discards its result. Fix: return the value (BenchmarkDotNet
  consumes it) or use `Consumer`. The JIT removes pure calls with unused results.
- Mistake: reading `Mean` alone. Fix: add `[MemoryDiagnoser]` and read `Allocated` and the `Gen0`
  column; allocation is often the real cost, and `Error` and `StdDev` tell whether a difference is
  real.
- Mistake: measuring steady state when the complaint is startup. Fix: use
  `[SimpleJob(RunStrategy.ColdStart)]` or time the process, since tiered compilation runs first
  calls through unoptimized code.
- Mistake: comparing two runs by eye. Fix: export CSV (`--exporters csv`) and run
  `scripts/compare_benchmarks.py` from this skill to fail on a regression over a threshold.
- Mistake: benchmarking on a different runtime than production. Fix: pin the target framework, and
  note `TieredPGO`, `TieredCompilation`, and server versus workstation GC settings; they change
  results.
- Mistake: `[Params]` left at one size. Fix: benchmark a small and a large input; span and pooling
  wins reverse at different sizes.

## Allocation

- Mistake: `string.Substring` and `Split` in a parser. Fix: slice with
  `ReadOnlySpan<char>`/`AsSpan()` and parse with `int.Parse(span)`. Spans are `ref struct`s: they
  cannot be fields of classes, captured by lambdas, stored across `await`, or used in iterators. Use
  `Memory<T>` when they must cross those.
- Mistake: `stackalloc` of a size from input. Fix: stackalloc only a small constant bound (for
  example 256 bytes) and fall back to `ArrayPool` above it; a large stackalloc overflows the stack
  and kills the process.
- Mistake: `ArrayPool<T>.Shared.Rent` treated as returning an exactly sized, zeroed array. Fix: the
  array is at least the requested length, may hold old data (`clearArray: true` on `Return` for
  secrets), and must be returned in `finally`. Use the requested length for your span, not
  `array.Length`, and never use the array after `Return`.
- Mistake: LINQ in a hot loop (`Where`, `Select`, `ToList`). Fix: a plain `for` or `foreach` over a
  `List<T>` or array. LINQ allocates enumerators and delegates; closures that capture locals
  allocate each call. A `static` lambda prevents accidental capture.
- Mistake: boxing through `object`, non-generic collections, `string.Format` with value types, or an
  interface call on a struct. Fix: generics with constraints; implement `IEquatable<T>` on structs
  used as dictionary keys, since the default `ValueType.Equals` uses reflection and boxes.
- Mistake: string concatenation in a loop. Fix: `StringBuilder` (reuse one and call `Clear`) or
  `string.Create`; interpolated strings in .NET 6+ use `DefaultInterpolatedStringHandler`, so a
  single interpolation is fine.
- Mistake: `async` methods on a hot path that almost always complete synchronously. Fix: return
  `ValueTask<T>`, and never await a `ValueTask` twice or call `.Result` before it completes; convert
  with `.AsTask()` if it must be stored or awaited many times.
- Mistake: making a struct large to "avoid allocation". Fix: structs over about 16 bytes are copied
  on every pass; use `in` parameters or `readonly struct` (avoids defensive copies) or keep a class.
- Mistake: `Dictionary` or `List` growing in a loop of known size. Fix: pass the capacity to the
  constructor, or `EnsureCapacity`.
- Mistake: `Regex` constructed per call. Fix: a static `Regex` with `RegexOptions.Compiled`, or the
  `[GeneratedRegex]` source generator (.NET 7+); do not use `Compiled` for a regex used a few times,
  because compile cost exceeds the gain.

## JIT and Runtime Configuration

- Mistake: hand-inlining methods. Fix: read `DOTNET_JitDisasm` or the BenchmarkDotNet
  `DisassemblyDiagnoser`; the JIT inlines small methods and
  `[MethodImpl(MethodImplOptions.AggressiveInlining)]` only overrides the size heuristic. It does
  not inline across virtual calls or methods with `try`/`catch` in older runtimes.
- Mistake: bounds-check removal by `unsafe` code. Fix: loop `for (i = 0; i < a.Length; i++)` over
  the same array, or a `foreach` over a span, lets the JIT drop checks; `Unsafe.Add` and
  `MemoryMarshal` skip them and create memory-safety bugs, so keep them only behind a test and a
  measured gain.
- Mistake: hand-written SIMD loops with `Vector128` for code that can use `Span<T>.IndexOf`,
  `SequenceEqual`, `Sum` from `System.Linq` (vectorized for primitives), or
  `System.Numerics.Tensors`. Fix: use the framework vectorized primitives first, and gate
  hardware-specific code on `Vector128.IsHardwareAccelerated` with a scalar fallback.
- Mistake: switching to Server GC or turning on concurrent GC settings globally for a latency
  problem. Fix: read GC metrics with `dotnet-counters` first: `dotnet.gc.collections` and
  `dotnet.gc.pause.time` on .NET 9 and later, or the older `gen-0-gc-count` and `time-in-gc`
  counters on .NET 8 and earlier. Server GC uses more memory and suits throughput on many cores;
  `GCHeapAffinitizeMask`/`GCHeapCount` and container limits matter.
- Mistake: Native AOT, ReadyToRun, or trimming enabled for speed without checking what they trade.
  Fix: ReadyToRun improves startup but tiered JIT may still rejit hot methods; Native AOT removes
  the JIT (no dynamic PGO) and breaks reflection that the trimmer cannot see.
- Mistake: `TieredCompilation=false` for benchmarks. Fix: leave it on as in production, unless
  startup-only behavior is the question; turning it off changes what is measured.

## Concurrency and Interop

- Mistake: `Task.Run` around CPU work inside an ASP.NET request to "parallelize". Fix: it moves work
  to the thread pool, adds queueing, and hurts throughput under load; use `Parallel.For` only for
  large independent work units, and cap `MaxDegreeOfParallelism`.
- Mistake: `lock` on a hot counter. Fix: `Interlocked.Increment`, or per-thread accumulation and a
  single merge; `volatile` alone does not make read-modify-write atomic.
- Mistake: `.Result` or `.Wait()` on tasks, which blocks thread-pool threads and starves the pool.
  Fix: await asynchronously all the way; thread-pool starvation shows up as latency spikes with low
  CPU.
- Mistake: `ConfigureAwait(false)` added everywhere as an optimization. Fix: it matters only in
  library code with a synchronization context; ASP.NET Core has none.
- Mistake: P/Invoke per item with marshaling. Fix: `LibraryImport` source generated marshalling
  (.NET 7+), blittable types, `SuppressGCTransition` only for tiny non-blocking calls, and batched
  calls; measure the boundary cost against the work inside.
