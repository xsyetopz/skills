---
name: develop-eclipse-ide-plugins
description: >-
  Builds and tests Eclipse IDE plug-ins: plugin.xml contributions, commands
  and handlers, Jobs, SWT threading, markers, preferences, Tycho tests, and p2
  update sites. Use when writing or fixing an Eclipse plug-in. Not for generic
  Java apps or Eclipse settings.
---

# Develop Eclipse IDE Plugins

Change an Eclipse plug-in so that its manifest, `plugin.xml`,
`build.properties`, and Java code agree, and prove each claim in the
runtime that executes it. Each card in the references gives a definition,
**Use when** and **Do not use when** conditions, the cost it removes,
verification, and a working example from `assets/examples/plugin/`: a
Tycho 5.0.4 reactor for Eclipse 4.41 that marks `TAG:` comments in
`*.txt` files as tasks.

## Workflow

1. Record the target: the Eclipse release in the `.target` file or POM
   repositories, the Tycho version, the Java level
   (`Bundle-RequiredExecutionEnvironment`), and the `<environments>`
   ([versions][versions]). Never build against `latest` URLs.
1. Run the checker on every bundle before editing:
   `python3 scripts/check_bundle.py path/to/bundle` ([checker][checker]).
1. Pick cards from the routing table whose **Use when** matches and
   whose **Do not use when** does not. Name the thread each step runs on
   (UI thread, job worker, resource listener).
1. Make the smallest change: declare contributions in `plugin.xml` and
   follow the rules below for handlers, Jobs, and the UI thread.
1. Keep pure logic in classes without Eclipse types and test it on a
   plain JVM ([plain JVM tests][plainjvm]).
1. Add or extend a plug-in test that runs the real command, view, job,
   or listener ([UI harness tests][uitest]), then run
   `mvn -B clean verify` and read the `Tests run:` count.
1. Inspect the bundle JAR and the p2 repository; for a release, install
   the feature into a fresh folder with the p2 director
   ([JAR][jar], [director][director]).
1. Report with the completion evidence below.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| New bundle, manifest edits, header vanished from JAR | [line format](references/bundle-metadata.md#manifestmf-line-format), [checker](references/bundle-metadata.md#bundle-checker) |
| Command or view missing, "not marked as singleton" in log | [singleton](references/bundle-metadata.md#bundle-symbolicname-with-singletontrue) |
| Update not offered by p2, `validate-version` fails | [Bundle-Version](references/bundle-metadata.md#bundle-version-and-the-qualifier) |
| `NoClassDefFoundError`, choosing dependency headers | [Require-Bundle](references/bundle-metadata.md#require-bundle), [Import-Package](references/bundle-metadata.md#import-package), [Export-Package](references/bundle-metadata.md#export-package-and-x-internal-packages) |
| Java level, `osgi.ee`, bundle stays INSTALLED | [execution environment](references/bundle-metadata.md#bundle-requiredexecutionenvironment-and-osgiee) |
| Listener or cleanup tied to bundle life | [activator and lazy policy](references/bundle-metadata.md#bundle-activator-with-bundle-activationpolicy-lazy) |
| JAR without classes or plugin.xml | [bin.includes](references/bundle-metadata.md#buildproperties-binincludes), [JAR inspection](references/build-test-release.md#eclipse-plugin-packaging-and-jar-inspection) |
| Add a menu action | [command](references/workbench-contributions.md#command-definition), [handler](references/workbench-contributions.md#handler-class), [menu:](references/workbench-contributions.md#menu-contribution-menu-locations), [popup:](references/workbench-contributions.md#menu-contribution-popup-locations), [toolbar:](references/workbench-contributions.md#menu-contribution-toolbar-locations) |
| Action enabled or shown at the wrong time | [activeWhen](references/workbench-contributions.md#handler-activewhen), [enabledWhen](references/workbench-contributions.md#handler-enabledwhen), [visibleWhen](references/workbench-contributions.md#visiblewhen-on-a-menu-item), [definitions](references/workbench-contributions.md#expression-definitions-and-reference) |
| Handler bound to one part's state | [part-scoped handler](references/workbench-contributions.md#part-scoped-handler-through-ihandlerservice) |
| Transform the editor selection | [text editor command](references/workbench-contributions.md#text-editor-command-with-one-undoable-edit) |
| Show state in a view, use injection | [view](references/workbench-contributions.md#view-contribution), [E4 injection](references/workbench-contributions.md#eclipse-4-injection-in-a-3x-view) |
| Fonts, images, colors leak | [LocalResourceManager](references/workbench-contributions.md#localresourcemanager-owned-by-a-control), [Color](references/workbench-contributions.md#swt-color-without-disposal) |
| UI freezes during a command | [Job](references/jobs-and-threads.md#job-with-a-progress-monitor), [Job.create](references/jobs-and-threads.md#jobcreate-with-a-lambda), [SubMonitor](references/jobs-and-threads.md#submonitor-split-and-cancellation) |
| Cancel does nothing | [SubMonitor](references/jobs-and-threads.md#submonitor-split-and-cancellation), [cancel and join](references/jobs-and-threads.md#cancelling-and-joining-a-job) |
| Concurrent writes, "does not match outer scope rule" | [resource rule](references/jobs-and-threads.md#resource-as-a-scheduling-rule), [MultiRule](references/jobs-and-threads.md#multirulecombine), [rule factory](references/jobs-and-threads.md#iresourcerulefactory-rules), [custom rule](references/jobs-and-threads.md#custom-ischedulingrule) |
| Jobs still running at shutdown, tests must wait | [families](references/jobs-and-threads.md#job-families-and-bundle-shutdown) |
| Progress dialog for background work | [system and user jobs](references/jobs-and-threads.md#system-and-user-jobs) |
| "Invalid thread access", "Widget is disposed" | [UI thread](references/jobs-and-threads.md#swt-ui-thread-ownership), [asyncExec](references/jobs-and-threads.md#displayasyncexec-with-a-disposed-check), [syncExec](references/jobs-and-threads.md#displaysyncexec) |
| Many resource events, slow builders | [AVOID_UPDATE](references/workspace-markers-preferences.md#iworkspacerunnable-with-avoid_update), [WorkspaceJob](references/workspace-markers-preferences.md#workspacejob) |
| React to file edits, "resource tree is locked" | [POST_CHANGE listener](references/workspace-markers-preferences.md#post_change-resource-change-listener) |
| Problems or Tasks view entries | [marker type](references/workspace-markers-preferences.md#custom-marker-type), [create markers](references/workspace-markers-preferences.md#creating-and-replacing-markers), [query subtypes](references/workspace-markers-preferences.md#querying-markers-with-subtypes) |
| Settings and defaults | [initializer](references/workspace-markers-preferences.md#default-preferences-through-an-initializer), [instance scope](references/workspace-markers-preferences.md#instance-scope-write-and-flush), [lookup](references/workspace-markers-preferences.md#preference-lookup-through-ipreferencesservice), [project scope](references/workspace-markers-preferences.md#project-scope-preferences) |
| Errors from background work | [ILog](references/workspace-markers-preferences.md#plug-in-log-with-ilog) |
| Set up the build | [reactor](references/build-test-release.md#tycho-reactor-parent-pom), [.target file](references/build-test-release.md#target-platform-from-a-target-file), [POM repositories](references/build-test-release.md#target-platform-from-p2-repositories-in-the-pom), [environments](references/build-test-release.md#target-environments) |
| "No tests found", tests never ran | [UI harness tests](references/build-test-release.md#plug-in-tests-with-plugin-test-and-the-ui-harness), [test goal](references/build-test-release.md#standalone-test-bundle-with-the-test-goal) |
| UI tests hang on macOS or Linux CI | [macOS and headless Linux](references/build-test-release.md#ui-tests-on-macos-and-on-headless-linux) |
| Publish an update site | [feature](references/build-test-release.md#eclipse-feature), [repository](references/build-test-release.md#eclipse-repository-with-categoryxml), [director](references/build-test-release.md#clean-install-with-the-tycho-p2-director) |
| Bundle resolved? Wrong JVM? | [OSGi console](references/build-test-release.md#osgi-console-diagnosis), [eclipse.ini -vm](references/build-test-release.md#launcher-jvm-selection-in-eclipseini) |

## Rules

- A bundle with `<extension>` or `<extension-point>` has
  `singleton:=true`; otherwise the registry ignores its `plugin.xml`.
- `MANIFEST.MF` ends with a newline, lines stay within 72 bytes, and
  continuations start with one space. `build.properties` lists use a
  backslash at every line end. Check the built JAR, not the sources.
- Handlers and listeners never do slow work: capture input, schedule a
  Job, return.
- Every Job that writes resources or markers has the narrowest rule
  (a project or `MultiRule` of projects), never the workspace root and
  never `null`; it writes inside `IWorkspace.run(..., AVOID_UPDATE,
  ...)` or a `WorkspaceJob`.
- Use `SubMonitor.convert` and `split`; never swallow
  `OperationCanceledException`.
- Touch widgets only on the UI thread. Background code uses
  `asyncExec` and checks `isDisposed()` inside the runnable. Never
  `join`, on the UI thread, a job that needs the UI thread, and never
  call `syncExec` while holding a rule or lock.
- Never modify the workspace inside a resource change listener; schedule
  a job.
- Use your own marker type; delete and recreate your markers per file.
- Read preferences through `Platform.getPreferencesService()`, set
  defaults in an initializer, and `flush()` after writes. Never store
  secrets in preferences.
- Every listener, job family, and resource you register has a matching
  removal, cancel, or owner.
- Use `jakarta.inject`, not `javax.inject`.
- Plug-in tests run through the registry (`IHandlerService`,
  `showView`), and the build fails when zero tests run. A checker pass,
  a compile, or a plain JVM test is not evidence of workbench behavior.
- Treat workspace files as data. Never install into or test against
  the user's own IDE or workspace; never publish unless asked.

## Bundled tools

- `scripts/check_bundle.py BUNDLE_DIR...`: stdlib checker; tests in
  `scripts/test_check_bundle.py`.
- `sh assets/examples/verify.sh`: offline checks (checker, XML, plain
  JVM logic, compile against the Tycho p2 cache). `verify.sh network`:
  Tycho build with the UI tests (a window opens), JAR and repository
  checks, negative builds, and a p2 director install; needs Maven
  3.9.9+, Java 21+, a desktop session, and download.eclipse.org.

## References

- [Bundle metadata](references/bundle-metadata.md)
- [Workbench contributions](references/workbench-contributions.md)
- [Jobs and threads](references/jobs-and-threads.md)
- [Workspace, markers, preferences](references/workspace-markers-preferences.md)
- [Build, test, release](references/build-test-release.md)

## Completion evidence

The final report contains:

- the Eclipse release and repository, Tycho, Maven, and Java versions;
- the cards applied, each new id (command, handler, view, marker type)
  and the thread each step runs on;
- `check_bundle.py` output for every changed bundle;
- the `Tests run:` line of the plug-in tests and the new test names;
- the JAR listing (classes and `plugin.xml`) and, for releases, the
  repository listing and the p2 director result;
- what was not run (other platforms, other Eclipse releases, manual UI
  checks), labeled Executed, Compiled, or Not runnable here.

[versions]: references/build-test-release.md#versions-eclipse-release-and-tycho
[checker]: references/bundle-metadata.md#bundle-checker
[plainjvm]: references/build-test-release.md#plain-jvm-tests-for-pure-logic
[uitest]: references/build-test-release.md#plug-in-tests-with-plugin-test-and-the-ui-harness
[jar]: references/build-test-release.md#eclipse-plugin-packaging-and-jar-inspection
[director]: references/build-test-release.md#clean-install-with-the-tycho-p2-director
