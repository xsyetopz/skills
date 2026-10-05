# .NET

Read when the C# compiler, a .NET analyzer, `.editorconfig`, or MSBuild reports a diagnostic. Every
form below is a suppression or a loosened check: refuse it, or ask the user first.

Versions checked on 2026-10-06:

| Tool | Version |
| --- | --- |
| .NET | 10, current GA and LTS (three years of support) |
| .NET 11 | Release candidate 1; general availability expected November 2026 |
| C# | 15 is in preview with the .NET 11 SDK; 14 is inferred to have shipped with .NET 10 |

The exact SDK patch number was not researched. Read `dotnet --version` and `global.json`.

## Contents

- [Suppression Forms to Refuse](#suppression-forms-to-refuse)
- [Config Keys That Loosen Checks](#config-keys-that-loosen-checks)
- [Stale Suppressions](#stale-suppressions)
- [Deprecations and Replacements](#deprecations-and-replacements)
- [Finding the Docs for a Code](#finding-the-docs-for-a-code)
- [Strict CI Form](#strict-ci-form)
- [Not Verified](#not-verified)

## Suppression Forms to Refuse

| Form | Effect, per the docs |
| --- | --- |
| `#pragma warning disable <list>`, `restore` | Takes effect from the next line; a bare `disable` "disables all warnings" |
| `[SuppressMessage("Usage", "CA2200:...", Justification = ...)]` | Suppresses in source, or in `GlobalSuppressions.cs` with `[assembly: ...]` and `Scope`/`Target`; the `[module: ...]` form covers compiler-generated code |
| `dotnet_diagnostic.<rule-ID>.severity = none` in `.editorconfig` | "disables the rule for your entire file or project" |
| `.globalconfig` or `is_global = true` file setting `severity = none` | Same effect, added with `<GlobalAnalyzerConfigFiles Include=... />` |
| `#nullable disable`, `disable warnings`, `disable annotations` | Turns off the nullable context; `restore` returns to the project setting |
| Null-forgiving `!` | "suppress all nullable warnings for the preceding expression"; no run-time effect |
| `<NoWarn>`, `-nowarn` | "Suppresses the specified warnings"; MSBuild also has `-noWarn:MSB3026` |

For a nullable warning, fix it with annotations such as `NotNullWhen`, which need no `!`. The
warning list (CS8600 series, CS8598) is the
`compiler-messages/nullable-warnings` page under the C# language reference.

The severity values are `error`, `warning`, `suggestion`, `silent`, `none`, and `default`. `none`
suppresses the rule completely and `silent` hides violations from the user. Docs:
<https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/configuration-options>.

## Config Keys That Loosen Checks

| Key | Loosens when |
| --- | --- |
| `dotnet_analyzer_diagnostic.category-<cat>.severity`, `dotnet_analyzer_diagnostic.severity` | Set to a lower severity; precedence is rule ID, then category, then all |
| `<Nullable>` | `disable`, `warnings`, or `annotations` instead of `enable`; unset defaults to `disable`, though .NET 6 and newer templates set `enable` (the partial values are loosening by inference) |
| `<TreatWarningsAsErrors>` | `false` |
| `<CodeAnalysisTreatWarningsAsErrors>` | `false`; it covers CAxxxx warnings only |
| `<WarningsNotAsErrors>` | Lists warnings that are not errors |
| `<WarningLevel>` | Lowered; the default matches `AnalysisLevel` since the .NET 7 SDK |
| `<AnalysisLevel>` | Pinned to an older value (`8`, `9.0`, `8-<mode>`); the docs show pinning to 8 so the default rule set does not change on upgrade |
| `<AnalysisMode>` | Set below `All`; `All` is more aggressive (the other value names were not re-verified) |
| `<EnableNETAnalyzers>` | `false`: "To disable code analysis in any project, set this property to false" |
| `<MSBuildWarningsAsMessages>`, `-warnAsMessage` | Turns warning codes into low-importance messages; defaults to `NoWarn` if set |
| `-warnNotAsError` (MSBuild 17.0+) | Excludes codes from `-warnAsError` |
| `dotnet format --severity` | Raising the threshold fixes fewer diagnostics; it fixes, not suppresses (loosening by inference) |

`dotnet format --diagnostics` narrows the scope of what is fixed. Docs for the properties:
<https://learn.microsoft.com/en-us/dotnet/core/project-sdk/msbuild-props> and
<https://learn.microsoft.com/en-us/visualstudio/msbuild/common-msbuild-project-properties>.

## Stale Suppressions

IDE0079, "Remove unnecessary suppression", "flags unnecessary pragma and `SuppressMessageAttribute`
attribute suppressions". The option `dotnet_remove_unnecessary_suppression_exclusions` defaults to
`none` (check all); `all` disables the rule, and a comma list takes IDs or `category:`. Docs:
<https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/style-rules/ide0079>.

The Microsoft docs are not explicit about whether IDE0079 runs in a build. Do not assume either:

- The IDE0079 page says: "Even if you enable code style rules on build, this rule is not enabled.
  It only surfaces in the IDE."
- The code analysis overview says to set `EnforceCodeStyleInBuild` to `true` and set each IDE
  rule's severity to `warning` or `error` in `.editorconfig`, but also says "a handful of
  code-style rules will still apply only in the Visual Studio IDE".

Test it in the repository: set `dotnet_diagnostic.IDE0079.severity = warning` (the page's example),
enable `EnforceCodeStyleInBuild`, add an unneeded `#pragma warning disable`, and see whether
`dotnet build` reports it. Report the result and do not rely on it for CI. `EnforceCodeStyleInBuild`
is off by default in builds.

Detection of a stale `!`, `#nullable disable`, `NoWarn` entry, or `.editorconfig`
`severity = none` entry was not researched. For a stale `!`, check whether the SDK has IDE0370
("Remove unnecessary suppression operator"; unverified).

## Deprecations and Replacements

- `[Obsolete("msg")]` gives warning CS0618 ("'member' is obsolete: 'text'", level 2).
  `[Obsolete("msg", true)]` gives error CS0619. Docs:
  <https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-messages/cs0618>.
- `ObsoleteAttribute` has `DiagnosticId` (the ID the compiler reports instead of CS0618),
  `UrlFormat` (a URL with the ID), and `IsError`. Docs:
  <https://learn.microsoft.com/en-us/dotnet/api/system.obsoleteattribute>.
- Platform obsoletions use IDs `SYSLIB0XXX` and `EXTOBS0XXX`, and "can't be suppressed using the
  standard diagnostic ID (CS0618)". The table at
  <https://learn.microsoft.com/en-us/dotnet/fundamentals/syslib-diagnostics/obsoletions-overview>
  names the replacement in each description. For example, SYSLIB0014 (`WebRequest`,
  `HttpWebRequest`, `ServicePoint`, `WebClient`): "Use HttpClient instead." SYSLIB0001 (UTF-7):
  "Consider using UTF-8 instead." SYSLIB0051 marks APIs for obsolete formatter-based serialization.
  Per-ID pages follow the pattern `.../syslib-diagnostics/syslib0014`.
- That page documents `#pragma warning disable SYSLIB0001` and
  `<NoWarn>$(NoWarn);SYSLIB0001</NoWarn>` as the way to suppress. Refuse them; use the
  replacement.
- Per-version breaking changes and API obsoletions:
  <https://learn.microsoft.com/en-us/dotnet/core/compatibility/breaking-changes>, and
  `.../compatibility/10.0` for .NET 10. The .NET 11 page was not researched.

## Finding the Docs for a Code

| Code | Where |
| --- | --- |
| CSxxxx | <https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-messages/>; filter by number; not every code has a page |
| CAxxxx | `https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/` then `ca2200` |
| IDExxxx | `https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/style-rules/ide0079` pattern (checked for IDE0079) |
| SYSLIBxxxx | The obsoletions table above |
| NETSDK | <https://learn.microsoft.com/en-us/dotnet/core/tools/sdk-errors/> |
| MSBxxxx | <https://learn.microsoft.com/en-us/visualstudio/msbuild/msbuild-errors> is a generic page; per-code lookup was not researched |

Rule default severities per release are in the dotnet/sdk repository (per the configuration options
page); it was not opened.

For build output, `dotnet build -bl` writes a binary log (`msbuild.binlog` by default). For
machine-readable compiler output, `<ErrorLog>compiler-diagnostics.sarif</ErrorLog>` writes SARIF;
the version argument is `1`, `2`, or `2.1`, default `1`, and `2` and `2.1` mean SARIF 2.1.0.

## Strict CI Form

- `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>` in the project or `-warnaserror`. The
  MSBuild switch is `-warnAsError[:codes]` (alias `-err`); with no values it treats all warnings as
  errors. With `-warnaserror`, code quality analysis warnings are also errors.
- Set `EnforceCodeStyleInBuild` to `true` and each IDE rule to `warning` or `error` in
  `.editorconfig`, knowing that some style rules still apply only in the IDE.
- Do not add `NoWarn`, `WarningsNotAsErrors`, `-warnNotAsError`, or `-warnAsMessage`.

## Not Verified

The research did not confirm these, so this file makes no claim about them:

- `<RunAnalyzersDuringBuild>`, `<SuppressObsoleteWarnings>` (not found in any page read), and
  `dotnet format --exclude-diagnostics`.
- The `AnalysisMode` value list, and CS0612 (obsolete without a message).
- Whether `Directory.Build.props` and `Directory.Build.targets` inherit the keys above.
- A `grep` workaround for banned suppression forms in CI is the research author's idea, not a doc.
