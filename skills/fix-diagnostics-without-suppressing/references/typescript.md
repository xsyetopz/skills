# TypeScript and JavaScript Diagnostics

Read when `tsc`, `tsgo`, ESLint, typescript-eslint, Biome, oxlint, or oxfmt reports a diagnostic.
Each section gives the suppression forms to refuse, the config keys that loosen checks, how to make
the tool report unused suppressions, and where it documents replacements.

Versions checked on 2026-10-06: typescript 7.0.2 (6.0 was the transition release),
@typescript/native-preview 7.0.0-dev.20260707.2, eslint 10.12.0, typescript-eslint 8.71.1,
@biomejs/biome 2.5.15, oxlint 1.87.0. These are the npm registry latest on that date; check the
installed version before you apply a rule below.

## Contents

- [tsc and tsgo](#tsc-and-tsgo)
- [ESLint and typescript-eslint](#eslint-and-typescript-eslint)
- [Biome](#biome)
- [oxlint and oxfmt](#oxlint-and-oxfmt)

## tsc and tsgo

### Suppression Forms to Refuse

| Form | Behavior |
| --- | --- |
| `// @ts-ignore` | Suppresses the next line's error and never reports that it went stale. |
| `// @ts-expect-error` | Suppresses the next line's error; reports `Unused '@ts-expect-error' directive.` once the error is gone. |
| `// @ts-nocheck` | At the top of a file, disables semantic checks for the whole file (since TS 3.7). |

Ask before adding any of them. `@ts-expect-error` is the narrowest of the three because it goes
stale loudly.

### Config Keys That Loosen Checks

| Key | Effect |
| --- | --- |
| `strict` and its family flags (`noImplicitAny`, and others) | Turning the umbrella or one family flag off removes checks. |
| `skipLibCheck` | Skips checking of all `.d.ts` files, "at the expense of type-system accuracy". |
| `noCheck` | "Disable full type checking" (added in TS 5.6). |
| `suppressExcessPropertyErrors`, `suppressImplicitAnyIndexErrors` | Removed in TS 5.5; the TS 5.0 deprecation list names them. |
| `allowJs`, `checkJs` | Leaving `checkJs` off skips checking of JavaScript files. |
| `ignoreDeprecations` | Silences option deprecations; see below. |

TS 6.0 changed defaults: `strict` is now true, `module` defaults to `esnext`, `target` defaults to
the current-year ES version (es2025), `noUncheckedSideEffectImports` is true, `libReplacement` is
false, `rootDir` defaults to `.`, and `types` defaults to `[]`. A project that relied on the old
`types` default sets `"types": ["node"]`; `["*"]` restores the 5.9 behavior. A new error after
upgrading is often one of these defaults, not a regression to silence.

### Stale Suppressions

Prefer `@ts-expect-error` over `@ts-ignore` when the user approves a suppression, because tsc
reports it when it is no longer needed. `@ts-ignore` has no staleness report; the typescript-eslint
`ban-ts-comment` rule (below) covers it.

### Deprecations and Replacements

- Option deprecations appear as config errors. `ignoreDeprecations` accepts `"5.0"` (TS 5.0 notes)
  and `"6.0"` (TS 6.0 blog) and only silences them. The 6.0 blog says TypeScript 7.0 will not
  support the deprecated options, so fix the option. The message form
  `Option 'baseUrl' is deprecated and will stop functioning in TypeScript 7.0. Specify
  compilerOption '"ignoreDeprecations": "6.0"' to silence this error` (code TS5107) comes from
  secondary sources and is unverified against a primary page.
- Deprecated in 6.0: `target: es5`, `downlevelIteration`, `moduleResolution` `node`/`node10` and
  `classic`, `module` `amd`/`umd`/`systemjs`/`none`, `baseUrl`, `esModuleInterop: false`,
  `allowSyntheticDefaultImports: false`, `alwaysStrict: false`, `outFile`, the `module` keyword for
  namespaces, `asserts` on imports (use `with`), and `/// <reference no-default-lib>`.
- TS5112 (verbatim from the 6.0 blog): `tsconfig.json is present but will not be loaded if files
  are specified on commandline. Use '--ignoreConfig' to skip this error.`
- TS 7.0 (native port, blog dated 2026-07-08) adopts the 6.0 defaults and makes every flag
  deprecated in 6.0 a hard error with no-op behavior. The blog says code that compiles cleanly with
  6.0 without `ignoreDeprecations` "should compile identically in 7.0".
  The `@typescript/typescript6` package provides `tsc6` side by side.
  Whether 7.0 still accepts `ignoreDeprecations: "6.0"` is unverified: the primary page does not
  say, and one secondary summary says it is rejected.
- Code deprecations (`/** @deprecated Use apiV2 instead. */`) show in the editor as strikethrough;
  tsc does not report them as errors. The replacement is the text of the `@deprecated` tag. Use
  `@typescript-eslint/no-deprecated` or `typescript/no-deprecated` (oxlint) to list them.

### Strict CI Form

Run `tsc` (or `tsgo`) with the repository's tsconfig and no `skipLibCheck` or
`ignoreDeprecations` added. Passing files on the command line skips the tsconfig (TS5112).

## ESLint and typescript-eslint

### Suppression Forms to Refuse

| Form | Scope |
| --- | --- |
| `/* eslint-disable */` | Rest of the file. |
| `/* eslint-enable */` | Re-enables after a block disable. |
| `// eslint-disable-line rule` | Current line. |
| `// eslint-disable-next-line rule1, rule2` | Next line. |

A description follows two or more dashes: `// eslint-disable-next-line no-console -- reason`.
Plugin rules use `plugin/rule-name`.

`@typescript-eslint/ban-ts-comment` reports the TypeScript directives. Its options are
`ts-expect-error`, `ts-ignore`, `ts-nocheck`, and `ts-check`, each `true`, `false`,
`'allow-with-description'`, or `{ descriptionFormat }`, plus `minimumDescriptionLength`. The
recommended config allows `@ts-expect-error` with a description and reports `@ts-ignore` and
`@ts-nocheck`; the strict config raises `minimumDescriptionLength` to 10. Do not relax these
options.

`@eslint-community/eslint-comments` adds rules that police the comments: `require-description`,
`no-unlimited-disable`, `disable-enable-pair`, `no-unused-enable`, `no-restricted-disable`, and
`no-use`.

### Config Keys That Loosen Checks

| Key or flag | Effect |
| --- | --- |
| `rules: { x: "off" }` or a lower severity | Disables or downgrades a rule. |
| `ignores` (global ignore objects) | Removes files from linting. |
| `linterOptions.noInlineConfig` | `true` disables all inline config comments; it also blocks the narrow comments. CLI: `--no-inline-config`. |
| `--max-warnings N` | Exits nonzero only when warnings exceed N. |
| `--quiet` | Hides warnings. |
| `linterOptions.reportUnusedDisableDirectives` set to `"off"` | Hides stale suppressions. |

### Stale Suppressions

Set `linterOptions: { reportUnusedDisableDirectives: "error" }` in the flat config. The setting
defaults to `"warn"`. The CLI has `--report-unused-disable-directives` and
`--report-unused-disable-directives-severity` (`off`, `warn`, `error`, `0`, `1`, `2`). Related:
`linterOptions.reportUnusedInlineConfigs` and `--report-unused-inline-configs` (default `"off"`).

### Deprecations and Replacements

`@typescript-eslint/no-deprecated` ("Disallow using code marked as @deprecated") needs type
information and is enabled by `strict-type-checked`. Its message carries the `@deprecated` text,
for example `'parse' is deprecated. Use the WHATWG URL API instead.` The replacement is in that
text. Rule pages are at `https://typescript-eslint.io/rules/<rule>`.

### Strict CI Form

`eslint --max-warnings 0` with `reportUnusedDisableDirectives: "error"`.

## Biome

### Suppression Forms to Refuse

| Form | Scope |
| --- | --- |
| `// biome-ignore lint/suspicious/noDebugger: <explanation>` | Next node. Categories: `lint`, `assist`, `syntax`; group and rule are optional. |
| `// biome-ignore-all lint/...: reason` | Whole file; must be at the top of the file. |
| `// biome-ignore-start ...` and `// biome-ignore-end ...` | A range; each start needs an end. |

Plugin rules use `lint/plugin` or `lint/plugin/<name>`. The docs show an explanation as part of the
syntax; whether a missing explanation is an error was not verified.

### Config Keys That Loosen Checks

`linter.enabled`, `linter.includes`, `files.includes`, `linter.rules.recommended`,
`linter.rules.<group>.<rule>` set to `"off"`, `"info"`, or `"warn"` (values are `"off"`, `"on"`,
`"info"`, `"warn"`, `"error"`), and `overrides`. CLI:
`--diagnostic-level=<info|warn|error>` sets the level shown.

### Stale Suppressions

The docs state one case: a top-level suppression comment that is not at the top of the file is
unused, and Biome emits a diagnostic with category `suppression/unused`. No separate rule page
exists (`no-unused-suppressions` is a 404), and the exact text for an unused inline `biome-ignore`
was not read.

### Deprecations and Replacements

`lint/suspicious/noDeprecatedImports` (since v2.2.5, not recommended, default severity warning,
project domain) restricts imports of exports with an `@deprecated` annotation. Its page is
`https://biomejs.dev/linter/rules/no-deprecated-imports/`. The replacement is in the `@deprecated`
text.

### Strict CI Form

`--error-on-warnings` makes Biome exit nonzero on warnings. `--max-diagnostics` is not a gate.

## oxlint and oxfmt

### Suppression Forms to Refuse

| Form | Scope |
| --- | --- |
| `/* oxlint-disable [rules] */` | Rest of the file. |
| `/* oxlint-enable [rules] */` | Ends a block disable. |
| `// oxlint-disable-line rule` | Current line. |
| `// oxlint-disable-next-line rule1, rule2` | Next line. |
| `eslint-*` forms | Also honored "for compatibility". |
| `// oxfmt-ignore` | oxfmt skips the next statement; `prettier-ignore` is also honored for other files. |

Rule options cannot be changed inline. The ignore-comments page documents no description syntax.

### Config Keys That Loosen Checks

| Key or flag | Effect |
| --- | --- |
| `categories`, `overrides[n].rules` | Turn rules or categories off or down. |
| `ignorePatterns`, `--no-ignore` | Change which files are linted. |
| `options.respectEslintDisableDirectives` | Default true; root config only. |
| `options.maxWarnings`, `--max-warnings=INT` | Allow up to INT warnings. |
| `-A/--allow`, `-W/--warn`, `--quiet` | Lower severities or hide warnings. |
| `--disable-nested-config` | Ignores nested configs. |

`options.denyWarnings` and `--deny-warnings` are the strict direction, as are `options.typeAware`
and `options.typeCheck`. `--fix-dangerously` is not a loosening key but rewrites code; ask first.

### Stale Suppressions

Reporting unused ignore comments is off by default. Use
`oxlint --report-unused-disable-directives` or `--report-unused-disable-directives-severity error`,
or set `"options": { "reportUnusedDisableDirectives": "error" }` (values `allow`, `off`, `warn`,
`error`, `deny`, or an integer; root config only; the CLI wins).

### Deprecations and Replacements

`typescript/no-deprecated` (pedantic, type-aware) flags code marked `@deprecated`; the replacement
is in the tag text. Type-aware linting needs `npm add -D oxlint-tsgolint@latest` and
`oxlint --type-aware`. It is powered by typescript-go and requires TypeScript 7.0+. The docs say
options deprecated in 6.0 and removed in 7.0 must be migrated first, and name a `ts5to6` tool that
upgrades the tsconfig. `--type-check` (experimental) reports TypeScript errors with lint results.
Pages: `https://oxc.rs/docs/guide/usage/linter/type-aware.html` and
`https://oxc.rs/docs/guide/usage/linter/rules/typescript/no-deprecated.html`.

### Strict CI Form

`oxlint --deny-warnings` (or `--max-warnings=0`) with the unused-directive report on. oxfmt is a
formatter with no lint diagnostics; its CI form is `oxfmt --check`. No suppression docs were found
for the other oxc tools (parser, transformer, minifier, resolver).
