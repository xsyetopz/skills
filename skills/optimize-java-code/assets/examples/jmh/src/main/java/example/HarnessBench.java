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
import org.openjdk.jmh.infra.Blackhole;

/**
 * JMH pitfalls after JMHSample_08_DeadCode and JMHSample_10_ConstantFold:
 * a discarded or constant result lets C2 delete the measured work. work()
 * is pure arithmetic, so C2 may delete or fold it when misused.
 */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Fork(2)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
public class HarnessBench {
    private double x = Math.PI; // non-final field: not a constant
    private static final double CONSTANT = Math.PI;

    /** A chain of 16 dependent divisions: pure, so removable if unused. */
    static double work(double v) {
        double r = v;
        for (int i = 0; i < 16; i++) {
            r = r / 1.0001 + 1.0;
        }
        return r;
    }

    @Benchmark
    public void baseline() {
        // empty: the harness floor
    }

    @Benchmark
    public void wrongDiscarded() {
        work(x); // result unused: dead-code eliminated
    }

    @Benchmark
    public double wrongConstant() {
        return work(CONSTANT); // folded at compile time
    }

    @Benchmark
    public double rightReturned() {
        return work(x);
    }

    /** The JMH sample's own Math.log case, kept to show platform variance. */
    @Benchmark
    public void logDiscarded() {
        Math.log(x);
    }

    @Benchmark
    public double logReturned() {
        return Math.log(x);
    }

    @Benchmark
    public void rightBlackhole(Blackhole bh) {
        bh.consume(work(x));
        bh.consume(work(x + 1));
    }
}
