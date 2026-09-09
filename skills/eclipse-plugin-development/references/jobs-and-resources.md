# Jobs, SWT and OSGi lifecycle

Research: 2026-09-09; current Eclipse Platform API.

## Background computation and UI application

Example fragment: supply `compute`, `render`, and a request-generation owner.

```java
Job job = new Job("Analyze selection") {
    @Override
    protected IStatus run(IProgressMonitor monitor) {
        if (monitor.isCanceled()) return Status.CANCEL_STATUS;
        var result = compute(monitor);
        if (monitor.isCanceled()) return Status.CANCEL_STATUS;
        display.asyncExec(() -> {
            if (control.isDisposed() || generation != currentGeneration())
                return;
            render(result);
        });
        return Status.OK_STATUS;
    }
};
job.schedule();
```

Capture immutable inputs and `display`/`control` identity on the UI thread
before starting. Re-check disposal and request generation in the UI callback.
`schedule()` queues work; it does not complete it. `cancel()` requests
cancellation for an active job, so computation must check the monitor. Joining
immediately on the UI thread defeats responsiveness and can deadlock.
[Jobs][ref-1].

Most SWT widget access belongs on the creating Display thread. `asyncExec`
schedules; `syncExec` blocks the caller and must not be used while holding a
lock needed by UI code. Disposed displays can reject scheduling, so shutdown
must stop producers before tearing down UI. [SWT threading][ref-2].

## Workspace and service ownership

For workspace resource mutation, use the appropriate scheduling
rule/WorkspaceJob so conflicting operations serialize. Choose the narrow
resource rule; a workspace-root rule can unnecessarily block unrelated work.
Snapshot resource-change events and schedule mutations after notification locks
are released. Preserve atomic workspace operations and expected marker/update
behavior. [Workspace jobs][ref-3].

Tie job families, service trackers and listeners to the bundle/component
lifetime. Declarative Services can bind/unbind dependencies as services come and
go; do not cache a disappearing service forever. Register capabilities during
activation. Defer workspace scans to feature execution. On stop, cancel owned
jobs, prevent new callbacks and coordinate completion without a UI/worker lock
cycle. Keep static initializers cheap.

## SWT resources and persistence

Dispose owned `Image`, `Font`, `Color` and other disposable resources according
to the target API's ownership contract. Do not dispose shared system resources
or resources owned by a registry/manager. A `LocalResourceManager` associated
with a control can make image/font lifetime explicit. Remove selection/document
listeners when the view/editor closes; clear references to disposed widgets.
[JFace resources][ref-4].

Use preference scopes intentionally: defaults, instance and project values
differ. Persist stable identifiers and serializable data, not live
workspace/widget references. A renamed preference needs an idempotent conversion
and a policy for old-version readers if those remain supported. Keep transient
job results out of authoritative persisted state unless the feature requires
them.

For validation, check cancellation, project/view close and workspace conflicts
only for touched behavior, alongside existing gates. Use the Eclipse host for
Display/OSGi behavior and p2 resolution for installation claims.

[ref-1]:
  https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_jobs.htm
[ref-2]:
  https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/swt_threading.htm
[ref-3]:
  https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_jobs_rules.htm
[ref-4]:
  https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/jface_resources.htm
