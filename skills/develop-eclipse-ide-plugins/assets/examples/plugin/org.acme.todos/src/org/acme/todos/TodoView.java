package org.acme.todos;

import jakarta.inject.Inject;

import org.eclipse.core.resources.IResourceChangeEvent;
import org.eclipse.core.resources.IResourceChangeListener;
import org.eclipse.core.resources.IWorkspace;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.e4.ui.di.UISynchronize;
import org.eclipse.swt.SWT;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Label;
import org.eclipse.ui.part.ViewPart;

/**
 * 3.x view created with Eclipse DI (inject="true" in plugin.xml):
 * fields annotated with @Inject are set before createPartControl.
 */
public final class TodoView extends ViewPart {
    public static final String ID = "org.acme.todos.view";

    @Inject
    private UISynchronize sync;

    private Label label;
    private final IResourceChangeListener markerListener =
            this::markersChanged;

    @Override
    public void createPartControl(Composite parent) {
        label = new Label(parent, SWT.NONE);
        refresh();
        ResourcesPlugin.getWorkspace().addResourceChangeListener(
                markerListener, IResourceChangeEvent.POST_CHANGE);
    }

    /** Runs on the thread that changed the workspace, not the UI. */
    private void markersChanged(IResourceChangeEvent event) {
        if (event.findMarkerDeltas(TodoMarkers.TYPE, true).length == 0) {
            return;
        }
        sync.asyncExec(() -> {
            if (!label.isDisposed()) {
                refresh();
            }
        });
    }

    private void refresh() {
        IWorkspace workspace = ResourcesPlugin.getWorkspace();
        try {
            label.setText(TodoMarkers.count(workspace.getRoot())
                    + " TODO marker(s)");
        } catch (CoreException e) {
            TodoLog.LOG.log(e.getStatus());
        }
        label.getParent().layout();
    }

    public String text() {
        return label.getText();
    }

    public boolean injected() {
        return sync != null;
    }

    @Override
    public void setFocus() {
        label.setFocus();
    }

    @Override
    public void dispose() {
        ResourcesPlugin.getWorkspace()
                .removeResourceChangeListener(markerListener);
        super.dispose();
    }
}
