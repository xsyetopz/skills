package example;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.LongAdder;
import java.util.function.Function;

/** Concurrency constructs: counters, memoization, virtual threads. */
public final class Concurrency {
    private Concurrency() {
    }

    /** Shared statistics counter. */
    public static final class Counters {
        private final AtomicLong atomic = new AtomicLong();
        private final LongAdder adder = new LongAdder();

        public void incrementAtomic() {
            atomic.incrementAndGet();
        }

        public void incrementAdder() {
            adder.increment();
        }

        public long atomicValue() {
            return atomic.get();
        }

        public long adderValue() {
            return adder.sum(); // not an atomic snapshot under updates
        }
    }

    /** Memoization in a ConcurrentHashMap. */
    public static final class Memo<K, V> {
        private final ConcurrentHashMap<K, V> map = new ConcurrentHashMap<>();
        private final Function<K, V> factory;

        public Memo(Function<K, V> factory) {
            this.factory = factory;
        }

        /** Check-then-act: two threads can both miss and both compute. */
        public V getOrComputeRacy(K key) {
            V value = map.get(key);
            if (value == null) {
                V created = factory.apply(key);
                V previous = map.putIfAbsent(key, created);
                value = previous == null ? created : previous;
            }
            return value;
        }

        /** Atomic: the factory runs at most once per absent key. */
        public V getOrCompute(K key) {
            return map.computeIfAbsent(key, factory);
        }
    }

    /**
     * Runs {@code threads} callers against the same keys at once and returns
     * how many times the factory ran.
     */
    public static int factoryCalls(boolean atomic, int threads, int keys)
            throws InterruptedException {
        AtomicInteger calls = new AtomicInteger();
        Memo<Integer, String> memo = new Memo<>(k -> {
            calls.incrementAndGet();
            sleep(Duration.ofMillis(2)); // widen the race window
            return "v" + k;
        });
        CountDownLatch start = new CountDownLatch(1);
        List<Thread> workers = new ArrayList<>();
        for (int t = 0; t < threads; t++) {
            workers.add(Thread.ofPlatform().start(() -> {
                await(start);
                for (int k = 0; k < keys; k++) {
                    String v = atomic ? memo.getOrCompute(k)
                                      : memo.getOrComputeRacy(k);
                    if (!v.equals("v" + k)) {
                        throw new IllegalStateException("wrong value");
                    }
                }
            }));
        }
        start.countDown();
        for (Thread w : workers) {
            w.join();
        }
        return calls.get();
    }

    /** Submits {@code tasks} blocking tasks and waits for all of them. */
    public static long runBlocking(ExecutorService executor, int tasks,
            Duration block) throws Exception {
        try (executor) {
            List<Future<Integer>> futures = new ArrayList<>(tasks);
            for (int i = 0; i < tasks; i++) {
                int id = i;
                futures.add(executor.submit(() -> {
                    sleep(block); // stands in for a blocking I/O call
                    return id;
                }));
            }
            long sum = 0;
            for (Future<Integer> f : futures) {
                sum += f.get();
            }
            return sum;
        }
    }

    public static ExecutorService platformPool(int size) {
        return Executors.newFixedThreadPool(size);
    }

    public static ExecutorService virtualPerTask() {
        return Executors.newVirtualThreadPerTaskExecutor();
    }

    static void sleep(Duration d) {
        try {
            Thread.sleep(d);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(e);
        }
    }

    private static void await(CountDownLatch latch) {
        try {
            latch.await();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(e);
        }
    }
}
