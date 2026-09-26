# Code generation constructs

These cards change what the JIT emits: dispatch, bounds checks, SIMD,
inlining, stack zeroing, and regex code. Examples live in
[`Codegen.cs`](../assets/examples/constructs/Codegen.cs); `CodegenChecks.Run`
holds the oracles.

Several of these constructs showed **no measurable difference**, because
.NET's dynamic PGO (on by default since .NET 8) and loop cloning already
remove the cost in the baseline. Expect that for monomorphic, warm code;
it is why each card requires a measurement before keeping the change.
Measured on an Apple M1 Max, .NET 10.0.11 Arm64, BenchmarkDotNet 0.15.8
`--job short`; numbers are machine-specific.

## Contents

- Sealed classes
- Bounds-check elimination by slicing
- Vectorized BCL primitives
- Portable SIMD with Vector of T
- Struct generic specialization
- AggressiveInlining
- SkipLocalsInit
- GeneratedRegex
- Enum.HasFlag semantics
- Span parameters instead of IEnumerable

## Sealed classes

**Definition.** A `sealed` class cannot be derived from, so a virtual call
through a reference whose static type is the sealed class has exactly one
target. The JIT can call it directly and inline it, and type checks
(`is`, casts) become a single method-table comparison
([sealed]).

**Use when.**

- A class with virtual or interface members has no subclasses and is not
  designed for inheritance (most application classes).
- Profiles show virtual/interface stubs or type-check helpers on leaf types,
  especially in NativeAOT or with `TieredPGO` disabled, where no runtime
  profile guides devirtualization.

**Do not use when.**

- The type is public in a library and consumers can derive from it:
  sealing is a breaking change.
- Mocking frameworks in the test suite subclass it (Moq/Castle proxies need
  unsealed classes or interfaces).

**Example.**

```csharp
public abstract class Shape
{
    public abstract double Area();
}

public sealed class SealedCircle(double radius) : Shape
{
    public override double Area() => Math.PI * radius * radius;
}

public static double CandidateTotal(SealedCircle[] circles)
{
    double total = 0;
    foreach (SealedCircle circle in circles)
    {
        total += circle.Area();
    }
    return total;
}
```

**Cost removed.** The indirect call through the vtable and the lost inlining
of `Area`. Measured, 1,024 items: `OpenDispatch` 1,111 ns versus
`SealedDispatchCall` 1,079 ns, inside the error bars, because guarded
devirtualization from dynamic PGO already handles this monomorphic loop.
Expect a measurable gain only where PGO does not apply.

**Verify.**

1. Behavior: `Check.Equal("sealed", ...)` compares totals.
1. Codegen: `DOTNET_TieredCompilation=0 DOTNET_JitDisasm='SealedDispatch:*'`
   on the verify run; with tiering off (no PGO) the open version shows an
   indirect `call`/`blr` through the method table and the sealed version
   does not.
1. Benefit: benchmark in the deployment configuration (for NativeAOT,
   benchmark the published binary).

## Bounds-check elimination by slicing

**Definition.** The JIT removes an array/span range check when it can prove
the index is in `[0, Length)`. The canonical proof is a loop
`for (i = 0; i < span.Length; i++)` over the same span. Slicing once with
`AsSpan(0, count)` validates `count` up front and gives the loop that
shape.

**Use when.**

- The disassembly of a hot loop contains `CORINFO_HELP_RNGCHKFAIL` (the
  range-check failure helper) inside the loop body.
- The loop bound is a separate `count` variable rather than the array
  length.

**Do not use when.**

- The listing already has no check in the hot path: the JIT may have
  cloned the loop into a checked and an unchecked copy.
- The plan is `Unsafe.Add` or `MemoryMarshal.GetReference` to remove a
  check the JIT could not: that removes memory safety and needs a written
  proof and a measured gain.

**Example.**

```csharp
[MethodImpl(MethodImplOptions.NoInlining)]
public static int CandidateSum(int[] values, int count)
{
    ReadOnlySpan<int> span = values.AsSpan(0, count);
    int sum = 0;
    for (int i = 0; i < span.Length; i++)
    {
        sum += span[i];
    }
    return sum;
}
```

`NoInlining` only keeps the method's listing standalone for inspection.

**Cost removed.** A compare-and-branch per element. Measured codegen: the
baseline listing contains one `bl CORINFO_HELP_RNGCHKFAIL`, the candidate
none. Measured time: 1,640 ns versus 1,588 ns for 4,096 ints, within
noise, because loop cloning already gave the baseline an unchecked fast
path. The exception changes: an out-of-range `count` throws
`ArgumentOutOfRangeException` from `AsSpan` instead of
`IndexOutOfRangeException` mid-loop, which the oracle asserts. Confirm no
caller catches the old type.

**Verify.**

1. Behavior: the oracle compares sums and asserts both exception types.
1. Codegen: `DOTNET_TieredCompilation=0 DOTNET_JitDisasm='BoundsChecks:*'
   dotnet Constructs.dll verify | grep -E 'listing|RNGCHK'` shows the helper
   only under `BaselineSum`.
1. Benefit: `BENCH_FILTER='*CodegenBenchmarks*' sh verify.sh measure`.

## Vectorized BCL primitives

**Definition.** Span methods such as `IndexOf`, `IndexOfAny`, `Count`,
`SequenceEqual`, `Contains`, `Replace`, and `System.Text.Ascii`/`Utf8`
helpers are implemented with `Vector128`/`Vector256`/`Vector512` paths in
the runtime and fall back to scalar code on unsupported hardware.

**Use when.**

- A hand-written loop counts, searches, compares, or copies primitive
  elements and an equivalent span method exists.

**Do not use when.**

- The loop does per-element work with side effects or early exits that the
  primitive cannot express.
- The data is tiny (a few elements): call overhead dominates. Measure.

**Example.**

```csharp
public static int CandidateCountBcl(ReadOnlySpan<byte> data, byte target) =>
    data.Count(target);
```

**Cost removed.** Scalar per-element compare and branch. Measure `Mean`
against the scalar loop on realistic lengths.

**Verify.**

1. Behavior: `Check.Equal("vectorization", ...)` on a 1,000-byte input.
1. Benefit: add a benchmark pair, and check that the target machine
   reports `Vector.IsHardwareAccelerated=True` (`sh verify.sh runtime`).

## Portable SIMD with Vector of T

**Definition.** `System.Numerics.Vector<T>` is a hardware-sized vector (its
lane count, `Vector<T>.Count`, is fixed per process). Arithmetic on it
compiles to SIMD instructions when `Vector.IsHardwareAccelerated` is true.
`Vector128<T>`/`Vector256<T>` in `System.Runtime.Intrinsics` give fixed
widths and platform intrinsics
([SIMD in .NET](https://learn.microsoft.com/en-us/dotnet/standard/simd)).

**Use when.**

- A profile shows a numeric loop over large primitive spans (sum, min/max,
  dot product, transform) and no BCL or `TensorPrimitives` method covers
  it.

**Do not use when.**

- Floating-point results must be bit-identical to the scalar loop:
  vectorized reduction reorders additions and changes rounding.
- Integer overflow semantics matter and lanes would overflow: widen
  first (as the example does) or keep `checked` scalar code.
- The rewrite has no scalar tail loop: lengths not divisible by the lane
  count would drop elements.

**Example.**

```csharp
public static long CandidateSum(ReadOnlySpan<int> data)
{
    long total = 0;
    int i = 0;
    if (Vector.IsHardwareAccelerated && data.Length >= Vector<int>.Count)
    {
        var accumulator = Vector<long>.Zero;
        int last = data.Length - Vector<int>.Count;
        for (; i <= last; i += Vector<int>.Count)
        {
            var chunk = new Vector<int>(data[i..]);
            Vector.Widen(chunk, out Vector<long> low, out Vector<long> high);
            accumulator += low + high;
        }
        total = Vector.Sum(accumulator);
    }
    for (; i < data.Length; i++)
    {
        total += data[i];
    }
    return total;
}
```

**Cost removed.** Scalar adds per element. Measured, 4,096 ints:
`ScalarSum` 3,027 ns, `VectorSum` 779 ns (NEON, 128-bit vectors on M1).

**Verify.**

1. Behavior: the oracle checks lengths 0, 1, 7, 8, 9, 33, and 1,000 with
   values near `int.MaxValue`, covering the tail loop and overflow into
   `long`.
1. Fallback: run once with `DOTNET_EnableHWIntrinsic=0` to force the scalar
   path and re-run the oracle.
1. Benefit: `ScalarSum` versus `VectorSum` rows.

## Struct generic specialization

**Definition.** The JIT compiles a dedicated body of a generic method per
struct type argument, so calls on a `where T : struct, IInterface`
parameter are direct and inlinable. Reference type arguments share one
body, and calls stay indirect
([generics in the runtime][generics-in-the-runtime]).

**Use when.**

- An algorithm invokes a `Func<>`/interface strategy per element in a
  hot loop, and the strategy set is known at compile time.

**Do not use when.**

- Data chooses the strategy at run time: the code ends up with a switch
  over instantiations.
- Code size matters (NativeAOT, many instantiations).

**Example.**

```csharp
public interface IBinaryOp
{
    int Apply(int left, int right);
}

public readonly struct AddOp : IBinaryOp
{
    public int Apply(int left, int right) => left + right;
}

public static int CandidateFold<TOp>(ReadOnlySpan<int> values, TOp op)
    where TOp : struct, IBinaryOp
{
    int acc = 0;
    foreach (int value in values)
    {
        acc = op.Apply(acc, value);
    }
    return acc;
}
```

**Cost removed.** The delegate invocation per element. Measured, 4,096
ints: `DelegateFold` 1,562 ns versus `StructFold` 1,556 ns, no measurable
difference, because dynamic PGO guarded-devirtualized the single delegate
target. The gain appears when the delegate call site is polymorphic or
PGO is unavailable (NativeAOT).

**Verify.**

1. Behavior and allocation: the oracle compares folds and asserts 0 B for
   the struct version.
1. Benefit: measure in the real configuration, and also with
   `DOTNET_TieredPGO=0` to see the cost PGO was hiding.

## AggressiveInlining

**Definition.** `[MethodImpl(MethodImplOptions.AggressiveInlining)]` asks the
JIT to inline the method beyond its default size heuristics. It is a
hint, not a guarantee: for example, methods with certain exception
handling still may not inline.

**Use when.**

- The listing of a hot caller shows a `call` to a small helper that the JIT
  declined to inline, and the call cost is visible in the profile.

**Do not use when.**

- Applying it broadly "for speed": inlining large methods grows code,
  can spill registers, and can slow the caller. .NET 10 also widens
  inlining when profile data shows a hot call site
  ([.NET 10 inlining][net-10-inlining]).

**Example.**

```csharp
[MethodImpl(MethodImplOptions.AggressiveInlining)]
private static int ClampInline(int value, int max) =>
    value > max ? max : value;
```

**Cost removed.** Call overhead and the optimizations blocked by the call
boundary. Confirm the call is gone from the caller's `DOTNET_JitDisasm`
output.

**Verify.**

1. Behavior: `Check.Equal("aggressive-inlining", ...)`.
1. Codegen: `DOTNET_JitDisasm='Inlining:CandidateClampAll'` shows no call
   to `ClampInline`; `BaselineClampAll` (with `NoInlining` on the helper)
   shows one.
1. Benefit: benchmark the caller; revert if there is no difference.

## SkipLocalsInit

**Definition.** `[SkipLocalsInit]` (C# 9, requires `AllowUnsafeBlocks`)
stops the compiler from emitting the `.locals init` flag, so the JIT does
not zero locals and `stackalloc` buffers on method entry
([SkipLocalsInit]).

**Use when.**

- A hot method `stackalloc`s a large buffer (hundreds of bytes or more) and
  always writes before reading.

**Do not use when.**

- Any code path can read the buffer before writing it: the contents are
  whatever was on the stack, which is a correctness and information-leak
  bug.

**Example.**

```csharp
// PERF/SAFETY: scratch is fully written by CopyTo before any read of
// the copied prefix, and Mix only reads scratch[..input.Length].
[SkipLocalsInit]
public static int CandidateChecksum(ReadOnlySpan<byte> input)
{
    Span<byte> scratch = stackalloc byte[1024];
    return Mix(input, scratch);
}
```

**Cost removed.** Zeroing the 1,024-byte buffer per call. Check that the
zeroing loop/`stp` sequence is gone from `DOTNET_JitDisasm`, and benchmark
the time per call.

**Verify.**

1. Behavior: the oracle compares checksums. Review every read of the
   buffer against the writes that precede it.
1. Benefit: benchmark with realistic input lengths. The saving matters
   only when the buffer is large relative to the work.

## GeneratedRegex

**Definition.** `[GeneratedRegex(pattern, options)]` on a `static partial`
method (.NET 7+) makes the Roslyn source generator emit the matching code
at build time, with no run-time regex parsing or IL emission. The
generated source is visible in the IDE and in `obj/`
([source generation][source-generation]).

**Use when.**

- A compile-time constant pattern is used repeatedly, `new Regex(...)`
  appears per call, `RegexOptions.Compiled` inflates startup, or the app
  is trimmed/NativeAOT.

**Do not use when.**

- The pattern is built at run time from input.
- The rewrite changes culture or options: keep the same `RegexOptions`,
  including `CultureInvariant`/`IgnoreCase`, and the same match timeout.

**Example.**

```csharp
public static partial class RegexUse
{
    [GeneratedRegex(@"^\d+\.\d+\.\d+$", RegexOptions.CultureInvariant)]
    private static partial Regex Version();

    public static bool CandidateIsVersion(string text) =>
        Version().IsMatch(text);
}
```

**Cost removed.** Pattern parsing and construction per call (baseline
`new Regex(...).IsMatch`), and run-time code generation for `Compiled`. The
oracle asserts 0 B allocated per `IsMatch` on the generated version.

**Verify.**

1. Behavior: the oracle matches four inputs with both implementations.
1. Benefit: `Check.NoAllocation("generated-regex", ...)`. Benchmark
   startup separately if `RegexOptions.Compiled` was replaced.

## Enum.HasFlag semantics

**Definition.** `value.HasFlag(mask)` returns true when **all** bits of
`mask` are set in `value`, and returns true for a zero mask
([Enum.HasFlag][enum-hasflag]).
Since .NET Core 2.1 the JIT treats it as an intrinsic for same-type enums,
so it does not box in optimized code.

**Use when.**

- Reviewing a proposed "optimization" that replaces `HasFlag`. This card
  prevents a semantic change; it does not recommend one.

**Do not use when.**

- Replacing `HasFlag(mask)` with `(value & mask) != 0`: that is "any bit",
  which differs for multi-bit masks (`ReadWrite`) and for `None`.

**Example.**

```csharp
public static bool HasFlag(Access value, Access mask) =>
    value.HasFlag(mask);

public static bool AllBits(Access value, Access mask) =>
    (value & mask) == mask; // equivalent to HasFlag

public static bool AnyBit(Access value, Access mask) =>
    (value & mask) != 0; // NOT equivalent
```

**Cost removed.** None on current .NET: the card prevents an incorrect
rewrite. The oracle asserts 0 B for `HasFlag` in optimized code.

**Verify.**

1. The oracle compares `HasFlag` and `AllBits` for every value/mask pair
   of the enum and asserts `AnyBit(Read, None)` is false while
   `HasFlag(Read, None)` is true.

## Span parameters instead of IEnumerable

**Definition.** An `IEnumerable<T>` parameter forces interface calls to
`GetEnumerator`/`MoveNext`/`Current` and boxes struct enumerators (such as
`List<T>.Enumerator`). A `ReadOnlySpan<T>` parameter iterates memory
directly. .NET 10 devirtualizes and can stack-allocate array enumerators in
some cases
([array enumeration de-abstraction][array-enumeration-de-abstraction]).

**Use when.**

- A hot, internal API receives arrays or lists through `IEnumerable<T>`.

**Do not use when.**

- Callers pass lazy sequences, generators, or LINQ queries: a span API
  forces them to materialize. Keep the `IEnumerable<T>` overload and add
  a span overload.
- The API is async or stores the data.

**Example.**

```csharp
public static int CandidateSum(ReadOnlySpan<int> values)
{
    int sum = 0;
    foreach (int value in values)
    {
        sum += value;
    }
    return sum;
}
```

C# 14 adds implicit conversions from arrays to spans, so array callers bind
to the span overload without `.AsSpan()`
([C# 14 first-class spans][c-14-first-class-spans]).
Check that adding the overload does not change which overload existing
callers bind to.

**Cost removed.** The boxed `List<T>.Enumerator` and interface calls.
Measured oracle output: `ALLOC span-parameter: 40 B -> 0 B` for a `List<int>`
passed as `IEnumerable<int>`.

**Verify.**

1. Behavior: the oracle sums the same list both ways.
1. Benefit: `Check.AllocatesLess("span-parameter", ...)`.

[sealed]: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/sealed
[generics-in-the-runtime]: https://learn.microsoft.com/en-us/dotnet/standard/generics/
[net-10-inlining]: https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-10/runtime#inlining-improvements
[skiplocalsinit]: https://learn.microsoft.com/en-us/dotnet/api/system.runtime.compilerservices.skiplocalsinitattribute
[source-generation]: https://learn.microsoft.com/en-us/dotnet/standard/base-types/regular-expression-source-generators
[enum-hasflag]: https://learn.microsoft.com/en-us/dotnet/api/system.enum.hasflag
[array-enumeration-de-abstraction]: https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-10/runtime#array-enumeration-de-abstraction
[c-14-first-class-spans]: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14#implicit-span-conversions
