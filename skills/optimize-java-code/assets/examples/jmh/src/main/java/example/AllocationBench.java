package example;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
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

/**
 * Allocation pairs. Run with -prof gc and read gc.alloc.rate.norm (B/op).
 * Inputs are built in @Setup(Level.Trial), outside the measured region.
 */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Fork(value = 2, jvmArgsAppend = {"-Xms1g", "-Xmx1g"})
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
public class AllocationBench {
    private int[] xs;
    private int[] positives;
    private int[] wide;
    private List<Integer> boxed;
    private List<String> parts;
    private Integer[] keys;
    private String[] tenants;
    private int[] ids;
    private Map<String, Integer> byString;
    private Map<Allocation.Keys.Key, Integer> byRecord;
    private String key;
    private int id;

    @Setup(Level.Trial)
    public void setup() {
        xs = Verify.ints(1_000);
        positives = new int[1_000];
        wide = new int[1_000];
        boxed = new ArrayList<>(xs.length);
        for (int i = 0; i < xs.length; i++) {
            positives[i] = i + 1;
            wide[i] = xs[i] * 1_000; // mostly outside the Integer cache
            boxed.add(wide[i]);
        }
        parts = new ArrayList<>();
        for (int i = 0; i < 64; i++) {
            parts.add("part" + i);
        }
        keys = new Integer[1_000];
        tenants = new String[1_000];
        ids = new int[1_000];
        for (int i = 0; i < keys.length; i++) {
            keys[i] = i * 7919;
            tenants[i] = "tenant" + (i % 10);
            ids[i] = i;
        }
        byString = Allocation.Keys.stringIndex(tenants, ids);
        byRecord = Allocation.Keys.recordIndex(tenants, ids);
        key = "user";
        id = 12_345;
    }

    @Benchmark
    public long escapeLocal() {
        return Allocation.Escape.local(xs);
    }

    @Benchmark
    @Fork(value = 2, jvmArgsAppend = {"-Xms1g", "-Xmx1g",
        "-XX:-DoEscapeAnalysis"})
    public long escapeLocalNoEA() {
        return Allocation.Escape.local(xs);
    }

    @Benchmark
    public long escapeEscaping() {
        return Allocation.Escape.escaping(xs);
    }

    @Benchmark
    public String stringLoopConcat() {
        return Allocation.Strings.loopConcat(parts);
    }

    @Benchmark
    public String stringLoopBuilder() {
        return Allocation.Strings.loopBuilder(parts);
    }

    @Benchmark
    public String stringExprConcat() {
        return Allocation.Strings.exprConcat(key, id, ':');
    }

    @Benchmark
    public String stringExprBuilder() {
        return Allocation.Strings.exprBuilder(key, id, ':');
    }

    @Benchmark
    public long boxedListSum() {
        return Allocation.Boxing.sumBoxedList(boxed);
    }

    @Benchmark
    public long primitiveArraySum() {
        return Allocation.Boxing.sumArray(wide);
    }

    @Benchmark
    public Long boxedAccumulator() {
        return Allocation.Boxing.boxedAccumulator(positives);
    }

    @Benchmark
    public long primitiveAccumulator() {
        return Allocation.Boxing.primitiveAccumulator(positives);
    }

    @Benchmark
    public List<Integer> listDefault() {
        return Allocation.Presize.listDefault(1_000);
    }

    @Benchmark
    public List<Integer> listPresized() {
        return Allocation.Presize.listPresized(1_000);
    }

    @Benchmark
    public Map<Integer, Integer> mapDefault() {
        return Allocation.Presize.mapDefault(keys);
    }

    @Benchmark
    public Map<Integer, Integer> mapCapacityArg() {
        return Allocation.Presize.mapCapacity(keys);
    }

    @Benchmark
    public Map<Integer, Integer> mapNewHashMap() {
        return Allocation.Presize.mapNewHashMap(keys);
    }

    @Benchmark
    public long keyLookupString() {
        return Allocation.Keys.lookupString(byString, tenants, ids);
    }

    @Benchmark
    public long keyLookupRecord() {
        return Allocation.Keys.lookupRecord(byRecord, tenants, ids);
    }

    @Benchmark
    public List<Long> squaresStream() {
        return Allocation.Pipelines.squaresStream(xs);
    }

    @Benchmark
    public List<Long> squaresLoop() {
        return Allocation.Pipelines.squaresLoop(xs);
    }

    @Benchmark
    public long sumStream() {
        return Allocation.Pipelines.sumStream(xs);
    }

    @Benchmark
    public long sumLoop() {
        return Allocation.Pipelines.sumLoop(xs);
    }
}
