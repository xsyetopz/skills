# Workbench contributions: commands, handlers, menus, views

The 3.x workbench extension points and the Eclipse 4 injection they
support. Runnable sources:
`assets/examples/plugin/org.acme.todos/plugin.xml` and
`org.acme.todos/src/org/acme/todos/`. Tests:
`org.acme.todos.tests/src/org/acme/todos/tests/`. Executed results come
from `sh assets/examples/verify.sh network` (Tycho 5.0.4 UI harness,
Eclipse 4.41, macOS 27 arm64, JDK 25.0.4.1; machine-specific).

## Contents

- [Command definition](#command-definition)
- [Handler class](#handler-class)
- [Handler activeWhen](#handler-activewhen)
- [Handler enabledWhen](#handler-enabledwhen)
- [Expression definitions and reference][toc-defs]
- [Menu contribution: menu: locations][toc-menu]
- [Menu contribution: popup: locations][toc-popup]
- [Menu contribution: toolbar: locations][toc-toolbar]
- [visibleWhen on a menu item](#visiblewhen-on-a-menu-item)
- [Part-scoped handler through IHandlerService][toc-part]
- [Executing a command from code or a test][toc-exec]
- [Text editor command with one undoable edit][toc-editor]
- [View contribution](#view-contribution)
- [LocalResourceManager owned by a control][toc-lrm]
- [SWT Color without disposal](#swt-color-without-disposal)
- [Eclipse 4 injection in a 3.x view][toc-di]

## Command definition

**Definition.** An `org.eclipse.ui.commands` `<command>` declares an
abstract action by `id` and `name`. It does nothing until a handler is
active for it ([commands guide][cmd]).

**Use when.**

- The action must be reachable from menus, toolbars, key bindings, or
  `IHandlerService.executeCommand`.

**Do not use when.**

- The code is an internal call with no UI or binding: call the Java
  method. A command adds registry entries and a lookup.
- An existing platform command fits (for example
  `org.eclipse.ui.file.refresh`): contribute a handler for it instead of
  a duplicate command.

**Example.**

```xml
<extension point="org.eclipse.ui.commands">
  <category id="org.acme.todos.category" name="TODO Markers"/>
  <command id="org.acme.todos.scan" name="Scan TODO Markers"
      categoryId="org.acme.todos.category"/>
</extension>
```

**Cost removed.** `NotDefinedException: Trying to execute a command
that is not defined` (Executed: seen when the registry ignored the
non-singleton bundle). The checker reports handler or menu references
to undeclared ids in the bundle's namespace (X002).

**Verify.**

1. `python3 scripts/check_bundle.py <bundle>` reports no X002 or X006.
1. A plug-in test runs the command by id (`ScanCommandIT`).

## Handler class

**Definition.** An `org.eclipse.ui.handlers` `<handler>` binds an
`IHandler` class (usually an `AbstractHandler`) to a `commandId`.
`execute(ExecutionEvent)` runs on the UI thread; `HandlerUtil` reads
the active shell, part, editor, and selection from the event
([handlers guide][handlers]).

**Use when.**

- Any command behavior declared in `plugin.xml`.

**Do not use when.**

- The work is slow and would run inside `execute`, on the UI thread:
  capture the input and schedule a Job ([Job card][job]).
- `execute` reads `PlatformUI.getWorkbench()...getSelection()`: use the
  event's context, which is what enablement evaluated.

**Example.** Runnable: `ScanTodosHandler.java`.

```java
public final class ScanTodosHandler extends AbstractHandler {
    @Override
    public Object execute(ExecutionEvent event)
            throws ExecutionException {
        IStructuredSelection selection =
                HandlerUtil.getCurrentStructuredSelection(event);
        IProject project = Adapters.adapt(
                selection.getFirstElement(), IProject.class);
        if (project == null || !project.isOpen()) {
            throw new ExecutionException("Select one open project");
        }
        Job job = new ScanTodosJob(List.of(project),
                TodoPreferences.tag());
        job.setUser(true);
        job.schedule();
        return null;
    }
}
```

`Adapters.adapt` also accepts objects that adapt to `IProject`, such as
Java projects in the Package Explorer.

**Cost removed.** UI freezes: the handler returns right after
scheduling, and the job appears in the Progress view. A test must call
`Job.getJobManager().join(FAMILY, null)` before asserting markers.

**Verify.**

1. `ScanCommandIT.scansTheSelectedProjectInABackgroundJob` passes
   (Executed).
1. `rg -n 'join\(|sleep\(' src` finds no waiting inside handlers.

## Handler activeWhen

**Definition.** `<activeWhen>` is a core expression that decides when
this handler, rather than another handler for the same command, is
active. With no active handler, the command is unhandled and
disabled ([handlers guide][handlers]).

**Use when.**

- The handler only makes sense in one context (a text editor, a view),
  which also lets several plug-ins contribute handlers for one
  command.

**Do not use when.**

- The condition is about the current selection's contents: use
  `enabledWhen`, which keeps the handler active but disabled.

**Example.** From the example `plugin.xml`:

```xml
<handler commandId="org.acme.todos.encodeFormValue"
    class="org.acme.todos.EncodeFormValueHandler">
  <activeWhen>
    <reference definitionId="org.acme.todos.inTextEditor"/>
  </activeWhen>
</handler>
```

**Cost removed.** A handler invoked in a part it cannot work with.
With a non-text part active, the command is disabled in the UI and
`executeCommand` throws `NotHandledException`.

**Verify.**

1. `EncodeFormValueIT` runs the command with a text editor active
   (Executed: 3 tests pass).
1. With no editor open, `IHandlerService.executeCommand` must throw
   `NotHandledException` (manual step; not in the example tests).

## Handler enabledWhen

**Definition.** `<enabledWhen>` is a core expression evaluated against
the application context; the default variable is the current selection
as a `java.util.Collection` ([expressions guide][expr]). A disabled
handler makes `executeCommandInContext` throw `NotEnabledException`.

**Use when.**

- The handler needs a specific selection; here, exactly one element
  that adapts to `IProject`.

**Do not use when.**

- An `<iterate>` lacks `ifEmpty="false"`: with the default `and`
  operator it returns `true` for an empty selection, which enables the
  handler with nothing selected ([expressions guide][expr]).

**Example.**

```xml
<enabledWhen>
  <reference definitionId="org.acme.todos.oneProject"/>
</enabledWhen>
```

The definition is in the next card.

**Cost removed.** Handler code for wrong input. Executed:
`ScanCommandIT.enabledWhenRejectsTwoProjects` and
`enabledWhenRejectsNonProjects` get `NotEnabledException` before
`execute` runs.

**Verify.**

1. Run the command with a failing selection and assert
   `NotEnabledException` (`ScanCommandIT`, Executed).
1. Run it with a passing selection and assert the effect.

## Expression definitions and reference

**Definition.** `org.eclipse.core.expressions.definitions` names a core
expression; `<reference definitionId="..."/>` evaluates it wherever an
expression is allowed ([handlers guide][handlers]).

**Use when.**

- One condition appears in more than one place, such as `enabledWhen`
  and `visibleWhen`.

**Do not use when.**

- The condition is used once: inline it; one less id to keep in sync.

**Example.**

```xml
<extension point="org.eclipse.core.expressions.definitions">
  <definition id="org.acme.todos.oneProject">
    <and>
      <count value="1"/>
      <iterate ifEmpty="false">
        <adapt type="org.eclipse.core.resources.IProject"/>
      </iterate>
    </and>
  </definition>
</extension>
```

Workbench elements such as `enabledWhen` take one child expression and
do not combine several children with `and` ([expressions guide][expr]).
Wrap them in `<and>`.

**Cost removed.** Two copies of a condition drifting apart. The
checker reports a `reference` to an undeclared definition in the
bundle's namespace (X004).

**Verify.**

1. `python3 scripts/check_bundle.py <bundle>` reports no X004.
1. `ScanCommandIT` (Executed) covers both outcomes of `oneProject`.

## Menu contribution: menu: locations

**Definition.** An `org.eclipse.ui.menus` `<menuContribution
locationURI="menu:<id>?after=<group>">` inserts items into the main
menu (`org.eclipse.ui.main.menu`), a top-level menu such as `edit` or
`file`, or a view's drop-down (view id) ([menus guide][menus]).

**Use when.**

- The command belongs in a menu bar or a view menu.

**Do not use when.**

- The contribution is a legacy action set: action sets are deprecated.
  Use commands and menus.

**Example.**

```xml
<menuContribution locationURI="menu:edit?after=additions">
  <command commandId="org.acme.todos.encodeFormValue"
      style="push">
    <visibleWhen checkEnabled="false">
      <reference definitionId="org.acme.todos.inTextEditor"/>
    </visibleWhen>
  </command>
</menuContribution>
```

**Cost removed.** Silent placement failures: a wrong scheme or menu id
shows nothing and logs nothing. The checker reports a `locationURI`
without `menu:`, `popup:`, or `toolbar:` (X003); an unknown menu id
shows up only in a running workbench.

**Verify.**

1. `python3 scripts/check_bundle.py <bundle>` reports no X003.
1. Not automated: launch the IDE (`verify.sh network` installs one) and
   open the Edit menu with a text editor active.

## Menu contribution: popup: locations

**Definition.** `popup:<id>` targets the context menu registered with
that id (by default the part id); `popup:org.eclipse.ui.popup.any`
targets every registered context menu ([menus guide][menus]).

**Use when.**

- The action applies to a selected object in any view, such as a
  project in the Project Explorer or Package Explorer.

**Do not use when.**

- The item would have no `visibleWhen`: with `popup.any` it appears in
  every context menu, including editors and consoles.

**Example.**

```xml
<menuContribution
    locationURI="popup:org.eclipse.ui.popup.any?after=additions">
  <command commandId="org.acme.todos.scan" style="push">
    <visibleWhen checkEnabled="false">
      <with variable="activeMenuSelection">
        <reference definitionId="org.acme.todos.oneProject"/>
      </with>
    </visibleWhen>
  </command>
</menuContribution>
```

`activeMenuSelection` is the selection of the menu's provider;
`<iterate><adapt type="..."/></iterate>` replaces the old
`objectClass` of `org.eclipse.ui.popupMenus` ([menus guide][menus]).

**Cost removed.** Context-menu clutter in unrelated views: right-click
a file or an editor, and the item is absent.

**Verify.**

1. `python3 scripts/check_bundle.py <bundle>` is clean.
1. Not automated: in a launched IDE, right-click a project (item
   present) and a file (item absent).

## Menu contribution: toolbar: locations

**Definition.** `toolbar:<id>` targets a view toolbar (view id), the
main toolbar (`org.eclipse.ui.main.toolbar`, which needs a nested
`<toolbar id="...">`), or a trim area such as
`toolbar:org.eclipse.ui.trim.status` ([menus guide][menus]).

**Use when.**

- The command is frequent and has an icon.

**Do not use when.**

- Visibility would depend on the selection: updating the main toolbar
  is expensive. The guide keeps visibility at the action-set or
  active-editor level and tracks the selection through the handler's
  enabled state ([menus guide][menus]).
- The icon file is missing from `bin.includes` (checker B007).

**Example.** Not in the example plug-in (guide form):

```xml
<menuContribution
    locationURI="toolbar:org.eclipse.ui.main.toolbar?after=additions">
  <toolbar id="org.acme.todos.toolbar">
    <command commandId="org.acme.todos.scan"
        icon="icons/scan.png" tooltip="Scan TODO markers"/>
  </toolbar>
</menuContribution>
```

**Cost removed.** Main-toolbar refreshes on every selection change.
Toolbar items carry no `visibleWhen` on selection variables
(`rg -n 'toolbar:' -A8 plugin.xml`).

**Verify.**

1. `python3 scripts/check_bundle.py <bundle>` checks the scheme (X003)
   and the icon packaging (B007). Tier: checker only; not launched.

## visibleWhen on a menu item

**Definition.** `<visibleWhen>` is a core expression that shows or
hides one menu item. `checkEnabled="true"` instead ties visibility to
the command's enabled state ([menus guide][menus]).

**Use when.**

- The item is meaningless in the current context (no text editor, no
  project selected) and should not appear.

**Do not use when.**

- The item should stay visible but greyed out: omit `visibleWhen` and
  rely on the handler's `enabledWhen`.

**Example.** From the example `plugin.xml`: the Edit menu item appears
only while a text editor is active, and the handler's `activeWhen`
references the same definition.

```xml
<extension point="org.eclipse.core.expressions.definitions">
  <definition id="org.acme.todos.inTextEditor">
    <with variable="activeEditor">
      <instanceof value="org.eclipse.ui.texteditor.ITextEditor"/>
    </with>
  </definition>
</extension>
<extension point="org.eclipse.ui.handlers">
  <handler commandId="org.acme.todos.encodeFormValue"
      class="org.acme.todos.EncodeFormValueHandler">
    <activeWhen>
      <reference definitionId="org.acme.todos.inTextEditor"/>
    </activeWhen>
  </handler>
</extension>
<extension point="org.eclipse.ui.menus">
  <menuContribution locationURI="menu:edit?after=additions">
    <command commandId="org.acme.todos.encodeFormValue" style="push">
      <visibleWhen checkEnabled="false">
        <reference definitionId="org.acme.todos.inTextEditor"/>
      </visibleWhen>
    </command>
  </menuContribution>
</extension>
```

**Cost removed.** A visible item that does nothing on click, which
users report as a bug. Check that the item's `visibleWhen` and its
handler's `activeWhen` (or `enabledWhen`) reference the same definition
(`rg -n definitionId plugin.xml`).

**Verify.**

1. `python3 scripts/check_bundle.py <bundle>` passes (X004 checks the
   reference).
1. Not automated: in a launched IDE, compare the menu for a matching and
   a non-matching selection.

## Part-scoped handler through IHandlerService

**Definition.** `IHandlerService.activateHandler(commandId, handler)`
from a part site's service keeps a handler active only while that part
is active; the activation ends when the part is disposed ([handlers
guide][handlers]).

**Use when.**

- The handler needs the part's live state (its viewer), such as a
  "Count entries" command for one view.

**Do not use when.**

- The handler needs no part state: declare it in `plugin.xml`, so it
  exists without creating the part.
- The service comes from the workbench, not the part site: that
  activation is global and never deactivates.

**Example.** Guide form, not in the example plug-in:

```java
@Override
public void createPartControl(Composite parent) {
    viewer = new ListViewer(parent);
    IHandlerService service =
            getSite().getService(IHandlerService.class);
    service.activateHandler("org.acme.todos.count",
            new AbstractHandler() {
                @Override
                public Object execute(ExecutionEvent event) {
                    return viewer.getList().getItemCount();
                }
            });
}
```

**Cost removed.** Handlers left active after their view closes. Tier:
guide example; not compiled or run here.

**Verify.**

1. Close the view and assert that
   `commandService.getCommand(id).isHandled()` is `false`.

## Executing a command from code or a test

**Definition.** `IHandlerService.executeCommand(id, event)` runs a
command in the current application context.
`executeCommandInContext(ParameterizedCommand, event, context)` runs it
in a context you build, so enablement and `HandlerUtil` see your
selection.

**Use when.**

- A plug-in test must exercise the real registration path: command id,
  handler lookup, enablement, and `execute`.

**Do not use when.**

- The test calls `new ScanTodosHandler().execute(...)`: that skips the
  registry and proves nothing about `plugin.xml`.

**Example.** Runnable: `ScanCommandIT.java`.

```java
IEvaluationContext context = new EvaluationContext(
        handlers.createContextSnapshot(false), List.of(selected));
context.addVariable(ISources.ACTIVE_CURRENT_SELECTION_NAME,
        new StructuredSelection(selected));
handlers.executeCommandInContext(new ParameterizedCommand(
        commands.getCommand(SCAN), null), null, context);
```

`IEvaluationContext` has no setter for the default variable; pass it
to the `EvaluationContext` constructor. Executed: a first attempt with
`setDefaultVariable` did not compile.

**Cost removed.** Tests that pass while the contribution is broken.
Executed: without `singleton:=true`, these tests failed with
`NotDefinedException` and `NullPointerException ... "handler" is null`.
A direct `new ScanTodosHandler().execute(...)` never reads
`plugin.xml`, so it cannot fail that way (inferred).

**Verify.**

1. `ScanCommandIT` passes (Executed: 3 tests).
1. Remove the handler from `plugin.xml`: the test must fail with
   `NotHandledException`.

## Text editor command with one undoable edit

**Definition.** A handler that resolves the active `ITextEditor` at
execution time, checks editability with
`ITextEditorExtension2.validateEditorInputState()`, and changes the
unsaved `IDocument` from the editor's document provider in one
`replace`: one undo step ([ITextEditorExtension2][ite2]).

**Use when.**

- The command transforms the selection in the editor buffer without
  saving.

**Do not use when.**

- The text must change on disk without an editor: use `IFile` APIs in a
  workspace operation.
- `ITextSelection.isEmpty()` stands for "nothing selected": it is
  `false` for a caret. Test `getLength() <= 0`
  ([TextSelection][textsel]).

**Example.** Runnable: `EncodeFormValueHandler.java`.

```java
if (editor instanceof ITextEditorExtension2 extended
        && !extended.validateEditorInputState()) {
    return null; // read-only file or user declined
}
if (!(editor.getSelectionProvider().getSelection()
        instanceof ITextSelection selection)
        || selection.getLength() <= 0) {
    return null;
}
IDocument document = editor.getDocumentProvider()
        .getDocument(editor.getEditorInput());
String encoded = URLEncoder.encode(document.get(
        selection.getOffset(), selection.getLength()),
        StandardCharsets.UTF_8);
document.replace(selection.getOffset(), selection.getLength(),
        encoded);
editor.selectAndReveal(selection.getOffset(), encoded.length());
```

The runnable file rejects block and multi-range selections with an
`ExecutionException`.

**Cost removed.** Edits written to disk behind the user, several undo
steps, and a dirty editor after a no-op. Executed
(`EncodeFormValueIT`): one `UNDO` action restores the text, the file on
disk keeps `prefix saved suffix`, and a caret-only run leaves
`isDirty()` `false`.

**Verify.**

1. `EncodeFormValueIT` passes (3 tests, Executed).
1. Assert that `Files.readString(file)` is unchanged after the
   command.

## View contribution

**Definition.** An `org.eclipse.ui.views` `<view id class name>`
declares a part the workbench creates on `IWorkbenchPage.showView(id)`.
The class implements `IViewPart`, usually by extending `ViewPart`
([views extension point][views]).

**Use when.**

- The plug-in shows persistent state (counts, lists) beside editors.

**Do not use when.**

- The result is shown once: a notification or dialog is enough.
- The view would keep listeners without removing them in `dispose()`:
  every open and close cycle adds one.

**Example.** Runnable: `TodoView.java`; registration:

```xml
<extension point="org.eclipse.ui.views">
  <category id="org.acme.todos.views" name="TODO Markers"/>
  <view id="org.acme.todos.view" name="TODO Count"
      category="org.acme.todos.views"
      class="org.acme.todos.TodoView" inject="true"/>
</extension>
```

The view adds a `POST_CHANGE` listener in `createPartControl` and
removes it in `dispose`.

**Cost removed.** Listener leaks per open and close. After `hideView`,
marker changes no longer reach the view (the test's `finally` closes
it).

**Verify.**

1. `TodoViewIT.injectedViewShowsCountAfterBackgroundScan` opens the
   view by id and reads its label (Executed).

## LocalResourceManager owned by a control

**Definition.** `new LocalResourceManager(JFaceResources.getResources(),
control)` is a local registry over the shared JFace registry. What it
creates from descriptors (`FontDescriptor`, `ImageDescriptor`,
`ColorDescriptor`) is released when the owner control is disposed
([LocalResourceManager][lrm], [JFace resources][jface-res]).

**Use when.**

- A view or dialog creates fonts or images: tie them to its top control
  instead of calling `dispose()` by hand.

**Do not use when.**

- The resource is a shared system resource (`Display.getSystemColor`,
  `JFaceResources.getDialogFont()`): it is not yours to release.

**Example.** From `TodoViewIT.localResourceManagerDisposesWithItsOwner`:

```java
Shell shell = new Shell();
ResourceManager resources = new LocalResourceManager(
        JFaceResources.getResources(), shell);
Font font = resources.create(
        FontDescriptor.createFrom("Monospace", 11, SWT.BOLD));
shell.dispose(); // font.isDisposed() is now true
```

**Cost removed.** OS handle leaks per open and close of a part.
Executed: `font.isDisposed()` changed from `false` to `true` when the
owner shell was disposed.

**Verify.**

1. `TodoViewIT.localResourceManagerDisposesWithItsOwner` (Executed).
1. `rg -n 'new (Font|Image)\(' src` finds no unmanaged allocations.

## SWT Color without disposal

**Definition.** In current SWT, "Colors do not need to be disposed".
Disposing one is still allowed for old code, and the constructors
without a `Device` are recommended ([Color][color]).

**Use when.**

- You need a fixed RGB color: `new Color(10, 20, 30)`.

**Do not use when.**

- The target platform is an old release whose `Color` still needs
  `dispose()`: check the `Color` Javadoc of that release.

**Example.**

```java
Color color = new Color(10, 20, 30);
label.setForeground(color);
```

**Cost removed.** Dispose bookkeeping for colors. Executed
(`TodoViewIT.colorNeedsNoDisplayAndNoDisposal`): the device-less
constructor works in the 4.41 runtime and `dispose()` raises nothing.

**Verify.**

1. `TodoViewIT.colorNeedsNoDisplayAndNoDisposal` (Executed).

## Eclipse 4 injection in a 3.x view

**Definition.** With `inject="true"` on a view, the workbench runs
Eclipse DI on the instance: after the no-argument constructor and
`init`, it injects `@Inject` fields and methods, calls one
`@PostConstruct` method, then calls `createPartControl`. Constructor
injection is not available ([views extension point][views]).

**Use when.**

- A 3.x view needs Eclipse 4 services such as
  `org.eclipse.e4.ui.di.UISynchronize` or `IEclipseContext` without
  static lookups.

**Do not use when.**

- The annotations come from `javax.inject`: E4 support for
  `javax.inject` and `javax.annotation` is deprecated and was scheduled
  to be disabled by default after the December 2025 release
  ([removals][removals]). Use `jakarta.inject` (the 4.41 repository
  ships 2.0.1).
- The view needs constructor injection: not supported.

**Example.** Runnable: `TodoView.java`.

```java
public final class TodoView extends ViewPart {
    @Inject
    private UISynchronize sync;

    private Label label;

    private void markersChanged(IResourceChangeEvent event) {
        if (event.findMarkerDeltas(TodoMarkers.TYPE, true)
                .length == 0) {
            return;
        }
        sync.asyncExec(() -> {
            if (!label.isDisposed()) {
                refresh();
            }
        });
    }
}
```

Manifest: `Import-Package: jakarta.inject;version="[2.0.0,3.0.0)"` and
`Require-Bundle: org.eclipse.e4.ui.di` (for `UISynchronize`).

**Cost removed.** Static `Display.getDefault()` lookups and untestable
singletons. Executed: `view.injected()` is `true` in `TodoViewIT`, and
the label reaches `2 TODO marker(s)` after a background scan.

**Verify.**

1. `TodoViewIT` passes (Executed).
1. Set `inject="false"` and rerun: the first assertion should fail
   because no injection runs (not executed here).

[cmd]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/workbench_cmd.htm
[handlers]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/workbench_cmd_handlers.htm
[menus]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/workbench_cmd_menus.htm
[expr]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/workbench_cmd_expressions.htm
[views]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/extension-points/org_eclipse_ui_views.html
[removals]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/porting/removals.html
[ite2]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/ui/texteditor/ITextEditorExtension2.html
[textsel]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/jface/text/TextSelection.html
[lrm]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/jface/resource/LocalResourceManager.html
[jface-res]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/jface_resources.htm
[color]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/swt/graphics/Color.html
[job]: jobs-and-threads.md#job-with-a-progress-monitor
[toc-defs]: #expression-definitions-and-reference
[toc-menu]: #menu-contribution-menu-locations
[toc-popup]: #menu-contribution-popup-locations
[toc-toolbar]: #menu-contribution-toolbar-locations
[toc-part]: #part-scoped-handler-through-ihandlerservice
[toc-exec]: #executing-a-command-from-code-or-a-test
[toc-editor]: #text-editor-command-with-one-undoable-edit
[toc-lrm]: #localresourcemanager-owned-by-a-control
[toc-di]: #eclipse-4-injection-in-a-3x-view
