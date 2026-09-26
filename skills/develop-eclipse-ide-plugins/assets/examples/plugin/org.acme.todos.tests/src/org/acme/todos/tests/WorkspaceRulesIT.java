package org.acme.todos.tests;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

import org.acme.todos.ScanTodosJob;
import org.acme.todos.TodoMarkers;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IMarkerDelta;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResourceChangeEvent;
import org.eclipse.core.resources.IResourceChangeListener;
import org.eclipse.core.resources.IResourceDelta;
import org.eclipse.core.resources.IWorkspace;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.resources.WorkspaceJob;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.ICoreRunnable;
import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;
import org.eclipse.core.runtime.SubMonitor;
import org.eclipse.core.runtime.jobs.ISchedulingRule;
import org.eclipse.core.runtime.jobs.Job;
import org.junit.Test;

public class WorkspaceRulesIT {
    private static final int MARKERS = 20;
    private final IWorkspace workspace = ResourcesPlugin.getWorkspace();

    /** Added TODO markers per POST_CHANGE event while work runs. */
    private List<Integer> addedPerEvent(ICoreRunnable work)
            throws CoreException {
        List<Integer> perEvent = new CopyOnWriteArrayList<>();
        IResourceChangeListener counter = e -> {
            int added = 0;
            for (IMarkerDelta d
                    : e.findMarkerDeltas(TodoMarkers.TYPE, false)) {
                if (d.getKind() == IResourceDelta.ADDED) {
                    added++;
                }
            }
            if (added > 0) {
                perEvent.add(added);
            }
        };
        workspace.addResourceChangeListener(counter,
                IResourceChangeEvent.POST_CHANGE);
        try {
            work.run(null);
        } finally {
            workspace.removeResourceChangeListener(counter);
        }
        return perEvent;
    }

    @Test
    public void avoidUpdateBatchesMarkerEvents() throws Exception {
        IProject project = Fixtures.project("batch");
        IFile file = Fixtures.file(project, "a.txt", "x\n");
        // The file creation triggers the bundle's rescan job; let it
        // finish so that its workspace operation does not interleave.
        Job.getJobManager().join(ScanTodosJob.FAMILY, null);
        List<Integer> unbatched = addedPerEvent(m -> {
            for (int i = 0; i < MARKERS; i++) {
                file.createMarker(TodoMarkers.TYPE);
            }
        });
        List<Integer> batched = addedPerEvent(m -> workspace.run(monitor -> {
            for (int i = 0; i < MARKERS; i++) {
                file.createMarker(TodoMarkers.TYPE);
            }
        }, project, IWorkspace.AVOID_UPDATE, null));
        System.out.println("added markers per POST_CHANGE event:"
                + " unbatched=" + unbatched + " batched=" + batched);
        assertTrue(unbatched.size() > 1);
        assertTrue(batched.contains(MARKERS));
    }

    @Test
    public void workspaceJobIsOneBatchedOperation() throws Exception {
        IProject project = Fixtures.project("workspace-job");
        IFile file = Fixtures.file(project, "a.txt", "x\n");
        Job.getJobManager().join(ScanTodosJob.FAMILY, null);
        List<Integer> perEvent = addedPerEvent(m -> {
            WorkspaceJob job = new WorkspaceJob("add markers") {
                @Override
                public IStatus runInWorkspace(IProgressMonitor monitor)
                        throws CoreException {
                    for (int i = 0; i < MARKERS; i++) {
                        file.createMarker(TodoMarkers.TYPE);
                    }
                    return Status.OK_STATUS;
                }
            };
            job.setRule(project);
            job.schedule();
            try {
                job.join();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
        System.out.println("WorkspaceJob markers per event: " + perEvent);
        assertTrue(perEvent.contains(MARKERS));
    }

    @Test
    public void ruleLimitsWhatTheRunnableMayTouch() throws Exception {
        IProject inside = Fixtures.project("rule-inside");
        IProject outside = Fixtures.project("rule-outside");
        IllegalArgumentException error = assertThrows(
                IllegalArgumentException.class,
                () -> workspace.run(monitor -> Fixtures.file(outside,
                        "a.txt", "x"), inside, IWorkspace.AVOID_UPDATE,
                        null));
        System.out.println("rule violation: " + error.getMessage());
        assertTrue(error.getMessage().contains("does not match outer"));
    }

    @Test
    public void conflictingRulesNeverOverlap() throws Exception {
        IProject project = Fixtures.project("mutex");
        assertEquals(1, maxOverlap(project, project));
        assertEquals(2, maxOverlap(null, null));
    }

    private static int maxOverlap(ISchedulingRule a, ISchedulingRule b)
            throws InterruptedException {
        AtomicInteger running = new AtomicInteger();
        AtomicInteger max = new AtomicInteger();
        Job[] jobs = new Job[2];
        ISchedulingRule[] rules = {a, b};
        for (int i = 0; i < 2; i++) {
            jobs[i] = Job.create("overlap " + i, monitor -> {
                max.accumulateAndGet(running.incrementAndGet(), Math::max);
                sleep(300);
                running.decrementAndGet();
                return Status.OK_STATUS;
            });
            jobs[i].setRule(rules[i]);
        }
        jobs[0].schedule();
        jobs[1].schedule();
        jobs[0].join();
        jobs[1].join();
        return max.get();
    }

    @Test
    public void splitCancellationBecomesCancelStatus() throws Exception {
        AtomicInteger done = new AtomicInteger();
        Job job = Job.create("cancellable", monitor -> {
            SubMonitor progress = SubMonitor.convert(monitor, 1000);
            for (int i = 0; i < 1000; i++) {
                progress.split(1); // throws OperationCanceledException
                sleep(5);
                done.incrementAndGet();
            }
            return Status.OK_STATUS;
        });
        job.schedule();
        Thread.sleep(200);
        job.cancel();
        job.join();
        System.out.println("iterations before cancel: " + done.get());
        assertEquals(IStatus.CANCEL, job.getResult().getSeverity());
        assertTrue(done.get() < 1000);
    }

    @Test
    public void postChangeListenerCannotModifyTheTree() throws Exception {
        IProject project = Fixtures.project("locked");
        AtomicReference<CoreException> failure = new AtomicReference<>();
        IResourceChangeListener writer = event -> {
            try {
                project.createMarker(TodoMarkers.TYPE);
            } catch (CoreException e) {
                failure.compareAndSet(null, e);
            }
        };
        workspace.addResourceChangeListener(writer,
                IResourceChangeEvent.POST_CHANGE);
        try {
            Fixtures.file(project, "a.txt", "x");
        } finally {
            workspace.removeResourceChangeListener(writer);
        }
        assertNotNull(failure.get());
        System.out.println("listener write: "
                + failure.get().getMessage());
        assertTrue(failure.get().getMessage().contains("locked"));
    }

    private static void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
