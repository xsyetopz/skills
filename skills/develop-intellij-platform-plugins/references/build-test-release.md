# Build, test, verify, sign, publish

Cards for the IntelliJ Platform Gradle Plugin 2.x and the release
pipeline. Build files: `assets/examples/plugin/build.gradle.kts`,
`settings.gradle.kts`, and `gradle.properties`.

Tier: Executed for `test`, `buildPlugin`,
`verifyPluginProjectConfiguration`, `verifyPluginStructure`,
`verifyPlugin`, `signPlugin`, and `verifyPluginSignature`, through
`sh assets/examples/verify.sh network` on this machine (macOS arm64,
Gradle 9.7.1, IntelliJ Platform Gradle Plugin 2.19.0, local IntelliJ
IDEA OSS 2026.2.2 build 262.10315.125 with JBR 25.0.4, Plugin Verifier
1.410). Durations come from this shared machine and are
machine-specific. For `runIde` and `publishPlugin`, see their cards.

## Contents

- IntelliJ Platform Gradle Plugin 2.x setup
- Platform dependency: intellijIdea(version)
- Platform dependency: local(path)
- Java toolchain and Kotlin version for the target
- Test framework dependencies
- Light test with BasePlatformTestCase
- runIde
- buildPlugin and archive inspection
- verifyPluginProjectConfiguration
- verifyPluginStructure
- verifyPlugin (Plugin Verifier)
- signPlugin and verifyPluginSignature
- publishPlugin

## IntelliJ Platform Gradle Plugin 2.x setup

**Definition.** Plugin id `org.jetbrains.intellij.platform`, current
release 2.19.0 (2026-09-14, [releases][ipgp-releases]). It requires
IntelliJ Platform 2023.3+, Gradle 9.0.0+, and Java 17+ to run Gradle
([Gradle plugin][ipgp]). It replaces the obsolete 1.x plugin
`org.jetbrains.intellij`; targeting 2024.2+ requires 2.x ([ranges]).
`intellijPlatform { defaultRepositories() }` supplies the repositories.

**Use when.**

- Any new plugin build, or a 1.x build that must target 2024.2+.
- Starting from the official template, which pins an older setup: at
  commit `7002f57` (2026-05-04) it uses settings plugin 2.16.0, Kotlin
  2.1.20, the Gradle 9.5.0 wrapper, and `intellijIdea("2025.2.6.2")`
  ([template][template]). Update those versions deliberately.

**Do not use when.**

- The repository has a working 1.x build targeting < 2024.2 and the task
  does not include migration. Keep its tooling.
- `settings.gradle.kts` sets `RepositoriesMode.FAIL_ON_PROJECT_REPOS`
  and the build also declares project repositories. Pick one place; for
  settings-level repositories use the settings plugin
  `org.jetbrains.intellij.platform.settings` ([ipgp]).

**Example.**

```kotlin
plugins {
    id("java")
    // Kotlin 2.4.0 is the stdlib bundled with IntelliJ Platform 2026.2.
    id("org.jetbrains.kotlin.jvm") version "2.4.0"
    id("org.jetbrains.intellij.platform") version "2.19.0"
}

repositories {
    mavenCentral()
    intellijPlatform {
        defaultRepositories()
    }
}
```

Runnable: `assets/examples/plugin/build.gradle.kts`.

**Cost removed.** Hand-managed IDE downloads, sandbox setup, and
descriptor patching. Measured: the first
`test buildPlugin verifyPluginProjectConfiguration verifyPluginStructure
verifyPlugin` run took 1 min 16 s, a later run 43 s.

**Verify.**

1. `gradle --version`: 9.0.0 or newer (here 9.7.1).
1. `gradle tasks --group "intellij platform"` lists `buildPlugin` and
   `runIde`. Since 2.19.0, verification tasks are in the group
   `intellij platform verification` ([release notes][ipgp-2190]).

## Platform dependency: intellijIdea(version)

**Definition.** `intellijIdea(version)` in
`dependencies { intellijPlatform { } }` resolves the IntelliJ IDEA
installer for the running OS; installers bundle JetBrains Runtime. EAP
builds need `useInstaller = false`, and non-installer archives have no
JBR ([Gradle plugin][ipgp]). From 2025.3 (build 253), IntelliJ IDEA is
one product type, `IntellijIdea` (`IU`); `IntellijIdeaCommunity` (`IC`)
and `intellijIdeaCommunity()` exist only for earlier versions ([types]).

**Use when.**

- CI and fresh machines, where the build must download a pinned target.
- The version is the plugin's oldest supported IDE ([ranges]).

**Do not use when.**

- The target is 2025.3+ and the code says `IC` or
  `intellijIdeaCommunity`. Resolution fails for those versions
  ([types]).
- A local IDE of the same version exists and the network is slow. Use
  `local()`.

**Example.**

```kotlin
dependencies {
    intellijPlatform {
        intellijIdea(providers.gradleProperty("platformVersion"))
        testFramework(TestFrameworkType.Platform)
    }
}
```

Runnable: `assets/examples/plugin/build.gradle.kts`.

Tier: Executed with `IDE=/nonexistent sh assets/examples/verify.sh
network`. The build downloaded `idea-2026.2.2-aarch64.dmg`
(1,517,171,147 bytes) into the Gradle cache. On the first run every
light test failed with "Cannot create extension (class=B.B.B.B.s)
[Plugin: com.intellij.modules.ultimate]" and "Cannot find suitable
constructor": the unified IU distribution ships the licensed Ultimate
module, and the test sandbox had an empty `disabled_plugins.txt`. The
fix in the example:

```kotlin
tasks.prepareTestSandbox {
    disabledPlugins.add("com.intellij.modules.ultimate")
}
```

The docs call `disabledPlugins` an internal field, and a
`subscriptionKey` re-enables the module ([extension]). After the fix
all 18 tests passed and Plugin Verifier reported
`IU-262.10315.125: Compatible` (82.5 s).

**Cost removed.** Builds that depend on whatever IDE a developer has
installed. The same version resolves on every machine, as `gradle
dependencies` shows.

**Verify.**

1. `IDE=/nonexistent sh assets/examples/verify.sh network`: `NETWORK
   PASSED` (this run).
1. `gradle printProductsReleases` lists valid versions ([tasks]).

## Platform dependency: local(path)

**Definition.** `local(path)` builds against an installed IDE
([Gradle plugin][ipgp]). The example reads the path from the Gradle
property `platformLocalPath`.

**Use when.**

- The target IDE is installed locally, as for this skill's verification
  (IntelliJ IDEA OSS 2026.2.2).

**Do not use when.**

- The build must be reproducible in CI; a local path differs per
  machine.
- The local product code misleads type selection. This OSS build reports
  `productCode` `IC` in `product-info.json` at 2026.2.2, although `IC`
  downloads exist only before 2025.3 ([types]). `local()` accepted it,
  and Plugin Verifier reported `IC-262.10315.125`.

**Example.**

```kotlin
val localIde = providers.gradleProperty("platformLocalPath")

dependencies {
    intellijPlatform {
        if (localIde.isPresent) {
            local(localIde)
        } else {
            intellijIdea(providers.gradleProperty("platformVersion"))
        }
        bundledPlugin("com.intellij.modules.json")
        testFramework(TestFrameworkType.Platform)
    }
}
```

Runnable: `assets/examples/plugin/build.gradle.kts`.

**Cost removed.** The installer download. Measured with `local()`: the
Gradle part of a `verify.sh network` run (compile, 12 tests at that
point, ZIP, verifier) took 1 min 16 s; a later run with 18 tests took
43 s.

**Verify.**

1. `gradle -PplatformLocalPath="/Applications/IntelliJ IDEA OSS.app"
   buildPlugin`: `BUILD SUCCESSFUL`.
1. The verifier line names the local build: `against IC-262.10315.125:
   Compatible`.

## Java toolchain and Kotlin version for the target

**Definition.** Each platform version requires a Java level: 2022.3 to
2024.1 need 17, 2024.2 to 2026.1 need 21, 2026.2 needs 25 ([ranges]).
The platform bundles the Kotlin stdlib (2.4.0 in 2026.2, 2.3.20 in
2026.1, 2.2.20 in 2025.3), so plugins must not bundle their own; set
`kotlin.stdlib.default.dependency=false` ([Kotlin][kotlin]).

**Use when.**

- Setting `kotlin { jvmToolchain(N) }` and the Kotlin Gradle plugin
  version for the oldest supported IDE.

**Do not use when.**

- The toolchain is newer than the oldest target's Java. Classes fail to
  load there (`UnsupportedClassVersionError`).
- Adding `kotlinx-coroutines` as a dependency. The platform provides it,
  and `verifyPluginProjectConfiguration` warns ([tasks]).

**Example.**

```kotlin
kotlin {
    jvmToolchain(25)
}
```

```properties
kotlin.stdlib.default.dependency=false
```

`/usr/libexec/java_home -V` found no registered JDK on this machine.
With a local IDE, `verify.sh` passes
`-Porg.gradle.java.installations.paths=<IDE>/Contents/jbr/Contents/Home`.
Without one, the toolchain still resolved (the Gradle daemon ran on
Homebrew OpenJDK 25.0.4, and no JDK 25 appeared in `~/.gradle/jdks`).
`settings.gradle.kts` applies
`org.gradle.toolchains.foojay-resolver-convention` 1.0.0, as the
official template does, so Gradle can download a JDK when none matches.

Runnable: `build.gradle.kts`, `gradle.properties`, `settings.gradle.kts`.

**Cost removed.** Runtime class-version errors, and a second,
conflicting stdlib in the plugin ZIP. The ZIP here holds only the plugin
jar and the searchable-options jar; `unzip -l` shows no
`kotlin-stdlib*.jar`.

**Verify.**

1. `gradle verifyPluginProjectConfiguration`: no output lines (this
   run).
1. `unzip -l build/distributions/*.zip`: no `kotlin-stdlib*.jar`.

## Test framework dependencies

**Definition.** Since 2024.2, test frameworks are declared explicitly;
`testFramework(TestFrameworkType.Platform)` provides
`BasePlatformTestCase` and the fixtures ([tests and fixtures][fixtures]).
Two documented workarounds: add `org.opentest4j:opentest4j`, which the
framework lacks (`NoClassDefFoundError: org/opentest4j/AssertionFailedError`,
IJPL-157292), and put JUnit 4 on the runtime classpath (`junit/
framework/TestCase` errors) ([FAQ][faq]).

**Use when.**

- Any light or heavy platform test. Add `TestFrameworkType.Plugin.Java`
  for Java PSI tests ([light and heavy tests][light]).

**Do not use when.**

- The test covers only pure logic. Run it without the platform (see
  `assets/examples/logic/WordTextCheck.kt`); it runs in seconds offline.

**Example.**

```kotlin
dependencies {
    intellijPlatform {
        testFramework(TestFrameworkType.Platform)
    }
    testImplementation("junit:junit:4.13.2")
    // Missing from the platform test framework (IJPL-157292).
    testImplementation("org.opentest4j:opentest4j:1.3.0")
}
```

Runnable: `assets/examples/plugin/build.gradle.kts`.

**Cost removed.** First-run `NoClassDefFoundError` failures in tests:
0 `NoClassDefFoundError` in `build/test-results`.

**Verify.**

1. `gradle test`: `TESTS ...: N run, 0 failed` for every class
   (`verify.sh network` prints the counts from the JUnit XML).
1. Delete the opentest4j line and rerun to see whether the target still
   needs it. Not tried.

## Light test with BasePlatformTestCase

**Definition.** `BasePlatformTestCase` (JUnit 3 style: methods named
`test*`) runs a real, headless platform and reuses one light project
across tests. `myFixture` (`CodeInsightTestFixture`) configures files
(`configureByText`, `<caret>` and `<selection>` markers), runs actions
(`performEditorAction(id)`, `testAction(action)`), and exposes
`editor`/`project` ([light and heavy tests][light]). Tests run on the
EDT.

**Use when.**

- Testing PSI, documents, actions, services, and settings against real
  platform implementations. The docs recommend light tests and no mocks
  ([testing]).

**Do not use when.**

- The test needs several modules. Use a heavy test
  (`HeavyPlatformTestCase`) ([light]).
- Calling a suspending API that switches to the EDT (such as
  `writeCommandAction`) inside `timeoutRunBlocking` on the EDT. It
  deadlocks; test the EDT variant, or pump events.
- Changing application-level state without a reset. It survives into
  the next light test; reset it in `tearDown`, as `WordStatsTest` does.

**Example.**

```kotlin
class WordStatsTest : BasePlatformTestCase() {
    fun testServiceScopeCountsAndTestReporterRecords() {
        val file = myFixture.configureByText("notes.txt", "one two three")
        val reporter = project.service<WordStatsReporter>()
        assertInstanceOf(reporter, RecordingReporter::class.java)
        timeoutRunBlocking {
            project.service<WordStatsService>()
                .countInBackground(file.virtualFile)
                .join()
        }
        assertContainsElements(
            (reporter as RecordingReporter).reports,
            "notes.txt" to 3,
        )
    }
}
```

`timeoutRunBlocking` is in `com.intellij.testFramework.common`. The
callback test pumps the EDT with
`PlatformTestUtil.dispatchAllInvocationEventsInIdeEventQueue()`.

Runnable: `src/test/kotlin/org/acme/wordstats/*.kt`.

**Cost removed.** Mocks that drift from platform behavior. Measured: 18
tests in 3 classes ran within a 43-second Gradle run.

**Verify.**

1. `gradle test`, then
   `build/test-results/test/TEST-*.xml`: `failures="0" errors="0"`.
1. `sh assets/examples/verify.sh network`: `TESTS ...` lines.

## runIde

**Definition.** `runIde` extends `JavaExec` and starts the target IDE
with the built plugin in a sandbox. Since 2.19.0 it logs
`IDE logs: <path to idea.log>` at the lifecycle level ([tasks],
[release notes][ipgp-2190]). Observed sandbox:
`.intellijPlatform/sandbox/word-stats/IC-2026.2.2/` in the project
directory, with `config_runIde`, `system_runIde`, and `log_runIde`; the
log is `log_runIde/idea.log`.

**Use when.**

- Manual checks of UI, menus, settings pages, notifications, and dynamic
  reload (Auto-Reload applies code changes to the running sandbox
  ([dynamic])).

**Do not use when.**

- Automated CI checks. Use `test`, or `testIdeUi` for UI tests.
- A shared or headless machine without a display session.

**Example.**

```text
$ RUNIDE_SECONDS=150 sh assets/examples/verify.sh runide
[org.jetbrains.intellij.platform] IDE logs: .../.intellijPlatform/sandbox/
  word-stats/IC-2026.2.2/log_runIde/idea.log
RUNIDE stopped after 25s (limit 150s)
RUNIDE PASSED: ... INFO - #c.i.p.i.b.AppStarter - Loaded custom plugins:
  Word Stats Example (0.1.0)
```

Runnable: `sh assets/examples/verify.sh runide`.

Tier: Executed (startup only). A GUI IDE window opened on this macOS
machine, and the script stopped it after the load line appeared. Menus,
settings, and notifications were not clicked through.

**Cost removed.** Development builds installed into the everyday IDE
profile. The sandbox under `.intellijPlatform/sandbox/` has its own
config, system, and plugins directories.

**Verify.**

1. `grep 'Loaded custom plugins:' <idea.log>` names "Word Stats
   Example (0.1.0)".
1. Tools | Word Stats menu and Settings | Tools | Word Stats appear.

## buildPlugin and archive inspection

**Definition.** `buildPlugin` zips the `prepareSandbox` output and the
searchable-options jar into `build/distributions/*.zip` ([tasks]). The
descriptor inside is the `patchPluginXml` output
(`build/tmp/patchPluginXml/plugin.xml`). The docs say `archiveBaseName`
defaults to the plugin name from `plugin.xml`, but with 2.19.0 the ZIP
was named after the Gradle project, `word-stats-0.1.0.zip`, not "Word
Stats Example".

**Use when.**

- Producing an artifact for manual install (Install Plugin from Disk), a
  custom repository, or the first Marketplace upload ([publishing]).

**Do not use when.**

- Repackaging libraries the platform provides (Kotlin stdlib,
  coroutines). 2.19.0 excludes them from sandbox runtime classpaths by
  default ([release notes][ipgp-2190]).

**Example.**

```text
$ unzip -l build/distributions/word-stats-0.1.0.zip
      705  word-stats/lib/word-stats-0.1.0-searchableOptions.jar
    45833  word-stats/lib/word-stats-0.1.0.jar
$ python3 scripts/check_plugin_xml.py --patched \
    --config-dir src/main/resources/META-INF \
    build/tmp/patchPluginXml/plugin.xml
checked 1 descriptor(s): 0 error(s), 0 warning(s)
```

The patched descriptor had `<idea-version since-build="262" />` and no
`until-build`.

Runnable: `sh assets/examples/verify.sh network`.

**Cost removed.** Shipping an archive nobody inspected. The ZIP here is
43,013 bytes with two jars.

**Verify.**

1. `unzip -l` lists only the expected jars.
1. The checker in `--patched` mode reports 0 errors.

## verifyPluginProjectConfiguration

**Definition.** Checks the project setup: `sinceBuild` not below the
platform major, `until-build` removed for 2024.3+, Java and Kotlin
levels aligned with `sinceBuild`, platform 2023.3+, no bundled Kotlin
stdlib, no explicit coroutines dependency, `.intellijPlatform` in
`.gitignore`, and a JBR runtime ([tasks]).

**Use when.**

- After changing any version: platform, Kotlin, Java, or `sinceBuild`.

**Do not use when.**

- As a compatibility proof. It checks configuration, not binaries.

**Example.**

```text
$ gradle verifyPluginProjectConfiguration
> Task :verifyPluginProjectConfiguration
```

No lines after the task header means no findings.

Runnable: `sh assets/examples/verify.sh network`.

**Cost removed.** Misconfigurations that users find at install time.
Findings here: 0.

**Verify.**

1. Run the task and count the lines it prints: 0 here.
1. Add `.intellijPlatform` to the target repository's `.gitignore` when
   the task asks (the example runs from a temp-dir copy, so no
   `.gitignore` applies).

## verifyPluginStructure

**Definition.** Validates `plugin.xml` completeness and the archive
structure of the prepared sandbox plugin ([tasks]).

**Use when.**

- Every build that changes `plugin.xml` or packaging.

**Do not use when.**

- Trusting its exit status alone. With a forbidden id prefix it printed
  the problem but did not fail, while `verifyPlugin` did. Likely cause
  (inferred, not checked): the structure check reports it as a warning,
  and `ignoreWarnings` defaults to `true` ([tasks]). Read its output, or
  run the checker.

**Example.**

```text
> Task :verifyPluginStructure
[org.jetbrains.intellij.platform] Invalid plugin descriptor 'plugin.xml'.
The plugin ID 'com.example.wordstats' has a prefix 'com.example' that is
not allowed.
```

Runnable: `sh assets/examples/verify.sh network`.

**Cost removed.** Marketplace upload rejections for descriptor problems.
Count the `Invalid plugin descriptor` lines in the task output (0 after
the id change).

**Verify.**

1. The task output has no `Invalid plugin descriptor` lines (true after
   the id change).
1. `check_plugin_xml.py` agrees (0 errors).

## verifyPlugin (Plugin Verifier)

**Definition.** Runs the IntelliJ Plugin Verifier CLI against the IDEs
in `intellijPlatform.pluginVerification.ides`. The verdict comes from
the report files, and the task fails when there is no verdict ([tasks]).
With no IDEs configured, `recommended()` applies ([extension]). The
default `failureLevel` is `COMPATIBILITY_PROBLEMS`,
`INTERNAL_API_USAGES`, and `OVERRIDE_ONLY_API_USAGES` ([extension]).
Since 2.19.0 each IDE is verified with its own bundled JBR
([release notes][ipgp-2190]).

**Use when.**

- Before every release, over the declared range. The docs require it
  before publishing ([ranges]).

**Do not use when.**

- Running the default IDE list on a slow network. `recommended()`
  downloads several full IDEs. Set `ides { current() }` or `local(...)`
  for local runs, and a real range in CI.

**Example.**

```kotlin
intellijPlatform {
    pluginVerification {
        ides {
            current()
        }
    }
}
```

```text
Plugin org.acme.wordstats:0.1.0 against IC-262.10315.125: Compatible.
1 usage of experimental API
    #Experimental API method ...CoroutinesKt.writeCommandAction(...)
Dynamic Plugin Eligibility:
    Plugin can probably be enabled or disabled without IDE restart
```

Runnable: `build.gradle.kts`; `sh assets/examples/verify.sh network`.

**Cost removed.** Binary incompatibilities (missing classes, changed
signatures, internal API) found by users. Measured: 11 to 23 s per
verification against the local IC build, 82.5 s against the downloaded
IU build.

**Verify.**

1. `gradle verifyPlugin`: "Compatible" for every IDE in the range.
1. `build/reports/pluginVerifier/<IDE>/`: read the experimental and
   deprecated API sections, not only the verdict.

## signPlugin and verifyPluginSignature

**Definition.** `signPlugin` signs the ZIP with the Marketplace ZIP
Signer into `*-signed.zip`. The key and certificate come from
`intellijPlatform.signing`, which defaults to the `PRIVATE_KEY`,
`PRIVATE_KEY_PASSWORD`, and `CERTIFICATE_CHAIN` environment variables
([extension], [signing]). `verifyPluginSignature` checks the signed
archive against the chain ([tasks]). The docs generate the key with
`openssl genpkey` and the chain with `openssl req -x509` ([signing]).

**Use when.**

- Before Marketplace publication. When a key and chain are set,
  `signPlugin` runs automatically before `publishPlugin` ([signing]).

**Do not use when.**

- The key or password would be committed or printed. Use environment
  variables or CI secrets ([signing]).
- Running `signPlugin verifyPluginSignature` in one invocation with
  2.19.0. Observed failure: "Task ':verifyPluginSignature' uses this
  output of task ':signPlugin' without declaring an explicit or implicit
  dependency". Run two invocations.

**Example.** From `verify.sh network`, with throwaway material:

```sh
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 \
    -out "$keys/private.pem"
openssl req -key "$keys/private.pem" -new -x509 -days 1 \
    -subj '/CN=verify-sh-throwaway' -out "$keys/chain.crt"
PRIVATE_KEY=$(cat "$keys/private.pem")
CERTIFICATE_CHAIN=$(cat "$keys/chain.crt")
PRIVATE_KEY_PASSWORD=
export PRIVATE_KEY CERTIFICATE_CHAIN PRIVATE_KEY_PASSWORD
gradle signPlugin
gradle verifyPluginSignature
```

Runnable: `sh assets/examples/verify.sh network` (the `network`
function).

**Cost removed.** The IDE's unsigned-plugin warning dialog at install
([signing]). Output here: `word-stats-0.1.0-signed.zip`, 45,094 bytes
(43,013 unsigned).

**Verify.**

1. `gradle verifyPluginSignature`: `BUILD SUCCESSFUL` (this run).
1. Tamper with the signed ZIP and rerun: expect failure. Not tried.

## publishPlugin

**Definition.** `publishPlugin` uploads the signed archive (or the
unsigned one when signing is not configured) to JetBrains Marketplace or
`publishing.host`. It needs `publishing.token`, which defaults to the
`PUBLISH_TOKEN` environment variable ([tasks], [extension]). A plugin's
first publication must be uploaded by hand on the Marketplace website
([publishing]).

**Use when.**

- Releasing a new version of a plugin already on Marketplace, usually
  from CI with the token as a secret.

**Do not use when.**

- The plugin was never uploaded. Upload the `buildPlugin`/`signPlugin`
  ZIP by hand first ([publishing]).
- `verifyPlugin` has not passed over the declared range.
- The user did not ask for a release; publishing is an external write.

**Example.**

```sh
export PUBLISH_TOKEN='<from plugins.jetbrains.com/author/me/tokens>'
gradle publishPlugin
```

Runnable: none (never executed by `verify.sh`).

Tier: Not runnable here. It needs a Marketplace account, a token, and an
existing listing, and `verify.sh` never calls it.

**Cost removed.** Manual uploads for every release after the first.
Nothing to observe locally; check the Marketplace version list.

**Verify.**

1. The Marketplace plugin page lists the new version and its
   compatibility range.
1. The IDE's Plugins | Marketplace tab offers the update.

[ipgp]: https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin.html
[ipgp-releases]: https://github.com/JetBrains/intellij-platform-gradle-plugin/releases
[ipgp-2190]: https://github.com/JetBrains/intellij-platform-gradle-plugin/releases/tag/2.19.0
[template]: https://github.com/JetBrains/intellij-platform-plugin-template
[tasks]: https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-tasks.html
[extension]: https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-extension.html
[types]: https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-types.html
[faq]: https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-faq.html
[ranges]: https://plugins.jetbrains.com/docs/intellij/build-number-ranges.html
[kotlin]: https://plugins.jetbrains.com/docs/intellij/using-kotlin.html
[fixtures]: https://plugins.jetbrains.com/docs/intellij/tests-and-fixtures.html
[light]: https://plugins.jetbrains.com/docs/intellij/light-and-heavy-tests.html
[testing]: https://plugins.jetbrains.com/docs/intellij/testing-plugins.html
[dynamic]: https://plugins.jetbrains.com/docs/intellij/dynamic-plugins.html
[signing]: https://plugins.jetbrains.com/docs/intellij/plugin-signing.html
[publishing]: https://plugins.jetbrains.com/docs/intellij/publishing-plugin.html
