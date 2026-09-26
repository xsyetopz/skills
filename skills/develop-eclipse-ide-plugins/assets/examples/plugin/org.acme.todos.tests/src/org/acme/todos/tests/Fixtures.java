package org.acme.todos.tests;

import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;
import java.util.function.BooleanSupplier;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.swt.widgets.Display;

/** Workspace fixtures shared by the tests. */
final class Fixtures {
    private Fixtures() {
    }

    static IProject project(String name) throws CoreException {
        IProject project =
                ResourcesPlugin.getWorkspace().getRoot().getProject(name);
        if (project.exists()) {
            project.delete(true, true, null);
        }
        project.create(null);
        project.open(null);
        return project;
    }

    static IFile file(IProject project, String name, String text)
            throws CoreException {
        IFile file = project.getFile(name);
        byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
        if (file.exists()) {
            file.setContents(bytes, IResource.FORCE, null);
        } else {
            file.create(bytes, IResource.FORCE, null);
        }
        return file;
    }

    /** Runs the UI event loop until the condition holds or time ends. */
    static boolean pumpUntil(BooleanSupplier done, long seconds) {
        Display display = Display.getCurrent();
        long end = System.nanoTime() + TimeUnit.SECONDS.toNanos(seconds);
        while (!done.getAsBoolean() && System.nanoTime() < end) {
            if (!display.readAndDispatch()) {
                display.timerExec(20, () -> { });
                display.sleep();
            }
        }
        return done.getAsBoolean();
    }
}
