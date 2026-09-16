# IntelliJ Platform starter

Replace placeholders. Select compatible Gradle, IntelliJ Platform Gradle plugin,
Kotlin, Java, and IDE versions. Generate the Gradle wrapper. Set
`__PLATFORM_TYPE__` for the selected distribution: downloadable IntelliJ IDEA
2025.3+ uses `IU`; `IC` applies to older Community distributions.

Use a vendor-owned reverse-domain plugin ID, a specific product name that does
not contain the generic word “plugin,” and a useful Marketplace description.

Leave `untilBuild` unset for current IntelliJ Platform releases unless a known
incompatibility requires a deliberate upper bound.

The project build declares dependency repositories. Do not forbid project
repositories in settings. Declare required platform/plugin dependencies and
verifier targets.

Replace the example action and test with the feature. Run affected tests. Run
Plugin Verifier for compatibility changes. Build and inspect the plugin ZIP for
packaging changes.

The example uses `EditorAction` with `EditorWriteActionHandler.ForEachCaret` for
UTF-8 form-value encoding. The platform owns write access, per-caret dispatch,
read-only handling, and command/undo integration; do not wrap the same action in
another custom transaction framework. Empty selections are unchanged. This is
not a whole-URL or URI-path encoder.

The platform fixture tests execute the registered editor action, including
multiple selections, selection preservation, one undo, and a caret-only no-op.
They use the JUnit 3/4-compatible platform fixture with Gradle's JUnit runner,
not a detached assertion about a resource string. Check test counts and failures
before accepting the result. Model fixtures do not establish Swing UI rendering
or plugin unload behavior.
