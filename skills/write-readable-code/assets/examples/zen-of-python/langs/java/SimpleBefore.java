// Replaced design: an interface, one implementation, and a factory for a
// single formatting rule. Kept only to compare output and class count.
import java.util.Map;

public final class SimpleBefore {
    interface PriceFormatter {
        String format(long cents);
    }

    static final class SymbolPriceFormatter implements PriceFormatter {
        private final String symbol;

        SymbolPriceFormatter(String symbol) {
            this.symbol = symbol;
        }

        @Override
        public String format(long cents) {
            return String.format("%s%d.%02d", symbol, cents / 100, cents % 100);
        }
    }

    static final class PriceFormatterFactory {
        private static final Map<String, String> SYMBOLS = Map.of("EUR", "€", "USD", "$");

        PriceFormatter create(String currency) {
            return new SymbolPriceFormatter(SYMBOLS.get(currency));
        }
    }

    public static String formatPrice(long cents, String currency) {
        return new PriceFormatterFactory().create(currency).format(cents);
    }
}
