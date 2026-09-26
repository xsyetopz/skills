package org.acme.todos.tests;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.util.List;

import org.acme.todos.ScanTodosJob;
import org.acme.todos.TodoMarkers;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IMarker;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.jobs.IJobChangeEvent;
import org.eclipse.core.runtime.jobs.Job;
import org.eclipse.core.runtime.jobs.JobChangeAdapter;
import org.junit.Test;

public class ScanTodosJobIT {
    @Test
    public void createsTaskSubtypeMarkersWithLineAndRange()
            throws Exception {
        IProject project = Fixtures.project("scan-job");
        IFile file = Fixtures.file(project, "a.txt",
                "one\n// TODO: first\nTODO:second\nno todo here\n");
        Fixtures.file(project, "b.md", "TODO: ignored, not *.txt\n");

        Job job = new ScanTodosJob(List.of(project), "TODO");
        assertEquals(project, job.getRule());
        job.schedule();
        job.join();

        assertTrue(job.getResult().isOK());
        IMarker[] markers = file.findMarkers(TodoMarkers.TYPE, false,
                IResource.DEPTH_ZERO);
        assertEquals(2, markers.length);
        IMarker first = markers[0].getAttribute(IMarker.LINE_NUMBER, 0)
                == 2 ? markers[0] : markers[1];
        assertEquals("TODO: first", first.getAttribute(IMarker.MESSAGE));
        assertEquals(7, first.getAttribute(IMarker.CHAR_START, -1));
        assertEquals(11, first.getAttribute(IMarker.CHAR_END, -1));
        assertEquals("org.acme.todos.todo", first.getType());
        assertTrue(first.isSubtypeOf(IMarker.TASK));
        // Querying the super type with includeSubtypes finds them.
        assertEquals(2, project.findMarkers(IMarker.TASK, true,
                IResource.DEPTH_INFINITE).length);
        assertEquals(0, project.findMarkers(IMarker.TASK, false,
                IResource.DEPTH_INFINITE).length);
    }

    @Test
    public void rescanReplacesInsteadOfDuplicating() throws Exception {
        IProject project = Fixtures.project("scan-twice");
        Fixtures.file(project, "a.txt", "TODO: once\n");
        for (int i = 0; i < 2; i++) {
            Job job = new ScanTodosJob(List.of(project), "TODO");
            job.schedule();
            job.join();
        }
        assertEquals(1, TodoMarkers.count(project));
    }

    @Test
    public void familyJoinWaitsForEveryScan() throws Exception {
        IProject a = Fixtures.project("family-a");
        IProject b = Fixtures.project("family-b");
        Fixtures.file(a, "a.txt", "TODO: a\n");
        Fixtures.file(b, "b.txt", "TODO: b\n");
        new ScanTodosJob(List.of(a), "TODO").schedule();
        new ScanTodosJob(List.of(b), "TODO").schedule();
        Job.getJobManager().join(ScanTodosJob.FAMILY, null);
        assertEquals(0, Job.getJobManager().find(ScanTodosJob.FAMILY)
                .length);
        assertEquals(1, TodoMarkers.count(a));
        assertEquals(1, TodoMarkers.count(b));
    }

    @Test
    public void cancelDuringScanLeavesMarkersUntouched() throws Exception {
        IProject project = Fixtures.project("scan-cancel");
        for (int i = 0; i < 200; i++) {
            Fixtures.file(project, "f" + i + ".txt", "TODO: old\n");
        }
        Job.getJobManager().join(ScanTodosJob.FAMILY, null);
        assertEquals(200, TodoMarkers.count(project));
        // A finished NOTE scan would replace all 200 TODO markers with
        // none, because the files contain no "NOTE:".
        Job job = new ScanTodosJob(List.of(project), "NOTE");
        job.addJobChangeListener(new JobChangeAdapter() {
            @Override
            public void running(IJobChangeEvent event) {
                event.getJob().cancel();
            }
        });
        job.schedule();
        job.join();
        System.out.println("cancelled scan: result=" + job.getResult()
                + " markers=" + TodoMarkers.count(project));
        assertEquals(IStatus.CANCEL, job.getResult().getSeverity());
        assertEquals(200, TodoMarkers.count(project));
    }
}
