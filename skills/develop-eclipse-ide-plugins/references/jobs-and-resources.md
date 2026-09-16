# Manage Eclipse Jobs, SWT resources, and OSGi lifecycle

Target-dependent API reference; refresh target-specific API contracts before
use.

## Background work and UI application

Capture immutable inputs and widget identity on the UI thread before scheduling
background analysis. Check the job's progress monitor during expensive work.
Post results through the owning Display, then reject disposed controls and
superseded requests before applying them. Generation checks matter when requests
can supersede each other without a document change; synchronous work needs no
extra request state.

`schedule()` queues work; it does not complete it. `cancel()` requests
cancellation for an active job, so computation must cooperate. Joining
immediately on the UI thread defeats responsiveness and can deadlock.
[Jobs][api-1].

Most SWT widget access belongs on the creating Display thread. `asyncExec`
schedules; `syncExec` blocks the caller and must not be used while holding a
lock needed by UI code. Disposed displays can reject scheduling, so shutdown
must stop producers before tearing down UI. Checking a control only inside the
callback does not protect the scheduling call itself. [SWT threading][api-2].

## Text commands

Resolve the active text editor at execution time. Use its document provider's
unsaved document rather than reopening the file. Validate editability through
the editor contract before changing text, and make one logical transformation
one undoable edit. Preserve the selected replacement and do not save without a
user request. Use the text selection's length to detect a caret-only selection;
`TextSelection.isEmpty()` describes an invalid selection, not zero selected
characters. The real workbench test caught a no-op replacement that incorrectly
made an unchanged editor dirty. [Text selection][text-selection], [editor
validation][editor-validation].

## Workspace and services

For workspace resource mutation, use the appropriate scheduling
rule/WorkspaceJob so conflicting operations serialize. Choose the narrow
resource rule; a workspace-root rule can unnecessarily block unrelated work.
Snapshot resource-change events and schedule mutations after notification locks
are released. Preserve atomic workspace operations and expected marker/update
behavior. [Workspace jobs][workspace-source].

Tie job families, service trackers and listeners to the bundle/component
lifetime. Declarative Services can bind/unbind dependencies as services come and
go; do not cache a disappearing service forever. Register capabilities during
activation. Defer workspace scans to feature execution. On stop, cancel owned
jobs, prevent new callbacks and coordinate completion without a UI/worker lock
cycle. Keep static initializers cheap.

[workspace-source]:
https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_jobs_rules.htm

## Resources and persistence

Dispose owned images, fonts and other disposable resources according to the
target API's ownership contract. Current SWT `Color` requires no disposal; check
the selected older target before applying that rule. Do not dispose shared
system resources or resources owned by a registry/manager. A
`LocalResourceManager` associated with a control can make image/font lifetime
explicit. Remove selection/document listeners when the view/editor closes; clear
references to disposed widgets. [JFace resources][resources-source].

Use preference scopes intentionally: defaults, instance and project values
differ. Persist stable identifiers and serializable data, not live
workspace/widget references. A renamed preference needs an idempotent conversion
and a policy for old-version readers if those remain supported. Keep transient
job results out of authoritative persisted state unless the feature requires
them.

For validation, check cancellation, project/view close and workspace conflicts
only for touched behavior, alongside existing validation requirements. Use the
Eclipse host for Display/OSGi behavior and p2 resolution for installation
claims.

[resources-source]:
https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/jface_resources.htm

[Current Color contract][color-api].

[color-api]:
https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/swt/graphics/Color.html
[api-1]:
https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_jobs.htm
[api-2]:
https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/swt_threading.htm
[text-selection]:
https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/jface/text/TextSelection.html
[editor-validation]:
https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/ui/texteditor/ITextEditorExtension2.html
