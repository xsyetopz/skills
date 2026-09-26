package example;

import java.lang.management.ManagementFactory;
import java.util.Objects;

/**
 * Oracle helpers shared by every construct. A failed check throws, so
 * verify.sh exits nonzero and names the construct.
 */
public final class Check {
    private static int count;

    private Check() {
    }

    public static int count() {
        return count;
    }

    public static void equal(String construct, Object expected,
            Object actual) {
        count++;
        if (!Objects.equals(expected, actual)) {
            throw new IllegalStateException(
                construct + ": expected " + expected + ", got " + actual);
        }
    }

    public static void isTrue(String construct, boolean condition,
            String detail) {
        count++;
        if (!condition) {
            throw new IllegalStateException(construct + ": " + detail);
        }
    }

    public static void throwsType(String construct,
            Class<? extends Throwable> type, Runnable action) {
        count++;
        try {
            action.run();
        } catch (Throwable t) {
            if (type.isInstance(t)) {
                return;
            }
            throw new IllegalStateException(
                construct + ": expected " + type.getName() + ", got " + t, t);
        }
        throw new IllegalStateException(
            construct + ": expected " + type.getName() + ", none thrown");
    }

    /** Bytes allocated by the current thread (HotSpot extension). */
    public static long threadAllocatedBytes() {
        var bean = (com.sun.management.ThreadMXBean)
            ManagementFactory.getThreadMXBean();
        return bean.getCurrentThreadAllocatedBytes();
    }
}
