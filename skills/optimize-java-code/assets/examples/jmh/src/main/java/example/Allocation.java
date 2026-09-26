package example;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import org.openjdk.jmh.annotations.CompilerControl;

/**
 * Allocation constructs. Each nested class holds a baseline and a candidate
 * that compute the same result; Verify proves equivalence and AllocationBench
 * measures gc.alloc.rate.norm with JMH -prof gc.
 */
public final class Allocation {
    private Allocation() {
    }

    /** Escape analysis and scalar replacement. */
    public static final class Escape {
        public record Point(int x, int y) {
            long lengthSquared() {
                return (long) x * x + (long) y * y;
            }
        }

        private Escape() {
        }

        /** The Point never leaves this frame: C2 can scalar-replace it. */
        public static long local(int[] xs) {
            long sum = 0;
            for (int i = 0; i < xs.length; i++) {
                Point p = new Point(xs[i], i);
                sum += p.lengthSquared();
            }
            return sum;
        }

        /** Same work, but the Point is passed to a call that is not inlined,
         *  so it escapes and must be allocated on the heap. */
        public static long escaping(int[] xs) {
            long sum = 0;
            for (int i = 0; i < xs.length; i++) {
                sum += measure(new Point(xs[i], i));
            }
            return sum;
        }

        @CompilerControl(CompilerControl.Mode.DONT_INLINE)
        private static long measure(Point p) {
            return p.lengthSquared();
        }
    }

    /** String building. */
    public static final class Strings {
        private Strings() {
        }

        public static String loopConcat(List<String> parts) {
            String result = "";
            for (String part : parts) {
                result = result + part;
            }
            return result;
        }

        public static String loopBuilder(List<String> parts) {
            StringBuilder result = new StringBuilder();
            for (String part : parts) {
                result.append(part);
            }
            return result.toString();
        }

        /** One expression: javac emits invokedynamic (JEP 280). */
        public static String exprConcat(String key, int id, char sep) {
            return key + sep + id;
        }

        public static String exprBuilder(String key, int id, char sep) {
            return new StringBuilder().append(key).append(sep).append(id)
                .toString();
        }
    }

    /** Boxing. */
    public static final class Boxing {
        private Boxing() {
        }

        public static long sumBoxedList(List<Integer> values) {
            long sum = 0;
            for (Integer value : values) {
                sum += value;
            }
            return sum;
        }

        public static long sumArray(int[] values) {
            long sum = 0;
            for (int value : values) {
                sum += value;
            }
            return sum;
        }

        /** Boxed accumulator: every += unboxes, adds, and re-boxes. */
        public static Long boxedAccumulator(int[] values) {
            Long total = 0L;
            for (int value : values) {
                total += value;
            }
            return total;
        }

        public static long primitiveAccumulator(int[] values) {
            long total = 0L;
            for (int value : values) {
                total += value;
            }
            return total;
        }
    }

    /** Presizing growable collections. */
    public static final class Presize {
        private Presize() {
        }

        public static List<Integer> listDefault(int n) {
            List<Integer> list = new ArrayList<>();
            for (int i = 0; i < n; i++) {
                list.add(i & 127); // cached Integer values: no boxing cost
            }
            return list;
        }

        public static List<Integer> listPresized(int n) {
            List<Integer> list = new ArrayList<>(n);
            for (int i = 0; i < n; i++) {
                list.add(i & 127);
            }
            return list;
        }

        public static Map<Integer, Integer> mapDefault(Integer[] keys) {
            Map<Integer, Integer> map = new HashMap<>();
            for (Integer key : keys) {
                map.put(key, key);
            }
            return map;
        }

        /** Looks presized, but the argument is a capacity, not a count. */
        public static Map<Integer, Integer> mapCapacity(Integer[] keys) {
            Map<Integer, Integer> map = new HashMap<>(keys.length);
            for (Integer key : keys) {
                map.put(key, key);
            }
            return map;
        }

        /** JDK 19+: sized for keys.length mappings without resizing. */
        public static Map<Integer, Integer> mapNewHashMap(Integer[] keys) {
            Map<Integer, Integer> map = HashMap.newHashMap(keys.length);
            for (Integer key : keys) {
                map.put(key, key);
            }
            return map;
        }
    }

    /** Composite map keys. */
    public static final class Keys {
        public record Key(String tenant, int id) {
        }

        private Keys() {
        }

        public static Map<String, Integer> stringIndex(String[] tenants,
                int[] ids) {
            Map<String, Integer> map = HashMap.newHashMap(ids.length);
            for (int i = 0; i < ids.length; i++) {
                map.put(tenants[i] + ":" + ids[i], i);
            }
            return map;
        }

        public static Map<Key, Integer> recordIndex(String[] tenants,
                int[] ids) {
            Map<Key, Integer> map = HashMap.newHashMap(ids.length);
            for (int i = 0; i < ids.length; i++) {
                map.put(new Key(tenants[i], ids[i]), i);
            }
            return map;
        }

        public static long lookupString(Map<String, Integer> map,
                String[] tenants, int[] ids) {
            long sum = 0;
            for (int i = 0; i < ids.length; i++) {
                sum += map.get(tenants[i] + ":" + ids[i]);
            }
            return sum;
        }

        public static long lookupRecord(Map<Key, Integer> map,
                String[] tenants, int[] ids) {
            long sum = 0;
            for (int i = 0; i < ids.length; i++) {
                sum += map.get(new Key(tenants[i], ids[i]));
            }
            return sum;
        }
    }

    /** Streams versus loops. */
    public static final class Pipelines {
        private Pipelines() {
        }

        public static List<Long> squaresStream(int[] values) {
            return Arrays.stream(values)
                .filter(v -> v > 0)
                .mapToLong(v -> (long) v * v)
                .boxed()
                .collect(Collectors.toList());
        }

        public static List<Long> squaresLoop(int[] values) {
            List<Long> result = new ArrayList<>(values.length);
            for (int v : values) {
                if (v > 0) {
                    result.add((long) v * v);
                }
            }
            return result;
        }

        public static long sumStream(int[] values) {
            return IntStream.of(values).filter(v -> v > 0)
                .asLongStream().sum();
        }

        public static long sumLoop(int[] values) {
            long sum = 0;
            for (int v : values) {
                if (v > 0) {
                    sum += v;
                }
            }
            return sum;
        }
    }
}
