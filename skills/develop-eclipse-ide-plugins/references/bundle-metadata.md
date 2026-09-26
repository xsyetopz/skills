# Bundle metadata: MANIFEST.MF, build.properties, plugin.xml

The three files that decide whether a plug-in resolves, gets packaged,
and has its extensions read. Runnable bundle:
`assets/examples/plugin/org.acme.todos/`. Results marked Executed come
from `assets/examples/verify.sh` on macOS 27 arm64 with JDK 25.0.4.1,
Maven 3.9.16, Tycho 5.0.4, and the Eclipse 4.41 repository
`R-4.41-202608281142` (September 2026); they are machine-specific.

## Contents

- [MANIFEST.MF line format](#manifestmf-line-format)
- [Bundle-SymbolicName with singleton:=true][toc-singleton]
- [Bundle-Version and the qualifier](#bundle-version-and-the-qualifier)
- [Require-Bundle](#require-bundle)
- [Import-Package](#import-package)
- [Export-Package and x-internal packages][toc-export]
- [Bundle-RequiredExecutionEnvironment and osgi.ee][toc-ee]
- [Bundle-Activator with Bundle-ActivationPolicy: lazy][toc-lazy]
- [build.properties bin.includes](#buildproperties-binincludes)
- [plugin.xml extensions](#pluginxml-extensions)
- [Bundle checker](#bundle-checker)

## MANIFEST.MF line format

**Definition.** `META-INF/MANIFEST.MF` is a JAR manifest: `Name: value`
headers, each line at most 72 bytes in UTF-8, longer values continued
on lines that start with exactly one space ([JAR spec][jar]). Bundle
headers go in the main section, which ends at the first blank line.

**Use when.**

- You edit any header by hand or review a generated manifest.

**Do not use when.**

- bnd generates the manifest (`bnd.bnd`, Tycho BND plugin): edit the bnd
  instructions, because hand edits are overwritten.

**Example.** Runnable:
`assets/examples/plugin/org.acme.todos/META-INF/MANIFEST.MF`.

```text
Manifest-Version: 1.0
Bundle-ManifestVersion: 2
Bundle-SymbolicName: org.acme.todos;singleton:=true
Bundle-Version: 1.0.0.qualifier
Require-Bundle: org.eclipse.core.runtime,
 org.eclipse.core.resources,
 org.eclipse.ui
Automatic-Module-Name: org.acme.todos
```

End the last line with a newline. Executed with
`assets/examples/logic/ManifestNewlineCheck.java` (JDK 25):

| Input | `java.util.jar.Manifest` | Equinox `ManifestElement` |
| --- | --- | --- |
| no newline after the last header | header dropped (`null`) | header kept |
| continuation with two spaces | value `a, b` (space kept) | value `a, b` |
| continuation without a space | `IOException: invalid header field` | `BundleException` |
| one 200-byte line | accepted | accepted |

Tycho packages with the JDK reader. Executed (`verify.sh network`): a
Tycho 5.0.4 build of a manifest without the final newline succeeded, and
the JAR lacked the last header (`Automatic-Module-Name`). The 72-byte
limit is a writer rule that neither reader enforces.

**Cost removed.** A header that silently disappears from the built JAR,
with no build error: `unzip -p target/*.jar META-INF/MANIFEST.MF` lacks
it, and `check_bundle.py` reports M002.

**Verify.**

1. `python3 scripts/check_bundle.py <bundle>` reports no M001 to M005.
1. After `mvn verify`, diff the header names of `META-INF/MANIFEST.MF`
   and the packaged manifest: every source header must be present.

## Bundle-SymbolicName with singleton:=true

**Definition.** `Bundle-SymbolicName` is the bundle id. The
`singleton:=true` directive lets the framework resolve at most one
version of the bundle ([OSGi Core 8, 3.6.2][osgi-module]). The Equinox
extension registry reads `plugin.xml` only from singleton bundles.

**Use when.**

- The bundle has a `plugin.xml` with any `<extension>` or
  `<extension-point>`. PDE reports otherwise: "Plug-ins declaring extensions or
  extension points must set the 'singleton' directive to 'true'"
  ([PDE messages][pde-messages]).

**Do not use when.**

- A library bundle without `plugin.xml` must allow several versions side
  by side: `singleton` blocks that.

**Example.**

```text
Bundle-SymbolicName: org.acme.todos;singleton:=true
```

**Cost removed.** A bundle that builds and resolves but contributes
nothing. Executed: without the directive, the Tycho build compiled and
packaged, the test runtime logged `The extensions and extension-points
from the bundle "org.acme.todos" are ignored. The bundle is not marked
as singleton.` in `.metadata/.log`, and 9 of 26 workbench tests failed
(`NotDefinedException: Trying to execute a command that is not
defined`, `PartInitException: Could not create view`).

**Verify.**

1. `python3 scripts/check_bundle.py <bundle>` reports no M009.
1. `grep 'not marked as singleton' <test workspace>/.metadata/.log`
   finds nothing after the plug-in tests run.

## Bundle-Version and the qualifier

**Definition.** `major.minor.micro.qualifier` ([OSGi Core 8,
3.2.5][osgi-module]). PDE and Tycho replace the literal `qualifier` at
build time (Tycho uses a UTC timestamp, for example
`1.0.0.202609251632`). Tycho requires the POM version to match, with
`-SNAPSHOT` in place of `.qualifier`.

**Use when.**

- Every build must produce a version p2 sees as newer, so an update
  installs it.

**Do not use when.**

- `Bundle-Version` holds `-SNAPSHOT` or other Maven syntax: not an OSGi
  version (checker M008).
- The reference is from `feature.xml`: use `version="0.0.0"` and let
  Tycho insert the built version.

**Example.** Manifest `Bundle-Version: 1.0.0.qualifier`, POM
`<version>1.0.0-SNAPSHOT</version>`, feature `<plugin
id="org.acme.todos" version="0.0.0"/>`
(`assets/examples/plugin/org.acme.todos.feature/feature.xml`).
From `assets/examples/plugin/org.acme.todos/META-INF/MANIFEST.MF`:

```text
Bundle-SymbolicName: org.acme.todos;singleton:=true
Bundle-Version: 1.0.0.qualifier
```

From `assets/examples/plugin/org.acme.todos/pom.xml`:

```xml
  <artifactId>org.acme.todos</artifactId>
  <version>1.0.0-SNAPSHOT</version>
  <packaging>eclipse-plugin</packaging>
```

From `assets/examples/plugin/org.acme.todos.feature/feature.xml`:

```xml
  <plugin id="org.acme.todos" version="0.0.0"/>
```

**Cost removed.** Builds whose bundle and POM versions disagree, and
releases whose version does not grow, so p2 sees nothing newer to install
(inferred from p2 version ordering, not tested here). Executed: with the
POM at `1.0.1-SNAPSHOT`, Tycho 5.0.4 failed in `validate-version` with
`Unqualified OSGi version 1.0.0.qualifier must match unqualified Maven
version 1.0.1-SNAPSHOT for SNAPSHOT builds`. The built JAR is named
`org.acme.todos_1.0.0.<timestamp>.jar` in `target/repository/plugins/`.

**Verify.**

1. `mvn -B verify` passes `tycho-packaging:validate-version`.
1. `ls */target/repository/plugins` shows a timestamp, not `qualifier`.

## Require-Bundle

**Definition.** Wires the bundle, by bundle id, to every package another
bundle exports ([OSGi Core 8, 3.13][osgi-module]). With
`visibility:=reexport`, the required bundle's exports pass on to
dependents.

**Use when.**

- The dependency is an Eclipse Platform bundle, such as `org.eclipse.ui`,
  `org.eclipse.core.runtime`, or `org.eclipse.core.resources`. This is the
  default: the platform's own bundles do it (the 4.41 `org.eclipse.ui.ide`
  manifest has `Require-Bundle: org.eclipse.core.runtime;
  bundle-version="[3.29...`), and `org.eclipse.core.runtime` is a split
  package: `org.eclipse.equinox.common` exports it with
  `common=split;mandatory:=common`.
- The test bundle needs the host bundle's classes.

**Do not use when.**

- The dependency is a third-party library package (for example
  `jakarta.inject`): OSGi prefers `Import-Package`, since
  `Require-Bundle` couples to a bundle name and admits split packages
  ([OSGi Core 8, 3.13.3][osgi-module]).
- The bundle-version range is omitted but the code calls API newer than
  the oldest supported target: resolution succeeds, then
  `NoSuchMethodError` appears at runtime.

**Example.**

```text
Require-Bundle: org.eclipse.core.runtime;bundle-version="3.29.0",
 org.eclipse.core.resources,
 org.eclipse.ui
```

`ILog.of(Class)` is "Since 3.29" of `org.eclipse.core.runtime`
([ILog][ilog]), so the range states that floor. The example manifest
omits ranges because it targets one pinned release.

**Cost removed.** `NoClassDefFoundError` at first use of a class from an
undeclared bundle. Tycho compiles against declared dependencies only, so
the error moves to build time as the ECJ error `The import ... cannot be
resolved` in `mvn verify`.

**Verify.**

1. `mvn -B verify` compiles (Executed for the example).
1. For a declared floor, build once with the floor release's repository
   in the target file.

## Import-Package

**Definition.** Wires the bundle to a package by name and version range,
from whichever bundle exports it ([OSGi Core 8, 3.6.4][osgi-module]).

**Use when.**

- The package is a versioned library API with several possible
  providers, for example `jakarta.inject;version="[2.0.0,3.0.0)"`.

**Do not use when.**

- The platform splits the package across bundles: a plain import of
  `org.eclipse.core.runtime` wires to one exporter and cannot see the
  other half. Use `Require-Bundle`.
- The range is unbounded (`version="2.0.0"` means 2.0.0 or newer): a
  future breaking major version also matches.

**Example.** From the example manifest:

```text
Import-Package: jakarta.inject;version="[2.0.0,3.0.0)"
```

The 4.41 repository ships `jakarta.inject.jakarta.inject-api` 1.0.5 and
2.0.1; the range selects the `jakarta.inject` 2.x package.

**Cost removed.** Wiring to the wrong provider when two versions are
installed. Executed in a p2-installed 4.41: the Equinox console command
`packages jakarta.inject` printed the exporter
`jakarta.inject.jakarta.inject-api_2.0.1` and
`org.acme.todos_1.0.0.202609251632 [12] imports`.

**Verify.**

1. `mvn -B verify` resolves, and the Tycho log lists no "Missing
   requirement".
1. `TodoViewIT.injectedViewShowsCountAfterBackgroundScan` asserts that
   the `@Inject` field was set (Executed: pass).

## Export-Package and x-internal packages

**Definition.** `Export-Package` lists the packages other bundles may
load. The Equinox directives `x-internal:=true` and `x-friends:="id,..."`
mark a package as not API; PDE flags access from other bundles
([PDE manifest editor][pde-editor]).

**Use when.**

- A test bundle or another plug-in must load the classes: export the
  package, and mark it `x-internal:=true` when it is not API.

**Do not use when.**

- Nothing outside the bundle needs the package: other bundles cannot load
  an unexported package, so it stays free to refactor.

**Example.**

```text
Export-Package: org.acme.todos
```

A library that keeps an implementation package private but opens it to
its tests:

```text
Export-Package: org.acme.todos.internal;
 x-friends:="org.acme.todos.tests"
```

**Cost removed.** `ClassNotFoundException` in the test bundle for an
unexported package; in Tycho the test bundle fails to compile instead.

**Verify.**

1. `mvn -B verify` compiles the test bundle (Executed).

## Bundle-RequiredExecutionEnvironment and osgi.ee

**Definition.** Both headers state the minimum Java. Per OSGi Core 8,
`Bundle-RequiredExecutionEnvironment` "is deprecated but must be fully
supported", and a bundle should use either it or an `osgi.ee`
requirement, not both ([OSGi Core 8, 3.4.1][osgi-module]).

**Use when.**

- The project is a PDE project: write
  `Bundle-RequiredExecutionEnvironment: JavaSE-21`, which PDE and Tycho
  read to pick the compiler level. Eclipse 4.41 requires Java 21 to run
  ([4.41 build page][drop]).

**Do not use when.**

- The level is newer than the oldest JVM your users run: an
  unsatisfied `osgi.ee` requirement keeps the bundle from resolving (OSGi
  resolution rules; not tested here).
- A hand-written `Require-Capability: osgi.ee` sits next to it: checker
  M010 warns.

**Example.** Source header and what Tycho 5.0.4 packaged (Executed):

```text
Bundle-RequiredExecutionEnvironment: JavaSE-21
Require-Capability: osgi.ee;filter:="(&(osgi.ee=JavaSE)(version=21))"
```

The source manifest has the first line; the built JAR has only the
second.

**Cost removed.** A bundle that resolves on a JVM that cannot load its
class files (`UnsupportedClassVersionError`). On a too-old JVM, `ss` in
the OSGi console should show the bundle staying `INSTALLED` (not tested
here; this machine has only JDK 25).

**Verify.**

1. `unzip -p target/*.jar META-INF/MANIFEST.MF | grep osgi.ee`.
1. `javap -v -cp target/classes org.acme.todos.TodoScanner | grep major`
   prints `major version: 65` (Java 21).

## Bundle-Activator with Bundle-ActivationPolicy: lazy

**Definition.** `Bundle-Activator` names a `BundleActivator` whose
`start`/`stop` run when the bundle starts and stops.
`Bundle-ActivationPolicy: lazy` starts the bundle on the first load of
one of its classes, not at framework start ([OSGi Core 8,
3.2.1.1][osgi-module]).

**Use when.**

- The bundle owns something with a bundle lifetime: here, a workspace
  `POST_CHANGE` listener registered in `start` and removed in `stop`,
  plus job cleanup in `stop`.

**Do not use when.**

- The work can be declared in `plugin.xml` (handlers, views,
  initializers): the registry creates those on demand without an
  activator.
- `start` would do slow work: it runs on the thread that first loaded a
  class, often the UI thread.

**Example.** Runnable: `org.acme.todos/src/org/acme/todos/Activator.java`.

```java
public final class Activator implements BundleActivator {
    private TodoRescanListener listener;

    @Override
    public void start(BundleContext context) {
        listener = new TodoRescanListener();
        ResourcesPlugin.getWorkspace().addResourceChangeListener(
                listener, IResourceChangeEvent.POST_CHANGE);
    }

    @Override
    public void stop(BundleContext context)
            throws InterruptedException {
        ResourcesPlugin.getWorkspace()
                .removeResourceChangeListener(listener);
        Job.getJobManager().cancel(ScanTodosJob.FAMILY);
        Job.getJobManager().join(ScanTodosJob.FAMILY, null);
    }
}
```

**Cost removed.** Start-up work for a bundle nobody used. Executed: in a
p2-installed 4.41 with the feature, the OSGi console printed
`12  STARTING  org.acme.todos_1.0.0.202609251632`: resolved, waiting for
its first class load.

**Verify.**

1. OSGi console `ss org.acme` shows `STARTING` before first use and
   `ACTIVE` after a command runs.
1. `RescanListenerIT` passes (Executed): the listener registered by
   `start` scans an edited file.

## build.properties bin.includes

**Definition.** PDE build configuration: `source..` lists the source
folders of the bundle's root classpath entry `.`, `output..` its class
folder, and `bin.includes` the files packaged into the JAR. Values follow
Java `.properties` rules: a multi-line list needs a trailing backslash on
each line.

**Use when.**

- Every PDE or Tycho bundle: `bin.includes` must name `META-INF/`, `.`,
  `plugin.xml`, and every runtime file such as `icons/`.

**Do not use when.**

- The bundle is built from `bnd.bnd` (Tycho BND workspace): packaging
  follows bnd instructions.

**Example.** Runnable: `org.acme.todos/build.properties`.

```properties
source.. = src/
output.. = bin/
bin.includes = META-INF/,\
               .,\
               plugin.xml
```

**Cost removed.** A JAR without classes or `plugin.xml` that installs and
does nothing. Executed: the same list with commas but no backslashes
built with Tycho 5.0.4 and produced a JAR with 0 classes and no
`plugin.xml` (7 entries, all under `META-INF/`).

**Verify.**

1. `python3 scripts/check_bundle.py <bundle>` reports no B001 to B007.
1. `unzip -l target/*.jar` lists `plugin.xml` and the classes.

## plugin.xml extensions

**Definition.** `plugin.xml` holds `<extension point="...">` elements
that the Equinox extension registry reads when the bundle resolves. The
extension point's schema defines the child elements. Classes named in
`class` attributes load only when used, which also activates a lazy
bundle.

**Use when.**

- You contribute to platform extension points: commands, handlers,
  menus, views, marker types, preference initializers.

**Do not use when.**

- The contribution is programmatic by design (handlers activated by a
  part through `IHandlerService`): use the service and deactivate with
  the part.
- An extension element names a `class` in a package that is not packaged
  or not on `source..`: the registry logs a `ClassNotFoundException` at
  first use.

**Example.** Runnable: `org.acme.todos/plugin.xml` (marker type,
preference initializer, commands, expression definitions, handlers,
menus, view).

```xml
<extension id="todo" name="TODO Marker"
    point="org.eclipse.core.resources.markers">
  <super type="org.eclipse.core.resources.taskmarker"/>
  <persistent value="true"/>
</extension>
```

The extension's full id is the bundle id plus `id`:
`org.acme.todos.todo`.

**Cost removed.** Broken references between ids that fail only when a
user clicks. `check_bundle.py` reports X002 to X007 without a build, and
`test_check_bundle.py` fires each rule on a targeted mutation.

**Verify.**

1. `python3 scripts/check_bundle.py <bundle>` is clean.
1. A plug-in test executes each command and opens each view (Executed:
   `ScanCommandIT`, `EncodeFormValueIT`, `TodoViewIT`).

## Bundle checker

**Definition.** `scripts/check_bundle.py BUNDLE_DIR...` is a stdlib
Python checker for the rules above: manifest lines (M001 to M005),
headers (M006 to M010), `build.properties` (B001 to B007), and
`plugin.xml` references (X001 to X007). Exit status 0, 1 (errors), or 2
(usage).

**Use when.**

- Before a Tycho build, and when reviewing any change to the three files.

**Do not use when.**

- You need proof that the bundle resolves or contributions work: it only
  reads files. Only a plug-in test or a launched IDE proves that.

**Example.**

```sh
python3 scripts/check_bundle.py \
  assets/examples/plugin/org.acme.todos \
  assets/examples/plugin/org.acme.todos.tests
# 0 error(s), 0 warning(s)
```

**Cost removed.** A build-and-launch cycle per metadata mistake.
Executed: 29 tests in `scripts/test_check_bundle.py`, one targeted
mutation per rule.

**Verify.**

1. `python3 scripts/test_check_bundle.py` prints `OK`.
1. `sh assets/examples/verify.sh` runs both commands.

[jar]: https://docs.oracle.com/en/java/javase/25/docs/specs/jar/jar.html
[osgi-module]: https://docs.osgi.org/specification/osgi.core/8.0.0/framework.module.html
[pde-messages]: https://github.com/eclipse-pde/eclipse.pde/blob/763c5f84b1ad9a2913c3424c57b05839ac6ea4ce/ui/org.eclipse.pde.core/src/org/eclipse/pde/internal/core/pderesources.properties
[pde-editor]: https://help.eclipse.org/latest/topic/org.eclipse.pde.doc.user/guide/tools/editors/manifest_editor/runtime.htm
[ilog]: https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/ILog.html
[drop]: https://download.eclipse.org/eclipse/downloads/drops4/R-4.41-202608281142/
[toc-singleton]: #bundle-symbolicname-with-singletontrue
[toc-export]: #export-package-and-x-internal-packages
[toc-ee]: #bundle-requiredexecutionenvironment-and-osgiee
[toc-lazy]: #bundle-activator-with-bundle-activationpolicy-lazy
