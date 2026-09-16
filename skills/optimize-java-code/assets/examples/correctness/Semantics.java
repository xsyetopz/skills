import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

public final class Semantics {
  private static boolean contract(boolean bad, int topic) {
    switch (topic) {
      case 1: { // Value equality must not depend on reference identity or VM caches.
        String left = new String("value"), right = new String("value");
        return bad ? left == right : left.equals(right);
      }
      case 2: { // Snapshot the mutable input used as a hash key.
        List<Integer> source = new ArrayList<>(Arrays.asList(1));
        Map<List<Integer>, String> map = new HashMap<>();
        map.put(bad ? source : new ArrayList<>(source), "value");
        source.add(2);
        return "value".equals(map.get(Arrays.asList(1)));
      }
      case 3: { // Fixed-order floating evaluation is not associative.
        double[] v = {1e16, -1e16, 1.0};
        double result = bad ? v[0] + (v[1] + v[2]) : (v[0] + v[1]) + v[2];
        return result == 1.0;
      }
      case 4: { // This boundary cannot throw InterruptedException: restore status.
        Thread.interrupted();
        try { throw new InterruptedException("cancel"); }
        catch (InterruptedException e) { if (!bad) Thread.currentThread().interrupt(); }
        return Thread.interrupted(); // Consume the flag to isolate later fixtures.
      }
      case 5: { // Two read-modify-write operations must not lose one increment.
        AtomicInteger value = new AtomicInteger();
        if (bad) { int a=value.get(), b=value.get(); value.set(a+1); value.set(b+1); }
        else { value.incrementAndGet(); value.incrementAndGet(); }
        return value.get() == 2;
      }
      case 6: { // User callback must run outside the private monitor.
        Object monitor = new Object();
        boolean held;
        if (bad) { synchronized (monitor) { held=Thread.holdsLock(monitor); } }
        else { synchronized (monitor) { /* capture state only */ } held=Thread.holdsLock(monitor); }
        return !held;
      }
      case 7: { // Canonical output order must be independent of arrival order.
        List<Integer> keys = new ArrayList<>(Arrays.asList(2,1));
        if (!bad) keys.sort(Integer::compareTo);
        return keys.equals(Arrays.asList(1,2));
      }
      case 8: // Machine identifiers use explicitly locale-independent case mapping.
        return "TITLE".toLowerCase(bad ? new Locale("tr", "TR") : Locale.ROOT).equals("title");
      default: throw new IllegalArgumentException("topic must be 1..8");
    }
  }
  public static void main(String[] args) {
    if (args.length != 2 || !(args[0].equals("red") || args[0].equals("green")))
      throw new IllegalArgumentException("usage: red|green TOPIC");
    int topic=Integer.parseInt(args[1]);
    boolean pass=contract(args[0].equals("red"),topic);
    System.out.printf("CONTRACT topic %d: %s%n",topic,pass?"PASS":"FAIL");
    if (!pass) System.exit(1);
  }
}
