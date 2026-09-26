package org.acme.todos.tests;

import static org.junit.Assert.assertEquals;

import org.acme.todos.ScanTodosJob;
import org.acme.todos.TodoMarkers;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.runtime.jobs.Job;
import org.junit.Test;

public class RescanListenerIT {
    @Test
    public void editingATextFileRescansItInTheBackground()
            throws Exception {
        IProject project = Fixtures.project("listener");
        // Loading a class of the bundle starts it (lazy activation),
        // which registers the POST_CHANGE listener.
        assertEquals(0, TodoMarkers.count(project));
        Fixtures.file(project, "a.txt", "TODO: one\n");
        Job.getJobManager().join(ScanTodosJob.FAMILY, null);
        assertEquals(1, TodoMarkers.count(project));
        Fixtures.file(project, "a.txt", "TODO: one\nTODO: two\n");
        Job.getJobManager().join(ScanTodosJob.FAMILY, null);
        assertEquals(2, TodoMarkers.count(project));
    }
}
