package example;

import java.lang.reflect.Field;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;

/**
 * Equivalence oracles and deterministic claims for every construct.
 * Run: java --add-opens java.base/java.util=ALL-UNNAMED
 *   --add-modules jdk.incubator.vector --enable-native-access=ALL-UNNAMED
 *   -Dnative.lib=... -cp benchmarks.jar example.Verify
 */
public final class Verify {
    private Verify() {
    }

    public static void main(String[] args) throws Exception {
        allocation();
        codegen();
        concurrency();
        interop();
        System.out.println("PASS " + Check.count() + " checks");
    }

    static int[] ints(int n) {
        int[] xs = new int[n];
        for (int i = 0; i < n; i++) {
            xs[i] = (i * 31 % 97) - 48;
        }
        return xs;
    }

    static void allocation() {
        for (int n : new int[] {0, 1, 7, 1_000}) {
            int[] xs = ints(n);
            Check.equal("escape", Allocation.Escape.local(xs),
                Allocation.Escape.escaping(xs));
            List<Integer> boxed = new ArrayList<>();
            for (int x : xs) {
                boxed.add(x);
            }
            Check.equal("boxed-list", Allocation.Boxing.sumArray(xs),
                Allocation.Boxing.sumBoxedList(boxed));
            Check.equal("boxed-accumulator",
                Allocation.Boxing.primitiveAccumulator(xs),
                (long) Allocation.Boxing.boxedAccumulator(xs));
            Check.equal("streams-collect",
                Allocation.Pipelines.squaresStream(xs),
                Allocation.Pipelines.squaresLoop(xs));
            Check.equal("streams-sum", Allocation.Pipelines.sumStream(xs),
                Allocation.Pipelines.sumLoop(xs));
            Check.equal("arraylist-presize",
                Allocation.Presize.listDefault(n),
                Allocation.Presize.listPresized(n));
        }
        List<String> parts = List.of("a", "", "é", "🙂", "\0");
        Check.equal("string-loop", Allocation.Strings.loopConcat(parts),
            Allocation.Strings.loopBuilder(parts));
        Check.equal("string-loop-empty",
            Allocation.Strings.loopConcat(List.of()),
            Allocation.Strings.loopBuilder(List.of()));
        Check.equal("string-expr",
            Allocation.Strings.exprConcat(null, -1, ':'),
            Allocation.Strings.exprBuilder(null, -1, ':'));
        Check.throwsType("boxed-null", NullPointerException.class,
            () -> Allocation.Boxing.sumBoxedList(
                Arrays.asList(1, null)));

        // Integer cache (JLS 5.1.7): == on boxes is identity, not value.
        Integer small1 = 127;
        Integer small2 = 127;
        Integer big1 = 1_000;
        Integer big2 = 1_000;
        Check.isTrue("integer-cache", small1 == small2,
            "127 must come from the Integer cache");
        Check.isTrue("integer-cache", big1.equals(big2),
            "equals compares values");
        Integer edge1 = 128;
        Integer edge2 = 128;
        System.out.println("INFO integer-cache: 128 == 128 is "
            + (edge1 == edge2) + ", 1000 == 1000 is " + (big1 == big2)
            + " (identity; not guaranteed by JLS 5.1.7)");

        boxedFootprint();
        hashMapResizes();
        recordKeys();
    }

    /** Heap bytes to hold n uncached int values: List of Integer vs int[]. */
    static void boxedFootprint() {
        final int n = 100_000;
        long before = Check.threadAllocatedBytes();
        List<Integer> list = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            list.add(i * 1_000 + 1_000); // outside the Integer cache
        }
        long listBytes = Check.threadAllocatedBytes() - before;
        before = Check.threadAllocatedBytes();
        int[] array = new int[n];
        for (int i = 0; i < n; i++) {
            array[i] = i * 1_000 + 1_000;
        }
        long arrayBytes = Check.threadAllocatedBytes() - before;
        System.out.printf("FOOTPRINT n=%d List<Integer>=%d B int[]=%d B%n",
            n, listBytes, arrayBytes);
        Check.equal("boxed-footprint", Allocation.Boxing.sumArray(array),
            Allocation.Boxing.sumBoxedList(list));
        Check.isTrue("boxed-footprint", listBytes > 4 * arrayBytes,
            "boxed list should need more than 4x the bytes of int[]");
    }

    static void hashMapResizes() {
        for (int n : new int[] {700, 1_000, 10_000}) {
            Integer[] keys = new Integer[n];
            for (int i = 0; i < n; i++) {
                keys[i] = i * 7919;
            }
            Map<Integer, Integer> a = Allocation.Presize.mapDefault(keys);
            Check.equal("hashmap-presize", a,
                Allocation.Presize.mapCapacity(keys));
            Check.equal("hashmap-presize", a,
                Allocation.Presize.mapNewHashMap(keys));
            int dflt = resizes(new HashMap<>(), keys);
            int cap = resizes(new HashMap<>(n), keys);
            int sized = resizes(HashMap.newHashMap(n), keys);
            System.out.printf("RESIZES n=%d default=%d new HashMap<>(n)=%d"
                + " newHashMap(n)=%d%n", n, dflt, cap, sized);
            Check.equal("newHashMap-no-resize", 0, sized);
            Check.isTrue("default-resizes", dflt > cap,
                "default constructor must resize more than presized");
        }
    }

    /** Counts table reallocations after the first one. */
    static int resizes(HashMap<Integer, Integer> map, Integer[] keys) {
        try {
            Field table = HashMap.class.getDeclaredField("table");
            table.setAccessible(true); // needs --add-opens java.base/java.util
            int count = 0;
            int length = 0;
            for (Integer key : keys) {
                map.put(key, key);
                Object[] t = (Object[]) table.get(map);
                if (length != 0 && t.length != length) {
                    count++;
                }
                length = t.length;
            }
            return count;
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException(e);
        }
    }

    record ArrayKey(int[] parts) {
    }

    static void recordKeys() {
        String[] tenants = {"acme", "acme", "beta", "a:b", "a"};
        int[] ids = {1, 2, 1, 3, 0};
        var byString = Allocation.Keys.stringIndex(tenants, ids);
        var byRecord = Allocation.Keys.recordIndex(tenants, ids);
        Check.equal("record-keys",
            Allocation.Keys.lookupString(byString, tenants, ids),
            Allocation.Keys.lookupRecord(byRecord, tenants, ids));
        Check.equal("record-equals", new Allocation.Keys.Key("a", 3),
            new Allocation.Keys.Key(new String("a"), 3));
        Check.equal("record-hash", new Allocation.Keys.Key("a", 3).hashCode(),
            new Allocation.Keys.Key(new String("a"), 3).hashCode());
        // Record equality uses the component's equals: arrays by identity.
        Check.isTrue("record-array-component",
            !new ArrayKey(new int[] {1}).equals(new ArrayKey(new int[] {1})),
            "array components compare by reference");
    }

    static void codegen() {
        for (int n : new int[] {0, 1, 5, 1_000}) {
            int[] xs = ints(n);
            Check.equal("final-cha",
                Codegen.Leaf.open(new Codegen.Leaf.OpenScaler(3), xs),
                Codegen.Leaf.closed(new Codegen.Leaf.FinalScaler(3), xs));
            Codegen.Shapes.Shape[] shapes = Codegen.Shapes.mixed(n);
            Check.equal("sealed-switch", Codegen.Shapes.virtualSum(shapes),
                Codegen.Shapes.switchSum(shapes));
        }
        byte[] a = new byte[4_096];
        Arrays.fill(a, (byte) 5);
        for (int at : new int[] {-1, 0, 17, 4_095}) {
            byte[] b = a.clone();
            if (at >= 0) {
                b[at] = 9;
            }
            Check.equal("arrays-equals", Codegen.Intrinsics.manualEquals(a, b),
                Codegen.Intrinsics.libraryEquals(a, b));
            Check.equal("arrays-mismatch",
                Codegen.Intrinsics.manualMismatch(a, b),
                Codegen.Intrinsics.libraryMismatch(a, b));
        }
        byte[] shorter = Arrays.copyOf(a, 10);
        Check.equal("arrays-mismatch-length",
            Codegen.Intrinsics.manualMismatch(a, shorter),
            Codegen.Intrinsics.libraryMismatch(a, shorter));

        // Floating-point addition is not associative (JLS 15.18.2).
        double[] v = {1e16, -1e16, 1.0};
        Check.isTrue("fp-regrouping",
            (v[0] + v[1]) + v[2] != v[0] + (v[1] + v[2]),
            "regrouping must change this sum");
        float[] fa = new float[1_027];
        float[] fb = new float[fa.length];
        for (int i = 0; i < fa.length; i++) {
            fa[i] = (i % 13) * 0.1f;
            fb[i] = ((i * 7) % 11) * 0.3f;
        }
        float scalar = Codegen.Simd.scalarDot(fa, fb);
        float vector = Codegen.Simd.vectorDot(fa, fb);
        System.out.printf("INFO vector-dot lanes=%d scalar=%s vector=%s"
            + " bitwiseEqual=%b%n", Codegen.Simd.lanes(), scalar, vector,
            Float.floatToIntBits(scalar) == Float.floatToIntBits(vector));
        Check.isTrue("vector-dot", Math.abs(scalar - vector)
            <= 1e-5f * Math.abs(scalar), "outside relative tolerance 1e-5");
    }

    static void concurrency() throws Exception {
        Concurrency.Counters counters = new Concurrency.Counters();
        List<Thread> threads = new ArrayList<>();
        for (int t = 0; t < 4; t++) {
            threads.add(Thread.ofPlatform().start(() -> {
                for (int i = 0; i < 100_000; i++) {
                    counters.incrementAtomic();
                    counters.incrementAdder();
                }
            }));
        }
        for (Thread t : threads) {
            t.join();
        }
        Check.equal("longadder", 400_000L, counters.atomicValue());
        Check.equal("longadder", 400_000L, counters.adderValue());

        int keys = 50;
        int racy = Concurrency.factoryCalls(false, 8, keys);
        int atomic = Concurrency.factoryCalls(true, 8, keys);
        System.out.printf("FACTORY CALLS keys=%d get+putIfAbsent=%d"
            + " computeIfAbsent=%d%n", keys, racy, atomic);
        Check.equal("computeIfAbsent-once", keys, atomic);
        Check.isTrue("racy-at-least-once", racy >= keys, "lost a key");

        int tasks = 400;
        Duration block = Duration.ofMillis(50);
        long expected = (long) tasks * (tasks - 1) / 2;
        long t0 = System.nanoTime();
        ExecutorService pool = Concurrency.platformPool(20);
        Check.equal("virtual-threads", expected,
            Concurrency.runBlocking(pool, tasks, block));
        long platformMs = (System.nanoTime() - t0) / 1_000_000;
        t0 = System.nanoTime();
        Check.equal("virtual-threads", expected,
            Concurrency.runBlocking(Concurrency.virtualPerTask(), tasks,
                block));
        long virtualMs = (System.nanoTime() - t0) / 1_000_000;
        System.out.printf("WALL blocking tasks=%d block=%dms"
            + " fixedPool(20)=%dms virtualPerTask=%dms%n", tasks,
            block.toMillis(), platformMs, virtualMs);
        Check.isTrue("virtual-threads-wall", virtualMs * 4 < platformMs,
            "virtual threads should finish blocking tasks >4x sooner");
    }

    static void interop() {
        int[][] cases = {{1, 2}, {-5, 3}, {Integer.MAX_VALUE, 1},
            {Integer.MIN_VALUE, -1}};
        for (int[] c : cases) {
            int expected = c[0] + c[1]; // wraps
            Check.equal("jni-add", expected, Interop.jniAdd(c[0], c[1]));
            Check.equal("ffm-add", expected, Interop.ffmAdd(c[0], c[1]));
            Check.equal("ffm-add-critical", expected,
                Interop.ffmAddCritical(c[0], c[1]));
        }
        Check.equal("ffm-strlen", 6L, Interop.strlen("héllo")); // UTF-8
        Check.equal("ffm-strlen", 0L, Interop.strlen(""));
        Check.throwsType("ffm-arena-closed", IllegalStateException.class,
            () -> Interop.closedSegment().get(
                java.lang.foreign.ValueLayout.JAVA_INT, 0));
    }
}
