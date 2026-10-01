# Changelog details

Source: [Keep a Changelog 2.0.0][kac]. The audit script checks this
profile only; it reports false errors on other formats.

## Contents

- [Layout and Unreleased](#layout-and-unreleased)
- [Release heading](#release-heading)
- [Change types](#change-types)
- [Fixed versus Changed](#fixed-versus-changed)
- [Entries for users](#entries-for-users)
- [Breaking changes](#breaking-changes)
- [Yanked releases](#yanked-releases)
- [Comparison links](#comparison-links)
- [Audit rules](#audit-rules)

## Layout and Unreleased

`## [Unreleased]` comes first and collects changes since the last
release; it may be empty right after a release. At release time rename
it to `[1.2.0] - YYYY-MM-DD`, add a new empty `## [Unreleased]` above,
and update the links. Never present unreleased changes as shipped.

## Release heading

`## [VERSION] - YYYY-MM-DD`: version in SemVer form (or the project's
scheme), ISO date, newest first. Do not renumber, redate, or delete a
published release.

## Change types

Only `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
Omit empty ones. A Security entry follows the project's disclosure
policy and leads with the CVE identifier when one exists.

## Fixed versus Changed

Fixed: the old behavior was wrong and is now correct. Changed: the old
behavior was intended and now differs. When unsure, ask whether the old
behavior was a bug. Never label an intentional behavior change a fix to
avoid a version bump.

- "Exports no longer leave `.tmp` files behind when validation fails":
  Fixed.
- "Exports now default to UTF-8 instead of the system encoding": Changed.

## Entries for users

State what changed for users (behavior, API, CLI, configuration), not the
internal work. Do not copy commit subjects; a subject is raw material.
Omit refactors, tests, and CI unless users notice them.

- Bad: "Refactor filter deserialization".
- Good: "Preserve empty search filters when reopening saved searches".

Verify each entry against its commit and the release's code
(`git show COMMIT`, `git grep` at the tag). Every entry comes from the
release range; nothing from memory. Determine the range from tags
(`git describe --tags --abbrev=0 --exclude '*-*'` for the last final
tag reachable from HEAD, then `PREV..HEAD`) and read merged PR
titles, which may describe user impact better than commits.

## Breaking changes

Mark the entry breaking and say what users must do. The replacement must
exist in the release; if no migration exists, say so rather than
invent one.

```markdown
### Removed

- **Breaking:** `GET /v1/exports` is removed. Use `GET /v2/exports`,
  which returns the same fields plus `status`.
```

## Yanked releases

A withdrawn published release keeps its section with `[YANKED]` after
the date, and the entry names the replacement:
`## [1.0.1] - 2026-08-02 [YANKED]`. A release that was never published
was never a release.

## Comparison links

Definitions at the end map each version to a tag comparison and
Unreleased to `v<latest>...HEAD`. Only link tags that exist
(`git tag -l 'v1.1.0'`).

```markdown
[Unreleased]: https://example.invalid/compare/v1.1.0...HEAD
[1.1.0]: https://example.invalid/compare/v1.0.1...v1.1.0
```

## Audit rules

`python3 scripts/audit_changelog.py FILE` reports `date-format`,
`invalid-category`, `unreleased-order`, `duplicate-version`,
`empty-version`, `empty-category`, `duplicate-category`,
`missing-unreleased`, `reverse-chronological`, `semver-format` (release
heading version), and `file-read`. It does not check that entries are
true; that is the verification above.

[kac]: https://keepachangelog.com/en/2.0.0/
