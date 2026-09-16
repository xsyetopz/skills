package example;
import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.*;

@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Fork(2)
@Warmup(iterations = 5)
@Measurement(iterations = 5)
public class DelimiterBench {
    @Param({"0", "16", "256", "4096"}) public int length;
    private String text;
    @Setup public void setup() {
        StringBuilder builder = new StringBuilder(length);
        for (int i = 0; i < length; i++) builder.append(i % 7 == 0 ? ':' : 'x');
        text = builder.toString();
        int expected = length == 0 ? 0 : (length - 1) / 7 + 1;
        if (split() != expected || scan() != expected) throw new IllegalStateException("delimiter oracle failed");
    }
    @Benchmark public int split() { return text.split(":", -1).length - 1; }
    @Benchmark public int scan() {
        int result = 0;
        for (int i = 0; i < text.length(); i++) if (text.charAt(i) == ':') result++;
        return result;
    }
}
