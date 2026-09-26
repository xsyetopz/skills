package example;

import static java.lang.foreign.ValueLayout.ADDRESS;
import static java.lang.foreign.ValueLayout.JAVA_INT;
import static java.lang.foreign.ValueLayout.JAVA_LONG;

import java.lang.foreign.Arena;
import java.lang.foreign.FunctionDescriptor;
import java.lang.foreign.Linker;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.SymbolLookup;
import java.lang.invoke.MethodHandle;
import java.nio.file.Path;

/**
 * Native calls: JNI versus the Foreign Function and Memory API (JEP 454).
 * The library path comes from -Dnative.lib (verify.sh builds it with cc).
 * javac -Xlint:restricted flags every restricted call; this class opts in.
 */
@SuppressWarnings("restricted")
public final class Interop {
    private static final Linker LINKER = Linker.nativeLinker();
    private static final FunctionDescriptor INT_INT_INT =
        FunctionDescriptor.of(JAVA_INT, JAVA_INT, JAVA_INT);
    private static final MethodHandle ADD;
    private static final MethodHandle ADD_CRITICAL;
    private static final MethodHandle STRLEN = LINKER.downcallHandle(
        LINKER.defaultLookup().find("strlen").orElseThrow(),
        FunctionDescriptor.of(JAVA_LONG, ADDRESS));

    static {
        String lib = System.getProperty("native.lib");
        if (lib == null) {
            throw new IllegalStateException("set -Dnative.lib=<path>");
        }
        System.load(lib); // JNI binding for jniAdd
        SymbolLookup lookup =
            SymbolLookup.libraryLookup(Path.of(lib), Arena.global());
        MemorySegment add = lookup.find("native_add").orElseThrow();
        ADD = LINKER.downcallHandle(add, INT_INT_INT);
        ADD_CRITICAL = LINKER.downcallHandle(add, INT_INT_INT,
            Linker.Option.critical(false));
    }

    private Interop() {
    }

    public static native int jniAdd(int a, int b);

    public static int ffmAdd(int a, int b) {
        try {
            return (int) ADD.invokeExact(a, b);
        } catch (Throwable t) {
            throw new IllegalStateException(t);
        }
    }

    public static int ffmAddCritical(int a, int b) {
        try {
            return (int) ADD_CRITICAL.invokeExact(a, b);
        } catch (Throwable t) {
            throw new IllegalStateException(t);
        }
    }

    /** strlen over a confined arena: memory is freed when the try ends. */
    public static long strlen(String s) {
        try (Arena arena = Arena.ofConfined()) {
            MemorySegment str = arena.allocateFrom(s);
            return (long) STRLEN.invokeExact(str);
        } catch (Throwable t) {
            throw new IllegalStateException(t);
        }
    }

    /** Returns a segment whose arena is already closed. */
    public static MemorySegment closedSegment() {
        MemorySegment seg;
        try (Arena arena = Arena.ofConfined()) {
            seg = arena.allocate(JAVA_INT);
            seg.set(JAVA_INT, 0, 42);
        }
        return seg;
    }
}
