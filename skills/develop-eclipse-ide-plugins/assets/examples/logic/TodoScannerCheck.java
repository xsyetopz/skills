import java.util.List;

import org.acme.todos.TodoScanner;
import org.acme.todos.TodoScanner.Todo;

/** Runs TodoScanner on a plain JVM: no OSGi, no workbench. */
public final class TodoScannerCheck {
    private static int failures;

    private static void check(String label, Object actual, Object expected) {
        boolean ok = expected.equals(actual);
        if (!ok) {
            failures++;
        }
        System.out.println((ok ? "ok   " : "FAIL ") + label + ": " + actual);
    }

    public static void main(String[] args) {
        List<Todo> todos = TodoScanner.scan(
                "one\n// TODO: first\nTODO:second\nno todo here\n", "TODO");
        check("count", todos.size(), 2);
        check("first", todos.get(0), new Todo(2, 7, 11, "first"));
        check("second", todos.get(1), new Todo(3, 19, 23, "second"));
        check("custom tag", TodoScanner.scan("FIXME: x\nTODO: y", "FIXME")
                .size(), 1);
        check("word boundary", TodoScanner.scan("XTODO: no", "TODO")
                .size(), 0);
        check("regex quoted", TodoScanner.scan("a.b: yes\naxb: no", "a.b")
                .size(), 1);
        try {
            TodoScanner.scan("x", " ");
            check("blank tag rejected", "accepted", "rejected");
        } catch (IllegalArgumentException e) {
            check("blank tag rejected", "rejected", "rejected");
        }
        if (failures > 0) {
            System.exit(1);
        }
    }
}
