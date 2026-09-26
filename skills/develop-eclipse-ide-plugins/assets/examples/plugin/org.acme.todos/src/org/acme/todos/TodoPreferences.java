package org.acme.todos;

import org.eclipse.core.runtime.Platform;
import org.eclipse.core.runtime.preferences.IEclipsePreferences;
import org.eclipse.core.runtime.preferences.InstanceScope;
import org.osgi.service.prefs.BackingStoreException;

/** The "tag" preference: instance scope over the default scope. */
public final class TodoPreferences {
    public static final String TAG = "tag";
    public static final String DEFAULT_TAG = "TODO";

    private TodoPreferences() {
    }

    /** Looks up instance, then configuration, then default scope. */
    public static String tag() {
        return Platform.getPreferencesService().getString(
                Activator.PLUGIN_ID, TAG, DEFAULT_TAG, null);
    }

    /** Stores the value for this workspace and writes it to disk. */
    public static void setTag(String value) throws BackingStoreException {
        IEclipsePreferences node =
                InstanceScope.INSTANCE.getNode(Activator.PLUGIN_ID);
        node.put(TAG, value);
        node.flush();
    }

    /** Removes the workspace value so the default applies again. */
    public static void resetTag() throws BackingStoreException {
        IEclipsePreferences node =
                InstanceScope.INSTANCE.getNode(Activator.PLUGIN_ID);
        node.remove(TAG);
        node.flush();
    }
}
