package org.acme.todos;

import org.eclipse.core.resources.IResourceChangeEvent;
import org.eclipse.core.resources.IWorkspace;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.jobs.Job;
import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;

/**
 * Started lazily (Bundle-ActivationPolicy: lazy) when a class of this
 * bundle is first loaded. Owns the rescan listener and all jobs.
 */
public final class Activator implements BundleActivator {
    public static final String PLUGIN_ID = "org.acme.todos";

    private TodoRescanListener listener;

    @Override
    public void start(BundleContext context) {
        listener = new TodoRescanListener();
        IWorkspace workspace = ResourcesPlugin.getWorkspace();
        workspace.addResourceChangeListener(listener,
                IResourceChangeEvent.POST_CHANGE);
    }

    @Override
    public void stop(BundleContext context) throws InterruptedException {
        ResourcesPlugin.getWorkspace()
                .removeResourceChangeListener(listener);
        listener = null;
        Job.getJobManager().cancel(ScanTodosJob.FAMILY);
        Job.getJobManager().join(ScanTodosJob.FAMILY, null);
    }
}
