package org.acme.todos;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Finds "TAG: message" comments in text. No Eclipse types. */
public final class TodoScanner {

    /** A match: 1-based line, 0-based char range of the tag. */
    public record Todo(int line, int charStart, int charEnd,
            String message) {
    }

    private TodoScanner() {
    }

    public static List<Todo> scan(String text, String tag) {
        if (tag.isBlank()) {
            throw new IllegalArgumentException("tag must not be blank");
        }
        Pattern pattern = Pattern.compile(
                "\\b" + Pattern.quote(tag) + ":[ \\t]*([^\\r\\n]*)");
        List<Todo> todos = new ArrayList<>();
        Matcher matcher = pattern.matcher(text);
        while (matcher.find()) {
            int line = 1;
            for (int i = 0; i < matcher.start(); i++) {
                if (text.charAt(i) == '\n') {
                    line++;
                }
            }
            todos.add(new Todo(line, matcher.start(),
                    matcher.start() + tag.length(),
                    matcher.group(1).strip()));
        }
        return todos;
    }
}
