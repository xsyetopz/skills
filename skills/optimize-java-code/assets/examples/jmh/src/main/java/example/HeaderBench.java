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
 * Compact object headers (JEP 519): the same allocation measured in a fork
 * with and without -XX:+UseCompactObjectHeaders. Returned objects escape,
 * so gc.alloc.rate.norm is the object size.
 */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Fork(2)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 3, time = 1)
public class HeaderBench {
    @Benchmark
    public Object objectDefault() {
        return new Object();
    }

    @Benchmark
    @Fork(value = 2, jvmArgsAppend = "-XX:+UseCompactObjectHeaders")
    public Object objectCompact() {
        return new Object();
    }

    @Benchmark
    public Object twoIntsDefault() {
        return new Workload.TwoInts();
    }

    @Benchmark
    @Fork(value = 2, jvmArgsAppend = "-XX:+UseCompactObjectHeaders")
    public Object twoIntsCompact() {
        return new Workload.TwoInts();
    }
}
