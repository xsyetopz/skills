# Workspace operations, markers, preferences, and logging

The resources API, marker types, preference scopes, and the plug-in log.
Runnable sources:
`assets/examples/plugin/org.acme.todos/src/org/acme/todos/`; tests
`WorkspaceRulesIT`, `ScanTodosJobIT`, `RescanListenerIT`,
`PreferencesIT`, and `LogIT`. Executed results come from
`sh assets/examples/verify.sh network` (Tycho 5.0.4 UI harness, Eclipse
4.41, macOS 27 arm64, JDK 25.0.4.1; machine-specific).

## Contents

- [IWorkspaceRunnable with AVOID_UPDATE][toc-run]
- [WorkspaceJob](#workspacejob)
- [POST_CHANGE resource change listener][toc-listener]
- [Custom marker type](#custom-marker-type)
- [Creating and replacing markers](#creating-and-replacing-markers)
- [Querying markers with subtypes](#querying-markers-with-subtypes)
- [Default preferences through an initializer][toc-default]
- [Instance scope write and flush](#instance-scope-write-and-flush)
- [Preference lookup through IPreferencesService][toc-lookup]
- [Project scope preferences](#project-scope-preferences)
- [Plug-in log with ILog](#plug-in-log-with-ilog)

## IWorkspaceRunnable with AVOID_UPDATE

**Definition.** `IWorkspace.run(runnable, rule, IWorkspace.AVOID_UPDATE,
monitor)` runs resource changes as one operation under `rule`.
`AVOID_UPDATE` suppresses intermediate resource change events and
broadcasts one at the end. Nested runnables join the outer batch
([batching guide][batch]).

**Use when.**

- One logical change touches many resources or markers (replace every
  marker of a file, create a set of files).

**Do not use when.**

- The call is the short form `run(runnable, monitor)`: it takes the
  workspace root as the rule and locks the whole workspace ([batching
  guide][batch]).
- A long computation runs inside the runnable, holding the rule: compute
  first, then open the operation for the writes only.

**Example.** From `ScanTodosJob.run`: read and scan first, then open
the operation for the marker writes.

```java
Map<IFile, List<Todo>> found = new LinkedHashMap<>();
SubMonitor scanning = progress.split(60)
        .setWorkRemaining(files.size());
for (IFile file : files) {
    scanning.split(1); // throws OperationCanceledException
    found.put(file, TodoScanner.scan(file.readString(), tag));
}
IWorkspaceRunnable replaceAll = inner -> {
    for (Map.Entry<IFile, List<Todo>> e : found.entrySet()) {
        TodoMarkers.replace(e.getKey(), tag, e.getValue());
    }
};
workspace.run(replaceAll, getRule(), IWorkspace.AVOID_UPDATE,
        progress.split(30));
```

The runnable's rule equals the job's rule, which "contains" it. The
runnable source file also collects per-file read errors into a
`MultiStatus`.

**Cost removed.** Listener and builder work per change, and
half-updated markers after a cancel. Executed
(`ScanTodosJobIT.cancelDuringScanLeavesMarkersUntouched`): a scan
cancelled as it started returned `IStatus.CANCEL` and left all 200
existing markers in place. Executed
(`WorkspaceRulesIT.avoidUpdateBatchesMarkerEvents`, three runs): 20
`createMarker` calls outside an operation produced 20 `POST_CHANGE`
events with one added marker each; inside `workspace.run(...,
AVOID_UPDATE, ...)` they produced one event with 20. An earlier count
of all events, not only marker events, varied between runs (19, 5),
likely because a concurrent workspace operation's notification merged
with ours. The per-event marker count stayed stable, so count only the
deltas you care about.

**Verify.**

1. `WorkspaceRulesIT.avoidUpdateBatchesMarkerEvents` passes and prints
   `batched=[20]` (Executed).

## WorkspaceJob

**Definition.** `WorkspaceJob` is a `Job` whose
`runInWorkspace(monitor)` runs as one workspace operation: change
notifications arrive at the end of the batch, and the workspace is not
locked against other threads meanwhile ([WorkspaceJob][wsjob]). Cancel
by throwing `OperationCanceledException`.

**Use when.**

- The job is all workspace writes, with no long computation.

**Do not use when.**

- Most of the time goes to computation (parsing, network): use a `Job`
  and open `IWorkspace.run` only for the writes, as `ScanTodosJob` does,
  so the operation stays short.

**Example.** From `WorkspaceRulesIT.workspaceJobIsOneBatchedOperation`:

```java
WorkspaceJob job = new WorkspaceJob("add markers") {
    @Override
    public IStatus runInWorkspace(IProgressMonitor monitor)
            throws CoreException {
        for (int i = 0; i < MARKERS; i++) {
            file.createMarker(TodoMarkers.TYPE);
        }
        return Status.OK_STATUS;
    }
};
job.setRule(project);
job.schedule();
```

**Cost removed.** Per-change events, as in the previous card. Executed:
one `POST_CHANGE` event carried all 20 markers.

**Verify.**

1. `WorkspaceRulesIT.workspaceJobIsOneBatchedOperation` (Executed).

## POST_CHANGE resource change listener

**Definition.** `IWorkspace.addResourceChangeListener(listener,
IResourceChangeEvent.POST_CHANGE)` delivers a resource delta tree after
each batch of changes. During `POST_CHANGE` "the workspace is locked
(no resources can be updated)" ([events guide][events]). Visit the
delta with `IResourceDeltaVisitor`; `getKind()` and `getFlags()` (such
as `IResourceDelta.CONTENT`) say what changed.

**Use when.**

- The plug-in must react to edits it did not make: rescan a changed
  file, refresh a view.

**Do not use when.**

- The listener would modify resources or markers: that fails. Schedule
  a job instead.
- The listener would do slow work: it runs on the thread that made the
  change, which may be the UI thread.

**Example.** Runnable: `TodoRescanListener.java` (excerpt).

```java
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
// then: new ScanTodosJob(changed, tag).schedule()
```

**Cost removed.** Lost writes and exceptions from mutating a locked
tree. Executed: `createMarker` inside a `POST_CHANGE` listener threw
`CoreException: The resource tree is locked for modifications.`
(`WorkspaceRulesIT.postChangeListenerCannotModifyTheTree`); a scheduled
job updated the markers (`RescanListenerIT`: 1, then 2).

**Verify.**

1. `WorkspaceRulesIT.postChangeListenerCannotModifyTheTree` and
   `RescanListenerIT` pass (Executed).
1. Every `addResourceChangeListener` has a matching
   `removeResourceChangeListener` in `stop` or `dispose`
   (`rg -n 'ResourceChangeListener\(' src`).

## Custom marker type

**Definition.** An `org.eclipse.core.resources.markers` extension
declares a marker type whose id is the bundle id plus the extension
`id`. `<super type>` inherits attributes; the platform types are
`org.eclipse.core.resources.problemmarker`, `taskmarker`, and
`bookmark`. `<persistent value="true"/>` keeps markers across restarts;
persistence is the one property a type does not inherit from its super
type ([markers guide][markers]).

**Use when.**

- The plug-in reports findings that users navigate from the Problems or
  Tasks view and that the plug-in must find and delete as its own.

**Do not use when.**

- The type is a platform type (`IMarker.TASK`): deleting "your" markers
  also deletes other plug-ins' tasks.
- The markers hold derived data the plug-in recomputes anyway: skip
  `persistent`, or stale markers survive a restart until the next scan.

**Example.**

```xml
<extension id="todo" name="TODO Marker"
    point="org.eclipse.core.resources.markers">
  <super type="org.eclipse.core.resources.taskmarker"/>
  <persistent value="true"/>
  <attribute name="tag"/>
</extension>
```

```java
public static final String TYPE = Activator.PLUGIN_ID + ".todo";
```

**Cost removed.** Deleting markers that belong to others. Executed
(`ScanTodosJobIT`): `marker.getType()` is `org.acme.todos.todo` and
`isSubtypeOf(IMarker.TASK)` is `true`.

**Verify.**

1. `python3 scripts/check_bundle.py <bundle>` passes (X007 checks super
   types in the bundle's namespace).
1. `ScanTodosJobIT.createsTaskSubtypeMarkersWithLineAndRange`
   (Executed).

## Creating and replacing markers

**Definition.** `IResource.createMarker(type, Map)` creates a marker
with attributes in one call; `deleteMarkers(type, includeSubtypes,
depth)` removes a type in bulk. Attribute values are `String`,
`Integer`, or `Boolean`. The platform deletes markers of deleted
resources, but "plug-ins are responsible for removing their stale
markers" ([markers guide][markers], [IResource][iresource]).

**Use when.**

- You recompute findings for a file: inside one workspace operation,
  delete this type at `DEPTH_ZERO`, then create the new set.

**Do not use when.**

- The calls would run in a loop outside a rule-holding operation: each
  call is its own operation and event (see the `AVOID_UPDATE` card).

**Example.** Runnable: `TodoMarkers.java`.

```java
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
```

**Cost removed.** Duplicate markers after each rescan. Executed
(`ScanTodosJobIT.rescanReplacesInsteadOfDuplicating`): two scans of a
one-TODO file leave 1 marker, and the first marker has `CHAR_START` 7 and
`CHAR_END` 11 for `// TODO: first` on line 2.

**Verify.**

1. `ScanTodosJobIT` passes (Executed: 3 tests).

## Querying markers with subtypes

**Definition.** `findMarkers(type, includeSubtypes, depth)` returns
markers of `type`, plus its subtypes when `includeSubtypes` is `true`,
on the resource and, by depth, its children: `DEPTH_ZERO`, `DEPTH_ONE`,
`DEPTH_INFINITE` ([markers guide][markers]).

**Use when.**

- You count or list findings for a project or the workspace root.

**Do not use when.**

- The query is `IMarker.TASK` with `includeSubtypes=false`: subtype
  instances, including your markers, are not returned.

**Example.**

```java
int mine = root.findMarkers(TodoMarkers.TYPE, true,
        IResource.DEPTH_INFINITE).length;
```

**Cost removed.** Views that show 0 because the query missed subtypes.
Executed (`ScanTodosJobIT`): for two TODO markers,
`findMarkers(IMarker.TASK, true, DEPTH_INFINITE)` returned 2 and
`findMarkers(IMarker.TASK, false, DEPTH_INFINITE)` returned 0.

**Verify.**

1. `ScanTodosJobIT.createsTaskSubtypeMarkersWithLineAndRange`
   (Executed).

## Default preferences through an initializer

**Definition.** An `<initializer class>` in the
`org.eclipse.core.runtime.preferences` extension point names an
`AbstractPreferenceInitializer`. Its
`initializeDefaultPreferences()` fills `DefaultScope` for the
qualifier on first access to the node. Default values "are not
changed or stored by the platform" ([runtime preferences][prefs]).

**Use when.**

- Every preference: the default lives in one place and "Restore
  Defaults" works.

**Do not use when.**

- Defaults go into `InstanceScope`: they become user values, and a later
  default change never reaches existing workspaces.

**Example.** Runnable: `TodoPreferenceInitializer.java`.

```java
public final class TodoPreferenceInitializer
        extends AbstractPreferenceInitializer {
    @Override
    public void initializeDefaultPreferences() {
        DefaultScope.INSTANCE.getNode(Activator.PLUGIN_ID)
                .put(TodoPreferences.TAG, TodoPreferences.DEFAULT_TAG);
    }
}
```

**Cost removed.** Defaults duplicated as literals at every read site.
Executed (`PreferencesIT.defaultComesFromTheInitializer`): after the
first lookup, `DefaultScope` holds `tag=TODO`.

**Verify.**

1. `PreferencesIT` passes (Executed).

## Instance scope write and flush

**Definition.** `InstanceScope.INSTANCE.getNode(qualifier)` is the
per-workspace node (the constructor is deprecated in favor of
`INSTANCE`). `put` changes memory; `flush()` writes
`<qualifier>.prefs` in the workspace's
`.metadata/.plugins/org.eclipse.core.runtime/.settings/` folder
([InstanceScope][instancescope], [runtime preferences][prefs]).

**Use when.**

- The user changes a setting for this workspace.

**Do not use when.**

- The value belongs to a project and must be shared through version
  control: use `ProjectScope`.
- The value is a secret: preference files are plain text. Use Equinox
  secure storage ([SecurePreferencesFactory][secure]).

**Example.** Runnable: `TodoPreferences.java`.

```java
IEclipsePreferences node =
        InstanceScope.INSTANCE.getNode(Activator.PLUGIN_ID);
node.put(TAG, value);
node.flush(); // throws BackingStoreException
```

**Cost removed.** Settings lost to a crash before shutdown. Executed:
after `flush()`, `org.acme.todos.prefs` in the test workspace contained
`tag=FIXME`.

**Verify.**

1. `PreferencesIT.instanceValueOverridesDefaultAndIsFlushed` reads the
   file (Executed).

## Preference lookup through IPreferencesService

**Definition.** `Platform.getPreferencesService().getString(qualifier,
key, default, contexts)` searches instance, then configuration, then
default scope when `contexts` is `null`; with explicit contexts it
searches those, then the default scope ([runtime preferences][prefs]).

**Use when.**

- Every preference read: it is the one call that honors scope order.

**Do not use when.**

- The read goes to `InstanceScope` directly: an unset key returns your
  literal default, not the initializer's.

**Example.**

```java
public static String tag() {
    return Platform.getPreferencesService().getString(
            Activator.PLUGIN_ID, TAG, DEFAULT_TAG, null);
}
```

**Cost removed.** Reads that ignore defaults or project overrides.
Executed: the lookup returned `FIXME` after an instance write and `TODO`
after `node.remove(TAG)`.

**Verify.**

1. `PreferencesIT` (Executed).

## Project scope preferences

**Definition.** `new ProjectScope(project).getNode(qualifier)` stores
values in `<project>/.settings/<qualifier>.prefs`, which travels with
the project in version control.

**Use when.**

- A team shares a setting per project (the TODO tag of one codebase).

**Do not use when.**

- The lookup passes `null` contexts: the project scope is searched only
  when it is in the context array.

**Example.** From `PreferencesIT`:

```java
IEclipsePreferences node =
        new ProjectScope(project).getNode("org.acme.todos");
node.put("tag", "HACK");
node.flush();
IScopeContext[] order = {new ProjectScope(project),
    InstanceScope.INSTANCE};
String tag = Platform.getPreferencesService()
        .getString("org.acme.todos", "tag", "TODO", order);
```

**Cost removed.** A shared setting that each developer re-enters.
Executed: `.settings/org.acme.todos.prefs` exists in the project, the
ordered lookup returns `HACK`, and the `null`-context lookup returns
`TODO`.

**Verify.**

1. `PreferencesIT.projectScopeIsStoredInTheProjectAndSearchedFirst`
   (Executed).

## Plug-in log with ILog

**Definition.** `ILog.of(Class)` returns the log of the class's bundle
("Since 3.29" of `org.eclipse.core.runtime`). `info`, `warn`, `error`,
and `log(IStatus)` write `!ENTRY <bundle> <severity>` records to
`<workspace>/.metadata/.log` and the Error Log view ([ILog][ilog]).
`Platform.getLog(Class)` (since 3.16) returns the same log and is not
deprecated ([Platform][platform]).

**Use when.**

- A failure is otherwise invisible to the user: a background job's
  per-file problems, a listener's `CoreException`.

**Do not use when.**

- The job's result status already reports the error to the user:
  logging it too produces two entries.
- The message would contain file contents, tokens, or paths outside the
  workspace.

**Example.** Runnable: `TodoLog.java` and `ScanTodosJob.java`.

```java
static final ILog LOG = ILog.of(TodoLog.class);
// ...
if (!problems.isOK()) {
    TodoLog.LOG.log(problems);
}
```

**Cost removed.** Silent failures. Executed (`LogIT`): `warn(...)`
wrote `!ENTRY org.acme.todos.tests 2` with the message to
`Platform.getLogFileLocation()`.

**Verify.**

1. `LogIT` passes (Executed).
1. In a launched IDE, after a failing scan, open Window, Show View, Error
   Log.

[batch]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/resAdv_batching.htm
[events]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/resAdv_events.htm
[markers]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/resAdv_markers.htm
[prefs]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_preferences.htm
[wsjob]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/resources/WorkspaceJob.html
[iresource]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/resources/IResource.html
[instancescope]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/preferences/InstanceScope.html
[ilog]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/ILog.html
[secure]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/equinox/security/storage/SecurePreferencesFactory.html
[platform]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/Platform.html
[toc-run]: #iworkspacerunnable-with-avoid_update
[toc-listener]: #post_change-resource-change-listener
[toc-default]: #default-preferences-through-an-initializer
[toc-lookup]: #preference-lookup-through-ipreferencesservice
