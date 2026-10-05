# Kotlin

Read when kotlinc, the Kotlin Gradle plugin, Gradle, detekt, or ktlint reports a diagnostic. Facts
come from the kotlinlang docs, the Gradle docs, and the detekt and ktlint docs. Where a source did
not say, this file says so.

Versions checked on 2026-10-06: Kotlin 2.4.20 (stable, 2026-09-07), Gradle 9.8.0 (2026-10-01),
detekt 2.0.0-alpha.6 (newest in the docs; newest 1.x is 1.23.8; stable status unverified), ktlint
docs at ktlint.github.io (install page shows 2.0.0-ALPHA-4; 1.8.0 looks like the latest stable,
unverified).

## Contents

- [Suppression Forms to Refuse](#suppression-forms-to-refuse)
- [Config Keys That Loosen Checks](#config-keys-that-loosen-checks)
- [Stale Suppressions](#stale-suppressions)
- [Deprecations and Replacements](#deprecations-and-replacements)
- [Strict CI Form](#strict-ci-form)
- [Not Verified](#not-verified)

## Suppression Forms to Refuse

| Form | Tool | Notes |
| --- | --- | --- |
| `@Suppress("NAME")` | kotlinc | "Suppresses the given compilation warnings in the annotated element"; targets include file, expression, local variable, type |
| `@file:Suppress("NAME")` | kotlinc, detekt, ktlint | Same annotation at file target |
| `@OptIn(Marker::class)` | kotlinc | "Its usages are not required to opt in to that API"; accepts the risk locally |
| `@Suppress("detekt:Rule")`, `@Suppress("style")`, `@Suppress("all")` | detekt | Prefixes `detekt:`, `detekt.all`, and rule-set names are accepted |
| `@SuppressWarnings("Rule")` | detekt, ktlint | Kotlin's `@Suppress` is favored when both are present |
| `@Suppress("ktlint")`, `@Suppress("ktlint:rule-set-id:rule-id")`, `@file:Suppress("ktlint")` | ktlint | Whole tool, one rule, or one file |
| `// ktlint-disable` and `ktlint-enable` | ktlint | Removed as a suppression mechanism in 0.50; a built-in rule converts them (release note not read) |
| `detektBaseline` task, `--baseline`, `--create-baseline` | detekt | Baseline files hide existing findings |
| `ktlint --baseline=ktlint-baseline.xml` | ktlint | "Violations that are registered in the baseline, will be ignored silently" |

Notes:

- Rules inside detekt's ktlint wrapper (the `formatting` rule set) can only be suppressed at file
  level. A rule such as `TooManyFunctions` needs a file annotation,
  `@file:Suppress("TooManyFunctions")`.
- For opt-in, the honest form is propagation: annotate your own declaration with the marker
  annotation, not `@OptIn`. The docs warn that without propagation "others might unknowingly use
  experimental APIs".
- ktlint's FAQ says suppression "is meant primarily as an escape latch for the rare cases when
  ktlint is not able to produce the correct result" and asks that such cases be reported.
- `!!` is not documented as a diagnostic suppression in the pages read. Treat it as a suppression
  in another form when it only quiets a nullability error (rule in SKILL.md); this is judgment, not
  a documented fact.

## Config Keys That Loosen Checks

| Setting | Where | Loosens when |
| --- | --- | --- |
| `-nowarn` ("Suppress all warnings during compilation") | kotlinc | Present |
| `-Xwarning-level=NAME:disabled` ("suppresses only the specified warning module-wide") | kotlinc | Present |
| `-Xwarning-level=NAME:warning` after `-Werror` | kotlinc | Present; it exempts one diagnostic from `-Werror` |
| Dropping `-Werror` | kotlinc | Removed |
| `suppressWarnings` ("Don't generate warnings"; default false) | Gradle Kotlin DSL `compilerOptions` | Set to true |
| `allWarningsAsErrors` ("Report an error if there are any warnings"; default false) | Gradle Kotlin DSL | Removed or set to false |
| `--warning-mode=none` or `summary` | Gradle | Hides detail; `none` suppresses all warnings including the summary. Default is `summary`. Also `org.gradle.warning.mode` |
| `config: validation: true`, `warningsAsErrors: false` | detekt.yml | Governs config validation only, not code findings; invalid or deprecated config options print as warnings unless it is true |
| `.editorconfig` `ktlint_standard_<rule> = disabled`, `ktlint_<ruleset> = disabled` | ktlint | Rule or rule set disabled; rule ids use hyphens |
| `disabled_rules`, `ktlint_disabled_rules` | ktlint `.editorconfig` | Deprecated properties; also a loosening |
| Baseline files | detekt, ktlint | See above |

Notes:

- `-Xwarning-level=NAME:error` and `-Werror` tighten. `-Xrender-internal-diagnostic-names` prints
  the NAME of each diagnostic. Many `-Xwarning-level` entries can go in an `@argfile`.
- Classifying the flags above as loosening or tightening is an inference from their documented
  meaning.
- detekt `maxIssues`, `active: false`, and per-rule `excludes` are not covered by the sources. The
  names are expected to loosen when raised, disabled, or widened, but this is unverified.

## Stale Suppressions

| Tool | Detection |
| --- | --- |
| kotlinc | No stale-suppression detection is documented in the sources read |
| detekt | None documented in the sources read. Baseline files have `ManuallySuppressedIssues` and `CurrentIssues` sections; regenerating one is a change that needs approval |
| ktlint | None documented in the sources read |
| Gradle | Not applicable; `--warning-mode` is about Gradle's own deprecation warnings |

Without detection, search for suppressions in the files you touch and report ones that no longer
match a finding. Do not remove them without asking, unless they are in scope (see SKILL.md).

## Deprecations and Replacements

- `@Deprecated` has levels `WARNING` (default, notifies consumers without breaking), `ERROR` ("no
  new Kotlin code can be compiled using the deprecated API"), and `HIDDEN` (usages look like
  unresolved references). Read the level before assuming the diagnostic is final.
- `ReplaceWith(expression, vararg imports)` on the declaration names the replacement; "tools such
  as IDEs can automatically apply the replacements". Use the IDE "Replace with" quick fix, or apply
  the same expression by hand, including the listed imports.
- `@Suppress("DEPRECATION")` is the matching suppression. Its exact name is not confirmed in the
  kotlinlang text read; it is widely used.
- Gradle deprecation warnings: run with `--warning-mode=all` for details. The upgrade guides are
  `docs.gradle.org/current/userguide/upgrading_version_9.html`, with sibling pages
  `upgrading_version_8` and `upgrading_version_7`. The 9.8.0 section was not read.
- Release notes: kotlinlang.org/docs/releases.html. detekt 1.x baselines are not compatible with
  detekt 2.x (the separator changes from `$` to `:`), so they must be regenerated; that is a
  baseline change, so ask first.

## Strict CI Form

| Goal | Form |
| --- | --- |
| Warnings fail the Kotlin build | `-Werror`, or Gradle `allWarningsAsErrors = true` |
| One diagnostic fails | `-Xwarning-level=NAME:error` |
| Gradle deprecations fail | `--warning-mode=fail` (logs all warnings and fails if there are any); `all` logs only |
| Config problems fail detekt | `warningsAsErrors: true` under `config:`; code findings are unaffected |

Do not combine these with `-nowarn` or a baseline.

## Not Verified

- `-Xsuppress-warning`: it does not appear in the compiler reference read; treat as unknown.
- detekt `maxIssues`, `active`, `excludes`, and stable versus alpha status.
- ktlint 1.8.x versus 2.0 alpha, and the 0.50 release note.
- The `@file:Suppress` form on kotlinlang pages (detekt docs use it) and `@Suppress("DEPRECATION")`.
- Any `!!` guidance in a primary source.
