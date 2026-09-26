package org.acme.todos;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.acme.todos.TodoScanner.Todo;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IWorkspace;
import org.eclipse.core.resources.IWorkspaceRunnable;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.MultiStatus;
import org.eclipse.core.runtime.Status;
import org.eclipse.core.runtime.SubMonitor;
import org.eclipse.core.runtime.jobs.ISchedulingRule;
import org.eclipse.core.runtime.jobs.Job;
import org.eclipse.core.runtime.jobs.MultiRule;

/** Scans *.txt files under the roots and replaces their markers. */
public final class ScanTodosJob extends Job {
    /** Family object for cancel/join; unique to this bundle. */
    public static final Object FAMILY = ScanTodosJob.class;

    private final List<IResource> roots;
    private final String tag;

    public ScanTodosJob(List<? extends IResource> roots, String tag) {
        super("Scan " + tag + " markers");
        this.roots = List.copyOf(roots);
        this.tag = tag;
        setRule(ruleFor(this.roots));
    }

    /** One rule per project: the job may only touch those projects. */
    static ISchedulingRule ruleFor(List<IResource> roots) {
        Set<ISchedulingRule> projects = new LinkedHashSet<>();
        for (IResource root : roots) {
            projects.add(root.getProject() != null
                    ? root.getProject() : root);
        }
        return MultiRule.combine(
                projects.toArray(ISchedulingRule[]::new));
    }

    @Override
    public boolean belongsTo(Object family) {
        return family == FAMILY;
    }

    @Override
    protected IStatus run(IProgressMonitor monitor) {
        SubMonitor progress = SubMonitor.convert(monitor, 100);
        List<IFile> files = new ArrayList<>();
        try {
            for (IResource root : roots) {
                root.accept(proxy -> {
                    if (proxy.getType() == IResource.FILE
                            && proxy.getName().endsWith(".txt")) {
                        files.add((IFile) proxy.requestResource());
                    }
                    return true;
                }, IResource.NONE);
            }
            progress.split(10);
            // Read and scan before the workspace operation opens: a
            // cancel here leaves every marker untouched.
            MultiStatus problems = new MultiStatus(Activator.PLUGIN_ID,
                    0, "Some files could not be scanned");
            Map<IFile, List<Todo>> found = new LinkedHashMap<>();
            SubMonitor scanning = progress.split(60)
                    .setWorkRemaining(files.size());
            for (IFile file : files) {
                scanning.split(1); // throws OperationCanceledException
                try {
                    found.put(file,
                            TodoScanner.scan(file.readString(), tag));
                } catch (CoreException e) {
                    problems.add(e.getStatus());
                }
            }
            // Only the marker writes run inside the batched operation.
            IWorkspaceRunnable replaceAll = inner -> {
                for (Map.Entry<IFile, List<Todo>> entry : found.entrySet()) {
                    TodoMarkers.replace(entry.getKey(), tag,
                            entry.getValue());
                }
            };
            IWorkspace workspace = ResourcesPlugin.getWorkspace();
            workspace.run(replaceAll, getRule(), IWorkspace.AVOID_UPDATE,
                    progress.split(30));
            if (!problems.isOK()) {
                TodoLog.LOG.log(problems);
            }
            return problems.isOK() ? Status.OK_STATUS : problems;
        } catch (CoreException e) {
            return e.getStatus();
        }
    }
}
