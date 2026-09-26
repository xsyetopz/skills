package org.acme.todos;

import java.util.List;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.runtime.Adapters;
import org.eclipse.core.runtime.jobs.Job;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.ui.handlers.HandlerUtil;

/** Runs on the UI thread: read the selection, schedule, return. */
public final class ScanTodosHandler extends AbstractHandler {
    @Override
    public Object execute(ExecutionEvent event)
            throws ExecutionException {
        IStructuredSelection selection =
                HandlerUtil.getCurrentStructuredSelection(event);
        IProject project =
                Adapters.adapt(selection.getFirstElement(), IProject.class);
        if (project == null || !project.isOpen()) {
            throw new ExecutionException("Select one open project");
        }
        Job job = new ScanTodosJob(List.of(project), TodoPreferences.tag());
        job.setUser(true); // user-initiated: progress dialog/view
        job.schedule();
        return null;
    }
}
