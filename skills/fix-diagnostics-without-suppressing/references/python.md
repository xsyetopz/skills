# Python Diagnostics

Read when ruff, pyright, basedpyright, mypy, a Python runtime warning, or pytest reports a
diagnostic. Each section gives the suppression forms to refuse, the config keys that loosen checks,
how to make the tool report unused suppressions, and where it documents replacements.

Versions checked on 2026-10-06: ruff 0.16.10, pyright 1.1.414 (the PyPI wrapper's version; the npm
package was not checked), basedpyright 1.40.2, mypy 2.4.0, pytest 9.1.1. These are the PyPI latest
on that date; check the installed version before you apply a rule below.

## Contents

- [ruff](#ruff)
- [pyright and basedpyright](#pyright-and-basedpyright)
- [mypy](#mypy)
- [Python Warnings and pytest](#python-warnings-and-pytest)

## ruff

### Suppression Forms to Refuse

| Form | Scope |
| --- | --- |
| `# noqa` | Blanket, the line. Flagged by PGH004 (`blanket-noqa`). |
| `# noqa: F841`, `# noqa: E741, F841` | The listed codes on the line. |
| `# ruff: noqa`, `# ruff: noqa: F841` | The whole file; on its own line. `# flake8: noqa` is treated as `# ruff: noqa`. |
| `# ruff: ignore[...]`, `file-ignore` forms | Line and file forms from the linter docs. |
| `# ruff: disable[E501]` ... `# ruff: enable[E501]` | A range; own-line, matching codes and indent, no blanket form. An implicit end emits RUF104. |
| `ruff check --add-noqa`, `--add-ignore` | Insert suppressions on every violating line. The docs call this useful when migrating a new codebase; it is not a fix. |

The linter page says: for a correctness issue, "you should try to fix it rather than suppressing
the error with noqa". PGH003 (`blanket-type-ignore`) flags `# type: ignore` without a code, and
RUF102 (`invalid-rule-code`, added 0.15.0) flags unknown codes in `noqa`.

### Config Keys That Loosen Checks

| Key | Effect |
| --- | --- |
| `lint.ignore` | "Ignore takes precedence over select." |
| `lint.per-file-ignores`, `lint.extend-per-file-ignores` | Drop rules for paths. |
| `lint.select` | Narrowing it drops rules (default: see Default Rules). |
| `lint.unfixable` | Stops autofixes for listed rules. |
| `exclude`, `extend-exclude`, `force-exclude`, `respect-gitignore` | Change which files are checked. |
| `preview` | Changes which rules run; see Deprecations. |
| `--exit-zero` (CLI) | Exit 0 even with diagnostics. |

`lint.extend-select` adds rules, which is the strict direction.

### Stale Suppressions

RUF100 (`unused-noqa`, added v0.0.155) reports `noqa` directives that no longer apply. Enable it
with `ruff check --extend-select RUF100`; `--fix` removes them. Caveats from the rule page: it
ignores unknown codes, and `--fix` can strip trailing comments after `# noqa`, so write
`# noqa: N802 # pylint: disable=...` with the `noqa` first.

### Deprecations and Replacements

- Deprecated Python APIs: UP035 (`deprecated-import`) flags imports deprecated for the minimum
  supported Python version, for example `from collections import Sequence` becomes
  `from collections.abc import Sequence`. `target-version` drives it. Page:
  `https://docs.astral.sh/ruff/rules/deprecated-import/`.
- Deprecated ruff rules: with preview on, deprecated rules are disabled. A deprecated rule selected
  explicitly raises an error, and one selected by category or prefix is not included
  (`https://docs.astral.sh/ruff/preview/`). The docs list no rule-code redirects, so read the error
  text and the rule page `https://docs.astral.sh/ruff/rules/<name>/`.

### Strict CI Form

`ruff check` without `--exit-zero` or `--add-noqa`, with RUF100 selected.

## pyright and basedpyright

### Suppression Forms to Refuse

| Form | Scope |
| --- | --- |
| `# type: ignore` | PEP 484; all diagnostics on the line. |
| `# pyright: ignore`, `# pyright: ignore[reportPrivateUsage, reportGeneralTypeIssues]` | The line, optionally by rule. |
| `# pyright: basic` | File level: lowers the mode for the file. |
| `# pyright: reportPrivateUsage=false` | File level: turns one rule off for the file. |
| `# pyright: reportOptionalCall=error` | File level: changes a rule's severity (loosening if it lowers). |

`# pyright: strict` at file level is the strict direction. Source:
`docs/comments.md` in the pyright repository.

### Config Keys That Loosen Checks

| Key | Effect |
| --- | --- |
| `enableTypeIgnoreComments` | Default true; does not affect `# pyright: ignore`. |
| `typeCheckingMode` | `"off"`, `"basic"`, `"standard"` (default), `"strict"`. |
| `ignore` | Paths whose diagnostics are suppressed. |
| `strict` | Paths checked strictly; removing paths loosens. |
| any `reportXxx` set to `"none"` or `false` | Disables the rule. |
| `reportMissingModuleSource` | Controls missing-stub-source reports. |

basedpyright adds `failOnWarnings` (the same as `--warnings`) and "recommended" and "all" rulesets;
"recommended" sets `failOnWarnings` true. It discourages `enableTypeIgnoreComments` in favor of
`# pyright: ignore`.

### Stale Suppressions

`reportUnnecessaryTypeIgnoreComment` reports a `# type: ignore` or `# pyright: ignore` comment that
would have no effect if removed. Its default is `"none"` in every mode, including strict, so turn
it on. basedpyright has the same rule. It also has `reportIgnoreCommentWithoutRule`, which enforces
that each ignore comment names a rule in brackets.

### Deprecations and Replacements

`reportDeprecated` reports use of a class or function marked deprecated (default `"none"`,
`"error"` in strict). `deprecateTypingAliases` (default false) reports PEP 585 aliases such as
`typing.List`. Code is marked with PEP 702 `warnings.deprecated` or
`typing_extensions.deprecated`; the message and the replacement are in its text. Docs:
`docs/configuration.md` in the pyright repository, and for basedpyright
`https://docs.basedpyright.com/latest/configuration/config-files/`. The basedpyright comments page
has a "Prefer `# pyright: ignore` comments" section.

### Strict CI Form

`typeCheckingMode: "strict"` with `reportUnnecessaryTypeIgnoreComment` on; for basedpyright also
`failOnWarnings`.

## mypy

### Suppression Forms to Refuse

| Form | Notes |
| --- | --- |
| `# type: ignore` | Blanket. |
| `# type: ignore[code]`, `# type: ignore[import,unused-ignore]` | Narrower; still a suppression, ask first. |
| `# type: ignore[deprecated]` | The docs' example for a deprecation (`old_function()  # type: ignore[deprecated]`). |

`enable_error_code = ["ignore-without-code"]` (or `# mypy: enable-error-code="ignore-without-code"`)
warns on a `# type: ignore` with no code. Ruff's PGH003 is the equivalent.

### Config Keys That Loosen Checks

`ignore_errors`, `ignore_missing_imports`, `disable_error_code`, per-module
`[[tool.mypy.overrides]]`, and `strict_optional = false`, which the docs call "evil. Avoid using
it". `--follow-imports=skip` was not verified in this research.

### Stale Suppressions

`warn_unused_ignores` (CLI `--warn-unused-ignores`) or `--enable-error-code unused-ignore` errors
on a `# type: ignore` that is not used. Both are part of `--strict`. The docs say `--strict`
"will catch type errors as long as intentional methods like type ignore or casting were not used";
its flag list "may change over time" and does not include `--warn-unreachable`.

### Deprecations and Replacements

The error code `deprecated` is opt-in: `--enable-error-code deprecated` reports use of a feature
decorated with `warnings.deprecated`. Related: `--report-deprecated-as-note`,
`--deprecated-calls-exclude`, and `# mypy: report-deprecated-as-error`. The replacement is in the
decorator message. Docs: `https://mypy.readthedocs.io/en/stable/` (error_code_list2).

### Strict CI Form

`mypy --strict` with no `ignore_errors` or `disable_error_code` entries added.

## Python Warnings and pytest

### Suppression Forms to Refuse

- `warnings.filterwarnings("ignore", ...)`, `-W ignore`, `PYTHONWARNINGS=ignore`.
- pytest: `filterwarnings = ["ignore:..."]` in config and
  `@pytest.mark.filterwarnings("ignore:...")` on a test. The docs' example of a config entry is
  `"ignore:function ham\\(\\) is deprecated:DeprecationWarning"`.

### Config Keys That Loosen Checks

Release builds of Python use these default filters: `default::DeprecationWarning:__main__`,
`ignore::DeprecationWarning`, `ignore::PendingDeprecationWarning`, `ignore::ImportWarning`, and
`ignore::ResourceWarning`. So a library's `DeprecationWarning` is hidden unless something enables
it. Absence of a warning in a plain run is not proof that the code is clean.

pytest `max_warnings` / `--max-warnings=N` (added in pytest 9.1) is a cap: exit code 6
(`MAX_WARNINGS_ERROR`) only when warnings exceed N, and filtered warnings are not counted. A
nonzero N is a loosening.

### Stale Suppressions

pytest and the `warnings` module have no unused-filter report in the sources read. Review each
`ignore` entry by deleting it and running the tests.

### Deprecations and Replacements

- `warnings.warn(message, DeprecationWarning, stacklevel=2)` raises a warning.
- `@warnings.deprecated(message, /, *, category=DeprecationWarning, stacklevel=1)` (added in Python
  3.13, PEP 702). The replacement is in the message.
- Docs: `https://docs.python.org/3/library/warnings.html`.

### Strict CI Form

| Tool | Setting |
| --- | --- |
| Python | `-Werror`, `-W error::DeprecationWarning`, or `PYTHONWARNINGS=error` (`https://docs.python.org/3/using/cmdline.html`) |
| pytest | `filterwarnings = ["error"]` turns all warnings into errors; `-W error::UserWarning` for one category |
