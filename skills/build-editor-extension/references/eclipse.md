# Eclipse IDE Plug-Ins

Gotchas for OSGi metadata, workbench contributions, Jobs, SWT threading, markers, preferences, and
Tycho builds. Run `python3 scripts/check_eclipse_bundle.py BUNDLE_DIR...` on each bundle
(`META-INF/MANIFEST.MF`, `build.properties`, `plugin.xml`); it reports rule IDs `M001` and up with
their sources.

## Contents

- [Bundle Metadata](#bundle-metadata)
- [Commands, Handlers, and Menus](#commands-handlers-and-menus)
- [Jobs and Threads](#jobs-and-threads)
- [Workspace, Markers, and Preferences](#workspace-markers-and-preferences)
- [Tycho Build and Tests](#tycho-build-and-tests)
- [Sources](#sources)

## Bundle Metadata

- Mistake: `<extension>` or `<extension-point>` in `plugin.xml` with a plain `Bundle-SymbolicName`.
  Fix: add `;singleton:=true`; otherwise the registry ignores the contributions (`M009`, a PDE
  error). [PDE manifest editor][pde-editor]
- Mistake: a `MANIFEST.MF` with no trailing newline. Fix: end the file with a newline;
  `java.util.jar.Manifest` silently drops the last header (`M002`). [JAR specification][jar]
- Mistake: lines over 72 bytes, or continuation lines starting with two spaces. Fix: wrap at 72
  bytes with one leading space; the extra space becomes part of the value (`M001`, `M004`). Count
  bytes in UTF-8, not characters.
- Mistake: a blank line inside the main manifest section. Fix: remove it; everything after ends up
  in a separate section (`M005`).
- Mistake: `build.properties` lists with a missing backslash at a line end. Fix: every continued
  line ends with `\`; check the built JAR, not the source tree, because a missing `bin.includes`
  entry drops `plugin.xml` or `META-INF` from the artifact.
- Mistake: `Bundle-Version` with a non-numeric micro or a qualifier in the wrong place. Fix:
  `major.minor.micro.qualifier`, numeric first three (`M008`). [OSGi module layer][osgi-module]
- Mistake: `Require-Bundle` for everything. Fix: prefer `Import-Package` for libraries;
  `Require-Bundle` only for UI bundles that need split packages or the extension registry.
- Mistake: `javax.inject` annotations. Fix: current Eclipse uses `jakarta.inject`. [API
  removals][removals]

## Commands, Handlers, and Menus

- Mistake: putting the work in `execute` of a handler. Fix: capture the input (selection, file),
  schedule a `Job`, and return; handlers run on the UI thread. [handlers][handlers]
- Mistake: an `activeWhen` or `enabledWhen` expression that evaluates the workspace. Fix: use core
  expressions on the selection or active part only; they run on every menu update.
  [expressions][expr]
- Mistake: a command with no handler in the target context. Fix: declare the handler with an
  `activeWhen` that matches where the menu shows, and test it through
  `IHandlerService.executeCommand`. [commands][cmd], [menus][menus]
- Mistake: `Display.getDefault()` during class loading of non-UI code. Fix: obtain the display only
  when running UI code. [SWT threading][swt]

## Jobs and Threads

- Mistake: slow work in handlers, listeners, or the activator. Fix: a `Job` (or `WorkspaceJob` when
  it writes resources). [jobs][jobs]
- Mistake: a Job that writes resources with no scheduling rule, the workspace root as its rule, or
  `null`. Fix: use the narrowest rule, from `IResourceRuleFactory` (a project, or a `MultiRule` of
  projects), and write inside `IWorkspace.run(..., IWorkspace.AVOID_UPDATE, ...)` or a
  `WorkspaceJob`. [rules][rules], [rule factory][rulefactory]
- Mistake: ignoring the monitor, or calling `convert` twice. Fix:
  `SubMonitor.convert(monitor, name, work)` once, `split()` per step, and never swallow
  `OperationCanceledException`. [SubMonitor][submon], [progress][progress]
- Mistake: touching widgets from a Job. Fix: `Display.asyncExec`, and check `widget.isDisposed()`
  inside the runnable. [SWT threading][swt]
- Mistake: `job.join()` on the UI thread for a job that uses the UI thread, or `syncExec` while
  holding a rule or lock. Fix: neither; both deadlock.
- Mistake: listeners, job families, and resources with no matching removal. Fix: pair each
  `addResourceChangeListener` with a remove in `stop`, cancel the job family, and dispose SWT
  `Color` and `Font` objects you create (use `LocalResourceManager`). [JFace resources][jface-res],
  [Color][color], [LRM][lrm]

## Workspace, Markers, and Preferences

- Mistake: modifying the workspace inside an `IResourceChangeListener`. Fix: the workspace is locked
  against changes during notification; schedule a Job. [resource events][events]
- Mistake: many single-resource changes, each firing events. Fix: batch inside `IWorkspaceRunnable`
  with `AVOID_UPDATE`. [batching][batch]
- Mistake: `IMarker.PROBLEM` for your own findings. Fix: declare your own marker type in
  `plugin.xml` (`org.eclipse.core.resources.markers`, super type `problemmarker` or `textmarker`),
  delete and recreate your markers per file on each scan. [markers][markers]
- Mistake: reading preferences with `getPluginPreferences()` or `new InstanceScope()`. Fix:
  `Platform.getPreferencesService()` with the scope chain, defaults set in a
  `AbstractPreferenceInitializer`, and `flush()` after writes. [preferences][prefs],
  [InstanceScope][instancescope]
- Mistake: secrets in preferences. Fix: use secure storage (`SecurePreferencesFactory`). [secure
  storage][secure]
- Mistake: `System.err` or `printStackTrace` for errors. Fix: log through the bundle's `ILog`.
  [ILog][ilog]

## Tycho Build and Tests

- Mistake: testing workbench behavior in a plain JVM test. Fix: run plug-in tests with
  `tycho-surefire:test` so the OSGi registry and workbench exist, and drive commands through
  `IHandlerService` and views through `showView`. [Tycho testing][testing],
  [plugin-test][plugin-test]
- Mistake: a test bundle that Tycho reports as zero tests and passes. Fix: fail the build when no
  tests ran, and check the run log for the test count. [AbstractTestMojo][abstract-test]
- Mistake: testing against the user's own Eclipse or workspace. Fix: use the Tycho-provisioned
  target and a temporary workspace, and never install the plug-in into the everyday IDE.
- Mistake: a repository with no category file. Fix: add `category.xml` and verify the update site
  with the p2 director into an empty profile. [director mojo][director]
- Mistake: pinning target platform versions from memory. Fix: read them from the release you target,
  such as the SimRel repository. [simrel][simrel]
- Mistake: publishing as part of verification. Fix: stop at the local repository unless asked.

## Sources

[abstract-test]: https://github.com/eclipse-tycho/tycho/blob/tycho-5.0.4/tycho-surefire/tycho-surefire-plugin/src/main/java/org/eclipse/tycho/surefire/AbstractTestMojo.java
[batch]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/resAdv_batching.htm
[cmd]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/workbench_cmd.htm
[color]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/swt/graphics/Color.html
[director]: https://tycho.eclipseprojects.io/doc/5.0.4/tycho-p2-director-plugin/director-mojo.html
[events]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/resAdv_events.htm
[expr]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/workbench_cmd_expressions.htm
[handlers]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/workbench_cmd_handlers.htm
[ilog]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/ILog.html
[instancescope]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/preferences/InstanceScope.html
[jar]: https://docs.oracle.com/en/java/javase/25/docs/specs/jar/jar.html
[jface-res]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/jface_resources.htm
[jobs]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_jobs.htm
[lrm]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/jface/resource/LocalResourceManager.html
[markers]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/resAdv_markers.htm
[menus]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/workbench_cmd_menus.htm
[osgi-module]: https://docs.osgi.org/specification/osgi.core/8.0.0/framework.module.html
[pde-editor]: https://help.eclipse.org/latest/topic/org.eclipse.pde.doc.user/guide/tools/editors/manifest_editor/runtime.htm
[plugin-test]: https://tycho.eclipseprojects.io/doc/5.0.4/tycho-surefire-plugin/plugin-test-mojo.html
[prefs]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_preferences.htm
[progress]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_jobs_progress.htm
[removals]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/porting/removals.html
[rulefactory]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/resources/IResourceRuleFactory.html
[rules]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_jobs_rules.htm
[secure]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/equinox/security/storage/SecurePreferencesFactory.html
[simrel]: https://download.eclipse.org/releases/2026-09/
[submon]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/SubMonitor.html
[swt]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/swt_threading.htm
[testing]: https://tycho.eclipseprojects.io/doc/5.0.4/TestingBundles.html
