# Tool thresholds

Default limits of common linters for the size, complexity, coupling, and
duplication checks behind the smells in the [catalog](smell-catalog.md).
A default is the tool author's choice, not a measure of quality. Tools
disagree by a factor of ten on the same idea (method length: RuboCop 10
lines, Checkstyle 150). Quote the tool, the rule, and the value when a
report uses one, and prefer the repository's configured value over any
number here.

## Contents

- [How to use a threshold](#how-to-use-a-threshold)
- [Functions and methods](#functions-and-methods)
- [Parameters](#parameters)
- [Classes, types, and files](#classes-types-and-files)
- [Coupling](#coupling)
- [Duplicated code](#duplicated-code)
- [Sources](#sources)

## How to use a threshold

1. Read the repository's linter configuration first. A configured value
   is the team's choice and wins.
1. With no configuration, run the language's linter with its defaults and
   report what it prints, naming the rule and the default.
1. A value over the default is a lead, not a verdict. Read the code and
   name the smell it points to, or drop it with the reason (a generated
   parser, a flat table of cases, a state machine that reads best as one
   `match`).
1. Do not mix thresholds across tools in one report. "Complexity 14" from
   ESLint and from Ruff can mean different things, because each tool
   counts slightly differently.

Cyclomatic complexity counts independent paths through a function.
Cognitive Complexity (SonarSource) instead weights nesting and breaks in
linear flow, and aims to "produce a measurement that more accurately
reflects the relative difficulty of understanding, and therefore of
maintaining methods, classes, and applications" ([whitepaper][cognitive]).

## Functions and methods

| Tool | Rule | Default |
| --- | --- | --- |
| ESLint | [`complexity`][eslint-complexity] | 20 |
| ESLint | [`max-depth`][eslint-max-depth] | 4 |
| ESLint | [`max-statements`][eslint-max-statements] | 10 |
| ESLint | [`max-nested-callbacks`][eslint-max-nested-callbacks] | 10 |
| ESLint | [`max-lines-per-function`][eslint-max-lines-per-function] | 50 |
| Pylint | [`max-branches`][pylint] | 12 |
| Pylint | [`max-statements`][pylint] | 50 |
| Pylint | [`max-returns`][pylint] | 6 |
| Pylint | [`max-nested-blocks`][pylint] | 5 |
| Pylint | [`max-locals`][pylint] | 15 |
| Ruff | [`lint.mccabe.max-complexity`][ruff-settings] (C901) | 10 |
| Clippy | [`cognitive-complexity-threshold`][clippy-config] | 25 (lint in the `restriction` group, off by default) |
| Clippy | [`too-many-lines-threshold`][clippy-config] | 100 |
| golangci-lint | [`gocyclo`][golangci] | 30 |
| golangci-lint | [`gocognit`][golangci] | 30 (the reference file adds "but we recommend 10-20") |
| golangci-lint | [`funlen`][golangci] | 60 lines, 40 statements |
| golangci-lint | [`nestif`][golangci] | 5 |
| Checkstyle | [`CyclomaticComplexity`][checkstyle-cyclomatic] | 10 |
| Checkstyle | [`NPathComplexity`][checkstyle-npath] | 200 |
| Checkstyle | [`MethodLength`][checkstyle-method-length] | 150 |
| PMD (Java) | [`CyclomaticComplexity`][pmd-design] | 10 per method, 80 per class |
| PMD (Java) | [`CognitiveComplexity`][pmd-design] | 15 |
| detekt | [`LongMethod`][detekt] | 60 |
| detekt | [`CyclomaticComplexMethod`][detekt] | 14 |
| SwiftLint | [`cyclomatic_complexity`][swiftlint] | warning 10, error 20 |
| SwiftLint | [`function_body_length`][swiftlint] | warning 50, error 100 |
| RuboCop | [`Metrics/MethodLength`][rubocop] | 10 |
| RuboCop | [`Metrics/AbcSize`][rubocop] | 17 |
| RuboCop | [`Metrics/CyclomaticComplexity`][rubocop] | 7 |
| RuboCop | [`Metrics/PerceivedComplexity`][rubocop] | 8 |

## Parameters

| Tool | Rule | Default |
| --- | --- | --- |
| ESLint | [`max-params`][eslint-max-params] | 3 |
| Pylint | [`max-args`][pylint], `max-positional-arguments` | 5, 5 |
| Ruff | [`max-args`][ruff-args] (PLR0913) | 5 |
| Clippy | [`too-many-arguments-threshold`][clippy-config] | 7 |
| Checkstyle | [`ParameterNumber`][checkstyle-parameters] | 7 |
| PMD (Java) | [`ExcessiveParameterList`][pmd-design] | 10 |
| detekt | [`LongParameterList`][detekt] | 5 for functions, 6 for constructors |
| SwiftLint | [`function_parameter_count`][swiftlint] | warning 5, error 8 |
| RuboCop | [`Metrics/ParameterLists`][rubocop] | 5 (optional parameters: 3) |

## Classes, types, and files

| Tool | Rule | Default |
| --- | --- | --- |
| ESLint | [`max-lines`][eslint-max-lines] | 300 per file (blank and comment lines count unless skipped) |
| Pylint | [`max-module-lines`][pylint] | 1000 |
| Pylint | [`max-attributes`][pylint] | 7 |
| Pylint | [`max-public-methods`][pylint] | 20 |
| Clippy | [`type-complexity-threshold`][clippy-config] | 250 |
| Clippy | [`enum-variant-size-threshold`][clippy-config] | 200 (bytes) |
| Checkstyle | [`FileLength`][checkstyle-file-length] | 2000 |
| detekt | [`LargeClass`][detekt] | 600 lines |
| detekt | [`TooManyFunctions`][detekt] | 11 per file, class, or object |
| SwiftLint | [`type_body_length`][swiftlint] | warning 250, error 350 |
| SwiftLint | [`file_length`][swiftlint-file-length] | warning 400, error 1000 |
| RuboCop | [`Metrics/ClassLength`][rubocop] | 100 |

PMD also has `GodClass`, which its documentation describes as a class
with high WMC (weighted method count), high ATFD (access to foreign
data), and low TCC (tight class cohesion). Read its cutoffs in the PMD
rule source before quoting them.

## Coupling

| Tool | Rule | Default |
| --- | --- | --- |
| Checkstyle | [`ClassDataAbstractionCoupling`][checkstyle-cdac] | 7 |
| Checkstyle | [`ClassFanOutComplexity`][checkstyle-fanout] | 20 |
| PMD (Java) | [`CouplingBetweenObjects`][pmd-design] | 20 |

Change coupling from history has its own thresholds; see
[change coupling](change-coupling.md#run-the-coupling-scan).

## Duplicated code

| Tool | Setting | Default |
| --- | --- | --- |
| Pylint | [`min-similarity-lines`][pylint] (R0801) | 4 |
| golangci-lint | [`dupl`][golangci] `threshold` | 150 tokens |
| PMD CPD | [`--minimum-tokens`][cpd] | none; the option is required |
| jscpd (Rust edition) | [`--min-tokens`, `--min-lines`][jscpd-rust] | 50 tokens, 5 lines |

CPD makes the caller choose a size. Start near the jscpd or `dupl`
values and report the value used.

## Sources

Each value above was read from the linked page or configuration file.
Linters change defaults between major versions: record the tool version
in the report and check its own documentation when it differs.

[cognitive]: https://www.sonarsource.com/docs/CognitiveComplexity.pdf
[eslint-complexity]: https://eslint.org/docs/latest/rules/complexity
[eslint-max-depth]: https://eslint.org/docs/latest/rules/max-depth
[eslint-max-statements]: https://eslint.org/docs/latest/rules/max-statements
[eslint-max-nested-callbacks]: https://eslint.org/docs/latest/rules/max-nested-callbacks
[eslint-max-lines-per-function]: https://eslint.org/docs/latest/rules/max-lines-per-function
[eslint-max-params]: https://eslint.org/docs/latest/rules/max-params
[eslint-max-lines]: https://eslint.org/docs/latest/rules/max-lines
[pylint]: https://pylint.readthedocs.io/en/stable/user_guide/configuration/all-options.html
[ruff-settings]: https://docs.astral.sh/ruff/settings/
[ruff-args]: https://docs.astral.sh/ruff/rules/too-many-arguments/
[clippy-config]: https://github.com/rust-lang/rust-clippy/blob/master/book/src/lint_configuration.md
[golangci]: https://github.com/golangci/golangci-lint/blob/main/.golangci.reference.yml
[checkstyle-cyclomatic]: https://checkstyle.org/checks/metrics/cyclomaticcomplexity.html
[checkstyle-npath]: https://checkstyle.org/checks/metrics/npathcomplexity.html
[checkstyle-method-length]: https://checkstyle.org/checks/sizes/methodlength.html
[checkstyle-parameters]: https://checkstyle.org/checks/sizes/parameternumber.html
[checkstyle-file-length]: https://checkstyle.org/checks/sizes/filelength.html
[checkstyle-cdac]: https://checkstyle.org/checks/metrics/classdataabstractioncoupling.html
[checkstyle-fanout]: https://checkstyle.org/checks/metrics/classfanoutcomplexity.html
[pmd-design]: https://docs.pmd-code.org/latest/pmd_rules_java_design.html
[cpd]: https://docs.pmd-code.org/latest/pmd_userdocs_cpd.html
[detekt]: https://github.com/detekt/detekt/blob/main/detekt-core/src/main/resources/default-detekt-config.yml
[swiftlint]: https://realm.github.io/SwiftLint/
[swiftlint-file-length]: https://realm.github.io/SwiftLint/file_length.html
[rubocop]: https://github.com/rubocop/rubocop/blob/master/config/default.yml
[jscpd-rust]: https://github.com/kucherenko/jscpd/blob/master/rust/jscpd/README.md
