# Services, persisted state, settings, notifications

Cards for services (light and registered, application and project
level), the injected coroutine scope, `PersistentStateComponent`
variants, the settings `Configurable`, and notification groups. Excerpts
come from `assets/examples/plugin/src/main/{kotlin,java}/org/acme/wordstats/`.

Tier: Executed unless a card says otherwise. The light tests in
`WordStatsTest.kt` and `NotificationAndActionTest.kt` ran through
`sh assets/examples/verify.sh network` on this machine: macOS arm64,
IntelliJ IDEA OSS 2026.2.2 (262.10315.125), IntelliJ Platform Gradle
Plugin 2.19.0, Kotlin 2.4.0, JBR 25.0.4.

## Contents

- Light application service
- Light project service
- Registered service with an interface
- Service constructor and retrieval rules
- Coroutine scope injected into a service
- SerializablePersistentStateComponent
- SimplePersistentStateComponent
- Java PersistentStateComponent
- Settings page: BoundConfigurable with Kotlin UI DSL
- Notification group: BALLOON
- Notification group: STICKY_BALLOON suggestion

## Light application service

**Definition.** A final class annotated `@Service` (level `APP` by
default), created on the first `service<T>()` call, once per
application, with no `plugin.xml` entry ([services]). If it implements
`Disposable`, it is disposed with the application or on plugin unload.

**Use when.**

- One instance serves the whole IDE: global settings, caches keyed by
  something other than a project.
- The service is not API for other plugins and tests need no
  replacement.

**Do not use when.**

- Other plugins must override it, or it needs `os`, `client`,
  `overrides`, or a test/headless implementation. Light services forbid
  these attributes ([services]); register it instead.
- The data belongs to one project. Application state would mix projects
  and keep closed projects reachable.
- It is a `PersistentStateComponent` with roaming. A light application
  PSC must set `roamingType = RoamingType.DISABLED` ([services]).

**Example.**

```kotlin
@Service
@State(
    name = "WordStatsSettings",
    storages = [
        Storage("wordStats.xml", roamingType = RoamingType.DISABLED),
    ],
)
class WordStatsSettings :
    SerializablePersistentStateComponent<WordStatsSettings.State>(State())
```

Runnable: `WordStatsSettings.kt`; retrieval: `service<WordStatsSettings>()`.

**Cost removed.** `plugin.xml` registration lines and their class-name
typos (`check_plugin_xml.py` counts unresolved class names).

**Verify.**

1. `WordStatsTest.testSerializableStateTracksModifications` obtains the
   service with `service<WordStatsSettings>()`.
1. DevKit inspections "Light service must be final" and "A service can
   be converted to a light one" ([services]). Not run (no IDE UI).

## Light project service

**Definition.** `@Service(Service.Level.PROJECT)` creates one instance
per open `Project`. The constructor may take `Project` and a
`CoroutineScope` ([services], [coroutine scopes][scopes]).

**Use when.**

- State or work belongs to one project: per-project caches, background
  jobs for that project.

**Do not use when.**

- The class would be module-level. The docs advise against module
  services because they raise memory use ([services]).
- Caching the instance in a static field or companion. It outlives the
  project and leaks it.

**Example.**

```kotlin
@Service(Service.Level.PROJECT)
class WordStatsService(
    private val project: Project,
    private val cs: CoroutineScope,
) : Disposable {
    fun countInBackground(file: VirtualFile): Job = cs.launch {
        val count = countWords(file) ?: return@launch
        project.service<ProjectWordStats>().record(file.url, count)
        project.service<WordStatsReporter>().report(file.name, count)
    }
    // ...
}
```

Runnable: `WordStatsService.kt`.

**Cost removed.** Project leaks: the platform disposes the instance and
cancels its scope when the project closes. Expected: after project
close, a heap dump has no `WordStatsService` instance (for the unload
leak check on `PluginClassLoader` references, see the dynamic plugin
card in [plugin.xml](descriptor.md)). Not checked.

**Verify.**

1. `WordStatsTest.testServiceScopeCountsAndTestReporterRecords`.
1. `gradle verifyPlugin`: "Compatible" (this run).

## Registered service with an interface

**Definition.** `<applicationService>` or `<projectService>` in
`<extensions defaultExtensionNs="com.intellij">` registers
`serviceImplementation`, optionally behind `serviceInterface`, and can
declare `testServiceImplementation`, `headlessImplementation`, and `os`
([services]).

**Use when.**

- Other plugins call the service as API, or tests need a replacement
  implementation.

**Do not use when.**

- Neither applies. Use a light service; DevKit flags convertible
  registrations ([services]).
- Setting `overrides="true"`. It blocks dynamic unloading ([dynamic]).

**Example.**

```xml
<projectService
    serviceInterface="org.acme.wordstats.WordStatsReporter"
    serviceImplementation="org.acme.wordstats.NotificationReporter"
    testServiceImplementation="org.acme.wordstats.RecordingReporter"/>
```

```kotlin
interface WordStatsReporter {
    fun report(fileName: String, count: Int)
}

class RecordingReporter : WordStatsReporter {
    val reports: MutableList<Pair<String, Int>> = CopyOnWriteArrayList()

    override fun report(fileName: String, count: Int) {
        reports += fileName to count
    }
}
```

Runnable: `WordStatsReporter.kt`.

**Cost removed.** Mocking frameworks in tests. In light tests,
`project.service<WordStatsReporter>()` returns `RecordingReporter`
automatically, and the `assertInstanceOf(reporter,
RecordingReporter::class.java)` assertion passes.

**Verify.**

1. `WordStatsTest.testServiceScopeCountsAndTestReporterRecords` asserts
   `assertInstanceOf(reporter, RecordingReporter::class.java)`.
1. `check_plugin_xml.py --src-root ...`: all three class names resolve.

## Service constructor and retrieval rules

**Definition.** A service constructor takes at most `Project` (or
`Module`) and a `CoroutineScope`. Injecting other services through the
constructor is deprecated, and light services do not support it. Get
other services at the call site, never in the constructor or into
fields. Getting a service needs no read action and works on any thread;
concurrent first calls block until one thread finishes initialization
([services]).

**Use when.**

- Every service and extension class.

**Do not use when.**

- Heavy work in the constructor. It runs on the first caller's thread,
  possibly the EDT, and slows startup ([services]).
- Storing `service<T>()` results in `static`/companion fields. The docs
  warn of "unexpected exceptions", and DevKit inspections flag it
  ([services]).

**Example.**

```kotlin
// Wrong: injected service, work in the constructor.
class Bad(project: Project, other: OtherService) {
    private val index = buildIndex(project)
}

// Right: store references only; resolve other services when used.
@Service(Service.Level.PROJECT)
class WordStatsService(
    private val project: Project,
    private val cs: CoroutineScope,
) : Disposable
```

Runnable: `WordStatsService.kt` (the "Right" form).

**Cost removed.** Startup time and initialization cycles; per the
documented service flow, a cycle throws `PluginException` ("Cyclic
Service Initialization") ([services]). Target: 0 DevKit inspection
findings.

**Verify.**

1. DevKit inspection "Non-default constructors for service and extension
   class" ([services]).
1. `rg -n 'init \{' src/main` inside `@Service` classes: expect no hits.

## Coroutine scope injected into a service

**Definition.** Since 2024.1, a service constructor may take a
`CoroutineScope` (`MyService(CoroutineScope)` or
`MyProjectService(Project, CoroutineScope)`). Each instance gets its own
scope with `Dispatchers.Default` and `CoroutineName(serviceClass)`,
cancelled when the application or project closes or the plugin unloads
([coroutine scopes][scopes], [launching coroutines][launching]).

**Use when.**

- Work must continue after the triggering UI event returns (background
  analysis, polling, deferred reports).

**Do not use when.**

- The work belongs to one `actionPerformed` call. Use
  `currentThreadCoroutineScope()` so the action system can cancel it
  ([launching]).
- Reaching for `Application.getCoroutineScope()`,
  `Project.getCoroutineScope()`, or `GlobalScope`. The docs call the
  first two deprecated leak sources (project or plugin class leaks)
  ([scopes]).

**Example.**

```kotlin
/** Counts off the EDT and reports; the caller returns at once. */
fun countInBackground(file: VirtualFile): Job = cs.launch {
    val count = countWords(file) ?: return@launch
    project.service<ProjectWordStats>().record(file.url, count)
    project.service<WordStatsReporter>().report(file.name, count)
}
```

Runnable: `WordStatsService.kt`.

**Cost removed.** Coroutines leaked past project close or plugin unload.
The scope is a supervisor, so a failed child does not cancel its
siblings ([scopes]). `rg` for `GlobalScope` and the deprecated scopes
returns 0 hits, and the test joins the returned `Job`.

**Verify.**

1. `WordStatsTest.testServiceScopeCountsAndTestReporterRecords` joins
   the returned `Job` with `timeoutRunBlocking` and asserts the report
   `"notes.txt" to 3`.
1. `rg -n 'GlobalScope|coroutineScope\.launch|application\.coroutineScope'
   src/main`: expect no hits.

## SerializablePersistentStateComponent

**Definition.** Since 2022.2, a Kotlin `PersistentStateComponent` that
holds an immutable data class. Writes go through
`updateState { it.copy(...) }`, which is atomic and counts modifications
(`PersistentStateComponentWithModificationTracker`) ([persisting]).
`@State(name, storages)` sets the XML root tag and file.

**Use when.**

- Kotlin settings with simple fields, read from several threads. It is
  the recommended Kotlin choice since 2022.2 ([persisting]).

**Do not use when.**

- The state holds secrets. Use `PasswordSafe`
  ([sensitive data][sensitive]).
- A field type is not a number, boolean, string, collection, map, or
  enum and has no `Converter` ([persisting]).
- An extension would persist state itself. Extensions cannot; put the
  state in a service ([persisting]).

**Example.**

```kotlin
var minLength: Int
    get() = state.minLength
    set(value) {
        updateState { it.copy(minLength = value) }
    }

data class State(
    @JvmField val minLength: Int = 1,
    @JvmField val notifyOnFinish: Boolean = true,
)
```

Runnable: `WordStatsSettings.kt`.

**Cost removed.** Lost updates from concurrent field writes, and
needless `getState()` calls at save time: the platform compares
`stateModificationCount` instead ([persisting]).

**Verify.**

1. `WordStatsTest.testSerializableStateTracksModifications`:
   `stateModificationCount` increases after the setter.
1. After `runIde`, read `wordStats.xml` in the sandbox `config/options`.
   Not executed (see the `runIde` card).

## SimplePersistentStateComponent

**Definition.** A Kotlin `PersistentStateComponent` over a mutable
`BaseState` subclass. Property delegates (`string()`, `property(0)`,
`list()`) record defaults and count modifications. In-place collection
changes may need `incrementModificationCount()` ([persisting]).

**Use when.**

- Mutable state is convenient (several fields updated together), such
  as project-level history kept in the workspace file with
  `@Storage(StoragePathMacros.WORKSPACE_FILE)`.

**Do not use when.**

- Threads share the state without a lock. Prefer the `Serializable`
  variant.
- A list is mutated in place and nothing calls
  `incrementModificationCount()`. The change may not be saved.

**Example.**

```kotlin
@Service(Service.Level.PROJECT)
@State(
    name = "WordStatsProject",
    storages = [Storage(StoragePathMacros.WORKSPACE_FILE)],
)
class ProjectWordStats :
    SimplePersistentStateComponent<ProjectWordStats.State>(State()) {

    class State : BaseState() {
        var lastFileUrl by string()
        var lastCount by property(0)
    }

    fun record(fileUrl: String, count: Int) {
        state.lastFileUrl = fileUrl
        state.lastCount = count
    }
}
```

Runnable: `ProjectWordStats.kt`.

**Cost removed.** Hand-written `getState`/`loadState` and default
handling: the class has no `getState`/`loadState` overrides, and the
test reads `state.lastCount`.

**Verify.**

1. `WordStatsTest.testServiceScopeCountsAndTestReporterRecords` asserts
   `state.lastCount == 3`.
1. The workspace file (`.idea/workspace.xml`) holds `WordStatsProject`
   after a save in `runIde`. Not executed.

## Java PersistentStateComponent

**Definition.** A Java service implements
`PersistentStateComponent<S>`: `getState()` returns the state object and
`loadState(S)` receives the deserialized one. Public fields and
annotated private fields are serialized; `S` needs a no-argument
constructor that yields the default state ([persisting]).

**Use when.**

- The plugin or class is Java. The docs recommend a separate state class
  ([persisting]).

**Do not use when.**

- The code is Kotlin. The base classes above track modifications for
  free.
- Fields hold PSI, `VirtualFile`, or `Project`. They are not
  serializable and leak.

**Example.**

```java
@Service
@State(
    name = "WordStatsRunLog",
    storages = @Storage(
        value = "wordStatsRunLog.xml",
        roamingType = RoamingType.DISABLED))
public final class LegacyRunLog
    implements PersistentStateComponent<LegacyRunLog.RunState> {

  public static final class RunState {
    public int runs;
    public List<String> recentFiles = new ArrayList<>();
  }

  private RunState state = new RunState();

  @Override
  public @NotNull RunState getState() {
    return state;
  }

  @Override
  public void loadState(@NotNull RunState loaded) {
    state = loaded;
  }
}
```

Runnable: `LegacyRunLog.java`.

**Cost removed.** Custom file I/O for settings; the platform owns load,
save, and roaming. The settings class has no `java.io`/`java.nio.file`
calls.

**Verify.**

1. `WordStatsTest.testJavaStateComponentKeepsFiveRecentFiles`.
1. `javac -Xlint:all -Werror` in `verify.sh offline`: no warnings.

## Settings page: BoundConfigurable with Kotlin UI DSL

**Definition.** `<applicationConfigurable>` (or `<projectConfigurable>`)
adds a Settings page. `parentId`, `id`, and `displayName` (or
`key`/`bundle`) are declared in XML, so the class loads only when the
user opens the page ([settings]). `BoundConfigurable` builds the page
with Kotlin UI DSL `panel { }`, whose `bind*` calls implement `apply()`,
`reset()`, and `isModified()` ([UI DSL][uidsl]).

**Use when.**

- User-editable settings backed by a persisted service.

**Do not use when.**

- The page builds Swing components or works in the constructor. The
  platform may create it on a background thread ([settings]).
- `parentId` is omitted or `other`. The page lands in a deprecated
  group; use `tools` for third-party settings ([settings]).
- The UI is a tool window with action controls. The docs say Kotlin UI
  DSL is not meant for that ([uidsl]).

**Example.**

```xml
<applicationConfigurable
    parentId="tools"
    instance="org.acme.wordstats.WordStatsConfigurable"
    id="org.acme.wordstats.WordStatsConfigurable"
    displayName="Word Stats"/>
```

```kotlin
class WordStatsConfigurable : BoundConfigurable("Word Stats") {
    override fun createPanel(): DialogPanel {
        val settings = service<WordStatsSettings>()
        return panel {
            row("Minimum word length:") {
                intTextField(1..50).bindIntText(settings::minLength)
            }
            row {
                checkBox("Notify when counting finishes")
                    .bindSelected(settings::notifyOnFinish)
            }
        }
    }
}
```

Runnable: `WordStatsConfigurable.kt`, `plugin.xml`.

**Cost removed.** Hand-written `apply`/`reset`/`isModified` code, where
"modified" flags get stuck. The declared attributes build the Settings
tree without loading the class ([settings]).

**Verify.**

1. `WordStatsTest.testConfigurableBindsToSettings`: `isModified` is
   false after `reset()`, true after the setting changes, false after
   another `reset()`.
1. `runIde`, then Settings | Tools | Word Stats. Not executed.

## Notification group: BALLOON

**Definition.** `<notificationGroup id="..." displayType="BALLOON"/>`
declares a user-configurable channel. `NotificationGroupManager` returns
the group, and `createNotification(content, type).notify(project)` shows
a balloon that closes after 10 seconds and stays in the Notifications
tool window ([notifications]).

**Use when.**

- Reporting a finished background task or a state the user should see
  without a modal dialog.

**Do not use when.**

- The user must act before continuing. Use a dialog.
- The group id is not declared in `plugin.xml`. `getNotificationGroup`
  finds nothing.
- The content repeats on every keystroke-driven event. Users disable the
  group.

**Example.**

```xml
<notificationGroup id="Word Stats" displayType="BALLOON"/>
```

```kotlin
NotificationGroupManager.getInstance()
    .getNotificationGroup("Word Stats")
    .createNotification(
        "$fileName: $count words",
        NotificationType.INFORMATION,
    )
    .notify(project)
```

Runnable: `WordStatsReporter.kt`, `plugin.xml`.

**Cost removed.** Modal `Messages` dialogs that block the EDT and the
user: `rg -n 'Messages\.show' src/main` returns 0 hits for result
reporting.

**Verify.**

1. `NotificationAndActionTest.testBalloonGroupNotification` subscribes
   to `Notifications.TOPIC` on `project.messageBus` and asserts group id,
   content, and type. `notify(project)` publishes on the project bus, so
   an application-bus subscriber sees nothing (the test's first run
   failed that way).
1. Settings | Appearance & Behavior | Notifications lists "Word Stats" in
   `runIde`. Not executed.

## Notification group: STICKY_BALLOON suggestion

**Definition.** `displayType="STICKY_BALLOON"` keeps the balloon until
the user acts. `setSuggestionType(true)` marks it as a suggestion that
shows the primary action as a button.
`NotificationAction.createSimpleExpiring` dismisses the notification
when clicked ([notifications]).

**Use when.**

- Proposing a configuration change the user must decide on.

**Do not use when.**

- The message is purely informational. Use `BALLOON`.
- There are more than two actions. The rest go into a "More" menu
  ([notifications]).

**Example.**

```kotlin
NotificationGroupManager.getInstance()
    .getNotificationGroup("Word Stats Suggestions")
    .createNotification(
        "No words counted in $fileName",
        "The minimum word length may be too high.",
        NotificationType.WARNING,
    )
    .setSuggestionType(true)
    .addAction(
        NotificationAction.createSimpleExpiring("Open settings") {
            ShowSettingsUtil.getInstance().showSettingsDialog(
                project,
                WordStatsConfigurable::class.java,
            )
        },
    )
    .notify(project)
```

Runnable: `WordStatsReporter.kt`.

**Cost removed.** Suggestions that vanish after 10 seconds, before the
user reads them. The test sees `isSuggestionType` true.

**Verify.**

1. `NotificationAndActionTest.testZeroCountBecomesStickySuggestion`:
   group "Word Stats Suggestions", `isSuggestionType`, one action.
1. `check_plugin_xml.py`: both groups are declared once.

[services]: https://plugins.jetbrains.com/docs/intellij/plugin-services.html
[scopes]: https://plugins.jetbrains.com/docs/intellij/coroutine-scopes.html
[launching]: https://plugins.jetbrains.com/docs/intellij/launching-coroutines.html
[dynamic]: https://plugins.jetbrains.com/docs/intellij/dynamic-plugins.html
[persisting]: https://plugins.jetbrains.com/docs/intellij/persisting-state-of-components.html
[sensitive]: https://plugins.jetbrains.com/docs/intellij/persisting-sensitive-data.html
[settings]: https://plugins.jetbrains.com/docs/intellij/settings-guide.html
[uidsl]: https://plugins.jetbrains.com/docs/intellij/kotlin-ui-dsl-version-2.html
[notifications]: https://plugins.jetbrains.com/docs/intellij/notification-balloons.html
