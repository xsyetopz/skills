# Build and distribute Eclipse IDE plugin bundles

Target-dependent API reference; stable **Eclipse Platform 4.40 (2026-06)**
([release build][release-build]), current PDE documentation and stable **Tycho
5.0.4** ([release][api-1]). Use the project's selected Eclipse target and
execution environment, not the developer's running IDE. Release, milestone and
integration builds are different channels; select a released target for new
stable work.

[release-build]:
https://download.eclipse.org/eclipse/downloads/drops4/R-4.40-202606010713/index.html

## Bundle and extension contracts

`META-INF/MANIFEST.MF` defines OSGi identity/classloading, `plugin.xml` declares
extensions, and `build.properties` selects packaged resources. Example bundle
metadata:

```text
Manifest-Version: 1.0
Bundle-ManifestVersion: 2
Bundle-Name: Example Tools
Bundle-SymbolicName: com.example.tools;singleton:=true
Bundle-Version: 1.0.0.qualifier
Bundle-RequiredExecutionEnvironment: JavaSE-21
Require-Bundle: org.eclipse.ui,
 org.eclipse.core.runtime
```

Continuation lines begin with a space; preserve the terminating newline. Set the
Java level from the target requirements. `Require-Bundle` couples to bundle
identity/exports; `Import-Package` couples to versioned package contracts. Avoid
split packages, accidental re-exports and broad dynamic imports. Export only
intended APIs and use package version ranges where required. An optional import
requires a code path that remains loadable when the dependency is absent. [PDE
metadata][metadata-2].

Declare the command and handler, then add its UI placement:

```xml
<plugin>
  <extension point="org.eclipse.ui.commands">
    <command id="com.example.inspect" name="Inspect"/>
  </extension>
  <extension point="org.eclipse.ui.handlers">
    <handler commandId="com.example.inspect"
             class="com.example.InspectHandler"/>
  </extension>
</plugin>
```

Add a menu/toolbar contribution through `org.eclipse.ui.menus` when needed; keep
enablement/context narrow. Public extension-point IDs and their schemas are
contracts. `internal` packages may compile but remain unsupported API.
[Commands][metadata-1].

[metadata-1]:
https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/workbench_cmd.htm
[metadata-2]:
https://help.eclipse.org/latest/topic/org.eclipse.pde.doc.user/guide/tools/editors/manifest_editor/editor.htm

## Target and reactor

Use a shared `.target` definition or pinned p2 repository for PDE and Tycho. A
moving `latest` repository can change resolution without a source edit. Prefer
selecting the exact required IUs and platform OS/WS/architecture environments.
Maven dependencies alone do not express all OSGi resolution rules. [Target
platforms][target-1].

The starter has a parent reactor, UI bundle, test bundle, feature and
repository. Replace placeholders consistently; remove feature/repository modules
for a bundle-only request. Build uses `mvn clean verify` with the selected
Java/Maven/Tycho. `eclipse-plugin`, `eclipse-test-plugin`, `eclipse-feature` and
`eclipse-repository` are distinct packaging roles. Keep Maven snapshot and OSGi
qualifier/version mappings consistent rather than changing IDs to silence
resolution failures. [Tycho][api-2].

Select the test goal together with its source layout. Tycho's modern
`plugin-test`/`verify` pair uses integration-test discovery and checks failures
at `verify`; running only `integration-test` is not a completed test
verification. Existing standalone test bundles can use `test` with the explicit
`eclipse-plugin` packaging configuration shown in the pinned Tycho 5.0.4 demo.
That configuration was exercised in the starter's real Equinox runtime; do not
replace it merely because the generic goal summary mentions only
`eclipse-test-plugin`. [Testing guide][testing-guide], [standalone
demo][standalone-demo].

For ordinary source under `src/`, a build fragment is:

```properties
source.. = src/
output.. = bin/
bin.includes = META-INF/,.,plugin.xml
```

Keep a property value on one line or use Java-properties backslash
continuations. Comma-separated lines without continuation are separate
properties: compilation can pass while the bundle omits every class and
`plugin.xml`. Inspect the actual JAR, not just `target/classes`.

Include icons, localization, schemas and other runtime assets if present.
Inspect packaged resources after compilation. Feature definitions select
bundles; `category.xml` selects featured installable units for a p2 repository.
A bundle JAR is not itself a complete p2 update site.

[target-1]: https://tycho.eclipseprojects.io/doc/latest/TargetPlatform.html

## Debug and distribute

Launch an Eclipse Application from PDE using the target and a disposable
workspace (`-data /path/to/case-workspace`). Inspect Error Log and bundle
resolution when a contribution is missing: check extension ID, class name,
exported dependencies and execution environment before editing UI code. In an
OSGi console, `ss` and `diag BUNDLE_ID` can expose unresolved requirements when
console support is configured.

If the native launcher fails before Equinox starts, check its JVM selection
separately from bundle resolution. Pass `-vm /absolute/jdk/bin/java` before
`-vmargs`, using a JDK compatible with the target and launcher architecture. In
`eclipse.ini`, put `-vm` and the path on separate lines before `-vmargs`. A
working shell `java` does not prove native-launcher discovery: on macOS, an
unselected JVM can fall back to the legacy system JavaVM framework and fail with
a missing `JNI_CreateJavaVM` symbol. Prefer an explicit launcher JVM over
changing system Java settings. [Launcher configuration][launcher-config].

For a local p2 check, the director application accepts `-application
org.eclipse.equinox.p2.director`, `-repository file:/absolute/repository`,
`-installIU com.example.feature.feature.group`, and a dedicated
`-destination`/`-profile`; select the platform environment when materializing
another platform. Do not target the user's normal IDE. Clean install and upgrade
resolution are different checks. [p2 director][distribution-1].

Use API Tools/baselines when exported API changes, Tycho/PDE tests for runtime
contracts, and inspect repository metadata/artifacts for packaging. Verify the
published update-site metadata and artifact hashes after distribution. Refresh a
target-specific extension schema or Tycho keyword only when it differs from the
selected version. Read [jobs and resource ownership](jobs-and-resources.md) for
scheduling and lifecycle contracts.

[distribution-1]:
https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/p2_director.html
[testing-guide]: https://tycho.eclipseprojects.io/doc/5.0.4/TestingBundles.html
[standalone-demo]:
https://github.com/eclipse-tycho/tycho/blob/tycho-5.0.4/demo/testing/tycho/standalone/test/pom.xml
[api-1]: https://github.com/eclipse-tycho/tycho/releases/tag/tycho-5.0.4
[api-2]: https://tycho.eclipseprojects.io/doc/latest/
[launcher-config]:
https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/misc/launcher_ini.html
