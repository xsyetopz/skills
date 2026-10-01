# IntelliJ Platform plugins

Gotchas for `plugin.xml`, threading, services, and the Gradle build. Run
`python3 scripts/check_intellij_plugin_xml.py --src-root src/main/kotlin
--src-root src/main/java src/main/resources/META-INF/plugin.xml` before
editing, and again with `--patched` on
`build/tmp/patchPluginXml/plugin.xml` after the build.

## Contents

- [Threading](#threading)
- [Actions](#actions)
- [Services and state](#services-and-state)
- [plugin.xml](#pluginxml)
- [Build, test, and release](#build-test-and-release)
- [Sources](#sources)

## Threading

- Mistake: file, PSI, index, network, or process work on the EDT or in
  `AnAction.update()`. Fix: run it on a background thread with a read
  action; the platform reports `SlowOperations` violations and freezes
  otherwise. [threading model][threading]
- Mistake: reading PSI or VFS outside a read action. Fix: use
  `readAction {}` in coroutines, `ReadAction.nonBlocking` for cancellable
  Java work, or `ReadAction.computeBlocking` for a short synchronous read.
  `ReadAction.compute` and `run` are deprecated from branch 261 although
  the SDK threading page still shows them. [ReadAction.java][ra-261]
- Mistake: holding a `PsiElement`, `VirtualFile`, or `Document` across two
  read actions. Fix: re-check `isValid()` in each read action, or keep a
  `SmartPsiElementPointer`; otherwise `PsiInvalidElementAccessException`.
  [coroutine read actions][cra]
- Mistake: changing a document or PSI outside a command. Fix: use
  `writeCommandAction {}` (or `WriteCommandAction.runWriteCommandAction`
  on the EDT) so the change is one undo step. [documents][documents]
- Mistake: catching `ProcessCanceledException` or `CancellationException`
  without rethrowing, or throwing PCE yourself. Fix: rethrow; call
  `ProgressManager.checkCanceled()` in long loops.
- Mistake: `GlobalScope`, `Application.getCoroutineScope()`, or
  `Project.getCoroutineScope()`. Fix: inject a `CoroutineScope` into a
  service, or call `currentThreadCoroutineScope()` in `actionPerformed`,
  so work is cancelled when the plugin or project unloads.
  [scopes][scopes], [launching][launching]
- Mistake: `Dispatchers.Main`. Fix: `Dispatchers.EDT` from the platform
  (in 2025.1+ `Main` forbids read and write actions); use
  `Dispatchers.Default` for CPU and `Dispatchers.IO` for blocking I/O.
  [dispatchers][dispatchers]

## Actions

- Mistake: an `AnAction` without `getActionUpdateThread()`. Fix: return
  `ActionUpdateThread.BGT` when `update` reads only `AnActionEvent` data,
  `EDT` only when it must touch Swing. [action system][actions]
- Mistake: an `AnAction` or extension with fields, or a Kotlin `object`.
  Fix: stateless `class`; instances are created per registration and must
  unload cleanly. State belongs in services.
- Mistake: ids that do not start with the plugin id. Fix: prefix action
  and group ids (`com.acme.demo.Run`); the Verifier rejects others.
- Mistake: an action that works during indexing but is not `DumbAware`,
  or the reverse. Fix: implement `DumbAware` only when it needs no index.

## Services and state

- Mistake: heavy work or service lookups in a service constructor. Fix:
  keep constructors empty; the only injectable parameters are `Project`
  and `CoroutineScope`. [services][services]
- Mistake: storing a service, `Project`, PSI, `Document`, or `Editor` in
  a static or companion field. Fix: retrieve with
  `service<T>()` or `project.service<T>()` when needed; statics leak the
  project and block dynamic unload.
- Mistake: `PersistentStateComponent` state with non-serializable types
  or no default constructor. Fix: use `SerializablePersistentStateComponent`
  or a simple bean with defaults. [persisting state][persisting]
- Mistake: storing tokens or passwords in persistent state. Fix: use
  `PasswordSafe`. [sensitive data][sensitive]
- Mistake: a notification group used but not registered. Fix: declare
  `<notificationGroup id=... displayType="BALLOON"/>` in `plugin.xml`.
  [notifications][notifications]

## plugin.xml

- Mistake: using another plugin's classes with no dependency. Fix:
  add `<depends>` on the module or plugin id; otherwise
  `NoClassDefFoundError` at run time. For an optional integration, use
  `<depends optional="true" config-file="...">` and put the contributions
  in the config file. [dependencies][deps]
- Mistake: a wrong or invented `until-build`. Fix: build against the
  oldest supported IDE, and widen the range only after a Plugin Verifier
  run over it. `strict-until-build` (2025.3 and later) makes the upper
  bound enforced. [build ranges][ranges]
- Mistake: an extension registered in `plugin.xml` that has no class
  in the sources. Fix: run the checker with `--src-root`; it lists
  unresolved class names.
- Mistake: the plugin asks for a restart on install or update. Fix: meet
  the dynamic-plugin requirements (no components, an `id` on every
  `<group>`, every extension point used is dynamic, no service with
  `overrides="true"`).
  [dynamic plugins][dynamic]
- Mistake: a custom extension point that is not `dynamic="true"`. Fix:
  set it; all registered implementations must then unload cleanly.
  [extension points][eps]

## Build, test, and release

- Mistake: IntelliJ Platform Gradle Plugin 1.x configuration
  (`intellij {}` block). Fix: 2.x uses the `intellijPlatform {}`
  extension and `dependencies { intellijPlatform { intellijIdea("...") } }`
  with `defaultRepositories`. [Gradle plugin][ipgp]
- Mistake: tests fail with `NoClassDefFoundError` for JUnit or test
  framework classes. Fix: add `testFramework(TestFrameworkType.Platform)`
  and the JUnit dependency the platform test framework needs.
  [testing][testing], [fixtures][fixtures]
- Mistake: tests with `HeavyPlatformTestCase` or a full project for
  simple PSI behavior. Fix: `BasePlatformTestCase` light tests; cover
  invalid input, undo, and cancellation. [light tests][light]
- Mistake: stopping at `compileKotlin` or the checker and saying it
  loads. Fix: run `gradle test buildPlugin verifyPluginProjectConfiguration
  verifyPluginStructure verifyPlugin`, list the archive with `unzip -l`,
  and report which IDE versions the Verifier covered. Use `runIde` only
  for UI or reload checks tests cannot cover. [tasks][tasks]
- Mistake: signing keys or tokens in `build.gradle.kts`, or a
  `publishPlugin` run as a check. Fix: read them from environment
  variables, and publish only when the user asked. [signing][signing],
  [publishing][publishing]

## Sources

[actions]: https://plugins.jetbrains.com/docs/intellij/action-system.html
[cra]: https://plugins.jetbrains.com/docs/intellij/coroutine-read-actions.html
[deps]: https://plugins.jetbrains.com/docs/intellij/plugin-dependencies.html
[dispatchers]: https://plugins.jetbrains.com/docs/intellij/coroutine-dispatchers.html
[documents]: https://plugins.jetbrains.com/docs/intellij/documents.html
[dynamic]: https://plugins.jetbrains.com/docs/intellij/dynamic-plugins.html
[eps]: https://plugins.jetbrains.com/docs/intellij/plugin-extension-points.html
[fixtures]: https://plugins.jetbrains.com/docs/intellij/tests-and-fixtures.html
[ipgp]: https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin.html
[launching]: https://plugins.jetbrains.com/docs/intellij/launching-coroutines.html
[light]: https://plugins.jetbrains.com/docs/intellij/light-and-heavy-tests.html
[notifications]: https://plugins.jetbrains.com/docs/intellij/notification-balloons.html
[persisting]: https://plugins.jetbrains.com/docs/intellij/persisting-state-of-components.html
[publishing]: https://plugins.jetbrains.com/docs/intellij/publishing-plugin.html
[ra-261]: https://github.com/JetBrains/intellij-community/blob/261/platform/core-api/src/com/intellij/openapi/application/ReadAction.java
[ranges]: https://plugins.jetbrains.com/docs/intellij/build-number-ranges.html
[scopes]: https://plugins.jetbrains.com/docs/intellij/coroutine-scopes.html
[sensitive]: https://plugins.jetbrains.com/docs/intellij/persisting-sensitive-data.html
[services]: https://plugins.jetbrains.com/docs/intellij/plugin-services.html
[signing]: https://plugins.jetbrains.com/docs/intellij/plugin-signing.html
[tasks]: https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-tasks.html
[testing]: https://plugins.jetbrains.com/docs/intellij/testing-plugins.html
[threading]: https://plugins.jetbrains.com/docs/intellij/threading-model.html
