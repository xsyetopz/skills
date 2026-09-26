package org.acme.todos.tests;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import java.util.List;

import org.acme.todos.ScanTodosJob;
import org.acme.todos.TodoMarkers;
import org.acme.todos.TodoView;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.jobs.Job;
import org.eclipse.jface.resource.FontDescriptor;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.jface.resource.LocalResourceManager;
import org.eclipse.jface.resource.ResourceManager;
import org.eclipse.swt.SWT;
import org.eclipse.swt.SWTException;
import org.eclipse.swt.graphics.Color;
import org.eclipse.swt.graphics.Font;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.PlatformUI;
import org.junit.Test;

public class TodoViewIT {
    @Test
    public void injectedViewShowsCountAfterBackgroundScan()
            throws Exception {
        ResourcesPlugin.getWorkspace().getRoot().deleteMarkers(
                TodoMarkers.TYPE, true, IResource.DEPTH_INFINITE);
        IWorkbenchPage page = PlatformUI.getWorkbench()
                .getActiveWorkbenchWindow().getActivePage();
        TodoView view = (TodoView) page.showView(TodoView.ID);
        try {
            assertTrue("@Inject field set", view.injected());
            assertEquals("0 TODO marker(s)", view.text());
            IProject project = Fixtures.project("view");
            Fixtures.file(project, "a.txt", "TODO: a\nTODO: b\n");
            new ScanTodosJob(List.of(project), "TODO").schedule();
            Job.getJobManager().join(ScanTodosJob.FAMILY, null);
            assertTrue(Fixtures.pumpUntil(
                    () -> view.text().equals("2 TODO marker(s)"), 10));
        } finally {
            page.hideView(view);
        }
    }

    @Test
    public void disposedWidgetRejectsLateUpdates() {
        Shell shell = new Shell();
        Label label = new Label(shell, SWT.NONE);
        shell.dispose();
        SWTException error =
                assertThrows(SWTException.class, () -> label.setText("x"));
        System.out.println("late update: " + error.getMessage());
        assertTrue(label.isDisposed());
    }

    @Test
    public void widgetAccessOffTheUiThreadFails() throws Exception {
        Shell shell = new Shell();
        try {
            Throwable[] seen = new Throwable[1];
            Thread worker = new Thread(() -> {
                try {
                    shell.setText("from worker");
                } catch (SWTException e) {
                    seen[0] = e;
                }
            });
            worker.start();
            worker.join();
            System.out.println("worker access: " + seen[0].getMessage());
            assertTrue(seen[0].getMessage().contains("Invalid thread"));
        } finally {
            shell.dispose();
        }
    }

    @Test
    public void localResourceManagerDisposesWithItsOwner() {
        Shell shell = new Shell();
        ResourceManager resources = new LocalResourceManager(
                JFaceResources.getResources(), shell);
        Font font = resources.create(
                FontDescriptor.createFrom("Monospace", 11, SWT.BOLD));
        assertTrue(!font.isDisposed());
        shell.dispose();
        System.out.println("font disposed with owner: "
                + font.isDisposed());
        assertTrue(font.isDisposed());
    }

    @Test
    public void colorNeedsNoDisplayAndNoDisposal() {
        Color color = new Color(10, 20, 30);
        assertEquals(20, color.getGreen());
        color.dispose(); // allowed for old code; not required
    }
}
