# JetBrains extension evaluation

Evaluated on 2026-09-12. The skill remains explicit-only. Eleven reference files
were inspected and consolidated into two coherent references.

## Implementation and behavior

Replaced the greeting action and resource-string test with a form-value encoder
and actual platform editor fixtures. The action uses `EditorAction` and
`EditorWriteActionHandler.ForEachCaret`, verified against the installed target's
class signatures and the [upstream implementation][handler]. The platform owns
per-caret execution, write access, read-only handling and command integration.
No parallel transaction framework, custom serializer or PSI pipeline was added.

Java's UTF-8 `URLEncoder` encodes each nonempty selection, then the action
selects the replacement. This is form-value encoding, not encoding a whole URL
or URI path. Removed the unused greeting resource bundle and wrapper. Gradle
patching now owns plugin identity, name, vendor and compatibility metadata; the
descriptor owns the contributed action and description.

Two `BasePlatformTestCase` tests execute the registered editor action. They
check multiple selections with Unicode, spaces and literal plus signs, an empty
caret, replacement selections, one undo restoring the original document, and a
caret-only operation preserving the modification stamp. The selected platform
fixture uses the JUnit 3/4-compatible Gradle runner; the obsolete Kotlin
resource assertion dependency was removed after replacing its consumer.

A temporary mutation returned the unencoded selection. The real platform test
failed its output comparison and Gradle returned failure. The fixture was then
restored. This establishes failure detection, not just successful discovery.

## Toolchain, distribution and verifier

The evaluation used Gradle 9.7.1, Kotlin 2.4.0, Java 25.0.4.1 and IntelliJ
Platform Gradle plugin 2.18.1. The actual installed IDE reports IntelliJ IDEA
OSS 2026.2.2, product IC, build 262.10315.125.

The temporary fixture used the installed IDE through `local(...)` for
compilation and verification. This avoids another IDE download but does not
validate remote artifact resolution. The starter's product type is now an
explicit placeholder: current downloadable IntelliJ IDEA 2025.3+ uses IU,
whereas the installed OSS build can still report IC. Those are distinct
contracts; see [product types][types].

`test`, `buildPlugin`, `verifyPluginProjectConfiguration` and `verifyPlugin`
passed. Test XML independently reports two tests with no errors, failures or
skips. The final ZIP contains the plugin JAR and the expected action class, not
tests or the retired greeting. Its patched descriptor contains the selected
identity, name, vendor and `since-build="262"`.

Plugin Verifier 1.410 initially rejected the fixture's reserved `com.example`
plugin ID. The fixture was corrected to a repository-owner namespace without
muting the diagnostic or publishing anything. Verification then reported
compatibility with IC-262.10315.125. That is evidence for this exact build, not
an open-ended product/version matrix. The dynamic-plugin eligibility result is a
static assessment, not proof of a real unload cycle.

## Sandbox host evidence

A bounded `runIde` launch started the actual IDE with configuration, system and
log paths under the temporary Gradle sandbox. Its log reports the custom
Selection Tools extension loaded. The owned launch process tree was terminated
after the observation window and confirmed gone. No normal IDE profile was used.

The host also reported missing built-in modules, a project-store override,
startup-state ordering and JCEF platform warnings. These were not suppressed or
attributed conclusively to a root cause. The launch establishes plugin loading,
not a clean full-UI session. Action execution is established by the model
fixtures, not by a simulated claim of clicking a menu. No UI rendering, unload,
publication or signing workflow is claimed.

## Guidance corrections and evidence

Removed mandatory settings-schema versioning and an incomplete text-insertion
fragment. Retained actual persisted-state migration boundaries, PSI/read-write
contracts, cancellation, disposal and distribution guidance.

Evidence artifacts:

- `/tmp/jetbrains-skill-baseline.log`
- `/tmp/jetbrains-skill-test.log`
- `/tmp/jetbrains-skill-mutant.log`
- `/tmp/jetbrains-skill-forbidden-id.log`
- `/tmp/jetbrains-skill-verifier.log`
- `/tmp/jetbrains-skill-runide.log`
- `/tmp/jetbrains-skill-evidence/build/reports/pluginVerifier/`
- `/tmp/jetbrains-skill-evidence/.intellijPlatform/sandbox/`

The remaining full repository goal is not established by this package's checks.

[handler]:
  https://github.com/JetBrains/intellij-community/blob/master/platform/platform-api/src/com/intellij/openapi/editor/actionSystem/EditorWriteActionHandler.java
[types]:
  https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-types.html
