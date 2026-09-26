package org.acme.todos.tests;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThrows;

import java.util.List;

import org.acme.todos.ScanTodosJob;
import org.acme.todos.TodoMarkers;
import org.eclipse.core.commands.NotEnabledException;
import org.eclipse.core.commands.ParameterizedCommand;
import org.eclipse.core.expressions.EvaluationContext;
import org.eclipse.core.expressions.IEvaluationContext;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.runtime.jobs.Job;
import org.eclipse.jface.viewers.StructuredSelection;
import org.eclipse.ui.ISources;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.commands.ICommandService;
import org.eclipse.ui.handlers.IHandlerService;
import org.junit.Test;

public class ScanCommandIT {
    private static final String SCAN = "org.acme.todos.scan";

    private static void execute(Object... selected) throws Exception {
        IWorkbenchWindow window =
                PlatformUI.getWorkbench().getActiveWorkbenchWindow();
        IHandlerService handlers = window.getService(IHandlerService.class);
        ICommandService commands = window.getService(ICommandService.class);
        // The default variable of handler expressions is a Collection.
        IEvaluationContext context = new EvaluationContext(
                handlers.createContextSnapshot(false), List.of(selected));
        context.addVariable(ISources.ACTIVE_CURRENT_SELECTION_NAME,
                new StructuredSelection(selected));
        handlers.executeCommandInContext(new ParameterizedCommand(
                commands.getCommand(SCAN), null), null, context);
    }

    @Test
    public void scansTheSelectedProjectInABackgroundJob() throws Exception {
        IProject project = Fixtures.project("command");
        Fixtures.file(project, "a.txt", "TODO: from command\n");
        execute(project);
        Job.getJobManager().join(ScanTodosJob.FAMILY, null);
        assertEquals(1, TodoMarkers.count(project));
    }

    @Test
    public void enabledWhenRejectsTwoProjects() throws Exception {
        IProject a = Fixtures.project("command-a");
        IProject b = Fixtures.project("command-b");
        assertThrows(NotEnabledException.class, () -> execute(a, b));
    }

    @Test
    public void enabledWhenRejectsNonProjects() {
        assertThrows(NotEnabledException.class, () -> execute("text"));
    }
}
