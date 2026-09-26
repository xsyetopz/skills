package org.acme.todos;

import java.util.ArrayList;
import java.util.List;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IResourceChangeEvent;
import org.eclipse.core.resources.IResourceChangeListener;
import org.eclipse.core.resources.IResourceDelta;
import org.eclipse.core.runtime.CoreException;

/**
 * POST_CHANGE listener. The tree is locked while it runs, so it only
 * collects the changed *.txt files and schedules a job to update them.
 */
final class TodoRescanListener implements IResourceChangeListener {
    @Override
    public void resourceChanged(IResourceChangeEvent event) {
        IResourceDelta delta = event.getDelta();
        if (delta == null) {
            return;
        }
        List<IFile> changed = new ArrayList<>();
        try {
            delta.accept(child -> {
                IResource resource = child.getResource();
                if (resource.getType() != IResource.FILE) {
                    return true;
                }
                boolean added = child.getKind() == IResourceDelta.ADDED;
                boolean edited = child.getKind() == IResourceDelta.CHANGED
                        && (child.getFlags() & IResourceDelta.CONTENT) != 0;
                if ((added || edited)
                        && "txt".equals(resource.getFileExtension())) {
                    changed.add((IFile) resource);
                }
                return false;
            });
        } catch (CoreException e) {
            TodoLog.LOG.log(e.getStatus());
            return;
        }
        if (!changed.isEmpty()) {
            ScanTodosJob job =
                    new ScanTodosJob(changed, TodoPreferences.tag());
            job.setSystem(true); // not user-initiated: no progress UI
            job.schedule();
        }
    }
}
