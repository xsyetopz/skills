# plugin.xml: identity, dependencies, compatibility, extension points

Cards for the plugin descriptor. Every excerpt comes from
`assets/examples/plugin/src/main/resources/META-INF/plugin.xml` (plugin id
`org.acme.wordstats`, IntelliJ IDEA 2026.2, build branch 262).

Tier: per card. "Executed" means that on this machine (macOS arm64,
Gradle 9.7.1, IntelliJ Platform Gradle Plugin 2.19.0, local IntelliJ IDEA
OSS 2026.2.2 build 262.10315.125, JBR 25.0.4)
`sh assets/examples/verify.sh network` built the ZIP, loaded the
descriptor in 18 light tests, and ran `verifyPluginStructure` and
`verifyPlugin`, and `verify.sh offline` ran the checker and its 15
tests. Sources: SDK docs at commit `70e2ca2` of
[intellij-sdk-docs][sdk-repo].

## Contents

- Plugin identity: id, name, vendor
- Required depends on a module or plugin
- Optional depends with a config file
- since-build and the target platform
- until-build and open-ended compatibility
- strict-until-build
- Declaring an interface extension point
- Registering an extension
- Dynamic plugin requirements
- plugin.xml structural checker

## Plugin identity: id, name, vendor

**Definition.** `<id>` is the permanent identifier the IDE and JetBrains
Marketplace use; `<name>` is the Title Case display name; `<vendor>`
names the author, with optional `url` and `email`
([plugin.xml reference][config]). `<id>` defaults to `<name>` and the
Gradle `patchPluginXml` task can supply it; `<name>` and `<vendor>` are
required.

**Use when.**

- Creating a plugin, or adding the descriptor to a Gradle project that
  does not yet patch `<id>`.
- Prefixing action ids, extension point names, and optional config
  files, which all derive from the plugin id.

**Do not use when.**

- Changing it on a published plugin: "the value cannot be changed later
  after public release" ([config]). A new id is a new plugin.
- The id starts with `com.example`, `net.example`, `org.example`,
  `edu.example`, `com.intellij`, or `org.jetbrains`, or has a component
  such as `intellij` or `pycharm`. Plugin Verifier rejects it
  ([PluginIdVerifier.kt][pv-id]).

**Example.**

```xml
<idea-plugin>
  <id>org.acme.wordstats</id>
  <name>Word Stats Example</name>
  <vendor email="dev@example.com" url="https://example.com">Example</vendor>
  <description><![CDATA[
    Counts words in comments and plain text, encodes selections as form
    values, and shows the result in a notification.
  ]]></description>
</idea-plugin>
```

Runnable: `src/main/resources/META-INF/plugin.xml`.

Tier: Executed (both ids were built and verified).

**Cost removed.** One failed verification per bad id. Measured: with the
id `com.example.wordstats`, `verifyPlugin` failed with "The plugin ID
'com.example.wordstats' has a prefix 'com.example' that is not allowed",
and `verifyPluginStructure` printed the same problem; after the rename
both passed. `check_plugin_xml.py` reports it offline in under a second.

**Verify.**

1. `python3 scripts/check_plugin_xml.py --src-root src/main/kotlin
   src/main/resources/META-INF/plugin.xml`: 0 errors.
1. `gradle verifyPluginStructure verifyPlugin`: no
   `ForbiddenPluginIdPrefix` or `TemplateWordInPluginId` problem.

## Required depends on a module or plugin

**Definition.** `<depends>ID</depends>` names a platform module or
plugin whose classes this plugin uses; if it is absent, the IDE does not
load the plugin ([plugin.xml reference][config]). A plugin that uses
only general platform APIs declares `com.intellij.modules.platform`
([plugin dependencies][deps]).

**Use when.**

- The code imports another plugin's classes (such as
  `com.intellij.java` or `org.jetbrains.plugins.yaml`) on every code
  path.
- Always declare `com.intellij.modules.platform` when only platform APIs
  are used.

**Do not use when.**

- Only part of the functionality needs the other plugin. Use an optional
  dependency (next card); otherwise the whole plugin disappears where
  that plugin is missing.
- The dependency is a Maven library. Use Gradle `implementation(...)`,
  not `<depends>` ([deps]).

**Example.** A platform module needs only the descriptor entry. A plugin
dependency needs both the `<depends>` entry and a Gradle declaration
with the same ID; this example's JSON `bundledPlugin` pairs with the
optional `<depends>` of the next card. Without the descriptor entry, the
docs name `java.lang.NoClassDefFoundError` at run time as the symptom.

```xml
<depends>com.intellij.modules.platform</depends>
```

```kotlin
dependencies {
    intellijPlatform {
        bundledPlugin("com.intellij.modules.json")  // compile classpath
    }
}
```

Runnable: `plugin.xml`, `build.gradle.kts`.

Tier: Executed for `com.intellij.modules.platform` and the JSON
`bundledPlugin` (the build and tests use both). `printBundledPlugins`
was not run.

**Cost removed.** Runtime `NoClassDefFoundError`, and a plugin that
loads without the classes it calls. `verifyPlugin` reports unresolved
classes; `printBundledPlugins` lists bundled plugin ids ([tasks]).

**Verify.**

1. `gradle printBundledPlugins | grep <id>`: the id exists in the target
   IDE.
1. `gradle verifyPlugin`: "Compatible", with no unresolved-dependency or
   missing-class problems in `build/reports/pluginVerifier/`.

## Optional depends with a config file

**Definition.** `<depends optional="true" config-file="F.xml">ID</depends>`
loads the plugin even when `ID` is missing and loads the extra
descriptor `F.xml` only when `ID` is present. `config-file` is required
with `optional="true"`, and the file must be named
`<pluginId>-<name>.xml` ([plugin dependencies][deps]).

**Use when.**

- One feature needs another plugin's classes (here `JsonFile` from the
  JSON plugin) and the rest must work without it.

**Do not use when.**

- Every feature needs the dependency. Declare it required.
- Registering classes that reference the optional plugin in the main
  `plugin.xml`. They fail to load where it is absent; register them only
  in the config file.

**Example.**

```xml
<depends optional="true"
         config-file="org.acme.wordstats-withJson.xml">
  com.intellij.modules.json
</depends>
```

`org.acme.wordstats-withJson.xml`, next to `plugin.xml`:

```xml
<idea-plugin>
  <extensions defaultExtensionNs="org.acme.wordstats">
    <wordFilter implementation="org.acme.wordstats.JsonLiteralFilter"/>
  </extensions>
</idea-plugin>
```

Runnable: `JsonLiteralFilter.kt` (the only class importing
`com.intellij.json.psi.JsonFile`).

Tier: Executed (JSON present). The IDE-without-JSON case was not run.

**Cost removed.** A hard dependency that hides the whole plugin in IDEs
without JSON support. The config-file naming rule prevents classloader
problems in tests ([IDEA-205964][idea-205964]).

**Verify.**

1. `check_plugin_xml.py`: no "has no config-file" or "does not exist"
   error.
1. `NotificationAndActionTest.testOptionalDependencyRegisteredJsonFilter`:
   `JsonLiteralFilter` is among `wordFilters()` when JSON is present.

## since-build and the target platform

**Definition.** `<idea-version since-build="B"/>` is the lowest
compatible IDE build. A build number is `BRANCH.BUILD[.FIX]`; the branch
is the last two digits of the year plus the release number (`262` is
2026.2). `since-build` must be a real build number, without `.*` or a
product code ([build ranges][ranges]). With Gradle, set
`intellijPlatform.pluginConfiguration.ideaVersion.sinceBuild`; it
defaults to the target platform's major build ([extension]).

**Use when.**

- Choosing the oldest supported IDE. Compile against that version: the
  docs strongly recommend it, and it is required when the range spans
  different Java levels ([ranges]).
- Selecting the Java toolchain: 2024.2 through 2026.1 require Java 21,
  2026.2 requires Java 25 ([ranges]).

**Do not use when.**

- The value is made up or ends in `.*`. Plugin Verifier rejects it, and
  so does Marketplace ([ranges]).
- Following the docs table row that lists 2026.2 under branch 261. It is
  a docs error: the docs' own `v.list` tags 2026.2.3 as
  `idea/262.10968.63`, and the local 2026.2.2 install reports build
  `262.10315.125`.

**Example.** `gradle.properties` and the patched result:

```properties
platformVersion=2026.2.2
pluginSinceBuild=262
```

```xml
<idea-version since-build="262" />
```

Runnable: `gradle.properties`, `build.gradle.kts`.

Tier: Executed (`since-build="262"` patched and verified).

**Cost removed.** Installs on IDEs that lack the APIs the plugin calls.
`verifyPluginProjectConfiguration` reports a `sinceBuild` below the
target platform's major version ([tasks]).

**Verify.**

1. `gradle patchPluginXml`, then read
   `build/tmp/patchPluginXml/plugin.xml`: `since-build="262"`.
1. `gradle verifyPluginProjectConfiguration`: no warnings (none in this
   run).

## until-build and open-ended compatibility

**Definition.** `until-build` is the highest compatible build; `262.*`
covers every 2026.2.x. Omitted, the plugin claims every future build
([build ranges][ranges]). The docs recommend not setting it ([config]),
and `verifyPluginProjectConfiguration` says to remove it for 2024.3+
([tasks]). With Gradle plugin 2.19.0 the patched descriptor has no
`until-build` (observed); the extension docs still describe a `MAJOR.*`
default, which is out of date.

**Use when.**

- A known incompatibility with a later branch exists and no per-branch
  release is planned. Set the last good branch, `262.*`.

**Do not use when.**

- Nothing is known to break. An upper bound hides the plugin from newer
  IDEs, and Marketplace can set one later ([config]).
- The value is invented (`999.*`, or `263.*` before 2026.3 exists).
  Plugin Verifier flags it ([ranges]).

**Example.**

```kotlin
intellijPlatform {
    pluginConfiguration {
        ideaVersion {
            sinceBuild = "252"
            untilBuild = "262.*"         // or provider { null } to omit
        }
    }
}
```

Runnable: none (snippet only; see Tier).

Tier: Not executed. The example sets no `until-build`, and the snippet's
`252` to `262.*` range was not built or verified. Only the absence of
`until-build` in the patched descriptor was observed.

**Cost removed.** Stale compatibility caps, or silent breakage on new
branches. Check the `verifyPlugin` verdicts for the IDEs at both ends of
the declared range.

**Verify.**

1. The patched `plugin.xml` contains exactly the intended `until-build`.
1. `gradle verifyPlugin` with `pluginVerification.ides` covering both
   ends of the range (see [build, test, release](build-test-release.md)).

## strict-until-build

**Definition.** `strict-until-build` (since 2025.3) is an upper bound for
plugins that publish one release per major IDE version ([config]).

**Use when.**

- The release process uploads a new plugin version for every IDE major
  version, and each build must not install on the next major.

**Do not use when.**

- One build serves several majors. Skip it, as the docs say ([config]).
- `since-build` is below 253. The attribute exists only since 2025.3
  ([config]); how older IDEs treat it was not checked.

**Example.**

```xml
<idea-version since-build="262" strict-until-build="262.*"/>
```

Runnable: none (snippet only; see Tier).

Tier: Checker only. `test_strict_until_build_before_since_is_rejected`
covers the order check; no IDE build used the attribute.

**Cost removed.** A per-major build installing on the next major.

**Verify.**

1. `check_plugin_xml.py`: the format and order checks cover
   `strict-until-build`.
1. `gradle verifyPluginStructure`: no descriptor problem.

## Declaring an interface extension point

**Definition.** `<extensionPoint name="n" interface="I" dynamic="true"/>`
declares the point `<pluginId>.n`, where other plugins register classes
implementing `I`. `beanClass` declares a data point instead. Exactly one
of `interface` and `beanClass`, and one of `name` and `qualifiedName`,
is allowed. At run time an `ExtensionPointName` built with the full name
enumerates registrations ([extension points][eps]).

**Use when.**

- Other plugins (or optional parts of this one) must contribute behavior
  that this plugin calls.

**Do not use when.**

- Only this plugin implements the behavior. An interface plus a service
  is simpler.
- The point would be project- or module-level (`area`). The docs
  strongly recommend application-level points that take `Project` as a
  parameter ([config]).

**Example.**

```xml
<extensionPoints>
  <extensionPoint name="wordFilter"
                  interface="org.acme.wordstats.WordFilter"
                  dynamic="true"/>
</extensionPoints>
```

```kotlin
interface WordFilter {
    /** Returns false to drop [word] found in [file]. Runs under read. */
    fun accepts(word: String, file: PsiFile): Boolean
}

private val EP_NAME =
    ExtensionPointName<WordFilter>("org.acme.wordstats.wordFilter")

/** Enumerated on every call: nothing caches extension instances. */
internal fun wordFilters(): List<WordFilter> = EP_NAME.extensionList
```

Runnable: `WordFilter.kt`. The SDK page's bean example registers
`key`/`implementationClass` attributes on an `interface` point; do not
copy that mix.

Tier: Executed.

**Cost removed.** Hard-coded feature lists that other plugins cannot
extend, and restart-only unloads: a non-dynamic point blocks dynamic
unloading ([dynamic]). Check the checker's "is not dynamic" warning
count (0 here) and the Plugin Verifier's "Dynamic Plugin Eligibility"
section.

**Verify.**

1. `check_plugin_xml.py`: no "undeclared extension point" or "is not
   dynamic" finding.
1. `WordStatsTest.testExtensionPointListsRegisteredFilters`.

## Registering an extension

**Definition.** A child of `<extensions defaultExtensionNs="NS">` named
after a point registers one instance: `implementation` for an
`interface` point, the `@Attribute` properties for a bean point. Every
extension also accepts `id`, `order` (`first`, `last`,
`before id`, `after id`), and `os` ([plugin.xml reference][config]).

**Use when.**

- Contributing to a platform point (`com.intellij.*`) or another
  plugin's point (declare `<depends>` on that plugin).

**Do not use when.**

- The class keeps state, works in its constructor, runs static
  initializers, is a Kotlin `object`, or has a `companion object`. The
  docs forbid these for extensions ([extensions]); keep state in a
  service.
- The same class is also registered as a service ([extensions]).

**Example.**

```xml
<extensions defaultExtensionNs="org.acme.wordstats">
  <wordFilter implementation="org.acme.wordstats.MinLengthFilter"/>
</extensions>
```

```kotlin
/** Stateless extension: reads settings through the service each call. */
class MinLengthFilter : WordFilter {
    override fun accepts(word: String, file: PsiFile): Boolean =
        word.length >= service<WordStatsSettings>().minLength
}
```

Runnable: `plugin.xml`, `WordFilter.kt`.

Tier: Executed.

**Cost removed.** Stale state after a settings change and leaked
instances after unload; the filter reads the setting at call time.
`testExtensionFilterReadsSettings` changes the setting and sees the new
count without re-registering anything.

**Verify.**

1. `check_plugin_xml.py --src-root ...`: every `implementation` resolves
   to a source file.
1. `WordStatsTest.testExtensionFilterReadsSettings`: minimum length 5
   drops `be`; the count is 2.

## Dynamic plugin requirements

**Definition.** A dynamic plugin installs, updates, and uninstalls
without an IDE restart when: it has no components; every `<group>` has
an `id`; every extension point it uses is dynamic; configurables that
depend on points implement `Configurable.WithEpDependencies`; and no
service uses `overrides="true"` ([dynamic plugins][dynamic]). Loading
and unloading run on the EDT under a write action.

**Use when.**

- Every new plugin. Set `require-restart="true"` on `<idea-plugin>` only
  for real blockers, such as native libraries.

**Do not use when.**

- Code keeps PSI in objects that outlive unload (use
  `SmartPsiElementPointer`), uses `FileType`/`Language` as map keys (use
  the id string), or holds a service in a static field. Each leaks the
  plugin class loader, and the IDE then asks for a restart.

**Example.** A group with an id, a dynamic point, cleanup in a service:

```xml
<group id="org.acme.wordstats.Menu" text="Word Stats" popup="true">
  <add-to-group group-id="ToolsMenu" anchor="last"/>
</group>
```

```kotlin
@Service(Service.Level.PROJECT)
class WordStatsService(
    private val project: Project,
    private val cs: CoroutineScope,   // cancelled on plugin unload
) : Disposable {
    // expireWith(this) cancels pending non-blocking reads on dispose.
    override fun dispose() = Unit
}
```

Runnable: `plugin.xml`, `WordStatsService.kt`.

Tier: Partly executed. Plugin Verifier 1.410 reported "Plugin can
probably be enabled or disabled without IDE restart". No unload or
reload was performed, and `NOT_DYNAMIC` was not set as a failure level.

**Cost removed.** IDE restarts on install and update. To diagnose a
leak: run with `-XX:+UnlockDiagnosticVMOptions`, set the registry key
`ide.plugins.snapshot.on.unload.fail`, reload the plugin, and search the
`.hprof` for `PluginClassLoader` references ([dynamic]).

**Verify.**

1. `check_plugin_xml.py`: no `<group> without id` error or non-dynamic
   point warning.
1. `gradle verifyPlugin` with `failureLevel` including `NOT_DYNAMIC`
   ([extension]); in 2.19.0 do not combine it with
   `teamCityOutputFormat` ([release notes][ipgp-2190]). Not executed;
   the default failure levels were used.

## plugin.xml structural checker

**Definition.** `scripts/check_plugin_xml.py`, a standard-library Python
checker that runs without an IDE. It checks required elements, the id
rules, build-range formats and order, optional config files, extension
point declarations against their uses, and action and group ids. With
`--src-root`, it checks that registered class names in packages the
sources own (the first two package segments exist under a source root)
have a source file; other packages (platform, other plugins) are
skipped.

**Use when.**

- Before a Gradle build, in review, or in CI without the platform
  download.
- On the patched descriptor (`--patched --config-dir
  src/main/resources/META-INF build/tmp/patchPluginXml/plugin.xml`),
  where `<id>`, `<version>`, `<idea-version>`, and `<description>` must
  exist.

**Do not use when.**

- Replacing `verifyPluginStructure` or `verifyPlugin`. It does not check
  binary compatibility, platform extension point names, or bean
  attributes.

**Example.**

```text
$ python3 scripts/check_plugin_xml.py --src-root src/main/kotlin \
    --src-root src/main/java src/main/resources/META-INF/plugin.xml
WARN ...plugin.xml: missing <version> (must come from patchPluginXml)
WARN ...plugin.xml: missing <idea-version> (must come from patchPluginXml)
checked 1 descriptor(s): 0 error(s), 2 warning(s)
```

Runnable: `scripts/check_plugin_xml.py`.

Tier: Executed.

**Cost removed.** Descriptor mistakes found in seconds instead of by a
failed build, a failed Marketplace upload, or a runtime `ClassNotFound`.
Errors must be 0.

**Verify.**

1. `python3 scripts/test_check_plugin_xml.py`: 15 tests OK.
1. `sh assets/examples/verify.sh offline`: `PASS plugin.xml checker`.

[sdk-repo]: https://github.com/JetBrains/intellij-sdk-docs
[config]: https://plugins.jetbrains.com/docs/intellij/plugin-configuration-file.html
[deps]: https://plugins.jetbrains.com/docs/intellij/plugin-dependencies.html
[ranges]: https://plugins.jetbrains.com/docs/intellij/build-number-ranges.html
[eps]: https://plugins.jetbrains.com/docs/intellij/plugin-extension-points.html
[extensions]: https://plugins.jetbrains.com/docs/intellij/plugin-extensions.html
[dynamic]: https://plugins.jetbrains.com/docs/intellij/dynamic-plugins.html
[tasks]: https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-tasks.html
[extension]: https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-extension.html
[pv-id]: https://github.com/JetBrains/intellij-plugin-verifier/blob/master/intellij-plugin-structure/structure-intellij/src/main/java/com/jetbrains/plugin/structure/intellij/verifiers/PluginIdVerifier.kt
[ipgp-2190]: https://github.com/JetBrains/intellij-platform-gradle-plugin/releases/tag/2.19.0
[idea-205964]: https://youtrack.jetbrains.com/issue/IDEA-205964
