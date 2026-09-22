# Extension case studies for Eclipse OSGi Plugin

## Eclipse: Job with cancellation and safe UI publication

```java
Job job = Job.create("Analyze", monitor -> {
    Result result = analyze(input, monitor);
    if (monitor.isCanceled()) return Status.CANCEL_STATUS;
    Display.getDefault().asyncExec(() -> {
        if (!viewer.getControl().isDisposed()) viewer.setInput(result);
    });
    return Status.OK_STATUS;
});
job.setRule(
    ResourcesPlugin.getWorkspace().getRuleFactory().modifyRule(resource)
);
job.schedule();
```

Use the actual workspace operation and scheduling rule for the mutation. Test
view disposal before callback, cancellation, concurrent jobs, and target bundle
resolution.

## Lifecycle evidence checklist

- activate/load once and twice;
- invoke normal and failing inputs;
- start async work, then edit/close/dispose before completion;
- cancel and verify no late publication;
- unload/reload or close/reopen project/workspace;
- inspect duplicate registrations, processes, timers, handles, and persisted
  state;
- build package, inspect contents, install in a clean declared host;
- distinguish stub/unit tests from real host execution.
