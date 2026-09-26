package org.acme.todos;

import org.eclipse.core.runtime.preferences.AbstractPreferenceInitializer;
import org.eclipse.core.runtime.preferences.DefaultScope;

/** Registered in plugin.xml; runs on first access to the node. */
public final class TodoPreferenceInitializer
        extends AbstractPreferenceInitializer {
    @Override
    public void initializeDefaultPreferences() {
        DefaultScope.INSTANCE.getNode(Activator.PLUGIN_ID)
                .put(TodoPreferences.TAG, TodoPreferences.DEFAULT_TAG);
    }
}
