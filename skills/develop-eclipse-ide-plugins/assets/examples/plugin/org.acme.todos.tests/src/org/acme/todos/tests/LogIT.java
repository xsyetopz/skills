package org.acme.todos.tests;

import static org.junit.Assert.assertTrue;

import java.nio.file.Files;

import org.eclipse.core.runtime.ILog;
import org.eclipse.core.runtime.Platform;
import org.junit.Test;

public class LogIT {
    @Test
    public void iLogWritesToTheWorkspaceLog() throws Exception {
        String marker = "log-it-" + System.nanoTime();
        ILog.of(LogIT.class).warn(marker);
        var file = Platform.getLogFileLocation().toPath();
        System.out.println("log file: " + file);
        String text = Files.readString(file);
        assertTrue(text.contains("!ENTRY org.acme.todos.tests 2"));
        assertTrue(text.contains(marker));
    }
}
