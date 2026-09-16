# IntelliJ descriptors, compatibility and resource ownership

Target-dependent API reference. Current platform documentation includes
**2026.2**, and an example Gradle plugin version recorded in the source archive
is **2.18.1** ([release][source-2]). EAP/proposed APIs are not a stable
baseline.

[source-2]:
https://github.com/JetBrains/intellij-platform-gradle-plugin/releases/tag/2.18.1

## Resolve product and runtime contracts

For downloadable 2025.3+ IntelliJ IDEA targets use `IU`, not legacy `IC`;
PyCharm uses `PY`, not legacy `PC`. An installed OSS build can still report `IC`
in its product metadata: local-installation metadata is not proof that a
matching downloadable `ideaIC` artifact exists. [Product types][product-types].

Compile against the oldest supported IDE product/build and verify the declared
matrix. Descriptor `since-build`/`until-build` use platform build numbers, not
the plugin's version; `until-build="261.*"` covers a branch, while omitting it
claims open-ended compatibility. Determine actual product build IDs rather than
inferring them from the year: current tables and product release metadata can
diverge. Java runtime requirements also change (current 2026.2 docs list Java
25; 2024.2–2026.1 list 21). Select Java from the target IDE runtime
requirements. [Build ranges][resolve-product-and-runtime-contracts-1].

A descriptor fragment for a platform-only action:

```xml
<idea-plugin>
  <id>com.example.inspect</id>
  <name>Example Inspect</name>
  <vendor>Example</vendor>
  <depends>com.intellij.modules.platform</depends>
  <actions>
    <action id="Example.Inspect" class="com.example.InspectAction"
            text="Inspect Selection">
      <add-to-group group-id="ToolsMenu" anchor="last"/>
    </action>
  </actions>
</idea-plugin>
```

Add Java/Kotlin/product plugin dependencies only for APIs actually used. Gradle
compile dependencies and descriptor runtime dependencies must agree. Optional
dependencies use a separate descriptor (`optional="true" config-file="..."`) so
absent plugin classes are not loaded eagerly. Keep one owner for values patched
by Gradle. [Descriptor schema][resolve-product-and-runtime-contracts-2].

[resolve-product-and-runtime-contracts-1]:
https://plugins.jetbrains.com/docs/intellij/build-number-ranges.html
[resolve-product-and-runtime-contracts-2]:
https://plugins.jetbrains.com/docs/intellij/plugin-configuration-file.html

## Gradle build and verification

The 2.x plugin uses `org.jetbrains.intellij.platform`, platform dependency
repositories and an `intellijPlatform` dependency block. Resolve starter
placeholders, Gradle wrapper, and target versions before building. The plugin
version is independent of the IDE and the plugin's release version. [Gradle
plugin][gradle-build-and-verification-2].

`./gradlew runIde` launches a sandbox IDE; `test` runs configured tests;
`buildPlugin` creates a distributable ZIP; `verifyPlugin` checks binary
compatibility against configured IDEs. Use `verifyPluginProjectConfiguration`
for inconsistent setup. Inspect the patched descriptor and ZIP resources.
Resolve missing-class verifier errors against product dependencies.
[Tasks][gradle-build-and-verification-1].

[gradle-build-and-verification-1]:
https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-tasks.html
[gradle-build-and-verification-2]:
https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin.html

## Service and disposal ownership

Use project services for project state, application services for truly shared
state, and shorter parents for dialogs/tool-window content. A service
implementing `Disposable` is disposed on its service lifetime, including unload.
An arbitrary extension implementing `Disposable` is not automatically
registered. Prefer the API's `parentDisposable` overload or `Disposer.register`
with a plugin-owned service. Using the raw Project/Application as parent can
outlive a dynamic plugin unload. [Disposer][ref-disposer].

Keep static fields free of Project, PSI, classloader-sensitive callbacks and
long-lived executors. Cancel service-owned coroutines and remove listeners at
shutdown. A cache key may use stable file identity, but invalidate cached
semantics on relevant changes. User state belongs in supported persistent-state
services, not a global singleton retaining IDE objects. Migrate existing
persisted settings only when their representation or meaning actually changes.
Add a version discriminator only for a real compatibility boundary, not every
new preference. [Services][ref-services], [persistent
state][service-and-disposal-ownership-1].

[service-and-disposal-ownership-1]:
https://plugins.jetbrains.com/docs/intellij/persisting-state-of-components.html

## Diagnose and distribute

Break on activation/action entry in `runIde`, inspect `idea.log`, and reproduce
with the supported product and indexing state. For dynamic unload failures,
inspect leaked listeners and threads as well as the descriptor. Test action
visibility, project close and affected reload behavior where relevant. Check the
declared compatibility range with Plugin Verifier and the affected product
behavior. For PSI and asynchronous mutation, read [model
access](psi-and-threading.md).

## Release procedure

Run `buildPlugin`, inspect the ZIP and patched descriptor, and run the
configured compatibility checks before preparing publication. Signing uses the
Gradle plugin's `signPlugin` task with the certificate chain, private key and
password supplied through secure configuration; verify the signed artifact with
`verifyPluginSignature`. Keep signing material out of the archive/repository and
do not change dependency packaging to hide verifier errors.
[Signing][ref-signing].

The first Marketplace upload must be manual: use the publishing account's **Add
new plugin** form with the signed artifact and concrete listing metadata. Later
releases can use `publishPlugin` with a securely configured publishing token and
intended channel, or upload through the existing plugin page. Inspect the
published version and declared IDE range afterward; confirm the version on the
Marketplace listing. For a private repository, provide its update metadata and
artifact URLs under that distribution contract rather than claiming Marketplace
registration. [Publication][release-procedure-1].

[release-procedure-1]:
https://plugins.jetbrains.com/docs/intellij/publishing-plugin.html
[product-types]:
https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-types.html

[ref-disposer]: https://plugins.jetbrains.com/docs/intellij/disposers.html
[ref-services]: https://plugins.jetbrains.com/docs/intellij/plugin-services.html
[ref-signing]: https://plugins.jetbrains.com/docs/intellij/plugin-signing.html
