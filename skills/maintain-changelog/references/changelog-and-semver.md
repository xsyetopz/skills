# Changelogs, release notes, and version decisions

## Establish the contract

Inspect the existing changelog, public API, version policy, release tags, and
release automation before writing. Default to
[Keep a Changelog 2.0.0](https://keepachangelog.com/en/2.0.0/) for a requested
changelog normalization or a new changelog. It is a human-oriented convention,
not a universal machine schema. Do not run its profile checker on arbitrary
release notes or silently replace a required project format.

Use [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html) only when
the project adopts SemVer. Do not convert published CalVer or other identifiers
to SemVer. Establish which behavior is public before proposing a version bump:
source compatibility alone does not prove behavioral or wire compatibility.

## Changelog edits

Put Unreleased first; it may be empty immediately after a release. Follow with
releases in reverse date order. Preserve existing published identifiers and
`YYYY-MM-DD` dates. Same-day releases are possible; do not guess their order
from dates alone. Do not sort historical maintenance releases by SemVer
precedence instead of publication chronology.

Group changes under applicable Added, Changed, Deprecated, Removed, Fixed, and
Security headings. Omit empty categories. Keep withdrawn releases and their
`[YANKED]` marker. Link versions to verified comparisons or tags. A reference to
a commit can support a useful entry; a hash alone is not evidence that the
changelog is a raw commit dump.

Describe user-visible consequences rather than implementation activity. For
example, "Preserve empty search filters when reopening saved searches" tells a
user more than "Refactor filter deserialization." Preserve deprecation notices,
removal consequences, and migration steps. Do not invent a migration flag or
replacement API: verify it in the relevant release's code or documentation.

## SemVer decisions

For a stable public API, incompatible changes require a major increment,
compatible functionality a minor increment, and compatible fixes a patch
increment. Deprecating public functionality also requires a minor increment.
`0.y.z` is initial development, not an assurance of compatibility. Follow the
project's documented pre-1.0 policy rather than assuming a patch is safe.

Prereleases have lower precedence than the corresponding normal release. Numeric
prerelease identifiers compare numerically; build metadata does not change
precedence. A tag's `v` prefix is not part of SemVer. Syntax validation cannot
establish the correct bump, release ordering, or compatibility.

Never renumber an already published release to repair a version decision.
Correct the release notes and plan the next release according to the actual
public impact. Distinguish a release's tag, artifact version, publication date,
and prerelease channel; they are separate facts.

## Release notes

Use the agreed release range, source changes, issues, and observed behavior.
Explain affected users, the before-and-after behavior, compatibility impact, and
required upgrade steps. Mark facts that remain unverified. Do not present
unreleased changes as shipped or equate merging a pull request with publishing
an artifact. Writing notes does not authorize tagging, uploading, or publishing.

Use the [validator contracts](validator-contracts.md) only for the matching
format. Review links, completeness, release facts, and API impact separately;
the scripts cannot establish them.
