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
import org.openjdk.jmh.annotations.Threads;
import org.openjdk.jmh.annotations.Warmup;

/**
 * Shared counter under contention: Scope.Benchmark shares one instance
 * across the 4 benchmark threads.
 */
@State(Scope.Benchmark)
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@Fork(2)
@Threads(4)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
public class ConcurrencyBench {
    private final Concurrency.Counters counters = new Concurrency.Counters();

    @Benchmark
    public void counterAtomicLong() {
        counters.incrementAtomic();
    }

    @Benchmark
    public void counterLongAdder() {
        counters.incrementAdder();
    }
}
