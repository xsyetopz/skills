# Build, test, and release with Tycho and p2

The Maven/Tycho reactor in `assets/examples/plugin/`: target platform,
packaging types, plug-in tests, features, p2 repositories, installation,
and diagnosis. Executed results come from
`sh assets/examples/verify.sh network` on macOS 27 arm64 with JDK
25.0.4.1 and Maven 3.9.16 (September 2026). A full run took 66 to 84 s of
wall time with a warm Maven cache (machine-specific).

## Contents

- [Versions: Eclipse release and Tycho][toc-versions]
- [Tycho reactor parent POM](#tycho-reactor-parent-pom)
- [Target platform from a .target file][toc-target]
- [Target platform from p2 repositories in the POM][toc-repos]
- [Target environments](#target-environments)
- [eclipse-plugin packaging and JAR inspection][toc-jar]
- [Plug-in tests with plugin-test and the UI harness][toc-uitest]
- [Standalone test bundle with the test goal][toc-testgoal]
- [UI tests on macOS and on headless Linux][toc-headless]
- [Plain JVM tests for pure logic](#plain-jvm-tests-for-pure-logic)
- [eclipse-feature](#eclipse-feature)
- [eclipse-repository with category.xml][toc-repo]
- [Clean install with the Tycho p2 director][toc-director]
- [OSGi console diagnosis](#osgi-console-diagnosis)
- [Launcher JVM selection in eclipse.ini][toc-vm]

## Versions: Eclipse release and Tycho

**Definition.** The target platform is the Eclipse release the plug-in
compiles and runs against; Tycho is the Maven extension that builds it.
Current as of September 2026: Eclipse 4.41 (build `R-4.41-202608281142`,
repository `https://download.eclipse.org/eclipse/updates/4.41/`), which
needs Java 21 or newer to run ([4.41 build][drop]), and Tycho 5.0.4
(released 2026-08-16), which needs Java 21 and Maven 3.9.9 or newer to
run the build ([Tycho releases][tycho-rel], [release notes][tycho-rn]).
The simultaneous release repository
`https://download.eclipse.org/releases/2026-09/` (child
`202609091000`) contains `org.eclipse.platform.feature.group`
`4.41.0.v20260828-1142`, the same build, plus projects such as EGit
7.8.0 ([2026-09 repository][simrel]).

**Use when.**

- You start a plug-in or raise its floor: target the oldest Eclipse
  release you support, and build with the newest Tycho.

**Do not use when.**

- The target is `releases/latest` or `updates/latest`: it moves without
  a source change.
- The target is the developer's running IDE.

**Example.** `pom.xml`: `<tycho-version>5.0.4</tycho-version>`;
`todos.target`: the 4.41 repository. From
`assets/examples/plugin/pom.xml`:

```xml
  <properties>
    <tycho-version>5.0.4</tycho-version>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>
```

From `assets/examples/plugin/todos.target`:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?pde version="3.8"?>
<target name="Eclipse 4.41 (2026-09)" sequenceNumber="1">
  <locations>
    <location includeAllPlatforms="false" includeConfigurePhase="false"
        includeMode="planner" includeSource="false" type="InstallableUnit">
      <repository
          location="https://download.eclipse.org/eclipse/updates/4.41/"/>
      <unit id="org.eclipse.platform.feature.group" version="0.0.0"/>
      <unit id="org.junit" version="0.0.0"/>
    </location>
  </locations>
</target>
```

**Cost removed.** Builds that change between two runs of the same
commit. `mvn -B -V verify` prints the Maven and Java versions, and the
target file names one release.

**Verify.**

1. `gh api repos/eclipse-tycho/tycho/releases --jq '.[0].tag_name'`
   prints the newest Tycho.
1. `curl -sL https://download.eclipse.org/eclipse/downloads/ | grep -o
   'R-4\.[0-9]*-[0-9]*' | sort -u` lists released builds.

## Tycho reactor parent POM

**Definition.** A `pom`-packaged parent that loads
`tycho-maven-plugin` with `<extensions>true</extensions>` (which adds
the `eclipse-*` packaging types and resolves dependencies from
`MANIFEST.MF`) and configures `target-platform-configuration` for all
modules ([Tycho docs][tycho]).

**Use when.**

- One Maven reactor builds bundles, tests, features, and a
  repository.

**Do not use when.**

- Maven `<dependencies>` repeat OSGi bundles the manifest declares: the
  manifest is the source of dependencies.

**Example.** Runnable: `assets/examples/plugin/pom.xml` (excerpt).

```xml
<properties>
  <tycho-version>5.0.4</tycho-version>
</properties>
<modules>
  <module>org.acme.todos</module>
  <module>org.acme.todos.tests</module>
  <module>org.acme.todos.feature</module>
  <module>org.acme.todos.repository</module>
</modules>
<build>
  <plugins>
    <plugin>
      <groupId>org.eclipse.tycho</groupId>
      <artifactId>tycho-maven-plugin</artifactId>
      <version>${tycho-version}</version>
      <extensions>true</extensions>
    </plugin>
  </plugins>
</build>
```

**Cost removed.** Hand-maintained classpaths. Executed: `mvn -B clean
verify` builds four modules and runs 26 tests.

**Verify.**

1. `mvn -B clean verify` ends with `BUILD SUCCESS` (Executed).

## Target platform from a .target file

**Definition.** A PDE target definition (`*.target`) lists
`InstallableUnit` locations from p2 repositories. Tycho's
`target-platform-configuration` reads it with
`<target><file>...</file></target>`. This is the default: Tycho
recommends target files so PDE and Tycho share one definition
([target platform][tp]).

**Use when.**

- The IDE and CI must resolve the same bundles.

**Do not use when.**

- The bundles are already in a feature: list the feature group, and the
  planner pulls the rest.
- The dependency is a project outside the Eclipse SDK and the only
  location is `eclipse/updates/4.41`: that holds the Platform, JDT, and
  PDE features. EGit and other projects are in `releases/2026-09`.

**Example.** Runnable: `assets/examples/plugin/todos.target`.

```xml
<target name="Eclipse 4.41 (2026-09)" sequenceNumber="1">
  <locations>
    <location includeAllPlatforms="false" includeConfigurePhase="false"
        includeMode="planner" includeSource="false" type="InstallableUnit">
      <repository
          location="https://download.eclipse.org/eclipse/updates/4.41/"/>
      <unit id="org.eclipse.platform.feature.group" version="0.0.0"/>
      <unit id="org.junit" version="0.0.0"/>
    </location>
  </locations>
</target>
```

Referenced from the parent POM as
`<file>${maven.multiModuleProjectDirectory}/todos.target</file>`.

**Cost removed.** Two dependency definitions that drift. Executed: with
this file alone, the target resolved and the test runtime started.

**Verify.**

1. `mvn -B verify` resolves (Executed).
1. Not run here: open the file in PDE's Target Editor and "Set as
   Active Target Platform"; no resolution errors.

## Target platform from p2 repositories in the POM

**Definition.** A Maven `<repository>` with `<layout>p2</layout>` adds a
whole p2 repository to the target platform ([target platform][tp]).

**Use when.**

- You need a first build running quickly, as the Tycho docs suggest.

**Do not use when.**

- PDE must see the same target: PDE ignores POM repositories.
- The URL moves (`releases/latest`): see the versions card.

**Example.**

```xml
<repositories>
  <repository>
    <id>eclipse-4.41</id>
    <layout>p2</layout>
    <url>https://download.eclipse.org/eclipse/updates/4.41/</url>
  </repository>
</repositories>
```

**Cost removed.** Writing a target file for a throwaway build. Tier:
not used by the example build.

**Verify.**

1. `mvn -B verify` resolves, and `-Dtycho.debug.resolver=true -X`
   prints the resolved units ([target platform][tp]).

## Target environments

**Definition.** `<environments>` in `target-platform-configuration`
lists the os/ws/arch triples Tycho resolves platform-specific fragments
for (SWT, file system natives).

**Use when.**

- Always: list the triple of the machine that runs the UI tests, plus
  every platform the p2 repository must install on.

**Do not use when.**

- You never test or ship the platform: listing it only adds resolution
  time.

**Example.** From the parent POM:

```xml
<environments>
  <environment>
    <os>macosx</os>
    <ws>cocoa</ws>
    <arch>aarch64</arch>
  </environment>
  <environment>
    <os>linux</os>
    <ws>gtk</ws>
    <arch>x86_64</arch>
  </environment>
</environments>
```

The example also lists `win32/win32/x86_64`.

**Cost removed.** A test runtime without the SWT fragment for the
build machine. The 4.41 repository has
`org.eclipse.swt.cocoa.macosx.aarch64`; with the triple listed, the
tests start a workbench (Executed).

**Verify.**

1. `mvn -B verify` on each CI platform.

## eclipse-plugin packaging and JAR inspection

**Definition.** `<packaging>eclipse-plugin</packaging>` builds a bundle
JAR from `MANIFEST.MF` and `build.properties`. Tycho replaces
`.qualifier` and, in 5.0.4, writes the execution environment as a
`Require-Capability: osgi.ee` header.

**Use when.**

- Every bundle module.

**Do not use when.**

- The evidence is `target/classes` alone: users install the JAR, and
  `bin.includes` decides its content. Inspect the JAR.

**Example.** Runnable: `org.acme.todos/pom.xml`. Inspection:

```sh
unzip -l org.acme.todos/target/org.acme.todos-1.0.0-SNAPSHOT.jar
unzip -p org.acme.todos/target/org.acme.todos-1.0.0-SNAPSHOT.jar \
  META-INF/MANIFEST.MF
```

**Cost removed.** Shipping a JAR without classes or `plugin.xml`.
Executed: the JAR lists `plugin.xml` and 12 classes, and the packaged
manifest has `Bundle-Version: 1.0.0.<timestamp>` and `osgi.ee`
instead of `Bundle-RequiredExecutionEnvironment`.

**Verify.**

1. `verify.sh network` checks both listings (Executed).

## Plug-in tests with plugin-test and the UI harness

**Definition.** `tycho-surefire-plugin:plugin-test` starts an OSGi
runtime with the bundle, its dependencies, and a test harness, and runs
tests in the `integration-test` phase; `verify` fails the build on test
failures. `useUIHarness=true` starts a workbench
(`org.eclipse.ui.ide.workbench` by default), and `useUIThread=true`
(the default) runs tests on its UI thread ([Testing bundles][testing],
[plugin-test][plugin-test]).

**Use when.**

- You claim anything about the registry, commands, views, jobs with
  workspace rules, markers, or preferences.

**Do not use when.**

- The code under test has no OSGi or Eclipse types: a plain JVM test
  is faster (see that card).

**Example.** Runnable: `org.acme.todos.tests/pom.xml` (excerpt).

```xml
<execution>
  <id>workbench-tests</id>
  <goals>
    <goal>plugin-test</goal>
    <goal>verify</goal>
  </goals>
</execution>
...
<configuration>
  <includes>
    <include>**/*IT.class</include>
  </includes>
  <useUIHarness>true</useUIHarness>
  <useUIThread>true</useUIThread>
  <forkedProcessTimeoutInSeconds>300</forkedProcessTimeoutInSeconds>
</configuration>
```

The test bundle marks `src` as a test folder in `.classpath`
(`<attribute name="test" value="true"/>`), so Tycho compiles it to
`target/test-classes`.

Trap: the `plugin-test` documentation gives the default patterns as
`PluginTest*.class, *IT.class`, but in 5.0.4 the goal inherits
`**/Test*.class, **/*Test.class, **/*Tests.class, **/*TestCase.class`
([AbstractTestMojo][abstract-test]). Executed: without `<includes>`,
`*IT` classes gave `No tests found` and a failed build.

**Cost removed.** Green builds that ran no tests, and host behavior
claimed from unit tests. Executed: `Tests run: 26, Failures: 0,
Errors: 0, Skipped: 0` in a real 4.41 workbench.

**Verify.**

1. Read the count from `target/failsafe-reports/failsafe-summary.xml`
   or the `Tests run:` line. Zero tests is a failure.
1. Keep `failIfNoTests` at its default (`true`).

## Standalone test bundle with the test goal

**Definition.** The Tycho 5.0.4 standalone demo builds its separate
test bundle with `eclipse-plugin` packaging, the `test` goal, and
`<packaging>eclipse-plugin</packaging>` in the surefire configuration
([standalone demo][standalone]). The Testing guide calls the older
`eclipse-test-plugin` packaging "not recommended for new designs"
([Testing bundles][testing]).

**Use when.**

- A build already uses this form. It runs in the `test` phase instead of
  `integration-test`.

**Do not use when.**

- The build is new: use `plugin-test` plus `verify`, as the example
  does.

**Example.**

```xml
<execution>
  <id>execute-integration-tests</id>
  <goals>
    <goal>test</goal>
  </goals>
</execution>
...
<configuration>
  <packaging>eclipse-plugin</packaging>
</configuration>
```

**Cost removed.** Migrating a working build without need. Tier: not
executed.

**Verify.**

1. `mvn -B verify` passes with a non-zero `Tests run:` count.

## UI tests on macOS and on headless Linux

**Definition.** On macOS, SWT must run on the process's first thread:
start the JVM with `-XstartOnFirstThread` ([SWT FAQ][swt-faq]). Tycho
5.0.4 does not add the flag to the test JVM (its printed command line
had none). On Linux CI without a display, the workbench needs an X
server.

**Use when.**

- `useUIHarness` is `true` and the build runs on macOS or on a
  display-less Linux agent.

**Do not use when.**

- The flag would apply unconditionally in a build that also runs on
  Windows or Linux: it is documented for macOS only. Keep it in an
  OS-activated profile.

**Example.** From the test POM, a profile that adds the flag on macOS:

```xml
<profile>
  <id>macos-ui-tests</id>
  <activation>
    <os>
      <family>mac</family>
    </os>
  </activation>
  <build>
    <plugins>
      <plugin>
        <groupId>org.eclipse.tycho</groupId>
        <artifactId>tycho-surefire-plugin</artifactId>
        <configuration>
          <argLine>-XstartOnFirstThread</argLine>
        </configuration>
      </plugin>
    </plugins>
  </build>
</profile>
```

On Linux: `xvfb-run -a mvn -B verify` (not executed here).

**Cost removed.** Test runtimes that die before the first test.
Executed on macOS: with the profile disabled (`-P '!macos-ui-tests'`),
the build failed in 10 s with `process returned error code 13` and
`.metadata/.log` showed `Application error` /
`SWTException: Invalid thread access`; with it, the workbench started
and all tests ran.

**Verify.**

1. `mvn -B verify` reaches the `Tests run:` line on each CI platform.

## Plain JVM tests for pure logic

**Definition.** Code without Eclipse types (here `TodoScanner`) runs on
any JVM. Tycho's Testing guide recommends `maven-surefire-plugin` for
tests that need no OSGi runtime ([Testing bundles][testing]).

**Use when.**

- The code is parsing, formatting, or computation that the plug-in
  calls.

**Do not use when.**

- The claim is about workbench behavior: a plain JVM result does not
  prove it.

**Example.** Runnable: `assets/examples/logic/TodoScannerCheck.java`,
compiled and run by `verify.sh` without Maven:

```sh
javac -d out plugin/org.acme.todos/src/org/acme/todos/TodoScanner.java
java -cp out logic/TodoScannerCheck.java
```

**Cost removed.** A workbench start per logic change. Measured
(machine-specific, shared machine): `javac` plus the 7 checks took
2.3 s of wall time; the UI test module took 7.2 to 9.8 s in three
`mvn verify` runs, after the target platform was cached.

**Verify.**

1. `sh assets/examples/verify.sh` prints `TodoScanner on a plain JVM:
   7 checks` (Executed).

## eclipse-feature

**Definition.** A feature (`feature.xml`, packaging `eclipse-feature`)
is an installable group of bundles. p2 installs features, not loose
bundles. `version="0.0.0"` on a `<plugin>` lets Tycho insert the built
version.

**Use when.**

- The bundle must be installed through Install New Software or the p2
  director.

**Do not use when.**

- Only tests in the reactor consume the bundle.

**Example.** Runnable: `org.acme.todos.feature/feature.xml`.

```xml
<feature id="org.acme.todos.feature" label="TODO Markers"
    version="1.0.0.qualifier" provider-name="Acme">
  <plugin id="org.acme.todos" version="0.0.0"/>
</feature>
```

The p2 installable unit is `org.acme.todos.feature.feature.group`.

**Cost removed.** A repository with nothing a user can select.
Executed: the director installed
`org.acme.todos.feature.feature.group/1.0.0.<timestamp>`.

**Verify.**

1. `ls org.acme.todos.repository/target/repository/features`.

## eclipse-repository with category.xml

**Definition.** Packaging `eclipse-repository` builds a p2 repository
(`content.jar`, `artifacts.jar`, `plugins/`, `features/`) from
`category.xml`, which lists features and the categories shown in
Install New Software.

**Use when.**

- You publish an update site.

**Do not use when.**

- The update site is a single bundle JAR: it has no p2 metadata.

**Example.** Runnable: `org.acme.todos.repository/category.xml`.

```xml
<site>
  <feature id="org.acme.todos.feature" version="0.0.0">
    <category name="org.acme.todos.category"/>
  </feature>
  <category-def name="org.acme.todos.category" label="TODO Markers"/>
</site>
```

**Cost removed.** Features that install but stay invisible in the
wizard for lack of a category. Executed: `target/repository` contains
`content.jar`, `artifacts.jar`, the plug-in JAR, and the feature JAR.

**Verify.**

1. `find org.acme.todos.repository/target/repository -type f`
   (Executed).

## Clean install with the Tycho p2 director

**Definition.** `tycho-p2-director-plugin:director` runs the p2
director without an Eclipse installation. It installs IUs from
repositories into a new `destination`; on macOS it creates an
`Eclipse.app` layout under a plain destination folder ([director
mojo][director]).

**Use when.**

- You must prove the repository installs into a clean product with all
  dependencies resolved.

**Do not use when.**

- The destination is the user's own IDE: use a fresh one.

**Example.** From `verify.sh network`:

```sh
mvn -B org.eclipse.tycho:tycho-p2-director-plugin:5.0.4:director \
  -Ddestination="$PWD/inst/eclipse" \
  -Drepositories="https://download.eclipse.org/eclipse/updates/4.41/,\
file:$PWD/org.acme.todos.repository/target/repository" \
  -DinstallIUs=org.eclipse.platform.ide,\
org.acme.todos.feature.feature.group \
  -Dprofile=SDKProfile -Droaming=true
```

Then list the roots with the installed launcher:

```sh
java -jar plugins/org.eclipse.equinox.launcher_*.jar -nosplash \
  -application org.eclipse.equinox.p2.director -listInstalledRoots
```

**Cost removed.** Update sites that miss a dependency. Executed: the
install completed (Maven reported 42.8 s total on the first run) and
listed
`org.acme.todos.feature.feature.group/1.0.0.<timestamp>` and
`org.eclipse.platform.ide/4.41.0.I20260828-1142`.

**Verify.**

1. `verify.sh network` asserts the feature root (Executed).

## OSGi console diagnosis

**Definition.** Starting Equinox with `-console` opens the Gogo shell:
`ss <name>` lists bundle states, `diag <bundle>` explains unresolved
requirements, and `packages <package>` shows exporters and importers.

**Use when.**

- A contribution is missing: confirm the bundle is `RESOLVED`,
  `STARTING`, or `ACTIVE` before reading UI code.

**Do not use when.**

- The only symptom is `STARTING` with lazy activation: that is normal
  until a class loads.

**Example.** Executed in the director-installed 4.41:

```text
g! ss org.acme
id  State       Bundle
12  STARTING    org.acme.todos_1.0.0.202609251632
g! diag org.acme.todos
org.acme.todos [12]
  No resolution report for the bundle.
g! packages jakarta.inject
... jakarta.inject.jakarta.inject-api_2.0.1 [11]>
  org.acme.todos_1.0.0.202609251632 [12] imports
```

**Cost removed.** Debugging UI code for a bundle that never resolved.

**Verify.**

1. `verify.sh network` parses the `ss` line (Executed).

## Launcher JVM selection in eclipse.ini

**Definition.** `eclipse.ini` holds one launcher argument per line.
`-vm` and its path are two lines and must come before `-vmargs`
([launcher ini][launcher]).

**Use when.**

- The native launcher picks the wrong JVM or none. Eclipse 4.41 needs
  Java 21 or newer.

**Do not use when.**

- The fix changes the system default Java for one IDE.

**Example.**

```text
-vm
/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home/bin/java
-vmargs
-Xmx2g
```

**Cost removed.** Launch failures before Equinox starts. Tier: not
executed here (the example runs the launcher JAR with `java -jar`).

**Verify.**

1. Start the IDE and open Help, About, Installation Details,
   Configuration: `java.home` must be the chosen JVM.

[drop]: https://download.eclipse.org/eclipse/downloads/drops4/R-4.41-202608281142/
[tycho-rel]: https://github.com/eclipse-tycho/tycho/releases/tag/tycho-5.0.4
[tycho-rn]: https://github.com/eclipse-tycho/tycho/blob/tycho-5.0.4/RELEASE_NOTES.md
[tycho]: https://tycho.eclipseprojects.io/doc/5.0.4/
[tp]: https://tycho.eclipseprojects.io/doc/5.0.4/TargetPlatform.html
[testing]: https://tycho.eclipseprojects.io/doc/5.0.4/TestingBundles.html
[plugin-test]: https://tycho.eclipseprojects.io/doc/5.0.4/tycho-surefire-plugin/plugin-test-mojo.html
[abstract-test]: https://github.com/eclipse-tycho/tycho/blob/tycho-5.0.4/tycho-surefire/tycho-surefire-plugin/src/main/java/org/eclipse/tycho/surefire/AbstractTestMojo.java
[standalone]: https://github.com/eclipse-tycho/tycho/tree/tycho-5.0.4/demo/testing/tycho/standalone
[director]: https://tycho.eclipseprojects.io/doc/5.0.4/tycho-p2-director-plugin/director-mojo.html
[simrel]: https://download.eclipse.org/releases/2026-09/
[swt-faq]: https://eclipse.dev/eclipse/swt/faq.html
[launcher]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/misc/launcher_ini.html
[toc-versions]: #versions-eclipse-release-and-tycho
[toc-target]: #target-platform-from-a-target-file
[toc-repos]: #target-platform-from-p2-repositories-in-the-pom
[toc-jar]: #eclipse-plugin-packaging-and-jar-inspection
[toc-uitest]: #plug-in-tests-with-plugin-test-and-the-ui-harness
[toc-testgoal]: #standalone-test-bundle-with-the-test-goal
[toc-headless]: #ui-tests-on-macos-and-on-headless-linux
[toc-repo]: #eclipse-repository-with-categoryxml
[toc-director]: #clean-install-with-the-tycho-p2-director
[toc-vm]: #launcher-jvm-selection-in-eclipseini
