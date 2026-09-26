// Simple is better than complex: one rule, one static method.
import java.util.Map;

public final class SimpleAfter {
    private static final Map<String, String> SYMBOLS = Map.of("EUR", "€", "USD", "$");

    private SimpleAfter() {}

    public static String formatPrice(long cents, String currency) {
        String symbol = SYMBOLS.get(currency);
        if (symbol == null) {
            throw new IllegalArgumentException("unknown currency " + currency);
        }
        return String.format("%s%d.%02d", symbol, cents / 100, cents % 100);
    }

    public static void main(String[] args) {
        long[] amounts = {0, 5, 99, 100, 123456};
        int cases = 0;
        for (long cents : amounts) {
            for (String currency : new String[] {"EUR", "USD"}) {
                String before = SimpleBefore.formatPrice(cents, currency);
                String after = formatPrice(cents, currency);
                if (!before.equals(after)) {
                    throw new AssertionError(before + " != " + after);
                }
                cases++;
            }
        }
        System.out.println("simple: " + cases + " cases match");
    }
}
