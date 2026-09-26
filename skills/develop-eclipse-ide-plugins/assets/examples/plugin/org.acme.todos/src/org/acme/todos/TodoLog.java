package org.acme.todos;

import org.eclipse.core.runtime.ILog;

/** The bundle's log: written to <workspace>/.metadata/.log. */
final class TodoLog {
    static final ILog LOG = ILog.of(TodoLog.class);

    private TodoLog() {
    }
}
