import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/** Java 8-compatible core. Neither variant mutates caller-owned inputs. */
public final class Pairs {
    private Pairs() { }

    public static String baselineJoin(List<String> values) {
        String result = "";
        for (String value : values) result = result + value;
        return result;
    }
    public static String candidateJoin(List<String> values) {
        StringBuilder result = new StringBuilder();
        for (String value : values) result.append(value);
        return result.toString();
    }
    public static Map<String, Integer> baselineCounts(List<String> values) {
        List<String> keys = new ArrayList<>();
        List<Integer> counts = new ArrayList<>();
        for (String value : values) {
            int index = keys.indexOf(value);
            if (index < 0) { keys.add(value); counts.add(1); }
            else counts.set(index, counts.get(index) + 1);
        }
        Map<String, Integer> result = new LinkedHashMap<>();
        for (int i = 0; i < keys.size(); i++) result.put(keys.get(i), counts.get(i));
        return result;
    }
    public static Map<String, Integer> candidateCounts(List<String> values) {
        Map<String, Integer> result = new LinkedHashMap<>();
        for (String value : values) result.merge(value, 1, Integer::sum);
        return result;
    }
    public static List<Boolean> baselineMembership(List<String> values, List<String> queries) {
        List<Boolean> result = new ArrayList<>();
        for (String query : queries) result.add(values.contains(query));
        return result;
    }
    public static List<Boolean> candidateMembership(List<String> values, List<String> queries) {
        Set<String> members = new HashSet<>(values);
        List<Boolean> result = new ArrayList<>();
        for (String query : queries) result.add(members.contains(query));
        return result;
    }
    public static long baselineSum(int[] values) {
        List<Long> temporary = new ArrayList<>();
        for (int value : values) if (value % 2 == 0)
            temporary.add(Math.multiplyExact((long) value, value));
        long result = 0;
        for (Long value : temporary) result = Math.addExact(result, value);
        return result;
    }
    public static long candidateSum(int[] values) {
        long result = 0;
        for (int value : values) if (value % 2 == 0)
            result = Math.addExact(result, Math.multiplyExact((long) value, value));
        return result;
    }
    public static List<Integer> baselineQueue(List<Integer> values) {
        List<Integer> pending = new ArrayList<>(values);
        List<Integer> result = new ArrayList<>();
        while (!pending.isEmpty()) result.add(pending.remove(0));
        return result;
    }
    public static List<Integer> candidateQueue(List<Integer> values) {
        ArrayDeque<Integer> pending = new ArrayDeque<>(values);
        List<Integer> result = new ArrayList<>();
        while (!pending.isEmpty()) result.add(pending.removeFirst());
        return result;
    }
    public static int baselineDelimiters(String text) {
        return text.split(":", -1).length - 1;
    }
    public static int candidateDelimiters(String text) {
        int result = 0;
        for (int i = 0; i < text.length(); i++) if (text.charAt(i) == ':') result++;
        return result;
    }
    public static List<Integer> baselineDistinct(List<Integer> values) {
        List<Integer> result = new ArrayList<Integer>();
        for (Integer value : values) if (!result.contains(value)) result.add(value);
        return result;
    }
    public static List<Integer> candidateDistinct(List<Integer> values) {
        Set<Integer> seen = new HashSet<Integer>();
        List<Integer> result = new ArrayList<Integer>();
        for (Integer value : values) if (seen.add(value)) result.add(value);
        return result;
    }
    public static List<Integer> baselineReverse(List<Integer> values) {
        List<Integer> result = new ArrayList<Integer>();
        for (Integer value : values) result.add(0, value);
        return result;
    }
    public static List<Integer> candidateReverse(List<Integer> values) {
        List<Integer> result = new ArrayList<Integer>(values);
        java.util.Collections.reverse(result);
        return result;
    }
    public static List<Long> baselinePositiveSquares(int[] values) {
        return Arrays.stream(values)
            .filter(value -> value > 0)
            .mapToLong(value -> (long) value * value)
            .boxed()
            .collect(Collectors.toList());
    }
    public static List<Long> candidatePositiveSquares(int[] values) {
        List<Long> result = new ArrayList<Long>(values.length);
        for (int value : values) if (value > 0) result.add((long) value * value);
        return result;
    }
    private static void equal(Object a, Object b) {
        if (!a.equals(b)) throw new IllegalStateException(a + " != " + b);
    }
    public static void verify() {
        int checks = 0;
        for (int length = 0; length <= 5; length++) {
            int possibilities = (int) Math.pow(3, length);
            for (int code = 0; code < possibilities; code++) {
                int rest = code;
                int[] numbers = new int[length];
                List<Integer> integers = new ArrayList<>();
                List<String> strings = new ArrayList<>();
                for (int i = 0; i < length; i++) {
                    numbers[i] = rest % 3 - 1; rest /= 3;
                    integers.add(numbers[i]); strings.add(Integer.toString(numbers[i]));
                }
                int[] saved = numbers.clone();
                equal(baselineJoin(strings), candidateJoin(strings));
                equal(new ArrayList<>(baselineCounts(strings).entrySet()), new ArrayList<>(candidateCounts(strings).entrySet()));
                equal(baselineMembership(strings, Arrays.asList("0", "9")), candidateMembership(strings, Arrays.asList("0", "9")));
                equal(baselineSum(numbers), candidateSum(numbers));
                equal(baselineQueue(integers), candidateQueue(integers));
                equal(baselineDelimiters(String.join(":", strings)), candidateDelimiters(String.join(":", strings)));
                equal(baselinePositiveSquares(numbers), candidatePositiveSquares(numbers));
                if (!Arrays.equals(saved, numbers)) throw new IllegalStateException("mutated input");
                checks += 8;
            }
        }
        List<String> unicode = Arrays.asList("é", "e\u0301", "é", "🙂", "\0");
        Map<String, Integer> expected = new LinkedHashMap<>();
        expected.put("é", 2); expected.put("e\u0301", 1); expected.put("🙂", 1); expected.put("\0", 1);
        equal(baselineCounts(unicode), expected); equal(candidateCounts(unicode), expected);
        equal(baselineJoin(Arrays.asList("a", "", "é", "🙂")), "aé🙂");
        equal(candidateJoin(Arrays.asList("a", "", "é", "🙂")), "aé🙂");
        equal(baselineDelimiters(":é::🙂:"), 4); equal(candidateDelimiters(":é::🙂:"), 4);
        equal(baselineDelimiters(""), 0); equal(candidateDelimiters(""), 0);
        equal(baselineSum(new int[] {-3, 2, 2, 0, 5}), 8L);
        equal(candidateSum(new int[] {-3, 2, 2, 0, 5}), 8L);
        equal(baselineQueue(Arrays.asList(2, 1, 2)), Arrays.asList(2, 1, 2));
        equal(candidateQueue(Arrays.asList(2, 1, 2)), Arrays.asList(2, 1, 2));
        for (boolean candidate : new boolean[] {false, true}) {
            boolean threw = false;
            try {
                int[] overflow = {Integer.MIN_VALUE, Integer.MIN_VALUE};
                if (candidate) candidateSum(overflow); else baselineSum(overflow);
            } catch (ArithmeticException expectedOverflow) { threw = true; }
            if (!threw) throw new IllegalStateException("overflow contract lost");
        }
        // A delimiter-preserving split is essential. Default split drops trailing empties.
        equal("a:".split(":").length, 1);
        equal("a:".split(":", -1).length, 2);
        System.out.println("PASS differential and expected result checks: " + checks + " + edge cases");
    }
    public static void main(String[] args) {
        if (args.length == 1 && args[0].equals("verify")) { verify(); return; }
        if (args.length != 3 || !(args[0].equals("baseline") || args[0].equals("candidate")))
            throw new IllegalArgumentException("usage: Pairs verify | baseline|candidate CASE SIZE");
        int which = Integer.parseInt(args[1]), size = Integer.parseInt(args[2]);
        if (size < 0 || size > 100000) throw new IllegalArgumentException("size 0..100000");
        boolean candidate = args[0].equals("candidate");
        int[] numbers = new int[size];
        List<Integer> integers = new ArrayList<>();
        List<String> strings = new ArrayList<>();
        for (int i = 0; i < size; i++) {
            numbers[i] = i % 31 - 15; integers.add(numbers[i]);
            strings.add(Integer.toString(numbers[i]));
        }
        Object result;
        switch (which) {
            case 1: result = candidate ? candidateJoin(strings) : baselineJoin(strings); break;
            case 2: result = candidate ? candidateCounts(strings) : baselineCounts(strings); break;
            case 3: result = candidate ? candidateMembership(strings, strings) : baselineMembership(strings, strings); break;
            case 4: result = candidate ? candidateSum(numbers) : baselineSum(numbers); break;
            case 5: result = candidate ? candidateQueue(integers) : baselineQueue(integers); break;
            case 6: String text = String.join(":", strings);
                    result = candidate ? candidateDelimiters(text) : baselineDelimiters(text); break;
            case 7: result = candidate ? candidateSum(numbers) : baselineSum(numbers); break;
            case 8: result = candidate ? candidatePositiveSquares(numbers) : baselinePositiveSquares(numbers); break;
            default: throw new IllegalArgumentException("case 1..8");
        }
        System.out.println(result);
    }
}
