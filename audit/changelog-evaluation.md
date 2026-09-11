# Changelog capability evaluation

Evaluated 2026-09-11. This evidence covers `maintain-changelog`, not the
remaining repository-documentation capabilities or the full skill suite.

## Boundary and sources

Changelog maintenance, release-note drafting, and version-impact reasoning share
release facts and compatibility evidence. They remain one capability. Hosted
publication and Git tagging remain separate authorization/workflow boundaries.
Five tiny references, including a router-only file, became two references:
release decisions and executable checker contracts. Existing explicit-only
OpenAI invocation policy was preserved, not silently changed.

Verified primary sources:

- [Keep a Changelog 2.0.0](https://keepachangelog.com/en/2.0.0/) is published
  June 7, 2026. The initial guidance incorrectly treated 1.1.0 as current. The
  2.0.0 page says the familiar categories, dates, and markers remain compatible;
  its guidance and anchors changed. The GitHub tags endpoint still showed v1.1.2
  first during this check; tag listing alone did not establish the current
  published convention. The skill now links the actual 2.0.0 page.
- [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html): version grammar, explicit
  public API, deprecation, prerelease precedence, and build metadata. The
  checker uses the published regex with ASCII and whole-string matching. It does
  not implement or claim precedence sorting or compatibility analysis.
- [markdown-it-py token API][source-1]:
  CommonMark headings, nested tokens, inline links, and source maps. Version
  4.2.0 was resolved and executed; this parser replaces source-line Markdown
  parsing in both helpers.
- [uv script environments](https://docs.astral.sh/uv/guides/scripts/): declared
  inline dependencies and isolated execution. No target-project dependency or
  root orchestration configuration was introduced.

The checker is explicitly a bounded Keep a Changelog + SemVer profile, not an
implementation of a universal changelog schema. CalVer and project-mandated
formats must not be silently rewritten to pass it. No invented version field,
parser framework, or precedence algorithm was introduced.

## Observed defects and regression evidence

New behavior tests were run before the parser/checker repair: 16 subcases failed
across 12 test methods. Reproduced defects included:

- empty Unreleased incorrectly rejected;
- empty categories accepted as entries;
- malformed version/date headings silently skipped;
- duplicate releases and misplaced Unreleased not reported;
- Markdown code examples incorrectly treated as release history;
- inline-linked/plain/Setext release headings not recognized correctly.

The repair uses parsed top-level sections, validates all release labels, and
checks actual section content. Further tests cover nested subsections and repeat
categories. A 5,000-digit version component now validates without Python's
integer-conversion limit; JSON numeric components are documented as decimal
strings rather than potentially overflowing numbers.

Removed unreliable claims that a commit hash proves a commit-log dump, an
attribution is mandatory, or a category heading proves an entry exists. File
errors are structured changelog findings; SemVer source failures retain stderr
and nonzero status without partial JSON. Both output modes retain error exit
status behavior.

## Executed validation

- 13 unittest methods passed on Python 3.14 and the declared minimum Python
  3.10, with markdown-it-py 4.2.0. Tests execute real CLIs and isolated Git
  repos.
- Ruff check and formatter check passed on all four Python files.
- Mypy strict passed on the three production Python modules; tests were not
  included in this type-check claim.
- Official skills-ref validation and bundled quick validation passed.
- Existing Markdown configuration passed on all three skill Markdown files.
- Current upstream Keep a Changelog `main/CHANGELOG.md` was downloaded and
  audited through the documented `uv run` command: 16 releases, no findings,
  exit 0. This is a compatibility smoke test, not a substitute for negative
  tests. Snapshot SHA-256:
  `663c710db14ea1168045f260b2bd4f9f8944f19fe6ece78bc52e1a46ef3243d9`.

The tests do not verify historical release completeness, remote links, published
artifacts, or the actual compatibility impact of arbitrary project changes.
Those remain evidence-driven review responsibilities stated in the skill.

## Independent forward task and activation

An independent reviewer received the skill and raw synthetic release facts, not
an intended edit or validator diagnosis. In disposable workspace
`/tmp/maintain-changelog-eval.Qb8ShZ/release`, it prepared a 1.4.1 patch
changelog and release notes for the saved-search filter fix. It retained 1.4.0
history, left Unreleased empty, and did not fabricate new tag/comparison
verification or perform publication. The coordinator inspected both artifacts.
The reviewer ran both helpers on the edited file and candidate version, plus the
13-method test suite: all passed. It removed the stale Unreleased comparison
pending verification of the new release ref; this unresolved link was explicitly
noted in the release notes rather than represented as validated.

Seven metadata-only activation cases respected the existing explicit-only
policy:

- Direct `$maintain-changelog update CHANGELOG.md`: activate.
- Paraphrase `record the last release changes`: no implicit activation.
- Incomplete `fix the changelog`: no implicit activation.
- Neighbor `publish this GitHub release`: inactive, also outside scope.
- Negative `fix search filter runtime code`: inactive.
- Ambiguous `release this`: inactive.
- Composition `$maintain-changelog draft notes and publish them when approved`:
  activate for drafting only; publication remains a separate workflow.

This verifies routing consistency with current metadata, not evidence that
explicit-only is the best collection-wide discovery policy. That policy remains
part of the full catalog integration audit. No concrete functional defect was
observed in this forward task; the automated defect tests above cover different
failure paths.

[source-1]: https://markdown-it-py.readthedocs.io/en/latest/using.html
