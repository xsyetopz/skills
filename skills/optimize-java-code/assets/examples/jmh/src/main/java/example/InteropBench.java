package example;

import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Warmup;

/**
 * JNI versus FFM downcalls to the same C function. verify.sh passes
 * -Dnative.lib and --enable-native-access through -jvmArgsAppend.
 */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Fork(2)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
public class InteropBench {
    private int x = 40;
    private int y = 2;

    @Benchmark
    public int jni() {
        return Interop.jniAdd(x, y);
    }

    @Benchmark
    public int ffm() {
        return Interop.ffmAdd(x, y);
    }

    @Benchmark
    public int ffmCritical() {
        return Interop.ffmAddCritical(x, y);
    }

    @Benchmark
    public int javaBaseline() {
        return x + y;
    }
}
