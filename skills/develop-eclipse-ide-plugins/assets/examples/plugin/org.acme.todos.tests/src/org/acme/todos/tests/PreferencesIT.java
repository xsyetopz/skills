package org.acme.todos.tests;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;

import org.acme.todos.TodoPreferences;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.ProjectScope;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.Platform;
import org.eclipse.core.runtime.preferences.DefaultScope;
import org.eclipse.core.runtime.preferences.IEclipsePreferences;
import org.eclipse.core.runtime.preferences.IScopeContext;
import org.eclipse.core.runtime.preferences.InstanceScope;
import org.junit.After;
import org.junit.Test;

public class PreferencesIT {
    @After
    public void reset() throws Exception {
        TodoPreferences.resetTag();
    }

    @Test
    public void defaultComesFromTheInitializer() {
        assertEquals("TODO", TodoPreferences.tag());
        assertEquals("TODO", DefaultScope.INSTANCE
                .getNode("org.acme.todos").get("tag", null));
    }

    @Test
    public void instanceValueOverridesDefaultAndIsFlushed()
            throws Exception {
        TodoPreferences.setTag("FIXME");
        assertEquals("FIXME", TodoPreferences.tag());
        Path prefs = ResourcesPlugin.getWorkspace().getRoot()
                .getLocation().toPath().resolve(".metadata/.plugins/"
                        + "org.eclipse.core.runtime/.settings/"
                        + "org.acme.todos.prefs");
        System.out.println("flushed to " + prefs);
        assertTrue(Files.readString(prefs).contains("tag=FIXME"));
        TodoPreferences.resetTag();
        assertEquals("TODO", TodoPreferences.tag());
    }

    @Test
    public void projectScopeIsStoredInTheProjectAndSearchedFirst()
            throws Exception {
        IProject project = Fixtures.project("prefs");
        IEclipsePreferences node =
                new ProjectScope(project).getNode("org.acme.todos");
        node.put("tag", "HACK");
        node.flush();
        assertTrue(project.getFile(".settings/org.acme.todos.prefs")
                .exists());
        IScopeContext[] order = {new ProjectScope(project),
            InstanceScope.INSTANCE};
        assertEquals("HACK", Platform.getPreferencesService()
                .getString("org.acme.todos", "tag", "TODO", order));
        // Without the project context the lookup ignores it.
        assertEquals("TODO", TodoPreferences.tag());
    }
}
