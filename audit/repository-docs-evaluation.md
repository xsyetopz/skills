# Repository documentation evaluation

Evaluated 2026-09-12. Integrated explicit-only `maintain-repository-docs` with
README/contribution guidance and one substantive structure/validation reference.
Retirement of the old umbrella package remains coupled to pending governance
integration; this result does not accept its unaudited material.

## Guidance and sources

Added reader-task distinctions from [Diátaxis](https://diataxis.fr/) without
requiring four directories or a new documentation framework. API reference uses
the actual source/specification and existing generator. ADRs preserve real
context and decisions rather than inventing schema versions or approvals.

Rechecked GitHub's [README rendering][readme] and [diagram support][diagrams].
Guidance distinguishes local paths, rendered fragments, public target content,
and private/offline link limits. Mermaid compatibility depends on the target
renderer; syntax checks do not establish rendering or accessibility.

Procedures now distinguish runtime behavior from Markdown validity, commands
from transcripts, and end-user installation from contributor builds. Destructive
publication examples are not executed merely to validate prose. Existing project
tooling remains authoritative; no formatter, site generator, parser, or new
production dependency was introduced.

## Independent forward task

A fresh-context evaluator received a source-only Python CSV command and a README
with unsupported input/output flags, a false report-file claim, and an invented
field-validation guarantee. The task authorized documentation changes only.

The evaluator inspected the real argparse/stdin/stdout contract, replaced the
procedure with a copyable pipeline, supplied its observed JSON output, and
removed unsupported claims without changing the application. It tested the
semicolon delimiter and the rejected old flag. The intended Python 3.10+ support
range stayed distinct from the actual tested interpreter, Python 3.14.7.

Review of the isolated diff confirms only README changed. Source and task
contract remained byte-identical. No release artifact, new dependencies, CI
policy, or governance rules were invented. The fixture's parser counts records;
this is not evidence of general CSV validation.

## Validation and limits

The package passes official skills-ref, the bundled quick validator, strict
Markdown, metadata assertions, and local-link checks. The forward task ran the
actual documented CLI, an alternative delimiter, and an unsupported-flag
failure. It did not test other Python versions, platforms, hosted rendering, or
live CI. The new guidance does not claim an executable API-doc generator or
rendered Mermaid fixture: those are task-specific procedures, not supplied
starter assets.

Raw report: `/tmp/repository-docs-forward-result.md`. Evaluated output:
`/tmp/repository-docs-work.nsMocS`. Both remain outside the repository.

[readme]:
  https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
[diagrams]:
  https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams
