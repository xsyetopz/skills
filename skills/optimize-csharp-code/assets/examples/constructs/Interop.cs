// Native interop constructs against the C runtime that every supported OS
// ships (libSystem on macOS, glibc on Linux, ucrtbase on Windows).
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.Marshalling;
using BenchmarkDotNet.Attributes;

public static partial class LibC
{
    public const string Name = "c-runtime";

    // Maps the logical name to the platform C runtime once per assembly.
    public static void Register() =>
        NativeLibrary.SetDllImportResolver(
            Assembly.GetExecutingAssembly(),
            (name, _, _) =>
                name != Name
                    ? IntPtr.Zero
                    : NativeLibrary.Load(
                        OperatingSystem.IsMacOS() ? "/usr/lib/libSystem.B.dylib"
                        : OperatingSystem.IsWindows() ? "ucrtbase.dll"
                        : "libc.so.6"
                    )
        );

    // Baseline: runtime-generated marshalling stub; the string is converted
    // with the default (ANSI/UTF-8 on Unix) policy at run time.
    [DllImport(Name, EntryPoint = "strlen", CharSet = CharSet.Ansi)]
    public static extern nuint StrlenDllImport(string text);

    // Candidate: the source generator emits the marshalling code at build
    // time (visible in obj/), so it is trimmable and NativeAOT-compatible.
    [LibraryImport(Name, EntryPoint = "strlen", StringMarshalling = StringMarshalling.Utf8)]
    public static partial nuint StrlenGenerated(string text);

    // UTF-8 bytes already in hand: pass a pointer, no marshalling at all.
    [LibraryImport(Name, EntryPoint = "strlen")]
    public static unsafe partial nuint StrlenPointer(byte* text);

    [LibraryImport(Name, EntryPoint = "qsort")]
    public static unsafe partial void Qsort(
        void* items,
        nuint count,
        nuint size,
        delegate* unmanaged[Cdecl]<void*, void*, int> compare
    );
}

public static unsafe class Callbacks
{
    // No delegate object exists, so there is nothing to root or collect.
    [UnmanagedCallersOnly(CallConvs = [typeof(CallConvCdecl)])]
    private static int CompareInt32(void* left, void* right) =>
        (*(int*)left).CompareTo(*(int*)right);

    public static void SortInPlace(int[] values)
    {
        // PERF/SAFETY: `fixed` pins values only for the synchronous qsort
        // call; qsort does not retain the pointer after returning.
        fixed (int* first = values)
        {
            LibC.Qsort(first, (nuint)values.Length, sizeof(int), &CompareInt32);
        }
    }
}

// Owned native memory: the finalizer-backed SafeHandle frees it exactly once
// even if Dispose is never called, and P/Invoke keeps it alive during calls.
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

    public unsafe Span<byte> AsSpan() => new((void*)handle, checked((int)Length));

    protected override bool ReleaseHandle()
    {
        unsafe
        {
            NativeMemory.Free((void*)handle);
        }
        return true;
    }
}

[StructLayout(LayoutKind.Sequential)]
public struct BlittablePoint
{
    public int X;
    public int Y;
}

public static class InteropChecks
{
    public static unsafe void Run()
    {
        LibC.Register();
        const string text = "héllo, native";
        nuint utf8Length = (nuint)System.Text.Encoding.UTF8.GetByteCount(text);
        Check.Equal("libraryimport", utf8Length, LibC.StrlenGenerated(text));
        Check.Equal("libraryimport", (nuint)5, LibC.StrlenDllImport("abcde"));

        // "u8" literals are null-terminated in the assembly's data section.
        fixed (byte* literal = "native\0"u8)
        {
            Check.Equal("utf8-literal", (nuint)6, LibC.StrlenPointer(literal));
        }
        Check.NoAllocation(
            "utf8-literal",
            () =>
            {
                fixed (byte* literal = "native\0"u8)
                {
                    LibC.StrlenPointer(literal);
                }
            }
        );

        int[] values = [5, -2, 9, 0, 3, 3];
        Callbacks.SortInPlace(values);
        Check.SequenceEqual("function-pointer", [-2, 0, 3, 3, 5, 9], values);
        Check.NoAllocation("function-pointer", () => Callbacks.SortInPlace(values));

        using (var buffer = new NativeBuffer(64))
        {
            buffer.AsSpan().Fill(7);
            Check.Equal("safehandle", 64 * 7, buffer.AsSpan().ToArray().Sum(b => (int)b));
        }

        Check.Equal("blittable", 8, Marshal.SizeOf<BlittablePoint>());
        Check.Equal("blittable", 8, Unsafe.SizeOf<BlittablePoint>());
        // Arrays on the pinned object heap never move, so a raw address
        // taken once stays valid across collections without `fixed`.
        byte[] pinned = GC.AllocateArray<byte>(16, pinned: true);
        nint before = (nint)Unsafe.AsPointer(ref MemoryMarshal.GetArrayDataReference(pinned));
        GC.Collect();
        GC.WaitForPendingFinalizers();
        GC.Collect();
        nint after = (nint)Unsafe.AsPointer(ref MemoryMarshal.GetArrayDataReference(pinned));
        Check.Equal("pinned-array", before, after);
    }
}

[MemoryDiagnoser]
public class InteropBenchmarks
{
    private const string Text = "a moderately long ASCII string for strlen";

    [GlobalSetup]
    public void Setup() => LibC.Register();

    [Benchmark(Baseline = true)]
    public nuint DllImportString() => LibC.StrlenDllImport(Text);

    [Benchmark]
    public nuint LibraryImportString() => LibC.StrlenGenerated(Text);

    [Benchmark]
    public unsafe nuint PointerLiteral()
    {
        fixed (byte* literal = "a moderately long ASCII string for strlen\0"u8)
        {
            return LibC.StrlenPointer(literal);
        }
    }
}
