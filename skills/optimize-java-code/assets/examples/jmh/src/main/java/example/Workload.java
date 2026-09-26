package example;

import java.time.Duration;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Plain-main workloads for the JVM tools in verify.sh: GC logs, JFR, jcmd,
 * JIT logs, and CDS/AOT startup.
 */
public final class Workload {
    private Workload() {
    }

    public static void main(String[] args) throws Exception {
        String mode = args.length > 0 ? args[0] : "";
        switch (mode) {
            case "gc" -> gc(Integer.parseInt(args[1]));
            case "startup" -> startup();
            case "pinning" -> pinning();
            case "jit" -> jit();
            case "wait" -> Thread.sleep(Duration.ofSeconds(
                Integer.parseInt(args[1])));
            default -> throw new IllegalArgumentException(
                "usage: gc SECONDS | startup | pinning | jit | wait SECONDS");
        }
    }

    /** Allocation churn with a bounded retained set (about 64 MiB). */
    static void gc(int seconds) {
        long end = System.nanoTime() + Duration.ofSeconds(seconds).toNanos();
        ArrayDeque<byte[]> retained = new ArrayDeque<>();
        long checksum = 0;
        while (System.nanoTime() < end) {
            for (int i = 0; i < 1_000; i++) {
                byte[] garbage = new byte[128 + (i & 1023)];
                checksum += garbage.length;
            }
            retained.addLast(new byte[64 * 1024]);
            if (retained.size() > 1_024) {
                retained.removeFirst();
            }
        }
        System.out.println("gc workload checksum " + checksum);
    }

    /** Small stream program in the style of JEP 483's HelloStream. */
    static void startup() {
        List<String> words = List.of("hello", "fuzzy", "world");
        String greeting = words.stream()
            .filter(w -> !w.contains("z"))
            .collect(Collectors.joining(", "));
        System.out.println(greeting);
    }

    /** Holds a class initializer that blocks: a virtual thread running it
     *  stays pinned even on JDK 24+ (JEP 491). */
    static final class SlowInit {
        static final int VALUE;

        static {
            Concurrency.sleep(Duration.ofMillis(60));
            VALUE = 7;
        }

        private SlowInit() {
        }
    }

    /** synchronized + sleep (does not pin on JDK 24+), then a blocking
     *  class initializer (still pins). */
    static void pinning() throws InterruptedException {
        Object lock = new Object();
        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            threads.add(Thread.ofVirtual().start(() -> {
                synchronized (lock) {
                    Concurrency.sleep(Duration.ofMillis(30));
                }
            }));
        }
        for (Thread t : threads) {
            t.join();
        }
        Thread init = Thread.ofVirtual().start(
            () -> System.out.println("SlowInit " + SlowInit.VALUE));
        init.join();
    }

    /** A hot loop for -XX:+PrintCompilation and PrintInlining. */
    static void jit() {
        int[] xs = new int[1_000];
        for (int i = 0; i < xs.length; i++) {
            xs[i] = i - 500;
        }
        long sum = 0;
        for (int round = 0; round < 50_000; round++) {
            sum += Allocation.Escape.local(xs);
        }
        System.out.println("jit workload " + sum);
    }

    /** Two int fields: the shape HeaderBench allocates. */
    static final class TwoInts {
        int a;
        int b;
    }
}
