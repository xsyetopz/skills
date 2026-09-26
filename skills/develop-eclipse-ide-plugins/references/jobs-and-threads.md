# Jobs, scheduling rules, and the SWT UI thread

Background work and returning its results to the UI. Runnable sources:
`assets/examples/plugin/org.acme.todos/src/org/acme/todos/`
(`ScanTodosJob`, `Activator`, `TodoView`) and the tests
`WorkspaceRulesIT`, `ScanTodosJobIT`, and `TodoViewIT`. Executed
results come from `sh assets/examples/verify.sh network` (Tycho 5.0.4
UI harness, Eclipse 4.41, macOS 27 arm64, JDK 25.0.4.1). Timings are
machine-specific, taken while other builds ran.

## Contents

- [Job with a progress monitor](#job-with-a-progress-monitor)
- [Job.create with a lambda](#jobcreate-with-a-lambda)
- [SubMonitor split and cancellation][toc-split]
- [Cancelling and joining a job](#cancelling-and-joining-a-job)
- [Resource as a scheduling rule](#resource-as-a-scheduling-rule)
- [MultiRule.combine](#multirulecombine)
- [IResourceRuleFactory rules](#iresourcerulefactory-rules)
- [Custom ISchedulingRule](#custom-ischedulingrule)
- [Job families and bundle shutdown](#job-families-and-bundle-shutdown)
- [System and user jobs](#system-and-user-jobs)
- [SWT UI thread ownership](#swt-ui-thread-ownership)
- [Display.asyncExec with a disposed check][toc-async]
- [Display.syncExec](#displaysyncexec)

## Job with a progress monitor

**Definition.** `org.eclipse.core.runtime.jobs.Job` is a unit of
asynchronous work: `schedule()` queues it, a worker thread calls
`run(IProgressMonitor)`, and the returned `IStatus` becomes
`getResult()`. The monitor "is never null" and is valid only during
`run` ([Job][job-api], [concurrency guide][jobs]).

**Use when.**

- Work started from the UI is slow (file reads, scanning, network).
- The work must show progress, be cancellable, or serialize with other
  workspace work through a rule.

**Do not use when.**

- The work is a few milliseconds of in-memory computation: run it
  inline.
- The UI thread calls `schedule()` and then `join()`: that blocks the UI
  and "you obtain no concurrency" ([concurrency guide][jobs]).

**Example.** Runnable: `ScanTodosJob.java` (excerpt).

```java
public final class ScanTodosJob extends Job {
    public ScanTodosJob(List<? extends IResource> roots, String tag) {
        super("Scan " + tag + " markers");
        this.roots = List.copyOf(roots);
        this.tag = tag;
        setRule(ruleFor(this.roots));
    }

    @Override
    protected IStatus run(IProgressMonitor monitor) {
        SubMonitor progress = SubMonitor.convert(monitor, 100);
        // collect *.txt files: progress.split(10)
        // read and scan each file: progress.split(60)
        // replace markers in one workspace operation: split(30)
        return Status.OK_STATUS;
    }
}
```

**Cost removed.** UI freezes. The handler returns at once and the job
appears by name in the Progress view; `ScanTodosJobIT` joins it and
asserts `getResult().isOK()` (Executed).

**Verify.**

1. `ScanTodosJobIT` passes (Executed: 3 tests).
1. Not automated: in a launched IDE, run the command on a large project
   and keep typing in an editor while the job runs.

## Job.create with a lambda

**Definition.** `Job.create(String, IJobFunction)` (since 3.6) and
`Job.create(String, ICoreRunnable)` (since 3.8) build a job from a
lambda; `Job.createSystem` builds a system job ([Job][job-api]).

**Use when.**

- The job needs no fields, no `belongsTo` family, and no rule logic in a
  subclass.

**Do not use when.**

- The job must belong to a family for shutdown: `belongsTo` needs a
  subclass.
- The lambda throws checked exceptions other than `CoreException`: both
  functional interfaces allow only that one.

**Example.** From `WorkspaceRulesIT`:

```java
Job job = Job.create("cancellable", monitor -> {
    SubMonitor progress = SubMonitor.convert(monitor, 1000);
    for (int i = 0; i < 1000; i++) {
        progress.split(1);
        sleep(5);
    }
    return Status.OK_STATUS;
});
```

Executed: a first version that called `Thread.sleep` directly in the
lambda did not compile (`InterruptedException` is not allowed).

**Cost removed.** A named subclass per trivial job; count them with
`rg -n 'extends Job'` in the change.

**Verify.**

1. `WorkspaceRulesIT.splitCancellationBecomesCancelStatus` (Executed).

## SubMonitor split and cancellation

**Definition.** `SubMonitor.convert(monitor, ticks)` wraps any monitor,
`null` included. `split(n)` returns a child for `n` ticks and throws
`OperationCanceledException` when the monitor is cancelled, but "Not every
call to this method will trigger a cancellation check"
([SubMonitor][submon]). The job worker catches
`OperationCanceledException` from `run` and sets the result to
`Status.CANCEL_STATUS` ([Worker.java][worker]).

**Use when.**

- Any method that takes an `IProgressMonitor`: convert once, split per
  sub-task, never call `done()` on split children.

**Do not use when.**

- Code drives `IProgressMonitor.beginTask`/`worked` by hand across
  method calls: tick totals drift and cancellation checks get forgotten.
- Code catches `OperationCanceledException` and continues: the cancel is
  lost.

**Example.** The SubMonitor Javadoc pattern; `collect` and `scan` stand
for your methods that take a monitor.

```java
SubMonitor progress = SubMonitor.convert(monitor, 100);
collect(progress.split(10));
SubMonitor each = progress.split(90).setWorkRemaining(files.size());
for (IFile file : files) {
    scan(file, each.split(1)); // throws OperationCanceledException
}
```

**Cost removed.** Jobs that keep running after the user clicks Cancel.
Executed: a 1000-iteration job (5 ms per step) cancelled after 200 ms
stopped after 31 to 34 iterations in each of nine recorded runs, with
`getResult()` severity `IStatus.CANCEL`.

**Verify.**

1. `WorkspaceRulesIT.splitCancellationBecomesCancelStatus` asserts
   `IStatus.CANCEL` and fewer than 1000 iterations (Executed).
1. Its printed `iterations before cancel` is far below 1000.

## Cancelling and joining a job

**Definition.** `cancel()` discards a job that has not started and
returns `true`; for a running job it returns `false` and only sets the
monitor's cancel flag. `join()` blocks until the job finishes. The
guide's idiom is `if (!job.cancel()) job.join();` ([concurrency
guide][jobs]).

**Use when.**

- New input supersedes a running computation, or the job must stop
  before shutdown.

**Do not use when.**

- The caller is the UI thread and the job may need it (for example, it
  calls `syncExec`): `join` deadlocks.
- A decision would rest on `getState()`: the guide calls the result "not
  always reliable". Use `IJobChangeListener` or `join`.

**Example.**

```java
if (!job.cancel()) {
    job.join();
}
```

**Cost removed.** Two computations writing results for the same input.
After `cancel`+`join`, `job.getState() == Job.NONE`.

**Verify.**

1. `WorkspaceRulesIT.splitCancellationBecomesCancelStatus` (Executed).

## Resource as a scheduling rule

**Definition.** `IResource` implements `ISchedulingRule`: a job or
`IWorkspace.run` holding a project rule excludes other writers of that
project and its descendants. "When a non-null scheduling rule is
used, any attempt to access a resource outside the scope of the
scheduling rule will trigger an exception" ([batching guide][batch]).

**Use when.**

- The job changes resources or markers in known projects.

**Do not use when.**

- One project suffices but the rule is the workspace root: the root rule
  blocks every other workspace writer.
- The job modifies resources and its rule is `null`: nothing serializes
  it against other writers.

**Example.** From `ScanTodosJob.java`; `ScanTodosJobIT` asserts that
`new ScanTodosJob(List.of(project), "TODO")` has `getRule() == project`.

```java
public ScanTodosJob(List<? extends IResource> roots, String tag) {
    super("Scan " + tag + " markers");
    this.roots = List.copyOf(roots);
    this.tag = tag;
    setRule(ruleFor(this.roots));
}

/** One rule per project: the job may only touch those projects. */
static ISchedulingRule ruleFor(List<IResource> roots) {
    Set<ISchedulingRule> projects = new LinkedHashSet<>();
    for (IResource root : roots) {
        projects.add(root.getProject() != null
                ? root.getProject() : root);
    }
    return MultiRule.combine(
            projects.toArray(ISchedulingRule[]::new));
}
```

**Cost removed.** Lost updates from concurrent writers. Executed
(`WorkspaceRulesIT`): two jobs holding the same project rule never
overlapped (max concurrency 1); with `null` rules they overlapped (max
2). Touching another project inside
`workspace.run(..., insideProject, ...)` threw
`IllegalArgumentException: Attempted to beginRule: P/rule-outside, does
not match outer scope rule: P/rule-inside`.

**Verify.**

1. `WorkspaceRulesIT.conflictingRulesNeverOverlap` and
   `ruleLimitsWhatTheRunnableMayTouch` pass (Executed).

## MultiRule.combine

**Definition.** `MultiRule.combine(ISchedulingRule...)` merges rules
into one. A thread may own only one rule at a time, so a job that
touches several projects needs the combination ([rules guide][rules]).

**Use when.**

- One job updates resources in several projects.

**Do not use when.**

- The rules nest (a file and its project): the project rule already
  contains the file.

**Example.** From `ScanTodosJob.ruleFor`:

```java
Set<ISchedulingRule> projects = new LinkedHashSet<>();
for (IResource root : roots) {
    projects.add(root.getProject() != null
            ? root.getProject() : root);
}
return MultiRule.combine(projects.toArray(ISchedulingRule[]::new));
```

With a single project, the combined rule equals that project (Executed:
`assertEquals(project, job.getRule())`).

**Cost removed.** `IllegalArgumentException ... does not match outer
scope rule` when the job reaches the second project; the text appears in
the job's result status.

**Verify.**

1. `ScanTodosJobIT.familyJoinWaitsForEveryScan` runs two jobs on two
   projects in parallel (Executed).

## IResourceRuleFactory rules

**Definition.** `workspace.getRuleFactory()` returns the rules the
workspace itself requires for an operation: `modifyRule(resource)`,
`createRule`, `deleteRule`, `moveRule`, `markerRule` (which may return
`null`) ([IResourceRuleFactory][rulefactory], [batching guide][batch]).

**Use when.**

- The operation spans more than one obvious project, such as a move
  between projects: combine `moveRule` and `modifyRule`.

**Do not use when.**

- The rule is a guess narrower than the factory's: the workspace throws
  the "does not match outer scope rule" error.

**Example.** Guide form:

```java
IResourceRuleFactory factory = workspace.getRuleFactory();
ISchedulingRule rule = MultiRule.combine(
        factory.moveRule(source, destination),
        factory.modifyRule(destination));
workspace.run(runnable, rule, IWorkspace.AVOID_UPDATE, monitor);
```

**Cost removed.** Over-wide root rules that serialize unrelated work.
Tier: guide example; not in the example tests.

**Verify.**

1. Run the operation under the factory rule in a plug-in test: no
   `IllegalArgumentException` from `beginRule`.

## Custom ISchedulingRule

**Definition.** An `ISchedulingRule` implementation: `isConflicting`
decides whether two holders may run together, `contains` whether a
holder may also acquire this rule ([rules guide][rules]).

**Use when.**

- Jobs must serialize over a non-workspace resource, such as one external
  process or one network endpoint.

**Do not use when.**

- The resource is in the workspace: the `IResource` rule already models
  the tree.

**Example.** From the rules guide, as a mutex:

```java
final class Mutex implements ISchedulingRule {
    @Override
    public boolean isConflicting(ISchedulingRule rule) {
        return rule == this;
    }

    @Override
    public boolean contains(ISchedulingRule rule) {
        return rule == this;
    }
}
```

**Cost removed.** Interleaved access to a shared external resource.
Without it, the guide's light-switch example ends in the wrong state.

**Verify.**

1. Two jobs sharing one `Mutex` never overlap; measure with the
   `maxOverlap` helper in `WorkspaceRulesIT`.

## Job families and bundle shutdown

**Definition.** `belongsTo(Object family)` groups jobs;
`IJobManager.cancel(family)`, `join(family, monitor)`, and
`find(family)` act on the group. The guide cancels and joins a bundle's
jobs in its `stop` method ([concurrency guide][jobs]).

**Use when.**

- The bundle schedules jobs that could still run when it stops, or tests
  must wait for all of them.

**Do not use when.**

- The family object is a common string such as `"build"`: another
  plug-in may use it. Use a bundle-specific object such as the job
  class.

**Example.**

```java
public static final Object FAMILY = ScanTodosJob.class;

@Override
public boolean belongsTo(Object family) {
    return family == FAMILY;
}
```

and in `Activator.stop`:

```java
Job.getJobManager().cancel(ScanTodosJob.FAMILY);
Job.getJobManager().join(ScanTodosJob.FAMILY, null);
```

**Cost removed.** Jobs that run after their bundle stopped and fail to
load classes. Executed: `ScanTodosJobIT.familyJoinWaitsForEveryScan`
finds 0 jobs of the family after `join`.

**Verify.**

1. `Job.getJobManager().find(ScanTodosJob.FAMILY).length == 0` after
   `join` (Executed).

## System and user jobs

**Definition.** `setSystem(true)` hides a job from progress UI;
`setUser(true)` marks a user-initiated job that may show a progress
dialog. Call both before `schedule()` ([progress
guide][progress]).

**Use when.**

- `setUser(true)`: the user clicked something and waits for it (the scan
  command).
- `setSystem(true)`: background work the user did not start (the rescan
  after a file edit).

**Do not use when.**

- Either call comes after `schedule()`: `setSystem` then throws.

**Example.** `ScanTodosHandler` (the user picked the command):

```java
Job job = new ScanTodosJob(List.of(project), TodoPreferences.tag());
job.setUser(true); // user-initiated: progress dialog/view
job.schedule();
```

`TodoRescanListener` (a resource change triggered it):

```java
ScanTodosJob job =
        new ScanTodosJob(changed, TodoPreferences.tag());
job.setSystem(true); // not user-initiated: no progress UI
job.schedule();
```

**Cost removed.** Progress dialogs for work nobody asked for. Edit a
`.txt` file in the IDE: no progress entry appears for the rescan.

**Verify.**

1. `rg -n 'setSystem|setUser' src` shows each call before `schedule()`.

## SWT UI thread ownership

**Definition.** The UI thread is the thread that created the `Display`.
SWT throws `SWTException` for widget calls from any other thread
([SWT threading][swt]).

**Use when.**

- Always: every widget read and write happens on the UI thread.

**Do not use when.**

- The API documents that any thread may call it, as `Display.asyncExec`,
  `syncExec`, and `wake` do. Call workbench, JFace, or SWT API from other
  threads only when "the API specifically allows call-in from a background
  thread" ([SWT
  threading][swt]).

**Example.** From `TodoViewIT.widgetAccessOffTheUiThreadFails`:

```java
Thread worker = new Thread(() -> shell.setText("from worker"));
```

**Cost removed.** Crashes and native lockups from cross-thread widget
access. Executed: the call threw `SWTException: Invalid thread access`.

**Verify.**

1. `TodoViewIT.widgetAccessOffTheUiThreadFails` (Executed).

## Display.asyncExec with a disposed check

**Definition.** `display.asyncExec(runnable)` queues the runnable for
the UI thread and returns at once. Widgets "may have been disposed" by
the time it runs, so the runnable must check ([Display][display]).
Eclipse 4 code can inject `UISynchronize`, which offers the same
`asyncExec`.

**Use when.**

- A job or listener on a background thread must update widgets.

**Do not use when.**

- The caller needs the result before continuing: use `syncExec`.
- The runnable does slow work: it blocks the UI thread while it runs.

**Example.** From `TodoView`:

```java
sync.asyncExec(() -> {
    if (!label.isDisposed()) {
        refresh();
    }
});
```

**Cost removed.** `SWTException: Widget is disposed` from late
updates. Executed (`TodoViewIT.disposedWidgetRejectsLateUpdates`):
`setText` on a disposed label threw exactly that.

**Verify.**

1. `TodoViewIT` passes (Executed): the view shows `2 TODO marker(s)`
   after a background scan, and the disposed case throws.

## Display.syncExec

**Definition.** `display.syncExec(runnable)` runs the runnable on the
UI thread and blocks the caller until it finishes ([SWT
threading][swt]).

**Use when.**

- A background thread must have a value only the UI thread can read (a
  widget size, a dialog answer) before it continues.

**Do not use when.**

- The caller holds a lock or scheduling rule that UI code may need: the
  UI thread waits for the lock while the caller waits for the UI thread.
- The UI thread may be waiting for this job (`join` on the UI thread):
  deadlock.
- A fire-and-forget update is enough: use `asyncExec`.

**Example.**

```java
Point[] size = new Point[1];
display.syncExec(() -> size[0] = shell.getSize());
```

**Cost removed.** Races from reading widget state off the UI thread.
Tier: not in the example tests.

**Verify.**

1. Take a thread dump (`jcmd <pid> Thread.print`) during the operation:
   no worker may be blocked in `syncExec` while the UI thread waits for
   it.

[jobs]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_jobs.htm
[rules]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_jobs_rules.htm
[progress]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_jobs_progress.htm
[batch]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/resAdv_batching.htm
[swt]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/swt_threading.htm
[job-api]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/jobs/Job.html
[submon]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/SubMonitor.html
[rulefactory]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/resources/IResourceRuleFactory.html
[display]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/swt/widgets/Display.html
[worker]: https://github.com/eclipse-platform/eclipse.platform/blob/cf70d8b4698e3246254c8fed687562c84b5dbfeb/runtime/bundles/org.eclipse.core.jobs/src/org/eclipse/core/internal/jobs/Worker.java
[toc-split]: #submonitor-split-and-cancellation
[toc-async]: #displayasyncexec-with-a-disposed-check
