# Scala

Read when scalac (2.13 or 3), sbt, or scalafix reports a diagnostic. Facts come from the
scala-lang.org docs, the sbt docs, and the scalafix docs. Where a source did not say, this file says
so.

Versions checked on 2026-10-06: Scala 2.13.18 (2025-11-24), Scala 3.9.0 LTS (2026-09-03), Scala
3.3.8 LTS (2026-06-10), sbt 2.0.9 (and 1.12.9 on the 1.x line), sbt-scalafix 0.14.9 (supports Scala
2.12.21, 2.13.18, 3.9.0).

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
| `@nowarn`, `@nowarn("cat=deprecation")`, `@nowarn("cat=deprecation&msg=...")` | scalac | Local suppression; same filter syntax as `-Wconf`; takes precedence over `-Wconf` and `-Werror` |
| `-Wconf:...:s` (silent), `-Wconf:any:s` | scalac | Filters pick warnings by `cat`, `msg`, `site`, `src`, `origin`, `since`, joined with `&` |
| `-nowarn`, `--no-warnings` ("Generate no warnings") | scalac | Whole compilation |
| `// scalafix:ok`, `// scalafix:ok Rule` | scalafix | Suppresses the whole expression; may come before or after it |
| `// scalafix:off` ... `// scalafix:on`, with an optional comma list of rules | scalafix | Region form |
| `@SuppressWarnings(Array("scalafix:Rule"))` | scalafix | Detected syntactically: any `@SuppressWarnings(..)` matches regardless of its package. Takes precedence over comments |

Notes:

- The scalafix page says suppression is for linters, and for linters only. Rewrite rules, such as
  `OrganizeImports`, are not suppressed this way (a reading of partly extracted text).
- Under `-Xsource:3`, migration warnings are errors by default (`-Wconf:cat=scala3-migration:e`).
  Turning them into warnings with `cat=scala3-migration:w` defers the migration; it does not fix it.
- Whether `@nowarn` in Scala 3 behaves the same was not read; the annotation exists in the 3.x API.

## Config Keys That Loosen Checks

| Setting | Where | Loosens when |
| --- | --- | --- |
| `-nowarn`, `--no-warnings` | scalacOptions | Added |
| `-Wconf:...:s`, `-Wconf:any:s`, or a `w` or `i` action for a category that was `e` | scalacOptions | Added |
| `-Werror` | scalacOptions | Removed (`scalacOptions -= "-Werror"`); `-Xfatal-warnings` is the older name (rename not verified) |
| `-Xsource:3` with `-Wconf:cat=scala3-migration:w` | scalacOptions | Used to keep migration warnings non-fatal |
| `-source:3.0-migration` or `future-migration` | scalacOptions | Turns migration errors into warnings; with `-rewrite` it rewrites sources |
| `evictionErrorLevel := Level.Info` | sbt | Set; hides eviction errors |
| `libraryDependencySchemes` | sbt | Used to opt out of an eviction error |
| Scalafix `.scalafix.conf` rule removed or `Disable*` entries relaxed | scalafix | Not covered by the sources; not researched |

Notes:

- Tightening: `-Werror`, `-Xlint`, `-Wunused:*`, and `-Wconf` actions `e`.
- The sbt 2.x docs say eviction errors are enforced in the Test configuration, and the error text
  says "this can be overridden using `libraryDependencySchemes` or `evictionErrorLevel`". Those two
  are the opt-outs to refuse. The Test-configuration statement comes from a search-snippet summary.
- `-Wconf` action letters are `s`, `e`, `w`, `i`. `-Wconf:any:wv` shows the category of each
  warning, and `-Wconf:help` lists the categories. The action section of the blog was only partly
  extracted.
- The Scala 3 `-Wconf` syntax and messages differ from 2.13: "the configuration string for -Wconf
  will likely require adjustment when migrating to Scala 3".

## Stale Suppressions

| Tool | Detection |
| --- | --- |
| scalac 2.13 `@nowarn` | Enable `-Xlint:unused` or `-Wunused:nowarn`; the compiler then warns `@nowarn annotation does not suppress any warnings` |
| scalafix | "Scalafix reports warnings when it encounters unused Scalafix suppressions, which you are safe to remove". With `@SuppressWarnings`, the `scalafix:` prefix is required to get these warnings |
| `-Wconf` filters | No stale-filter detection is documented in the sources read |
| Scala 3 `@nowarn` | Not read |
| sbt `evictionErrorLevel`, `libraryDependencySchemes` | No detection documented in the sources read |

## Deprecations and Replacements

- `-deprecation` shows deprecation details. In the 2.13 to 3.3 options table, `-Xlint:deprecation`
  maps to `-deprecation`; the full flag text was not read.
- `@deprecated(message, since)` is the declaration form. "A deprecation warning is issued upon
  usage." Libraries prefix `since` with their name, for example `"FooLib 12.0"`, and the compiler
  groups warnings by library and version. The `message` carries the replacement; Scala has no
  `ReplaceWith` equivalent in `@deprecated` (inference from the signature).
- Scala 3 migration: compile with `-source:3.0-migration` to get warnings, then add `-rewrite` to
  auto-fix. "The rewrites are not applied if the code compiles in error. You cannot choose which
  rules are applied." `-explain` gives more detail on errors.
- From 2.13, `-Xsource:3` gives migration warnings; 2.13.14 and later support cross-building with
  `-Xsource-features:<features>`. Guide: docs.scala-lang.org/scala3/guides/migration/
  tooling-scala2-xsource3.html.
- Scalafix rules and the migration rewrites are the automated routes; the sbt plugin is
  `"sbt-scalafix" % "0.14.9"`.
- Compiler options: docs.scala-lang.org/overviews/compiler-options/index.html. The sbt 2.x
  migration guide is at scala-sbt.org/2.x/docs/en/changes/migrating-from-sbt-1.x.html (read in a
  snippet only).

## Strict CI Form

| Goal | Form |
| --- | --- |
| Warnings fail the build | `-Werror` ("Fail the compilation if there are any warnings") |
| Unused imports, privates, locals, implicits | `-Wunused:imports,privates,locals,implicits`, which `-Xlint:unused` enables; `-Wunused:imports` warns when an import selector is not referenced |
| Stale `@nowarn` | `-Wunused:nowarn` (2.13) |
| One category fails | `-Wconf:cat=deprecation:e`; quote the argument so the shell does not expand `&` or `*` |
| Scalafix lint | Run scalafix and treat its unused-suppression warnings as findings |

Do not add `-Wconf:any:s` or `-nowarn` next to these.

## Not Verified

- Scala 3 `-Wconf` filter syntax, `-Wunused:all` semantics, and `@nowarn` semantics.
- Whether `-Xfatal-warnings` was renamed to `-Werror`, and the exact patch version that introduced
  `-Wconf` (the blog says 2.13.2).
- `sbt --warn` and sbt 2.x deprecations.
- Scalafix config keys that loosen checks.
