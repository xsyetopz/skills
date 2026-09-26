package example;

import java.util.Arrays;
import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Level;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Warmup;

/** Dispatch, intrinsic, and SIMD pairs. */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Fork(value = 2, jvmArgsAppend = {"--add-modules", "jdk.incubator.vector"})
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
public class CodegenBench {
    private int[] xs;
    private Codegen.Leaf.OpenScaler open;
    private Codegen.Leaf.FinalScaler closed;
    private Codegen.Shapes.Shape[] shapes;
    private byte[] a;
    private byte[] b;
    private float[] fa;
    private float[] fb;

    @Setup(Level.Trial)
    public void setup() {
        xs = Verify.ints(1_000);
        open = new Codegen.Leaf.OpenScaler(3);
        closed = new Codegen.Leaf.FinalScaler(3);
        shapes = Codegen.Shapes.mixed(1_000);
        a = new byte[4_096];
        Arrays.fill(a, (byte) 5);
        b = a.clone(); // equal: both loops scan the whole array
        fa = new float[4_096];
        fb = new float[4_096];
        for (int i = 0; i < fa.length; i++) {
            fa[i] = (i % 13) * 0.1f;
            fb[i] = ((i * 7) % 11) * 0.3f;
        }
    }

    @Benchmark
    public long leafOpen() {
        return Codegen.Leaf.open(open, xs);
    }

    @Benchmark
    public long leafFinal() {
        return Codegen.Leaf.closed(closed, xs);
    }

    @Benchmark
    public double shapesVirtual() {
        return Codegen.Shapes.virtualSum(shapes);
    }

    @Benchmark
    public double shapesSwitch() {
        return Codegen.Shapes.switchSum(shapes);
    }

    @Benchmark
    public boolean equalsManual() {
        return Codegen.Intrinsics.manualEquals(a, b);
    }

    @Benchmark
    public boolean equalsLibrary() {
        return Codegen.Intrinsics.libraryEquals(a, b);
    }

    @Benchmark
    public float dotScalar() {
        return Codegen.Simd.scalarDot(fa, fb);
    }

    @Benchmark
    public float dotVector() {
        return Codegen.Simd.vectorDot(fa, fb);
    }
}
