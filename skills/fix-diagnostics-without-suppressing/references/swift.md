# Swift

Read when swiftc, SwiftPM, Xcode, or SwiftLint reports a diagnostic. Facts come from the Swift
compiler docs, swift-evolution proposals, The Swift Programming Language (TSPL), the Swift migration
guide, and the SwiftLint docs. Where a source did not say, this file says so.

Versions checked on 2026-10-06: Swift 6.4.0 (released 2026-09-15), SwiftLint 0.65.1 (docs header;
not cross-checked as the newest release).

## Contents

- [Find the Diagnostic Group](#find-the-diagnostic-group)
- [Suppression Forms to Refuse](#suppression-forms-to-refuse)
- [Config Keys That Loosen Checks](#config-keys-that-loosen-checks)
- [Stale Suppressions](#stale-suppressions)
- [Deprecations and Replacements](#deprecations-and-replacements)
- [Strict CI Form](#strict-ci-form)
- [Not Verified](#not-verified)

## Find the Diagnostic Group

Compile with `-print-diagnostic-groups`. The compiler prints the narrowest group name in brackets
after each warning (SE-0443). Open the page named after the group in the compiler's diagnostics docs
(`userdocs/diagnostics` in swiftlang/swift, rendered at docs.swift.org/compiler/documentation/
diagnostics/; the rendered site needs JavaScript). The index is `diagnostic-groups.md`. Group names
are stable and only grow, for example `DeprecatedDeclaration` sits inside `Deprecated`.

## Suppression Forms to Refuse

| Form | What it does |
| --- | --- |
| `@diagnose(Group, as: ignored, reason: "...")` (SE-0522) | Per-declaration warning control; `ignored` silences the group in that scope |
| `-suppress-warnings` | "Disables the emission of all warnings" |
| `-Wwarning Group` | Keeps a group as a warning "even if previously suppressed or upgraded to errors" |
| `-no-warnings-as-errors` | Turns off warnings as errors |
| `nonisolated(unsafe)` | Disables all isolation checking for a variable |
| `@unchecked Sendable` | "Turn off enforcement of that protocol's requirements"; Sendable is the only supported protocol |
| `@preconcurrency` on a declaration or import | "Suppress strict concurrency checking"; on an import it downgrades diagnostics |
| `// swiftlint:disable ...` and the `:next`, `:this`, `:previous` forms | SwiftLint comment commands |
| `// swiftlint:disable all` | Disables every SwiftLint rule until `enable all` |

Notes:

- `@diagnose` is available since Swift 6.4 (SE-0522, status "Implemented (Swift 6.4)"). Its
  grammar is `@diagnose(<group>, as: <behavior>, reason: <static string literal>)` with `error`,
  `warning`, or `ignored` as the behavior; `reason` is optional. It works per declaration, not per
  line or statement, and only on warnings: compile errors "cannot be controlled". The proposal
  header still lists the experimental feature flag `SourceWarningControl`. Whether 6.4 still
  requires that flag is unverified.
- The compiler docs read for this file show no `#pragma`-style or comment-based suppression in
  swiftc. This is absence in the sources read, not a proof.
- `nonisolated(unsafe)` is for state you guard with a lock or dispatch queue. The compiler note says
  to use it only if all accesses are protected by an external synchronization mechanism. For
  `MutableGlobalVariable`, the documented fix is to make the state immutable or protect it with a
  global actor.
- Lowering the language mode or the strictness is a suppression too; see the next section.

## Config Keys That Loosen Checks

| Setting | Where | Loosens when |
| --- | --- | --- |
| `-suppress-warnings` | swiftc | Present at all; position-independent; wins over `-no-warnings-as-errors`; cannot combine with `-Wwarning` or `-Werror` (compiler error) |
| `-no-warnings-as-errors`, `-Wwarning Group` | swiftc | Present after `-warnings-as-errors` or `-Werror`; flags apply left to right and "the last one wins" |
| `.treatAllWarnings(as: .warning)`, `.treatWarning("Group", as: .warning)` | SwiftPM `swiftSettings` (SE-0480, Swift 6.2) | Present; they map to `-no-warnings-as-errors` and `-Wwarning Group` |
| `unsafeFlags([...])` | SwiftPM `swiftSettings` | Used to pass the loosening flags above; SE-0480 names it as the workaround that `treatWarning` replaces |
| `SWIFT_SUPPRESS_WARNINGS` ("Don't emit any warnings.") | Xcode | Set to YES |
| `SWIFT_TREAT_WARNINGS_AS_ERRORS` | Xcode | Removed or set to NO |
| `swiftLanguageModes: [.v5]`, `-swift-version 5`, `-language-mode 5` | SwiftPM, swiftc | A package or target moves to a lower mode; `SWIFT_VERSION` is the Xcode setting |
| `-strict-concurrency=minimal` or `targeted`, `SWIFT_STRICT_CONCURRENCY` below `complete` | swiftc, Xcode | Lowered; Xcode says it is always `complete` in Swift 6 mode |
| `disabled_rules`, `excluded`, `only_rules`, `lenient: true` | `.swiftlint.yml` | Rule disabled, path excluded, rule set narrowed, errors lowered to warnings |
| `baseline`, `write_baseline` | `.swiftlint.yml` | A baseline filters out detected violations |

Notes:

- The migration guide enables data-race safety with `swiftLanguageModes`, `-swift-version 6` through
  `-Xswiftc`, `-strict-concurrency=complete` (warnings in Swift 5 mode), or Xcode
  `SWIFT_STRICT_CONCURRENCY = complete`. Moving a package from mode 6 to 5, or lowering strict
  concurrency, turns data-race errors into warnings or silence. That reading follows from the guide
  and is not a quoted statement of it.
- SE-0441 (Swift 6.1) made `-language-mode` the same as `-swift-version`, and SwiftPM's
  `swiftLanguageModes` replaces `swiftLanguageVersions`.
- `-enable-upcoming-feature X` and SwiftPM `.enableUpcomingFeature("X")` add checks. A misspelled
  feature name is silently ignored unless the `StrictLanguageFeatures` group is enabled.
- SwiftLint keys that tighten, not loosen: `strict: true` ("treat all warnings as errors") and
  `opt_in_rules`.

## Stale Suppressions

| Tool | Detection |
| --- | --- |
| SwiftLint | `superfluous_disable_command`: a `disable` is superfluous "when the disabled rule would not have triggered a violation in the disabled region". Enabled by default, severity warning. Follow a command with a dash and a reason to document it |
| SwiftLint | `blanket_disable_command`: `swiftlint:disable` should use `next`, `this`, or `previous`, or be re-enabled immediately. Enabled by default, severity warning. `allowed_rules` defaults to `file_header`, `file_length`, `file_name`, `file_name_no_space`, `single_test_class`; `always_blanket_disable` defaults to empty |
| `@preconcurrency import` | The `PreconcurrencyImport` group finds extraneous ones. It is "experimental and disabled by default" |
| `@diagnose`, `nonisolated(unsafe)`, `@unchecked Sendable` | No stale-suppression detection is documented in the sources read |
| Compiler warning-control flags | No stale-suppression detection is documented in the sources read |

A warning for a group name the compiler does not know, `unknown warning group: 'x'`, can be made an
error with the `UnknownWarningGroup` group.

## Deprecations and Replacements

- Read the `@available` attribute on the declaration. `message:` is the text the compiler shows for
  a deprecated, obsoleted, or `noasync` use. `renamed:` names the new declaration, and the compiler
  shows the new name when it reports a use of a renamed declaration.
- The `DeprecatedDeclaration` page documents the form
  `@available(iOS, deprecated: 10.0, renamed: "newFunction")`, which reports
  `'oldFunction()' is deprecated: renamed to 'newFunction'`.
- Swift 5.9 and later provide `#warning` and `#error` as the standard library macros `warning(_:)`
  and `error(_:)` (originally SE-0196). Treat a `#warning` in code you touch as a diagnostic to fix.
- Release notes and the migration guide: github.com/swiftlang/swift-migration-guide, and
  swift.org/blog for each release.
- To remove an `@preconcurrency` after dependencies migrate, follow the TSPL note that it is a
  stopgap until clients migrate.

## Strict CI Form

| Goal | Form |
| --- | --- |
| All warnings are errors | `swiftc -warnings-as-errors`, or SwiftPM `.treatAllWarnings(as: .error)`, or Xcode `SWIFT_TREAT_WARNINGS_AS_ERRORS = YES` |
| One group is an error | `-Werror Group`, or `.treatWarning("Group", as: .error)` |
| See groups in the log | `-print-diagnostic-groups` |
| Typo in a group name fails | Enable the `UnknownWarningGroup` group as an error |
| Lint | `swiftlint --strict`, or `strict: true` in `.swiftlint.yml` |

Do not append `-Wwarning Group` or `-Wwarning` flags after these to make a build pass.

## Not Verified

- Whether Swift 6.4 still requires the `SourceWarningControl` flag for `@diagnose`.
- SwiftPM restrictions on `unsafeFlags`, the Xcode way to pass `-Werror Group` through
  `OTHER_SWIFT_FLAGS`, and whether `deprecated` plus `renamed:` yields an automatic fix-it.
- The spelling of the SwiftLint CLI flags for baselines and `lenient`, and `warning_threshold`; only
  the config keys are confirmed. `swiftlint --fix --strict` appears in the README.
- Whether `#warning` can be silenced with `-Wwarning`, `swift --explain`, and the trade-offs of each
  concurrency escape hatch beyond the quotes above.
