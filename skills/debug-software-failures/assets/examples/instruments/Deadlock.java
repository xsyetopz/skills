// Two threads lock two monitors in opposite order. `jcmd <pid> Thread.print`
// ends with "Found one Java-level deadlock" and both stacks.
public final class Deadlock {
    private static final Object A = new Object();
    private static final Object B = new Object();

    public static void main(String[] args) throws Exception {
        var holdBoth = new java.util.concurrent.CyclicBarrier(2);
        Thread first = new Thread(() -> lockBoth(A, B, holdBoth), "first");
        Thread second = new Thread(() -> lockBoth(B, A, holdBoth), "second");
        first.start();
        second.start();
        System.out.println("started " + ProcessHandle.current().pid());
        first.join();
    }

    private static void lockBoth(Object outer, Object inner,
            java.util.concurrent.CyclicBarrier barrier) {
        synchronized (outer) {
            try {
                barrier.await();
            } catch (Exception e) {
                throw new IllegalStateException(e);
            }
            synchronized (inner) {
                System.out.println("unreachable");
            }
        }
    }
}
