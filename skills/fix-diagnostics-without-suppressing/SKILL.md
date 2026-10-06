---
name: fix-diagnostics-without-suppressing
description: >-
  Fixes compiler, linter, and type-checker errors and warnings, including deprecations,
  at the cause in tsc, ESLint, ruff, pyright, clippy, clang, MSVC, Roslyn, and Swift.
  Use when a build, lint, or CI check reports warnings or errors, or an API is deprecated.
  Not for adding ignore comments.
---

# Fix Diagnostics Without Suppressing

A diagnostic is the tool telling you something about the code, so fix what it reports or move to the
replacement it names. Agents instead silence it, disable the rule, loosen the config, or weaken the
test until the check passes, and report the check as green.

## Rules

- Never suppress without asking. Ask the user before you add a suppression comment or attribute
  (`eslint-disable`, `oxlint-disable`, `biome-ignore`, `@ts-ignore`, `@ts-expect-error`, `noqa`,
  `type: ignore`, `#[allow]`, `#[expect]`, `NOLINT`, `#pragma warning`, `@Suppress`, `@nowarn`,
  `@SuppressWarnings`, `swiftlint:disable`), and before you add a baseline file.
- Never loosen the check to pass it: no rule disabled, severity lowered, `-Wno-*`, removed
  `-Werror`, raised `--max-warnings`, new ignore glob, `skipLibCheck`, `strict` off, lowered
  language mode, `ignoreDeprecations`, or changed CI flags. Never weaken, skip, or delete a test to
  make it pass.
- Every severity counts: note, info, hint, warning, error, and deprecation. A note often names the
  real cause of the error above it, so read the whole diagnostic, not only the first line.
- Fix the cause, not the symptom. A cast, `any`, `!`, `unwrap()`, an unused `_` binding, or a
  `None` check added only to quiet the tool is a suppression in another form.
- For a deprecation, find the replacement before editing. Read the deprecation message, then the
  `@deprecated`, `[Obsolete]`, `#[deprecated]`, or `@available` note on the declaration, then the
  release notes or migration guide for the installed version. Use the replacement it names. If none
  is named, report that with the sources you read and ask.
- Check the installed version, not your memory. Read the lockfile or run the tool's `--version`,
  and read the docs for that version. A flag or API you remember may be renamed, removed, or not
  yet added.
- Do not upgrade or downgrade a dependency or tool to make a diagnostic go away without asking.
- When asking to suppress, give the user the exact diagnostic, why it cannot be fixed at the cause
  (a false positive with a minimal repro, a third-party header, generated code), and the narrowest
  form: one line, one rule code, with a reason the tool records. Never a blanket or file-wide form.
- Leave existing suppressions alone unless they are in scope. Report a suppression that the tool
  marks unused or that hides a real defect.
- A repository convention that suppresses or loosens checks is not permission. Fix the diagnostic in
  touched code, name the convention with evidence, and ask before changing untouched code.

## Workflow

1. Reproduce: run the exact command that reported the diagnostic, with the repository's config, and
   save its output to a file. Record the tool and its version.
1. List each diagnostic with its rule code, severity, and `file:line`. Group by rule code, because
   one cause often produces many reports.
1. For each group, read the rule's documentation page (most tools print its URL or code) and the
   code at the location. Decide: real defect, deprecation, or false positive.
1. Fix real defects at the cause. Move deprecated uses to the replacement. For a false positive,
   build the smallest repro and ask before suppressing.
1. Rerun the same command. Report it done only when the output has no diagnostics left that you
   were asked to fix, and no new ones. Name each check you skipped and each diagnostic you left,
   with the reason.

## References

Read the reference for the tool that reported the diagnostic. Each gives the suppression forms to
refuse, the config keys that loosen checks, how the tool reports unused suppressions, and where it
documents replacements:

| Tools | Reference |
| --- | --- |
| tsc, tsgo, ESLint, Biome, oxlint | [`references/typescript.md`](references/typescript.md) |
| ruff, pyright, basedpyright, mypy, Python warnings, pytest | [`references/python.md`](references/python.md) |
| rustc, clippy, Cargo lints | [`references/rust.md`](references/rust.md) |
| GCC, Clang, MSVC, clang-tidy, clangd, CMake, xmake | [`references/c-cpp.md`](references/c-cpp.md) |
| C# compiler, .NET analyzers, `.editorconfig`, MSBuild | [`references/dotnet.md`](references/dotnet.md) |
| swiftc, Swift language modes, SwiftLint | [`references/swift.md`](references/swift.md) |
| kotlinc, Gradle, detekt, ktlint | [`references/kotlin.md`](references/kotlin.md) |
| scalac 2.13 and 3, sbt, scalafix | [`references/scala.md`](references/scala.md) |
| PCSX2 and DuckStation command lines and settings, Ghidra | [`references/emulators-and-ghidra.md`](references/emulators-and-ghidra.md) |
