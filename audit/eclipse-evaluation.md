# Eclipse plug-in evaluation

Evaluated on 2026-09-12. The skill remains explicit-only. Eight overlapping
reference fragments were reviewed and consolidated into two references.

## Behavioral implementation

The starter now contributes a form-value encoding command instead of a greeting.
It uses Java's UTF-8 `URLEncoder`, not a custom encoder. It operates on the
editor's unsaved document, selects the replacement and leaves saving to the
user. This is form-value encoding, not whole-URL or URI-path encoding.

Three real workbench tests exercise:

- UTF-8, spaces and literal plus signs, unsaved-buffer precedence, selected
  replacement, a single undo, and unchanged file contents;
- a caret-only selection leaving the document clean and unchanged;
- rejection of disjoint and block selections without modifying intervening text.

The tests execute the contributed command through the workbench handler service,
not by calling a detached string helper. They use temporary files and a separate
Tycho workbench workspace. No user's normal workspace is opened.

## Defects found by actual execution

The original `build.properties` split comma-separated values across lines
without Java-properties continuation backslashes. The reactor compiled
successfully, but the actual bundle JAR contained neither `plugin.xml` nor
handler classes. Both bundle include lists now use a single property line. The
packaged and installed JARs contain the contribution and handler class.

The first implementation treated `TextSelection.isEmpty()` as zero selected
characters. A real test failed because a no-op replacement made the editor
dirty. The corrected length check passed the same test. The distinction is
confirmed by the [TextSelection API][selection].

Cocoa rejected the UI test JVM without `-XstartOnFirstThread`. A macOS-only
Maven profile now supplies it. Tests retain their real UI harness, UI-thread
execution, and a 120-second process timeout. Missing direct OSGi dependencies
were fixed in the test manifest, without relaxing compiler access restrictions.

The pinned Tycho standalone demo uses the existing `test` goal with explicit
`eclipse-plugin` packaging configuration. Actual Equinox execution confirmed
this works, despite the generic goal summary's narrower wording. It was not
replaced based on that summary alone. The alternative `plugin-test` and `verify`
pair has different discovery and lifecycle requirements. See the [pinned
demo][demo].

## Toolchain and package evidence

The instantiated reactor used Maven 3.9.16, Java 25.0.4.1, Tycho 5.0.4,
JavaSE-21 bundle execution environments, and macosx/cocoa/aarch64. Its target
was [Eclipse Platform 4.40, R-4.40-202606010713][target], not a moving latest
site.

`mvn clean verify` passed all five modules. Surefire XML reports three tests,
zero failures, zero errors and zero skipped tests. The reactor built the feature
and p2 repository, and actual JAR inspection confirmed packaged runtime assets.

An official Eclipse Platform 4.40 macOS aarch64 DMG was downloaded, checked
against the official SHA-512 checksum, mounted read-only, copied into an
isolated temporary directory, and detached. The actual p2 director installed the
generated feature into that copy's SDKProfile. A separate `-listInstalledRoots`
invocation confirmed the installed feature. The installed bundle contains both
the handler class and `plugin.xml`.

The native launcher returned 254 and displayed a legacy Apple JavaVM framework
error. Direct execution of the Equinox launcher JAR with the tested JDK
completed the p2 operations successfully. No system Java settings or quarantine
attributes were changed. This proves p2 installation, not successful
native-launcher UI startup. Real UI behavior was tested through Tycho's direct
Java launch.

## Guidance and evidence limits

Removed an incomplete background-job scaffold in favor of lifecycle decisions.
Documented the Display scheduling/disposal boundary. Corrected blanket SWT Color
disposal advice: the [current Color API][color] does not require disposal. Other
owned SWT resources retain their documented disposal requirements.

No Marketplace publication, p2 upgrade, exported API baseline comparison,
Windows/Linux UI execution, native-launcher repair, or unrelated workspace/job
feature is claimed. Those checks apply when the affected feature requires them.

Evidence files retained outside the repository:

- `/tmp/eclipse-skill-baseline.log`
- `/tmp/eclipse-skill-empty-selection-failure.log`
- `/tmp/eclipse-skill-ui.log`
- `/tmp/eclipse-skill-evidence/` (instantiated reactor and Surefire reports)
- `/tmp/eclipse-install-evidence/install-java.log`
- `/tmp/eclipse-install-evidence/roots.log`

The skill validator, strict Markdown, XML parsing and diff checks passed. These
are supplementary to real host/package evidence, not proof of full goal
completion.

[selection]:
  https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/jface/text/TextSelection.html
[demo]:
  https://github.com/eclipse-tycho/tycho/blob/tycho-5.0.4/demo/testing/tycho/standalone/test/pom.xml
[target]: https://download.eclipse.org/eclipse/updates/4.40/R-4.40-202606010713
[color]:
  https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/swt/graphics/Color.html
