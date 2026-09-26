# Native interop constructs

Examples live in [`Interop.cs`](../assets/examples/constructs/Interop.cs)
and call the platform C runtime (libSystem on macOS, glibc on Linux,
ucrtbase on Windows) through a `NativeLibrary` resolver. Measured on an
Apple M1 Max, .NET 10.0.11 Arm64, BenchmarkDotNet 0.15.8 `--job short`.

## Contents

- LibraryImport source-generated P/Invoke
- UTF-8 string literals for native calls
- Function pointers and UnmanagedCallersOnly
- SafeHandle for owned native resources
- Pinned object heap arrays
- Blittable structs
- Callback lifetime and rooting
- Native-library workloads: SDL3, fonts, images, BASS

## LibraryImport source-generated P/Invoke

**Definition.** `[LibraryImport]` on a `static partial` method (.NET 7+)
makes a source generator emit the marshalling stub at compile time, and
the generated code calls a plain blittable `DllImport`. A `DllImport`
with non-blittable parameters instead gets an IL stub generated at run
time
([P/Invoke source generation][p-invoke-source-generation]).

**Use when.**

- A .NET 7+ project uses `DllImport` with strings, arrays, `bool`, or
  `SetLastError`.
- The project is trimmed or published with NativeAOT, or run-time stub
  generation shows up at startup.

**Do not use when.**

- The signature uses marshalling features the generator does not support
  (for example some `UnmanagedType` variants): it emits a diagnostic, and
  the call needs manual marshalling.
- The target is .NET Framework or .NET 6 and below.

**Example.**

```csharp
[LibraryImport(Name, EntryPoint = "strlen",
    StringMarshalling = StringMarshalling.Utf8)]
public static partial nuint StrlenGenerated(string text);
```

**Cost removed.** Run-time IL stub generation and its per-call marshalling
overhead. Measured, 41-character string: `DllImportString`
16.3 ns, `LibraryImportString` 12.8 ns.

**Verify.**

1. Behavior: the oracle compares `strlen` of a non-ASCII string with
   `Encoding.UTF8.GetByteCount`, proving UTF-8 marshalling.
1. Generated code: inspect `obj/.../generated/` (set
   `EmitCompilerGeneratedFiles=true`) to read the stub.
1. Benefit: `BENCH_FILTER='*InteropBenchmarks*' sh verify.sh measure`.

## UTF-8 string literals for native calls

**Definition.** A `"text"u8` literal (C# 11+) is a `ReadOnlySpan<byte>`
over UTF-8 bytes stored in the assembly's data, with no allocation or
encoding at run time. It is **not** implicitly null-terminated in the
span's length, so include `\0` when the native API expects a C string
([UTF-8 literals][utf-8-literals]).

**Use when.**

- Constant strings (names, keys, format strings) go to native code on
  every call.

**Do not use when.**

- The native side keeps the pointer after the call: the span is pinned
  only inside `fixed`.

**Example.**

```csharp
fixed (byte* literal = "native\0"u8)
{
    nuint length = LibC.StrlenPointer(literal); // 6
}
```

**Cost removed.** Per-call string-to-UTF-8 conversion and its buffer.
Measured: `PointerLiteral` 6.5 ns versus `LibraryImportString` 12.8 ns;
the oracle asserts 0 B.

**Verify.**

1. Behavior: the oracle asserts `strlen` returns 6.
1. Benefit: `Check.NoAllocation("utf8-literal", ...)`.

## Function pointers and UnmanagedCallersOnly

**Definition.** A `static` method marked `[UnmanagedCallersOnly]` can be
called directly from native code; `&Method` yields a
`delegate* unmanaged[Cdecl]<...>` pointer (C# 9+) with no delegate object,
no GC root, and no marshalling thunk
([UnmanagedCallersOnly],
[function pointers][function-pointers]).

**Use when.**

- Native code calls back into managed code (sort comparators, audio
  callbacks, event hooks), and the callback needs no captured state or
  can receive it through a native `void* user` parameter.

**Do not use when.**

- The callback must capture instance state and the native API has no
  user pointer. Use a rooted delegate (next cards).
- Exceptions could escape: an exception thrown from an
  `UnmanagedCallersOnly` method terminates the process. Catch inside and
  return an error code.
- Parameters are non-blittable: only blittable types are allowed.

**Example.**

```csharp
[UnmanagedCallersOnly(CallConvs = [typeof(CallConvCdecl)])]
private static int CompareInt32(void* left, void* right) =>
    (*(int*)left).CompareTo(*(int*)right);

public static void SortInPlace(int[] values)
{
    fixed (int* first = values)
    {
        LibC.Qsort(first, (nuint)values.Length, sizeof(int),
            &CompareInt32);
    }
}
```

**Cost removed.** Delegate allocation, reverse-P/Invoke marshalling thunk,
and the risk of a collected callback. The oracle asserts 0 B per sort.

**Verify.**

1. Behavior: the oracle sorts `[5, -2, 9, 0, 3, 3]` via native `qsort`.
1. Benefit: `Check.NoAllocation("function-pointer", ...)`.

## SafeHandle for owned native resources

**Definition.** A `SafeHandle` subclass owns a native handle, frees it in
`ReleaseHandle` exactly once (on `Dispose` or finalization), and is
reference-counted by the marshaller so the handle cannot be released while
a P/Invoke call is using it
([SafeHandle]).

**Use when.**

- Managed code owns a native resource (memory, file descriptor, library
  object) currently held as `IntPtr` with manual `Free` calls.

**Do not use when.**

- The handle is borrowed (the native library owns it): pass
  `ownsHandle: false` or keep a plain `IntPtr`. Freeing a borrowed handle
  is a double free.

**Example.**

```csharp
public sealed class NativeBuffer : SafeHandle
{
    public NativeBuffer(nuint bytes)
        : base(IntPtr.Zero, ownsHandle: true)
    {
        unsafe
        {
            SetHandle((IntPtr)NativeMemory.AllocZeroed(bytes));
        }
        Length = bytes;
    }

    public nuint Length { get; }

    public override bool IsInvalid => handle == IntPtr.Zero;

    protected override bool ReleaseHandle()
    {
        unsafe
        {
            NativeMemory.Free((void*)handle);
        }
        return true;
    }
}
```

**Cost removed.** Leaks on exception paths and use-after-free races during
concurrent `Dispose`. Watch native memory with the platform tool (macOS
`leaks <pid>`, Linux RSS over time) during a stress loop.

**Verify.**

1. Behavior: the oracle fills and sums a 64-byte buffer inside `using`.
1. Leak check: loop allocate/dispose under `leaks` or RSS monitoring.

## Pinned object heap arrays

**Definition.** `GC.AllocateArray<T>(length, pinned: true)` (.NET 5+)
allocates on the pinned object heap. The array never moves, so native
code can use its address for as long as the array is alive, without
`fixed` or `GCHandle`
([GC.AllocateArray][gc-allocatearray]).

**Use when.**

- A long-lived buffer is pinned repeatedly (I/O rings, audio buffers, GPU
  upload staging).

**Do not use when.**

- The buffer is short-lived: only gen2 collections free POH objects, so
  churn grows the heap.
- `T` contains references: pinned allocation does not allow them.

**Example.**

```csharp
byte[] pinned = GC.AllocateArray<byte>(16, pinned: true);
nint before = (nint)Unsafe.AsPointer(
    ref MemoryMarshal.GetArrayDataReference(pinned));
GC.Collect();
nint after = (nint)Unsafe.AsPointer(
    ref MemoryMarshal.GetArrayDataReference(pinned));
// before == after
```

**Cost removed.** Repeated `fixed`/`GCHandle.Alloc(Pinned)` and the heap
fragmentation from pinning in gen0.

**Verify.**

1. Behavior: the oracle asserts the address is unchanged across full
   collections.
1. Lifetime: the array stays referenced for as long as native code can
   touch it.

## Blittable structs

**Definition.** A struct is blittable when all its fields have identical
managed and native representation (primitive numerics, pointers, other
blittable structs) and its layout is sequential or explicit. It goes to
native code by pointer, without copying or conversion
([blittable types][blittable-types]).
`bool` and `char` are not blittable.

**Use when.**

- Structs cross the native boundary in hot calls.

**Do not use when.**

- The native layout's packing or alignment is not matched: a size or
  offset mismatch corrupts memory silently.

**Example.**

```csharp
[StructLayout(LayoutKind.Sequential)]
public struct BlittablePoint
{
    public int X;
    public int Y;
}
```

For a native `bool` field, use `byte` (or `int` for Win32 `BOOL`) and
convert at the edge.

**Cost removed.** Per-call marshalling copies of the struct.

**Verify.**

1. Oracle asserts `Marshal.SizeOf<BlittablePoint>()` equals
   `Unsafe.SizeOf<BlittablePoint>()` (8).
1. Compare field offsets with the native header (`offsetof` in a C test)
   for every struct passed.

## Callback lifetime and rooting

**Definition.** A delegate passed to native code becomes a function
pointer that stays valid only while the delegate object is alive. The GC
does not know the native side still holds the pointer
([native interop best practices][native-interop-best-practices]).

**Use when.**

- A callback must capture state and the native API has no user pointer, so
  `UnmanagedCallersOnly` cannot be used.

**Do not use when.**

- The function pointer card applies: it removes the lifetime problem.

**Example.**

```csharp
public sealed class Registration : IDisposable
{
    // Rooted for as long as native code may call it.
    private readonly NativeCallback callback;

    public Registration(Action<int> onEvent)
    {
        callback = value => onEvent(value);
        Native.Register(callback);
    }

    public void Dispose()
    {
        Native.Unregister();
        // Only after unregister (and any in-flight callback finishing,
        // per the library's contract) may the delegate become collectable.
        GC.KeepAlive(callback);
    }
}
```

**Cost removed.** Crashes from calling a collected delegate
(`CallbackOnCollectedDelegate` MDA on .NET Framework; access violation on
.NET).

**Verify.**

1. Stress: register, force `GC.Collect()` repeatedly, trigger callbacks,
   and confirm no crash.
1. Review: the delegate is stored in a field or static for the whole
   registration, not a local.

## Native-library workloads: SDL3, fonts, images, BASS

These rules come from the libraries' own documentation. Apply them before
changing ownership or batching in those workloads.

- **SDL3.** Keep event pumping and renderer calls on the main thread.
  `SDL_PollEvent`, `SDL_RenderGeometry`, and `SDL_RenderPresent` return
  `bool` in SDL3 (not SDL2's `int`)
  ([SDL_PollEvent](https://wiki.libsdl.org/SDL3/SDL_PollEvent),
  [SDL_RenderPresent](https://wiki.libsdl.org/SDL3/SDL_RenderPresent)).
  The backbuffer is not preserved after present. A blocking present is not
  proof that the frame is GPU-bound; measure CPU submission separately.
- **FontStashSharp / StbImageSharp.** Both are managed C# ports, not native
  P/Invoke wrappers
  ([FontStashSharp](https://github.com/FontStashSharp/FontStashSharp),
  [StbImageSharp](https://github.com/StbSharp/StbImageSharp)). Their costs
  are managed allocations and CPU; measure them with the allocation cards.
  Cache glyph layouts with a key covering font, size, scale, and text.
- **BASS / ManagedBass.** Callbacks run on BASS threads with deadlines:
  do not allocate, block, or log synchronously inside them. Keep callback
  delegates rooted until the channel is freed
  ([BASS documentation](https://www.un4seen.com/doc/)).

Verify each rule the same way as the matching card: an oracle for output
equality, a counter or benchmark for the claimed cost, and a stress run for
lifetime.

[p-invoke-source-generation]: https://learn.microsoft.com/en-us/dotnet/standard/native-interop/pinvoke-source-generation
[utf-8-literals]: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/reference-types#utf-8-string-literals
[unmanagedcallersonly]: https://learn.microsoft.com/en-us/dotnet/api/system.runtime.interopservices.unmanagedcallersonlyattribute
[function-pointers]: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/unsafe-code#function-pointers
[safehandle]: https://learn.microsoft.com/en-us/dotnet/api/system.runtime.interopservices.safehandle
[gc-allocatearray]: https://learn.microsoft.com/en-us/dotnet/api/system.gc.allocatearray
[blittable-types]: https://learn.microsoft.com/en-us/dotnet/framework/interop/blittable-and-non-blittable-types
[native-interop-best-practices]: https://learn.microsoft.com/en-us/dotnet/standard/native-interop/best-practices
