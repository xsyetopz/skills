# Allocation constructs

Each card removes managed heap allocations from a measured hot path. Every
example is a method pair in
[`Allocation.cs`](../assets/examples/constructs/Allocation.cs); the oracle in
`AllocationChecks.Run` proves equivalence and the allocation claim.

Measured on an Apple M1 Max, macOS, .NET SDK 10.0.400, runtime 10.0.11
Arm64 RyuJIT, BenchmarkDotNet 0.15.8 `--job short`. Byte counts from
`GC.GetAllocatedBytesForCurrentThread` are deterministic for a given
runtime and input; timings are not portable.

## Contents

- Span slicing instead of Substring and Split
- Bounded stackalloc with ArrayPool fallback
- ArrayPool rent and return
- string.Create
- TryWrite and ISpanFormattable into caller storage
- Presized StringBuilder
- Static lambdas and state-passing overloads
- IEquatable on struct keys
- LINQ pipeline to loop
- Presized collections
- CollectionsMarshal.GetValueRefOrAddDefault
- CollectionsMarshal.AsSpan
- ValueTask for synchronous completion
- SearchValues
- Frozen collections
- Dictionary alternate lookup
- params ReadOnlySpan
- JIT stack allocation (.NET 10)

## Span slicing instead of Substring and Split

**Definition.** `ReadOnlySpan<char>` is a bounds-checked view over existing
memory. `MemoryExtensions.Split(ReadOnlySpan<char>, char)` (.NET 9+) yields
`Range` values, and `csv[range]` slices without copying, so parsing never
creates intermediate `string` or `string[]` objects.

**Use when.**

- A profile or `[MemoryDiagnoser]` shows `string.Split`, `Substring`, or
  `Trim` allocations in a parse or tokenize loop.
- The parsed pieces are consumed immediately (parsed to numbers, compared,
  hashed) and not stored.

**Do not use when.**

- The pieces must outlive the call (stored in a collection or returned):
  a span cannot live on the heap, so the strings get allocated anyway.
- The code path is `async` or an iterator and the span would cross an
  `await`/`yield`: spans are `ref struct`, so the compiler rejects it.
- The target framework is below .NET 9, which lacks the span `Split`
  overload. Use `IndexOf` slicing instead.

**Example.**

```csharp
public static int CandidateSum(ReadOnlySpan<char> csv)
{
    int sum = 0;
    foreach (Range range in csv.Split(';'))
    {
        sum += int.Parse(csv[range].Trim());
    }
    return sum;
}
```

Runnable: `SpanParsing` in `assets/examples/constructs/Allocation.cs`.

**Cost removed.** One `string[]` plus one `string` per field, and one per
`Trim` that changes the text; see the BenchmarkDotNet `Allocated` column.
Measured, 8 fields: `SplitParse` 328 B/op, 144.8 ns; `SpanParse` 0 B/op,
86.3 ns.

**Verify.**

1. Equivalence: `sh assets/examples/verify.sh verify` runs
   `Check.Equal("span-parsing", ...)` on an input with spaces and a negative
   field; both methods must throw the same `FormatException` on an empty
   field (`int.Parse` of an empty span and of `""` both throw).
1. Benefit: `Check.NoAllocation("span-parsing", ...)` must pass, and
   `sh assets/examples/verify.sh measure` with
   `BENCH_FILTER='*AllocationBenchmarks*'` must show `-` in `Allocated` for
   the candidate row.

## Bounded stackalloc with ArrayPool fallback

**Definition.** `stackalloc T[n]` reserves `n` elements in the current stack
frame and yields a `Span<T>`, freed when the method returns. Pairing it
with `ArrayPool<T>.Shared.Rent` above a fixed bound gives zero heap
allocation for small inputs and bounded stack use for large ones.

**Use when.**

- A method needs a temporary buffer whose size is known at call time and
  usually small (encoding, formatting, hashing scratch space).
- The buffer does not escape the method.

**Do not use when.**

- The size is attacker-controlled or unbounded without the fallback: a large
  `stackalloc` throws `StackOverflowException`, which cannot be caught and
  terminates the process.
- The `stackalloc` sits inside a loop: each iteration grows the frame until
  the method returns.
- The method is `async` or an iterator: spans cannot cross
  `await`/`yield`.

**Example.**

```csharp
private const int StackLimitBytes = 256;

public static int Candidate(string text)
{
    int maxBytes = Encoding.UTF8.GetMaxByteCount(text.Length);
    byte[]? rented = null;
    Span<byte> buffer = maxBytes <= StackLimitBytes
        ? stackalloc byte[StackLimitBytes]
        : (rented = ArrayPool<byte>.Shared.Rent(maxBytes));
    try
    {
        int written = Encoding.UTF8.GetBytes(text, buffer);
        return Fold(buffer[..written]);
    }
    finally
    {
        if (rented is not null)
        {
            ArrayPool<byte>.Shared.Return(rented);
        }
    }
}
```

Runnable: `Utf8Checksum` in `Allocation.cs`. `stackalloc` a constant size
(256), not `maxBytes`: a constant keeps the frame size fixed and lets the
JIT skip dynamic stack probing.

**Cost removed.** The `byte[]` from `Encoding.UTF8.GetBytes(string)` on every
call; see `GC.GetAllocatedBytesForCurrentThread` deltas or the `Allocated`
column. The oracle asserts 0 B for a short input (stack path) and for a
4,000-character input (pool path, after the pool is warm).

**Verify.**

1. Equivalence: the oracle compares `Baseline` and `Candidate` for `""`, a
   non-ASCII string, and a 1,000-character string (forces the pool path).
1. Benefit: `Check.NoAllocation("stackalloc-pool", ...)` for both paths.
1. Safety: search for `stackalloc` inside `for`/`while` bodies and for
   sizes derived from input without a bound (`rg -n 'stackalloc' src/`).
   Every `Rent` needs a `Return` in a `finally`.

## ArrayPool rent and return

**Definition.** `ArrayPool<T>.Shared.Rent(minimumLength)` returns an array of
*at least* `minimumLength` elements from a shared, thread-safe pool;
`Return(array, clearArray)` makes it reusable. A rented array can be
larger than requested and holds stale data from previous renters
([ArrayPool docs][arraypool-docs]).

**Use when.**

- A temporary array larger than a safe stack buffer is allocated per call
  (I/O chunks, serialization scratch, sort buffers).
- Ownership is simple: one method rents and the same method returns.

**Do not use when.**

- The array escapes (stored in a field, returned, captured by a
  continuation that outlives the method): a later renter overwrites it.
- The code uses `array.Length` as the logical length. Track the
  requested length separately.
- The array holds secrets or references and is returned without
  `clearArray: true`: the next renter can read them, and references keep
  objects alive.

**Example.** The pool branch of `Utf8Checksum.Candidate` above. Minimal
shape:

```csharp
byte[] rented = ArrayPool<byte>.Shared.Rent(length);
try
{
    Span<byte> buffer = rented.AsSpan(0, length); // logical length
    Fill(buffer);
    return Process(buffer);
}
finally
{
    ArrayPool<byte>.Shared.Return(rented, clearArray: false);
}
```

**Cost removed.** Large per-call arrays (≥ 85,000 bytes land on the large
object heap per the
[GC config docs][gc-config-docs]),
their zeroing, and the Gen0/LOH collections they trigger. Watch
`Allocated` per operation and the
`dotnet.gc.last_collection.heap.size` metric (`gc.heap.generation=loh`) in
`dotnet-counters monitor --counters System.Runtime`.

**Verify.**

1. Every `Rent` has exactly one `Return` on every path: `rg -n
   'ArrayPool<.*>\.Shared\.(Rent|Return)'` and read each method.
1. No use after return: the returned array is not referenced after the
   `finally`.
1. Benefit: the allocation test shows 0 B per call after the first
   (warm) call.

## string.Create

**Definition.** `string.Create<TState>(int length, TState state,
SpanAction<char, TState> action)` allocates the final string once and lets
the callback write its characters directly, with no intermediate buffers.

**Use when.**

- The final length is known up front and the content is built from
  pieces (reversing, hex encoding, fixed-format IDs).
- The current code builds a `char[]`, `StringBuilder`, or LINQ sequence only
  to call `new string(...)`.

**Do not use when.**

- The length is unknown before writing: use `StringBuilder` or
  `DefaultInterpolatedStringHandler`.
- The callback would capture locals: pass them through `state` and mark
  the lambda `static`, or the closure allocation cancels the gain.

**Example.**

```csharp
public static string CandidateReverse(string text) =>
    string.Create(text.Length, text, static (span, source) =>
    {
        source.AsSpan().CopyTo(span);
        span.Reverse();
    });
```

**Cost removed.** Baseline `new string(text.Reverse().ToArray())` allocates an
enumerator, a growing buffer, a `char[]`, and the string. Measured oracle
output: `ALLOC string-create: 176 B -> 48 B` for a 10-character input
(48 B is the result string itself).

**Verify.**

1. Equivalence: the oracle reverses `"abcé"` with both methods. Both
   reverse UTF-16 code units, so they split surrogate pairs identically;
   if the contract needs grapheme-correct reversal, neither is correct.
1. Benefit: `Check.AllocatesLess("string-create", ...)` prints the byte
   counts and fails unless the candidate allocates less.

## TryWrite and ISpanFormattable into caller storage

**Definition.** `MemoryExtensions.TryWrite(Span<char>, ref
TryWriteInterpolatedStringHandler, out int)` (.NET 6+) formats an
interpolated string directly into a caller-provided span, calling
`ISpanFormattable.TryFormat` on each hole. It returns `false` instead of
allocating when the span is too small.

**Use when.**

- The formatted text goes to a buffer, stream, or native API rather than
  becoming a long-lived `string` (logging sinks, protocol writers, UI text
  caches keyed by value).

**Do not use when.**

- The consumer requires a `string` anyway: `$"..."` with
  `DefaultInterpolatedStringHandler` already formats without boxing.
- Culture matters and the rewrite drops the `IFormatProvider` overload:
  `TryWrite(span, provider, $"...")` must receive the same provider the
  baseline used.

**Example.**

```csharp
public static int CandidatePoint(Span<char> destination, int x, int y) =>
    destination.TryWrite($"({x}, {y})", out int written) ? written : -1;
```

**Cost removed.** `string.Format("({0}, {1})", x, y)` boxes both integers
into `object` parameters and allocates the result string. The candidate
allocates nothing when the destination is reused (oracle:
`Check.NoAllocation("span-formatting", ...)`).

**Verify.**

1. Equivalence and overflow: the oracle compares the text for `(-4, 12)`
   and asserts `-1` for a 3-character destination.
1. Benefit: `Check.NoAllocation` passes only under optimized code. Under
   tier-0 JIT the same call allocated 48 B, so run allocation assertions
   with `DOTNET_TieredCompilation=0` (verify.sh does this) or after the
   method has tiered up.

## Presized StringBuilder

**Definition.** `StringBuilder` appends into chunked buffers and materializes
one string at `ToString()`; the final capacity passed to the constructor
avoids chunk growth. Repeated `string +=` in a loop copies the whole
accumulated string on every iteration (quadratic bytes copied).

**Use when.**

- A string is accumulated across a loop with a data-dependent number of
  pieces.

**Do not use when.**

- The number of pieces is fixed and small: `string.Concat(a, b, c)` or an
  interpolated string computes the length once and is already optimal.
- The pieces are already in an array/list: `string.Concat(parts)` or
  `string.Join(sep, parts)` does the length pass itself.

**Example.**

```csharp
public static string CandidateJoin(string[] parts)
{
    int length = 0;
    foreach (string part in parts)
    {
        length += part.Length;
    }
    var builder = new StringBuilder(length);
    foreach (string part in parts)
    {
        builder.Append(part);
    }
    return builder.ToString();
}
```

**Cost removed.** Intermediate strings from `+=`. Measured, 64 parts:
`ConcatJoin` 12,872 B/op, 1,304 ns; `BuilderJoin` 832 B/op, 245 ns.
`string.Concat(parts)` also removes the builder allocation; measure both
when the input is already an array.

**Verify.**

1. Equivalence: the oracle compares both joins for 64 parts.
1. Benefit: `Check.AllocatesLess("stringbuilder", ...)` and the
   `Allocated` column of `ConcatJoin` versus `BuilderJoin`.

## Static lambdas and state-passing overloads

**Definition.** A lambda that captures locals compiles to a closure class
instance plus a delegate allocated each time the enclosing code runs. The
`static` modifier (C# 9) forbids captures; APIs with a `TArg` state
parameter (for example `ConcurrentDictionary.GetOrAdd(key, factory,
factoryArgument)`) let a static lambda receive the data instead.

**Use when.**

- A hot call site passes a capturing lambda to an API that offers a
  state-passing overload (`GetOrAdd`, `AddOrUpdate`, `string.Create`,
  `ThreadPool.UnsafeQueueUserWorkItem`, `CancellationToken.Register`).

**Do not use when.**

- The API has no state overload: packing state into a tuple and casting
  from `object` boxes value types, often costing as much as the closure.
- The call runs once (startup configuration): keep the clearer form.

**Example.**

```csharp
public static int CandidateGetOrAdd(
    ConcurrentDictionary<int, int> cache, int key, int offset) =>
    cache.GetOrAdd(key, static (k, extra) => k + extra, offset);
```

**Cost removed.** The closure object and delegate per call. .NET 10 can
stack-allocate a non-escaping delegate but still heap-allocates the closure
([.NET 10 runtime: delegates][net-10-runtime-delegates]),
so the capture still costs. Watch `Allocated`.

**Verify.**

1. The compiler proves the `static` lambda captures nothing (CS8820 if it
   does).
1. Benefit: `Check.NoAllocation("static-lambda", ...)` on a cache hit.

## IEquatable on struct keys

**Definition.** `Dictionary<TKey,TValue>`, `HashSet<T>`, and
`EqualityComparer<T>.Default` call `IEquatable<T>.Equals(T)` when the struct
implements it; otherwise they fall back to `ValueType.Equals(object)` and
`ValueType.GetHashCode()`, which box the key
([ValueType.Equals remarks][valuetype-equals-remarks]).

**Use when.**

- A struct is used as a dictionary/set key, in `Contains`/`IndexOf`, or in
  equality-heavy code.

**Do not use when.**

- Never skip it for a key struct; the only question is which fields
  define equality. Keep `Equals(object)`, `GetHashCode`, and
  `IEquatable<T>.Equals` consistent, or lookups silently miss.

**Example.**

```csharp
public readonly struct EquatableKey(int a, int b)
    : IEquatable<EquatableKey>
{
    public int A { get; } = a;
    public int B { get; } = b;

    public bool Equals(EquatableKey other) =>
        A == other.A && B == other.B;

    public override bool Equals(object? obj) =>
        obj is EquatableKey other && Equals(other);

    public override int GetHashCode() => HashCode.Combine(A, B);
}
```

A `record struct` generates the same members.

**Cost removed.** Boxing on every hash and compare. Measured, one lookup:
`PlainStructKey` 72 B/op, 21.3 ns; `EquatableStructKey` 0 B/op, 2.8 ns.

**Verify.**

1. Equivalence: the oracle looks up the same key in both dictionaries.
1. Benefit: `Check.NoAllocation("iequatable-key", ...)` and the
   `Allocated` column.

## LINQ pipeline to loop

**Definition.** LINQ operators over `IEnumerable<T>` allocate iterator
objects and delegate instances, and make an indirect delegate call per
element. A `foreach` over a span does the same work with direct code.

**Use when.**

- The pipeline runs per request/frame/item in a profiled hot path.
- The source is an array, `List<T>`, or span, so the loop can iterate
  directly.

**Do not use when.**

- The query is deferred on purpose (lazy I/O source, or the source
  changes before enumeration): a loop evaluates immediately.
- The code is not hot: LINQ is clearer, and .NET keeps optimizing it.
- The loop would drop overflow checks: `Enumerable.Sum` on `long` is
  `checked` and throws `OverflowException`, so the loop must use
  `checked` too.

**Example.**

```csharp
public static long CandidateEvenSquares(ReadOnlySpan<int> values)
{
    long sum = 0;
    foreach (int value in values)
    {
        if (value % 2 == 0)
        {
            sum = checked(sum + (long)value * value);
        }
    }
    return sum;
}
```

**Cost removed.** `Where` and `Select` iterator objects and the per-element
delegate calls. The oracle asserts the candidate allocates 0 B.

**Verify.**

1. Equivalence: the oracle includes a value near `int.MaxValue`, so an
   unchecked loop would disagree with `Enumerable.Sum` on overflow.
1. Benefit: `Check.NoAllocation("linq-to-loop", ...)`.

## Presized collections

**Definition.** `List<T>`, `Dictionary<TKey,TValue>`, and `HashSet<T>` grow by
allocating a larger backing store and copying; the capacity constructor
allocates the final store once.

**Use when.**

- The final count is known or cheaply computable before filling.

**Do not use when.**

- The count is a guess that is often far too large: the unused capacity
  stays allocated for the collection's lifetime.

**Example.**

```csharp
public static List<int> CandidateSquares(int count)
{
    var list = new List<int>(count);
    for (int i = 0; i < count; i++)
    {
        list.Add(i * i);
    }
    return list;
}
```

**Cost removed.** Intermediate backing arrays and copies. Measured oracle
output for 1,000 items: `ALLOC presize: 8424 B -> 4056 B`.

**Verify.**

1. Equivalence: `Check.SequenceEqual("presize", ...)`.
1. Benefit: `Check.AllocatesLess("presize", ...)`.

## CollectionsMarshal.GetValueRefOrAddDefault

**Definition.** `CollectionsMarshal.GetValueRefOrAddDefault(dictionary, key,
out bool exists)` (.NET 6+) returns a `ref` to the value slot, adding a
default entry when missing, so read-modify-write needs one hash lookup
instead of two.

**Use when.**

- A hot path does `TryGetValue` followed by an indexer set on the same key
  (counters, accumulators, grouping).

**Do not use when.**

- The dictionary is mutated (Add/Remove/resize) while the ref is held:
  the ref then points at stale storage and writes are lost.
- The dictionary is shared across threads without a lock
  (`ConcurrentDictionary` has no equivalent).

**Example.**

```csharp
public static void CandidateCount(
    Dictionary<string, int> counts, string key)
{
    ref int slot = ref CollectionsMarshal.GetValueRefOrAddDefault(
        counts, key, out _);
    slot++;
}
```

**Cost removed.** The second hash computation and bucket search per update.
Benchmark time per operation over realistic key distributions;
allocation is unchanged (0 B on hit).

**Verify.**

1. Equivalence: the oracle counts the same key sequence both ways and
   compares sorted contents.
1. Review: no other mutation of the dictionary between obtaining and using
   `slot`.

## CollectionsMarshal.AsSpan

**Definition.** `CollectionsMarshal.AsSpan(List<T>)` returns a `Span<T>` over
the list's current backing array, for span-based loops and APIs without
the list enumerator's version checks.

**Use when.**

- A hot loop reads or writes a `List<T>` that no other code resizes during
  the loop.

**Do not use when.**

- The list can grow or shrink while the span exists: after a resize the
  span points at the old array and changes are lost silently (no
  `InvalidOperationException`, unlike `foreach`).

**Example.**

```csharp
public static int CandidateSumList(List<int> values)
{
    int sum = 0;
    foreach (int value in CollectionsMarshal.AsSpan(values))
    {
        sum += value;
    }
    return sum;
}
```

**Cost removed.** Enumerator version checks and bounds checks per element.
Measure time per operation; allocation does not change because the list's
struct enumerator does not allocate.

**Verify.**

1. Equivalence: the oracle sums a 100-item list both ways.
1. Review: the span's scope contains no call that can mutate the list.

## ValueTask for synchronous completion

**Definition.** `ValueTask<T>` wraps either a result or a `Task<T>`. An
`async` method or cache that often completes synchronously returns the
result without allocating a `Task<T>`
([ValueTask docs][valuetask-docs]).

**Use when.**

- Profiling shows `Task<T>` allocations from an API whose calls mostly
  complete synchronously (cache hits, buffered reads).

**Do not use when.**

- Callers await the result more than once, await concurrently, or call
  `.Result` before completion: those are unsupported for `ValueTask` and
  can corrupt pooled sources.
- The method almost always completes asynchronously: the wrapper adds
  size and saves no allocation.

**Example.**

```csharp
public ValueTask<int> CandidateGetAsync(int key)
{
    if (cache.TryGetValue(key, out int hit))
    {
        return new ValueTask<int>(hit);
    }
    return new ValueTask<int>(LoadAsync(key));
}
```

**Cost removed.** The `Task<int>` per synchronous hit (the runtime caches
only a few small `Task<int>` results). Measured oracle output, key 42:
`ALLOC valuetask: 72 B -> 0 B`.

**Verify.**

1. Equivalence: the oracle compares the loaded value from both caches.
1. Consumption rule: `rg -n 'CandidateGetAsync|YourMethod' src/` and
   confirm each call site awaits exactly once or calls `.AsTask()` first.
1. Benefit: `Check.AllocatesLess("valuetask", ...)`.

## SearchValues

**Definition.** `SearchValues<T>` (.NET 8+; `SearchValues<string>` since
.NET 9) precomputes a vectorized lookup structure for a fixed set of values,
used by `IndexOfAny`, `ContainsAny`, and related span methods
([SearchValues docs][searchvalues-docs]).

**Use when.**

- A fixed set of characters or bytes is searched repeatedly (validation,
  tokenizers, escaping).

**Do not use when.**

- The set changes per call: every call pays the creation cost.
- The set has one to three values: `IndexOfAny(a, b, c)` is already
  vectorized.

**Example.**

```csharp
private static readonly SearchValues<char> Forbidden =
    SearchValues.Create("<>:\"/\\|?*\0\t\r\n");

public static int CandidateFirstInvalid(ReadOnlySpan<char> name) =>
    name.IndexOfAny(Forbidden);
```

**Cost removed.** Per-call analysis of the `char[]` set inside
`IndexOfAny(char[])`. Measure time per operation on realistic input
lengths; allocation is 0 B in both.

**Verify.**

1. Equivalence: the oracle compares indexes for valid, invalid, empty,
   and control-character inputs.
1. Benefit: add a benchmark row pair and compare `Mean` with matched input.

## Frozen collections

**Definition.** `FrozenDictionary<TKey,TValue>` and `FrozenSet<T>` (.NET 8+,
`System.Collections.Frozen`) are immutable collections that spend extra
time at creation choosing a lookup strategy for the actual keys
([Frozen collections][frozen-collections]).

**Use when.**

- A lookup table is built once (startup, configuration) and read many times.

**Do not use when.**

- The collection is rebuilt or updated often: creation costs more than
  for `Dictionary`, and a frozen collection cannot be mutated.

**Example.**

```csharp
private static readonly FrozenSet<string> Frozen =
    Keywords.ToFrozenSet(StringComparer.Ordinal);

public static int CandidateCount(string[] words)
{
    int hits = 0;
    foreach (string word in words)
    {
        hits += Frozen.Contains(word) ? 1 : 0;
    }
    return hits;
}
```

**Cost removed.** Lookup time on read-heavy tables. Measure `Mean` per
lookup and, separately, the one-time creation cost. Keep the change only
if total time over the table's lifetime drops.

**Verify.**

1. Equivalence: the oracle counts hits with case variants and an empty
   string, using the same comparer.
1. Benefit: benchmark lookups and creation separately.

## Dictionary alternate lookup

**Definition.** `GetAlternateLookup<ReadOnlySpan<char>>()` on a
`Dictionary<string,TValue>` (.NET 9+) returns a view that looks up, adds,
and updates entries by span, if the dictionary's comparer implements
`IAlternateEqualityComparer<ReadOnlySpan<char>, string>`; the built-in
`StringComparer.Ordinal` and `OrdinalIgnoreCase` do
([GetAlternateLookup]).

**Use when.**

- Keys arrive as slices of a larger buffer (parsers, word counts, header
  maps) and most lookups hit existing keys.

**Do not use when.**

- The dictionary uses a custom comparer without the alternate interface:
  `GetAlternateLookup` throws `InvalidOperationException`.
- Most operations insert new keys: each insert still allocates the key
  string.

**Example.**

```csharp
public static void CandidateCountWords(
    Dictionary<string, int> counts, ReadOnlySpan<char> text)
{
    var lookup = counts.GetAlternateLookup<ReadOnlySpan<char>>();
    foreach (Range range in text.Split(' '))
    {
        ReadOnlySpan<char> word = text[range];
        if (word.IsEmpty)
        {
            continue;
        }
        lookup[word] = lookup.TryGetValue(word, out int n) ? n + 1 : 1;
    }
}
```

**Cost removed.** One string per token for lookups that hit. The oracle
asserts 0 B once every word exists in the dictionary.

**Verify.**

1. Equivalence: the oracle counts a sentence with a double space both
   ways (both skip empty tokens).
1. Benefit: `Check.NoAllocation("alternate-lookup", ...)`.

## params ReadOnlySpan

**Definition.** C# 13 allows `params` on span and other collection types.
With `params ReadOnlySpan<T>` the compiler passes call-site arguments in
stack storage instead of allocating an array
([params collections][params-collections]).

**Use when.**

- A frequently called variadic API (`Max(a, b, c)`, logging helpers) uses
  `params T[]`.

**Do not use when.**

- The method stores the arguments or is `async`.
- Adding the overload rebinds existing callers in a way that breaks a
  public contract. Check the call sites that recompile.

**Example.**

```csharp
public static int CandidateMax(params ReadOnlySpan<int> values)
{
    int max = int.MinValue;
    foreach (int value in values)
    {
        max = Math.Max(max, value);
    }
    return max;
}
```

**Cost removed.** The `int[]` allocated at each `params int[]` call site.
The oracle asserts 0 B for `CandidateMax(3, 9, -1)`.

**Verify.**

1. Equivalence: `Check.Equal("params-span", ...)`.
1. Benefit: `Check.NoAllocation("params-span", ...)`; in IL
   (`ildasm`/ILSpy) the call site has no `newarr`.

## JIT stack allocation (.NET 10)

**Definition.** The .NET 10 JIT stack-allocates small fixed-size arrays
(value and reference element types), objects referenced only from
non-escaping local struct fields, and non-escaping delegates, when escape
analysis proves they do not outlive the method
([.NET 10 runtime: stack allocation][net-10-runtime-stack-allocation]).

**Use when.**

- Deciding whether a remaining small allocation is worth rewriting: on
  .NET 10 a small, local, non-escaping `new int[] { 1, 2, 3 }` can already
  cost no heap allocation.

**Do not use when.**

- The target is not .NET 10, or the array/delegate escapes (stored,
  passed to a non-inlined call, returned).
- Correctness or a documented zero-allocation guarantee depends on it:
  this is a JIT heuristic.

**Example.**

```csharp
static int SumOfThree()
{
    int[] numbers = { 1, 2, 3 };
    int sum = 0;
    for (int i = 0; i < numbers.Length; i++)
    {
        sum += numbers[i];
    }
    return sum;
}
```

**Cost removed.** The heap array and its GC tracking. Check with
`GC.GetAllocatedBytesForCurrentThread` in optimized code (0 B) or with
`DOTNET_JitDisasm=SumOfThree`: the listing has no `CORINFO_HELP_NEWARR_*`
call.

**Verify.**

1. Run with `DOTNET_TieredCompilation=0 DOTNET_JitDisasm=SumOfThree` and
   search the listing for `CORINFO_HELP_NEWARR`.
1. Repeat on the project's target runtime: the result does not transfer
   to earlier runtimes.

[arraypool-docs]: https://learn.microsoft.com/en-us/dotnet/api/system.buffers.arraypool-1
[gc-config-docs]: https://learn.microsoft.com/en-us/dotnet/core/runtime-config/garbage-collector#large-object-heap-threshold
[net-10-runtime-delegates]: https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-10/runtime#delegates
[valuetype-equals-remarks]: https://learn.microsoft.com/en-us/dotnet/api/system.valuetype.equals
[valuetask-docs]: https://learn.microsoft.com/en-us/dotnet/api/system.threading.tasks.valuetask-1
[searchvalues-docs]: https://learn.microsoft.com/en-us/dotnet/api/system.buffers.searchvalues
[frozen-collections]: https://learn.microsoft.com/en-us/dotnet/api/system.collections.frozen
[getalternatelookup]: https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.dictionary-2.getalternatelookup
[params-collections]: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/method-parameters#params-modifier
[net-10-runtime-stack-allocation]: https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-10/runtime#stack-allocation
