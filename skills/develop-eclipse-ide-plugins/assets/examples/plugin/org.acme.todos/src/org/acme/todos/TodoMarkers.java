package org.acme.todos;

import java.util.List;
import java.util.Map;

import org.acme.todos.TodoScanner.Todo;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IMarker;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.runtime.CoreException;

/** Creates and removes markers of the type declared in plugin.xml. */
public final class TodoMarkers {
    /** Bundle-SymbolicName + "." + the markers extension id. */
    public static final String TYPE = Activator.PLUGIN_ID + ".todo";

    private TodoMarkers() {
    }

    /** Replaces this file's TODO markers. Call inside a batch. */
    public static void replace(IFile file, String tag, List<Todo> todos)
            throws CoreException {
        file.deleteMarkers(TYPE, false, IResource.DEPTH_ZERO);
        for (Todo todo : todos) {
            file.createMarker(TYPE, Map.of(
                    IMarker.MESSAGE, tag + ": " + todo.message(),
                    IMarker.LINE_NUMBER, todo.line(),
                    IMarker.CHAR_START, todo.charStart(),
                    IMarker.CHAR_END, todo.charEnd(),
                    IMarker.PRIORITY, IMarker.PRIORITY_NORMAL,
                    "tag", tag));
        }
    }

    public static int count(IResource root) throws CoreException {
        return root.findMarkers(TYPE, true, IResource.DEPTH_INFINITE)
                .length;
    }
}
